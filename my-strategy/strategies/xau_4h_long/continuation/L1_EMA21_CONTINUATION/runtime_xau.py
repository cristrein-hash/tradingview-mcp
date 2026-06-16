#!/usr/bin/env python3
"""Runtime XAU-only L1 (Production v2) — orquestração híbrida.

Lê o chart XAU 4H via MCP (tv_read_adapter), aplica o gate de exaustão RSI já existente,
e — só para candidato OPERACIONAL aprovado da L1 — dispara candidate notification Telegram.
A AUTORIDADE do gate-base é o scanner; este runtime ORQUESTRA (regime/precondição, dedup,
journal, notify). NÃO duplica a lógica do gate-base.

Modos: --dry-run (default) | --once | --send-telegram (opt-in real). XAU-only. Sem scheduler,
sem daemon, sem LaunchAgent, sem broker, sem MCP de gestão de trade.

Regime D-1 = regime_L1_v4 (fonte EXPLÍCITA nova; regime legacy v1 B/regime_B_v3 = IRRECUPERÁVEL,
não-autoridade). Se o feed regime_L1_v4 não cobrir D-1 recente → no_candidate/regime_l1_v4_stale.
Com regime_L1_v4 fresco, avalia normalmente (regime != BULL → no_candidate; BULL → segue gate).
"""
import json, sys, argparse, hashlib, subprocess
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
def _repo(p):
    for d in [p] + list(p.parents):
        if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
            return d
    return p.parents[5]
REPO = _repo(HERE)
CORE = REPO / "my-strategy" / "core"
sys.path.insert(0, str(CORE))
from group_model_xau import GROUPS, telegram_allowed  # noqa: E402

# Regime D-1 = regime_L1_v4 (fonte EXPLÍCITA nova). O regime legacy v1 B/regime_B_v3 foi
# declarado IRRECUPERÁVEL (ver core/regime/README.md) e NÃO é mais autoridade operacional.
REGIME_L1V4 = REPO / "my-strategy/core/regime_l1/regime_l1_v4_classifications.jsonl"
sys.path.insert(0, str(REPO / "my-strategy/core/regime_l1"))
from regime_l1_v4 import latest_state_before  # noqa: E402
sys.path.insert(0, str(HERE))
import scanner  # reusa os MESMOS gates/filtros/SL do scanner (autoridade única)  # noqa: E402
CONSUMER = "L1_EMA21_CONTINUATION"
GROUP = "XAU_240"
RSI_VS_MA_THR = -9.35
STATE_DIR = HERE / ".runtime_state"
FEATURE_HISTORY = STATE_DIR / "l1_feature_history.jsonl"  # NAS por bar p/ SHIFT1 causal (gitignored)
FEATURE_HISTORY_MAX = 600


def persist_feature(bar_time, nas_dist):
    """Append-only: grava (bar_time, nas_dist) do bar atual p/ uso SHIFT1 em ciclos futuros.
    Dedup por bar_time. NÃO usa futuro. Rotação simples."""
    if bar_time is None:
        return
    STATE_DIR.mkdir(exist_ok=True)
    seen = set()
    if FEATURE_HISTORY.exists():
        for ln in FEATURE_HISTORY.read_text().splitlines():
            try: seen.add(json.loads(ln)["bar_time"])
            except Exception: pass
    if bar_time in seen:
        return
    with open(FEATURE_HISTORY, "a") as f:
        f.write(json.dumps({"bar_time": bar_time, "nas_dist": nas_dist,
                            "persisted_at": datetime.now(timezone.utc).isoformat()}) + "\n")
    # rotação: manter últimas N linhas
    lines = FEATURE_HISTORY.read_text().splitlines()
    if len(lines) > FEATURE_HISTORY_MAX:
        FEATURE_HISTORY.write_text("\n".join(lines[-FEATURE_HISTORY_MAX:]) + "\n")


def nas_from_history(bar_time):
    """NAS_DISTANCE persistido para um bar_time específico (i-1). None se ausente."""
    if bar_time is None or not FEATURE_HISTORY.exists():
        return None
    val = None
    for ln in FEATURE_HISTORY.read_text().splitlines():
        try:
            r = json.loads(ln)
            if r.get("bar_time") == bar_time:
                val = r.get("nas_dist")
        except Exception:
            pass
    return val


