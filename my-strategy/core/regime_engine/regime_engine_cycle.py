#!/usr/bin/env python3
"""REGIME ENGINE — serviço de regime LIVE PERMANENTE (Cris 2026-07-17).
Ciclo: (1) append das barras 4H (tab 240) e 1H (tab 60) FECHADAS via MCP aos ficheiros RAW canónicos
(raw_4h_ohlc.jsonl / raw_1h_ohlc.jsonl) — validado, monotónico, sem dup, fail-closed — o que também
ressuscita leg_v3 e todo o research que os lê; (2) corre o detetor canónico engine_4h_regime_gate_RAW
sobre os dados atualizados → regime atual (v5 hour-causal, BEAR/BULL/RANGE); (3) persiste current + regista
TRANSIÇÕES (regime_transitions.jsonl); (4) alerta na virada se REGIME_TELEGRAM=1. Tab-pinned, sem tocar
symbol/TF, sem pausa. py3.9 stdlib. Default dry (não envia). --once = 1 ciclo.
"""
import os, sys, json, time, datetime as dt, importlib.util
from pathlib import Path
CORE = Path(__file__).resolve().parents[1]         # my-strategy/core
REV = CORE.parent / "research" / "revalidation"
sys.path.insert(0, str(CORE))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient

RAW4 = REV / "raw_4h_ohlc.jsonl"
RAW1 = REV / "raw_1h_ohlc.jsonl"
ENGINE = REV / "engine_4h_regime_gate_RAW.py"
STATE = Path(__file__).resolve().parent / ".regime_state"; STATE.mkdir(exist_ok=True)
CUR_F = STATE / "current_regime.json"
TRANS_F = STATE / "regime_transitions.jsonl"
LOG = STATE / "regime_cycle.log"
dur = {"240": 14400, "60": 3600}
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")   # convenção Cris 2026-07-17: TODA hora humana em Lisboa (interno fica epoch)
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")


def _load_last_t(f):
    try:
        lines = f.read_text().splitlines()
        return json.loads(lines[-1])["t"] if lines else 0
    except Exception:
        return 0


def append_bars(res, tid, path):
    """Lê a tab pinada (res), acrescenta barras FECHADAS novas (t+dur ≤ now) ao ficheiro. Fail-closed."""
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        oh = c.call_tool("data_get_ohlcv", {"count": 500}) or {}
        bars = oh.get("bars") or []
    finally:
        c.stop()
    if not bars:
        return 0, "sem barras MCP"
    now = int(time.time()); D = dur[res]; last = _load_last_t(path)
    phase = last % D                        # fase do ficheiro (4H XAU = 7200s; 1H = 0) — não epoch-aligned
    new = []
    prev_t = last
    for b in sorted(bars, key=lambda x: x.get("time") or 0):
        t = b.get("time")
        if t is None or b.get("close") is None:
            continue
        if t <= last:                       # já temos
            continue
        if t % D != phase:                  # grelha (mesma fase do ficheiro)
            return 0, f"t {iso(t)} fora da fase da grelha {res} ({t % D} != {phase})"
        if t + D > now:                     # barra em formação -> não entra
            continue
        o, h, l, cc = b["open"], b["high"], b["low"], b["close"]
        if not (h >= l and h >= cc >= l and h >= o >= l):
            return 0, f"OHLC inválido em {iso(t)}"
        if prev_t and t <= prev_t:
            return 0, "não-monotónico"
        new.append({"t": t, "o": o, "h": h, "l": l, "c": cc}); prev_t = t
    if new:
        with open(path, "a") as fh:
            for r in new:
                fh.write(json.dumps(r) + "\n")
    return len(new), None


def compute_regime():
    """Importa o detetor canónico FRESCO (lê os ficheiros já atualizados) → regime da última barra fechada."""
    spec = importlib.util.spec_from_file_location("reg_fresh", ENGINE)
    reg = importlib.util.module_from_spec(spec)
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):     # silencia os panels do módulo
        spec.loader.exec_module(reg)
    now = int(time.time())
    last4 = reg.TS4[-1]
    cur = reg.regime_at(last4)
    stable = reg.stable_prevday(last4)
    return {"regime": cur, "stable_daily": stable, "as_of_bar": iso(last4),
            "last_4h": iso(reg.TS4[-1]), "n4": len(reg.TS4)}


def main():
    once = "--once" in sys.argv
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    out = {"ts": ts}
    # STORE-FIRST (Fase 1, 2026-07-18): o bar-store é o dono dos appends aos RAW 4H/1H.
    # Se o store estiver fresco, zero MCP aqui; senão, fallback legado (append próprio).
    store_ok = False
    try:
        import store_reader as SR
        store_ok = SR.fresh("240", mult=3)
    except Exception:
        store_ok = False
    if store_ok:
        out["source"] = "store"
    else:
        out["source"] = "mcp-fallback"
        tid4 = tab_pin.discover_tab("240"); tid1 = tab_pin.discover_tab("60")
        if not tid4:
            out["status"] = "HARD_STOP: sem tab 240 (e store não-fresco)"; _log(out); print(json.dumps(out)); return
        n4, e4 = append_bars("240", tid4, RAW4)
        n1, e1 = (append_bars("60", tid1, RAW1) if tid1 else (0, "sem tab 60"))
        out.update({"appended_4h": n4, "appended_1h": n1, "err_4h": e4, "err_1h": e1})
        if e4:
            out["status"] = f"HARD_STOP append 4H: {e4}"; _log(out); print(json.dumps(out)); return
    r = compute_regime()
    out.update(r)
    # transição?
    prev = None
    if CUR_F.exists():
        try: prev = json.loads(CUR_F.read_text()).get("regime")
        except Exception: prev = None
    out["prev_regime"] = prev
    if prev is not None and prev != r["regime"]:
        out["TRANSITION"] = f"{prev} -> {r['regime']}"
        with open(TRANS_F, "a") as fh:
            fh.write(json.dumps({"ts": ts, "from": prev, "to": r["regime"], "as_of": r["as_of_bar"]}) + "\n")
        if os.environ.get("REGIME_TELEGRAM") == "1":
            _notify(f"🔄 REGIME XAU: {prev} → {r['regime']} (as-of {r['as_of_bar']} Lisboa)")
    tmp = CUR_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps({**r, "ts": ts})); os.replace(tmp, CUR_F)
    # LAYER1 1D = autoridade macro (consolidação Cris 2026-07-19): este serviço é o ÚNICO daemon de
    # regime; corre também o Layer1 1D (pura computação, matemática congelada + gate de paridade) e
    # escreve current_layer1.json. v5-4H (acima) fica como leitura AUXILIAR. Fail-soft: erro no Layer1
    # não derruba o ciclo de regime.
    try:
        sys.path.insert(0, str(CORE / "layer1_service"))
        import layer1_cycle as L1
        out["layer1"] = L1.compute_and_write()
    except Exception as e:
        out["layer1"] = {"status": "ERR", "err": f"{type(e).__name__}:{str(e)[:60]}"}
    out["status"] = "OK"
    _log(out); print(json.dumps(out, ensure_ascii=False, indent=1))


def _log(o):
    with open(LOG, "a") as fh:
        fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def _notify(text):
    try:
        sys.path.insert(0, str((CORE.parent / "strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")))
        import telegram_notify as TN
        TN.send_telegram(text)
    except Exception as e:
        _log({"notify_err": str(e)[:80]})


if __name__ == "__main__":
    main()
