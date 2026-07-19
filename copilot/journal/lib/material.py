#!/usr/bin/env python3
"""COPILOT/JOURNAL — montagem do MATERIAL do dia (P2), ZERO-CDP. Junta, para uma data (Lisboa):
  - sessão: barras 15M do store na janela do dia (OHLC/range) ou 'mercado fechado';
  - regime atual (market_context.axes.regime) — v5-4H + Layer1-1D;
  - sinais dos engines na janela: Cp (alerted.jsonl), b_forward (forward_log), router (log tail);
  - trades do Cris capturados hoje (trades.jsonl) + snapshot completo (sidecar);
  - carry-forward: últimos N entries + lessons.
Degrada com honestidade: fonte ausente = nota, NUNCA inventa. Devolve dict (bloco de grounding)."""
import json, sys, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
REPO = Path("/Users/cristrein/tradingview-mcp")
J = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "alert-bridge"))
LX = ZoneInfo("Europe/Lisbon")
MKT = REPO / "external_factors_v2/snapshots/market_context.json"
CP_ALERTED = REPO / "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION/.cp_state/alerted.jsonl"
BFWD = REPO / "my-strategy/research/revalidation/b_forward/forward_log.jsonl"
ROUTER_LOG = REPO / "my-strategy/strategies/xau_15m_long/ENTRY_ROUTER/.router_state/router_cycle.log"
CARRY_N = 7


def _jl(f):
    try: return [json.loads(x) for x in Path(f).read_text().splitlines() if x.strip()]
    except Exception: return []


def _window(date_str):
    d0 = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=LX)
    return int(d0.timestamp()), int((d0 + dt.timedelta(days=1)).timestamp())


def build_material(date_str=None):
    import store_reader as SR
    if date_str is None:
        date_str = dt.datetime.now(LX).strftime("%Y-%m-%d")
    t0, t1 = _window(date_str)
    M = {"date": date_str, "weekday": dt.datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")}

    # sessão (barras 15M na janela)
    bars = [b for b in (SR.bars("15") or []) if t0 <= b.get("t", 0) < t1]
    if bars:
        hi = max(b["h"] for b in bars); lo = min(b["l"] for b in bars)
        M["session"] = {"n_bars_15m": len(bars), "open": bars[0]["o"], "close": bars[-1]["c"],
                        "high": hi, "low": lo, "range": round(hi - lo, 2),
                        "first": dt.datetime.fromtimestamp(bars[0]["t"], LX).strftime("%H:%M"),
                        "last": dt.datetime.fromtimestamp(bars[-1]["t"], LX).strftime("%H:%M")}
    else:
        M["session"] = {"note": "sem barras 15M na janela (mercado fechado / fim-de-semana)"}

    # regime atual (é o corrente, não histórico do dia — declarado)
    try:
        M["regime_now"] = json.loads(MKT.read_text()).get("axes", {}).get("regime")
    except Exception as e:
        M["regime_now"] = {"error": str(e)[:60]}

    # sinais dos engines na janela
    sig = {}
    cp = [r for r in _jl(CP_ALERTED) if t0 <= (r.get("etime") or r.get("fundo_t") or 0) < t1]
    sig["cp"] = [{"fundo_t": r.get("fundo_t"), "ent": r.get("ent"), "sl": r.get("sl"),
                  "tgt": r.get("tgt"), "stale": r.get("stale", False)} for r in cp] or "nenhum"
    bf = [r for r in _jl(BFWD) if str(r.get("fundo_dt", "")).startswith(date_str)]
    sig["b_forward"] = [{"fundo_dt": r.get("fundo_dt"), "engine": r.get("engine"),
                         "outcome": r.get("outcome"), "status": r.get("status")} for r in bf] or "nenhum"
    rl = _jl(ROUTER_LOG)
    sig["router_last"] = (rl[-1] if rl else "sem log")
    M["engine_signals"] = sig

    # trades do Cris capturados na janela (+ snapshot completo)
    trades = []
    for r in _jl(J / "trades.jsonl"):
        if not (t0 <= (r.get("detected_epoch") or 0) < t1):
            continue
        snap = None
        try:
            snap = json.loads((J / r["snapshot_ref"]).read_text())
        except Exception:
            snap = {"note": "snapshot ilegível"}
        trades.append({"record": r, "snapshot": snap})
    M["cris_trades"] = trades or "nenhum trade capturado nesta janela"

    # carry-forward (últimos N entries estruturados + lições)
    entries = _jl(J / "entries.jsonl")[-CARRY_N:]
    M["carry_forward"] = [{"date": e.get("date"), "carry": e.get("carry_forward"),
                           "scorecard": e.get("scorecard")} for e in entries] or "sem journals anteriores"
    M["recurring_lessons"] = _jl(J / "lessons.jsonl")[-30:] or "sem lições registadas ainda"
    return M


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else None
    M = build_material(d)
    print(f"material {M['date']} ({M['weekday']}): {len(json.dumps(M, ensure_ascii=False))} bytes")
    print("  sessão:", M["session"])
    print("  trades:", len(M["cris_trades"]) if isinstance(M["cris_trades"], list) else M["cris_trades"])
    print("  regime:", (M.get("regime_now") or {}))