def align_study_values(eval_t, prev_t, nas_series, rsi_series):
    """Alinha por TIMESTAMP (nunca índice): NAS do eval_bar e do bar fechado anterior; RSI do eval_bar.
    source_time só é setado quando há match EXATO do time pedido. Retorna dict com values+source_times+status."""
    nas_by_t = {r.get("time"): r.get("nas_dist") for r in (nas_series or []) if r.get("time") is not None}
    rsi_by_t = {r.get("time"): (r.get("rsi"), r.get("rsi_ma")) for r in (rsi_series or []) if r.get("time") is not None}
    nas_eval = nas_by_t.get(eval_t); nas_shift1 = nas_by_t.get(prev_t); rsi_eval = rsi_by_t.get(eval_t)
    rsi_ok = bool(rsi_eval and rsi_eval[0] is not None and rsi_eval[1] is not None)
    status = "ok" if (nas_eval is not None and nas_shift1 is not None and rsi_ok) else "incomplete"
    return {
        "nas_eval_value": nas_eval, "nas_eval_source_time": (eval_t if nas_eval is not None else None),
        "nas_shift1_value": nas_shift1, "nas_shift1_source_time": (prev_t if nas_shift1 is not None else None),
        "rsi_eval_value": rsi_eval, "rsi_eval_source_time": (eval_t if rsi_ok else None),
        "alignment_status": status}


def build_live_series(bars_closed, ob_zones, rsi_eval, nas_shift1):
    """Constrói scanner.Series com OHLCV truncado ATÉ o eval_bar (último = eval_bar fechado).
    rsi_eval=(rsi,rma) do eval_bar; nas_shift1=NAS do bar fechado anterior. Reusa scanner.evaluate.
    Retorna (S, eval_idx) ou (None, motivo)."""
    if len(bars_closed) < 60:
        return None, "insufficient_ohlcv(<60)"
    zlist = [(z["high"], z["low"]) for z in (ob_zones or [])
             if isinstance(z.get("high"), (int, float)) and isinstance(z.get("low"), (int, float))]
    if not zlist:
        return None, "missing_ob_zones"
    if not (rsi_eval and rsi_eval[0] is not None and rsi_eval[1] is not None):
        return None, "missing_rsi_eval"
    if nas_shift1 is None:
        return None, "missing_nas_shift1"
    S = scanner.Series()
    S.T = [b["time"] for b in bars_closed]; S.idx = {t: i for i, t in enumerate(S.T)}; S.N = len(S.T)
    S.O = [b["open"] for b in bars_closed]; S.H = [b["high"] for b in bars_closed]
    S.L = [b["low"] for b in bars_closed]; S.C = [b["close"] for b in bars_closed]
    S.V = [b.get("volume") or 0 for b in bars_closed]
    S.EMA21 = scanner.ema(S.C, 21); S.SMA50 = scanner.sma(S.C, 50)
    N = S.N; H = S.H; L = S.L; C = S.C
    TR = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, N)]
    S.ATR14 = [None] * N
    if N >= 14:
        a = sum(TR[:14]) / 14; S.ATR14[13] = a
        for i in range(14, N): a = (a * 13 + TR[i]) / 14; S.ATR14[i] = a
    i = N - 1  # último bar truncado = eval_bar (FECHADO)
    S.zones_at = {S.T[i - 1]: zlist}                 # zonas OB p/ lookback demand_zone(i-1)
    S.rsi_at = {S.T[i]: rsi_eval}                    # RSI do eval_bar (fechado, alinhado por time)
    S.nas_at = {S.T[i - 1]: nas_shift1}              # NAS SHIFT1 = bar fechado anterior (alinhado por time)
    S.CLS = [json.loads(l) for l in REGIME_L1V4.read_text().splitlines() if l.strip()]
    return S, i


def regime_d1_state(bar_time_unix):
    """Lê regime_L1_v4 p/ a última classificação ANTES de bar_time (D-1 causal).
    Retorna (state|None, stale: bool). stale se o feed não cobrir D-1 recente."""
    if bar_time_unix is None or not REGIME_L1V4.exists():
        return None, True
    cls = [json.loads(l) for l in REGIME_L1V4.read_text().splitlines() if l.strip()]
    return latest_state_before(cls, bar_time_unix)


