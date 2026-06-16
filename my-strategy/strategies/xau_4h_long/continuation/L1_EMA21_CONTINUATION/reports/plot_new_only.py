#!/usr/bin/env python3
"""Plotagem CANÔNICA dos 25 NEW_ONLY (regime_l1_v4) no chart 4H — long_position nativo.
Por entrada: entry=close do bar; SL ESTRUTURAL = low da zona de demanda Custom OB (ou swing low
recente) menos 0.1xATR; TARGET = entry + 3R (3 x risco). overrides stopLevel/profitLevel em TICKS
(mintick XAU=0.01), convenção de alert-bridge/draw_xau_4h_trades.py. Label curto #id.
NÃO inventa nível arbitrário (SL=estrutura real, target=3R do risco real). NÃO Telegram/broker/trade mgmt.
NÃO apaga desenhos (draw_list=0). Deixa o chart em PEPPERSTONE:XAUUSD/240."""
import sys, csv, json, math
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
L1 = HERE.parent
REPO = L1.parents[4]
sys.path.insert(0, str(L1)); sys.path.insert(0, str(REPO / "my-strategy/core"))
import scanner
from tv_read_adapter import _MCP

CSV = HERE / "l1_old_vs_new_regime_comparison.csv"
WANT_SYMBOL, WANT_TF, MINTICK = "PEPPERSTONE:XAUUSD", "240", 0.01
BOX_BARS, R_MULT = 20, 3.0

def to_unix(ts): return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def ticks(entry, level): return int(round(abs(level - entry) / MINTICK))

def structural_sl(S, i):
    """SL estrutural: low da zona de demanda Custom OB tocada; senão swing low recente. -0.1xATR buffer."""
    atr = S.ATR14[i] or 0
    dz = scanner.demand_zone(S, i)
    if dz is not None:
        base = dz[1]                      # zone low (estrutura OB)
        src = "OB_zone_low"
    else:
        base = min(S.L[max(0, i-9):i+1])  # swing low recente
        src = "swing_low_10"
    return base - 0.1 * atr, src

def run():
    rows = [r for r in csv.DictReader(open(CSV)) if r["status"] == "NEW_ONLY"]
    S = scanner.build_series()
    plan, skipped = [], []
    for r in rows:
        u = to_unix(r["timestamp"]); i = S.idx.get(u)
        if i is None:
            cand = [k for k in range(S.N) if abs(S.T[k]-u) <= 4*3600]
            i = min(cand, key=lambda k: abs(S.T[k]-u)) if cand else None
        if i is None:
            skipped.append({"id": r["candidate_id"], "ts": r["timestamp"], "reason": "bar ausente no RAW"}); continue
        entry = S.C[i]; sl, slsrc = structural_sl(S, i)
        risk = entry - sl
        if risk <= 0:
            skipped.append({"id": r["candidate_id"], "ts": r["timestamp"], "reason": f"risco<=0 (entry={entry} sl={sl})"}); continue
        target = entry + R_MULT * risk
        exit_i = min(i + BOX_BARS, S.N - 1)
        plan.append({"id": r["candidate_id"], "ts": r["timestamp"], "entry_time": S.T[i],
                     "exit_time": S.T[exit_i], "entry": round(entry,2), "sl": round(sl,2),
                     "target": round(target,2), "risk": round(risk,2), "sl_src": slsrc})
    c = _MCP(); c.start(); drawn = 0; chart = {}
    try:
        st = c.call("chart_get_state"); chart["before"] = {"symbol": st.get("symbol"), "tf": str(st.get("resolution"))}
        if st.get("symbol") != WANT_SYMBOL: c.call("chart_set_symbol", {"symbol": WANT_SYMBOL})
        if str(st.get("resolution")) != WANT_TF: c.call("chart_set_timeframe", {"timeframe": WANT_TF})
        chk = c.call("chart_get_state"); sym, res = chk.get("symbol"), str(chk.get("resolution"))
        if not (str(sym).endswith("XAUUSD") and res == WANT_TF):
            c.stop(); return {"HARD_STOP": f"chart não confirmou 240: {sym}/{res}"}
        chart["used"] = {"symbol": sym, "tf": res}
        for p in plan:
            r1 = c.call("draw_shape", {"shape": "long_position",
                "point": {"time": p["entry_time"], "price": p["entry"]},
                "point2": {"time": p["exit_time"], "price": p["target"]},
                "overrides": json.dumps({"stopLevel": ticks(p["entry"], p["sl"]),
                                          "profitLevel": ticks(p["entry"], p["target"])})})
            if r1.get("success"): drawn += 1
            else: p["draw_error"] = r1
            c.call("draw_shape", {"shape": "text",
                "point": {"time": p["entry_time"], "price": round(p["target"] + 0.4*(S.ATR14[S.idx.get(p['entry_time'], 0)] or 1), 2)},
                "text": f"#{p['id']}", "overrides": json.dumps({"color": "#1565c0", "bold": True, "fontsize": 10})})
        chart["left_on"] = chart["used"]
    finally:
        try: c.stop()
        except Exception: pass
    res = {"new_only": len(rows), "planned": len(plan), "drawn_long_position": drawn,
           "skipped": skipped, "target": "3R", "sl": "structural (OB zone low / swing low) -0.1ATR",
           "chart": chart, "telegram": "none", "broker": "untouched", "trades": plan}
    (HERE / "l1_new_only_plotting_result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(json.dumps({k: res[k] for k in ["new_only","planned","drawn_long_position","skipped","target","sl","chart"]}, indent=2, ensure_ascii=False))
    return res

if __name__ == "__main__":
    run()
