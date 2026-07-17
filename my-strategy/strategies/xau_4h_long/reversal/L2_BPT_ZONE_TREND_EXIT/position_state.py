#!/usr/bin/env python3
"""L2/BPT — state-machine de POSIÇÕES (alert-only, FASE 2 runtime).

Posições MÚLTIPLAS concorrentes; nenhuma ordem real — só rastreio p/ alertas de saída.
Estado: .runtime_state/l2_positions.json (write atómico tmp+os.replace).
Journal: .runtime_state/l2_events.jsonl (append-only; nunca reescrito).

Regras de fecho POR BARRA FECHADA (ordem STOP-FIRST, verbatim do motor
l2_engine.regime_flip / l2_bpt_trailing_exit_test.py:31-35):
  1. L[j] <= sl                      -> CLOSED(STOP)        R = -1.0 - COST
  2. rótulo de regime da barra == BEAR -> CLOSED(REGIME_FLIP) R = (C[j]-entry)/risk - COST
  3. bars_held >= CAP (500)          -> CLOSED(CAP)         R = (C[j]-entry)/risk - COST
R arredondado 2dp (paridade research, COST=0.35). risk = entry - sl (como no R_of do motor).

Catch-up determinístico: processa TODAS as barras fechadas entre last_processed_bar_time
e a última; eventos atrasados levam late_bars>0 (timestamp honesto: bar_time = barra do
evento; detected_at = agora). Gap descontínuo (last_processed não está no ledger) -> HARD_STOP.

py3.9 stdlib. Módulo PURO (sem MCP): o runtime injeta barras+rótulos de regime.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

COST = 0.35   # paridade research (l2_engine.COST)
CAP = 500     # paridade research (l2_engine.CAP)

HERE = Path(__file__).resolve().parent
STATE_DIR = HERE / ".runtime_state"
POSITIONS_PATH = STATE_DIR / "l2_positions.json"
EVENTS_PATH = STATE_DIR / "l2_events.jsonl"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def empty_state():
    return {"last_processed_bar_time": None, "positions": [], "updated_at": None}


def load_state(path=POSITIONS_PATH):
    p = Path(path)
    if not p.exists():
        return empty_state()
    return json.loads(p.read_text())


def save_state(state, path=POSITIONS_PATH):
    """Write atómico tmp+os.replace (nunca estado meio-escrito)."""
    p = Path(path)
    p.parent.mkdir(exist_ok=True)
    state = dict(state, updated_at=_now_iso())
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    os.replace(tmp, p)
    return state


def append_event(ev, path=EVENTS_PATH):
    p = Path(path)
    p.parent.mkdir(exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def open_positions(state):
    return [x for x in state["positions"] if x["status"] == "OPEN"]


def has_signal(state, signal_hash):
    return any(x.get("signal_hash") == signal_hash for x in state["positions"])


def open_position(state, cand, journal_path=EVENTS_PATH):
    """Abre posição advisory a partir de um ENTRY candidate do scanner.
    cand: {signal_hash, bar_time, ledger_idx, entry, sl, risk, sl_type, regime, zona, ...}.
    Dedup por signal_hash (idempotente em re-corridas). Devolve (pos|None, event|None)."""
    if has_signal(state, cand["signal_hash"]):
        return None, None
    pos = {
        "id": f"L2-{cand['bar_time']}",
        "signal_hash": cand["signal_hash"],
        "status": "OPEN",
        "entry_bar_time": cand["bar_time"],
        "entry_idx": cand["ledger_idx"],          # índice no ledger (append-only -> estável)
        "entry": cand["entry"], "sl": cand["sl"], "risk": cand["risk"],
        "sl_type": cand.get("sl_type"), "regime": cand.get("regime"),
        "zona": cand.get("zona"), "tipo": cand.get("tipo"), "source": cand.get("source"),
        "late_bars_at_open": cand.get("late_bars", 0),
        "opened_at": _now_iso(),
    }
    state["positions"].append(pos)
    ev = {"type": "OPEN", "bar_time": pos["entry_bar_time"], "signal_hash": pos["signal_hash"],
          "entry": pos["entry"], "sl": pos["sl"], "risk": pos["risk"],
          "regime": pos.get("regime"), "late_bars": pos["late_bars_at_open"],
          "detected_at": pos["opened_at"]}
    append_event(ev, journal_path)
    return pos, ev


def _close(pos, mot, R, bar_time, bar_idx, late_bars, journal_path):
    pos["status"] = "CLOSED"
    pos["closed"] = {"mot": mot, "R": R, "bar_time": bar_time, "bar_idx": bar_idx,
                     "late_bars": late_bars, "closed_at": _now_iso()}
    ev = {"type": "CLOSE", "mot": mot, "R": R, "bar_time": bar_time,
          "signal_hash": pos["signal_hash"], "entry": pos["entry"], "sl": pos["sl"],
          "hold": bar_idx - pos["entry_idx"], "late_bars": late_bars,
          "detected_at": pos["closed"]["closed_at"]}
    append_event(ev, journal_path)
    return ev


def process_closed_bar(state, j, bar, regime_label, latest_idx, journal_path=EVENTS_PATH):
    """Aplica a barra fechada j (bar={'t','o','h','l','c'}, regime_label=rótulo dessa barra)
    a todas as posições OPEN. Ordem STOP-FIRST verbatim. late_bars = latest_idx - j.
    Devolve lista de eventos CLOSE."""
    events = []
    late = max(0, latest_idx - j)
    for pos in open_positions(state):
        if j <= pos["entry_idx"]:
            continue                          # motor começa a avaliar em bi+1
        risk = pos["entry"] - pos["sl"]       # fonte: l2_engine.R_of (entry - sl)
        if bar["l"] <= pos["sl"]:
            events.append(_close(pos, "STOP", round(-1.0 - COST, 2),
                                 bar["t"], j, late, journal_path))
            continue
        if regime_label == "BEAR":
            R = round((bar["c"] - pos["entry"]) / risk - COST, 2)
            events.append(_close(pos, "REGIME_FLIP", R, bar["t"], j, late, journal_path))
            continue
        if j - pos["entry_idx"] >= CAP:
            R = round((bar["c"] - pos["entry"]) / risk - COST, 2)
            events.append(_close(pos, "CAP", R, bar["t"], j, late, journal_path))
    return events


def check_continuity(state, ledger_T):
    """Gap descontínuo -> HARD_STOP. last_processed precisa existir no ledger (ou ser None
    = primeiro ciclo, inicialização a cargo do runtime SEM varrer o passado)."""
    lp = state.get("last_processed_bar_time")
    if lp is None:
        return True, "first_cycle"
    if lp not in set(ledger_T):
        return False, f"last_processed_bar_time {lp} não está no ledger (gap descontínuo)"
    return True, "ok"


# ---------------------------------------------------------------------
# SELFTEST sintético (offline): STOP-first vs REGIME_FLIP; CAP; catch-up multi-barra LATE.
# ---------------------------------------------------------------------
def _selftest():
    import tempfile
    tmpd = Path(tempfile.mkdtemp(prefix="l2_pos_selftest_"))
    jpath = tmpd / "events.jsonl"
    fails = []

    def bar(t, o, h, l, c):
        return {"t": t, "o": o, "h": h, "l": l, "c": c}

    # T1: STOP e REGIME_FLIP na MESMA barra -> STOP ganha (ordem stop-first)
    st = empty_state()
    cand = {"signal_hash": "t1", "bar_time": 1000, "ledger_idx": 10,
            "entry": 100.0, "sl": 95.0, "risk": 5.0, "regime": "RANGE"}
    open_position(st, cand, jpath)
    evs = process_closed_bar(st, 11, bar(1014, 99, 99, 94.0, 98.0), "BEAR", 11, jpath)
    if not (len(evs) == 1 and evs[0]["mot"] == "STOP" and evs[0]["R"] == -1.35):
        fails.append(f"T1 stop-first: {evs}")

    # T2: REGIME_FLIP fecha em C[j] com R=(C-entry)/risk-COST
    st = empty_state()
    open_position(st, dict(cand, signal_hash="t2"), jpath)
    evs = process_closed_bar(st, 12, bar(1028, 101, 112, 100.5, 110.0), "BEAR", 12, jpath)
    expR = round((110.0 - 100.0) / 5.0 - COST, 2)   # 1.65
    if not (len(evs) == 1 and evs[0]["mot"] == "REGIME_FLIP" and evs[0]["R"] == expR):
        fails.append(f"T2 flip: {evs} exp R={expR}")

    # T3: CAP em bars_held>=500 (sem stop/flip)
    st = empty_state()
    open_position(st, dict(cand, signal_hash="t3"), jpath)
    evs = process_closed_bar(st, 10 + CAP, bar(9000, 103, 104, 102, 103.5), "BULL", 10 + CAP, jpath)
    expR = round((103.5 - 100.0) / 5.0 - COST, 2)
    if not (len(evs) == 1 and evs[0]["mot"] == "CAP" and evs[0]["R"] == expR):
        fails.append(f"T3 cap: {evs} exp R={expR}")

    # T4: catch-up multi-barra: barra intermédia fecha com late_bars>0; posição 2 sobrevive
    st = empty_state()
    open_position(st, dict(cand, signal_hash="t4a"), jpath)                       # stopa na j=11
    open_position(st, {"signal_hash": "t4b", "bar_time": 1001, "ledger_idx": 10,
                       "entry": 100.0, "sl": 90.0, "risk": 10.0, "regime": "RANGE"}, jpath)
    all_evs = []
    seq = [(11, bar(1014, 99, 99, 94.0, 98.0), "RANGE"),      # stopa t4a (94<=95), t4b vive (94>90)
           (12, bar(1028, 98, 99, 97, 98.5), "RANGE"),
           (13, bar(1042, 98, 99, 97, 98.0), "RANGE")]
    for j, b, rl in seq:
        all_evs += process_closed_bar(st, j, b, rl, 13, jpath)
    lates = [e for e in all_evs if e["type"] == "CLOSE"]
    if not (len(lates) == 1 and lates[0]["signal_hash"] == "t4a" and lates[0]["late_bars"] == 2):
        fails.append(f"T4 catch-up/LATE: {all_evs}")
    if len(open_positions(st)) != 1 or open_positions(st)[0]["signal_hash"] != "t4b":
        fails.append("T4 posição concorrente t4b devia continuar OPEN")

    # T5: entrada não avaliada na própria barra (j <= entry_idx)
    st = empty_state()
    open_position(st, dict(cand, signal_hash="t5"), jpath)
    evs = process_closed_bar(st, 10, bar(1000, 99, 99, 80.0, 98.0), "BEAR", 10, jpath)
    if evs:
        fails.append(f"T5 barra da entrada não deve fechar: {evs}")

    # T6: continuidade — gap descontínuo detetado
    st = empty_state(); st["last_processed_bar_time"] = 555
    ok, why = check_continuity(st, [100, 200, 300])
    if ok:
        fails.append("T6 gap devia dar HARD_STOP")

    # T7: dedup por signal_hash + write atómico roundtrip
    st = empty_state()
    p1, _ = open_position(st, dict(cand, signal_hash="t7"), jpath)
    p2, _ = open_position(st, dict(cand, signal_hash="t7"), jpath)
    if p1 is None or p2 is not None:
        fails.append("T7 dedup signal_hash falhou")
    sp = tmpd / "pos.json"
    save_state(st, sp)
    if load_state(sp)["positions"][0]["signal_hash"] != "t7":
        fails.append("T7 roundtrip save/load falhou")

    print(json.dumps({"selftest": "position_state", "result": "PASS" if not fails else "FAIL",
                      "fails": fails, "journal": str(jpath)}, ensure_ascii=False, indent=2))
    return 0 if not fails else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