def signal_hash(symbol, tf, ts_iso):
    base = symbol.split(":")[-1]
    key = f"{ts_iso}|{base}|{tf}|L1_EMA21_CONTINUATION|continuation"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def already_sent(dedup_path, sh):
    if not dedup_path or not Path(dedup_path).exists():
        return False
    return any(line.strip() == sh for line in Path(dedup_path).read_text().splitlines())


def mark_sent(dedup_path, sh):
    if dedup_path:
        with open(dedup_path, "a") as f:
            f.write(sh + "\n")


def evaluate(snapshot):
    """Avalia a config APROVADA no live, reusando os gates do scanner sobre uma Series construída
    do snapshot. NAS SHIFT1 vem do histórico persistido (i-1), nunca do NAS atual. Sem proxy.
    Estados: operational_candidate / blocked_exhaustion / blocked_l1_refined_filter /
             blocked_missing_nas_shift1 / blocked_missing_base_rule_live_fields /
             blocked_missing_closed_bar_study_values / blocked_bar_not_closed / no_candidate."""
    sym = snapshot["symbol"]; tf = snapshot["timeframe"]
    bt = snapshot.get("bar_time")
    ts_iso = datetime.utcfromtimestamp(bt).isoformat() if bt else "?"
    sh = signal_hash(sym, tf, ts_iso)
    base = {"symbol": sym, "timeframe": tf, "candidate_timestamp": ts_iso, "signal_hash": sh,
            "strategy": "L1 · EMA21 CONTINUATION", "suite": "XAU 4H LONG — CONTINUATION",
            "strategy_route": CONSUMER}

    bars = snapshot.get("ohlcv_recent") or []
    if len(bars) < 2:
        return {**base, "operational": False, "state": "blocked_missing_base_rule_live_fields",
                "reason": "ohlcv insuficiente p/ identificar i-1"}

    # 0) SELEÇÃO DA ÚLTIMA BARRA 4H FECHADA (close-only-causal). data_get_ohlcv inclui o realtime
    # (bar em formação) como última; bar 4H com time t fecha em t+14400. eval_bar = última fechada.
    TF_SEC = 14400
    now = datetime.now(timezone.utc).timestamp()
    closed_idx = None
    for k in range(len(bars) - 1, -1, -1):
        t = bars[k].get("time")
        if t is not None and now >= t + TF_SEC:
            closed_idx = k; break
    returned_last_bar_time = bars[-1].get("time")
    if closed_idx is None:
        return {**base, "operational": False, "state": "blocked_bar_not_closed",
                "reason": f"nenhuma barra fechada na janela (returned_last={returned_last_bar_time}, now={int(now)})"}
    eval_bar_time = bars[closed_idx].get("time")
    previous_closed_bar_time = bars[closed_idx - 1].get("time") if closed_idx >= 1 else None
    forming_bar_excluded = (closed_idx != len(bars) - 1)
    diag = {"returned_last_bar_time": returned_last_bar_time, "eval_bar_time": eval_bar_time,
            "previous_closed_bar_time": previous_closed_bar_time,
            "forming_bar_excluded": forming_bar_excluded}
    # candidate_timestamp = eval_bar (fechada), não o realtime
    base["candidate_timestamp"] = datetime.utcfromtimestamp(eval_bar_time).isoformat()
    base["signal_hash"] = signal_hash(sym, tf, base["candidate_timestamp"])
    base["bar_diagnostics"] = diag

    # ALINHAMENTO POR TIMESTAMP (nunca índice / nunca forming): study-values do bar FECHADO via
    # data_get_study_values_at_bar. Exige match EXATO de time p/ NAS(eval), NAS(i-1) e RSI(eval).
    al = align_study_values(eval_bar_time, previous_closed_bar_time,
                            snapshot.get("nas_series"), snapshot.get("rsi_series"))
    base["study_alignment"] = al
    # fallback/debug (não substitui a tool): persiste o NAS do eval_bar fechado quando alinhado
    if al["nas_eval_source_time"] == eval_bar_time and al["nas_eval_value"] is not None:
        persist_feature(eval_bar_time, al["nas_eval_value"])
    if not (al["nas_shift1_source_time"] == previous_closed_bar_time
            and al["rsi_eval_source_time"] == eval_bar_time
            and al["nas_eval_source_time"] == eval_bar_time):
        return {**base, "operational": False, "state": "blocked_missing_closed_bar_study_values",
                "reason": (f"study-values não alinharam por time (eval={eval_bar_time}, "
                           f"prev={previous_closed_bar_time}); status={al['alignment_status']}")}

    # truncar OHLCV ATÉ o eval_bar (descarta forming) -> eval_bar = último bar da série
    S, info = build_live_series(bars[:closed_idx + 1], snapshot.get("ob_zones"),
                                rsi_eval=al["rsi_eval_value"], nas_shift1=al["nas_shift1_value"])
    if S is None:
        return {**base, "operational": False, "state": "blocked_missing_base_rule_live_fields",
                "reason": f"campos live insuficientes: {info}"}

    # MESMO gate do scanner (regime+base-rule+exhaustion+refined filter+SL/target) sobre o eval_bar FECHADO
    out = scanner.evaluate(S, info)
    return {**base,
            "operational": out["operational"],
            "exhaustion_gate": out["exhaustion_gate"],
            "refined_filter_pass": out.get("refined_filter_pass"),
            "state": out["state"],
            "rsi_vs_ma": out.get("rsi_vs_ma"),
            "entry_price": out.get("entry_price"),
            "stop_price": out.get("stop_price"),
            "target_price": out.get("target_price"),
            "nas_eval_value": al["nas_eval_value"], "nas_eval_source_time": al["nas_eval_source_time"],
            "nas_shift1_value": al["nas_shift1_value"], "nas_shift1_source_time": al["nas_shift1_source_time"],
            "rsi_eval_value": al["rsi_eval_value"], "rsi_eval_source_time": al["rsi_eval_source_time"],
            "filter_trace": out.get("filter_trace"),
            "reason": out.get("gate_reason", out["state"])}


def notify(cand, send, dedup_path):
    """Dispara candidate notification via telegram_notify.py se operacional+allowlist+não-dedup."""
    sh = cand["signal_hash"]
    if not cand.get("operational"):
        return {"sent": False, "skip": f"não-operacional ({cand.get('state')})"}
    if not telegram_allowed(GROUP, CONSUMER):
        return {"sent": False, "skip": "consumer fora da allowlist do grupo"}
    if already_sent(dedup_path, sh):
        return {"sent": False, "skip": f"dedup: signal_hash {sh} já enviado"}
    notifier = HERE / "telegram_notify.py"
    args = [sys.executable, str(notifier)] + (["--send"] if send else [])
    r = subprocess.run(args, input=json.dumps(cand), capture_output=True, text=True)
    sent = send and "SENT=True" in r.stdout
    if sent:
        mark_sent(dedup_path, sh)
    return {"sent": sent, "stdout": r.stdout.strip(), "dry_run": not send}


def main():
    ap = argparse.ArgumentParser(description="Runtime XAU-only L1 (hybrid MCP read).")
    ap.add_argument("--once", action="store_true", help="executa 1 ciclo e sai")
    ap.add_argument("--send-telegram", action="store_true", help="envio real (opt-in; default dry-run)")
    ap.add_argument("--dedup-path", default=None, help="arquivo de dedup de signal_hash (1 envio/sinal)")
    ap.add_argument("--snapshot-file", default=None, help="(teste) lê snapshot de arquivo em vez do MCP live")
    args = ap.parse_args()

    if args.snapshot_file:                       # modo teste: snapshot injetado
        snap = json.load(open(args.snapshot_file))
    else:                                        # modo live: lê o chart via MCP
        from tv_read_adapter import read_xau_snapshot
        snap = read_xau_snapshot("240")
    if not snap.get("ok") and "candidate" not in snap and "operational" not in snap:
        print(json.dumps({"runtime": "HARD_STOP", "reason": snap.get("hard_stop", snap)}, ensure_ascii=False, indent=2))
        return 2

    # snapshot do adapter -> evaluate; OU candidato já pronto (teste consumindo scanner)
    if "state" in snap and "signal_hash" in snap:   # já é um candidato (ex.: saída do scanner)
        cand = snap
    else:
        cand = evaluate(snap)

    res = notify(cand, send=args.send_telegram, dedup_path=args.dedup_path)
    out = {"group": GROUP, "consumer": CONSUMER, "candidate": cand, "notify": res,
           "telegram_real": bool(args.send_telegram)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
