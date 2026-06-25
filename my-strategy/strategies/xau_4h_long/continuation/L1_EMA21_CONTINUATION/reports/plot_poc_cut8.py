#!/usr/bin/env python3
"""Plotagem CANÔNICA dos 8 LOSERS cortados pelo filtro dist_poc<=0.35 ATR (POC-wall) na L1 EMA21, p/ Cris olhar.
Mesma convenção de plot_new_only.py: long_position nativo, entry=close do bar, SL ESTRUTURAL = low zona demanda
Custom OB (ou swing low) -0.1xATR, TARGET = entry + 3R, overrides stopLevel/profitLevel em TICKS (mintick 0.01).
Label vermelho #cut dp=<dist_poc>. NÃO apaga desenhos. NÃO Telegram/broker. Deixa PEPPERSTONE:XAUUSD/240."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone
L1 = Path("/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
REPO = Path("/Users/cristrein/tradingview-mcp")
RES = L1 / "research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5" if (L1 / "research").exists() else Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5")
sys.path.insert(0, str(L1)); sys.path.insert(0, str(REPO / "my-strategy/core"))
import scanner
from tv_read_adapter import _MCP

WANT_SYMBOL, WANT_TF, MINTICK, R_MULT, BOX_BARS = "PEPPERSTONE:XAUUSD", "240", 0.01, 3.0, 20
def to_unix(ts): return int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
def ticks(entry, level): return int(round(abs(level - entry) / MINTICK))
def structural_sl(S, i):
    atr = S.ATR14[i] or 0; dz = scanner.demand_zone(S, i)
    base = dz[1] if dz is not None else min(S.L[max(0, i-9):i+1])
    return base - 0.1 * atr

# dist_poc por ts (p/ label)
DP = {t["ts"]: float(t["dist_poc"]) for t in json.load(open(RES / "l1_contrastive_features.json"))
      if t["dist_poc"] not in (None, "None", "")}
ts_list = json.load(open(RES / "l1_poc_cut8_ts.json"))
S = scanner.build_series(); plan, skipped = [], []
for ts in ts_list:
    u = to_unix(ts); i = S.idx.get(u)
    if i is None:
        cand = [k for k in range(S.N) if abs(S.T[k]-u) <= 4*3600]
        i = min(cand, key=lambda k: abs(S.T[k]-u)) if cand else None
    if i is None: skipped.append({"ts": ts, "reason": "bar ausente"}); continue
    entry = S.C[i]; sl = structural_sl(S, i); risk = entry - sl
    if risk <= 0: skipped.append({"ts": ts, "reason": f"risco<=0"}); continue
    target = entry + R_MULT * risk; exit_i = min(i + BOX_BARS, S.N - 1)
    plan.append({"ts": ts, "entry_time": S.T[i], "exit_time": S.T[exit_i], "entry": round(entry,2),
                 "sl": round(sl,2), "target": round(target,2), "dp": DP.get(ts, 0.0), "atr": S.ATR14[i] or 1})
c = _MCP(); c.start(); drawn = 0; chart = {}
try:
    st = c.call("chart_get_state"); chart["before"] = {"symbol": st.get("symbol"), "tf": str(st.get("resolution"))}
    if st.get("symbol") != WANT_SYMBOL: c.call("chart_set_symbol", {"symbol": WANT_SYMBOL})
    if str(st.get("resolution")) != WANT_TF: c.call("chart_set_timeframe", {"timeframe": WANT_TF})
    chk = c.call("chart_get_state"); sym, resn = chk.get("symbol"), str(chk.get("resolution"))
    if not (str(sym).endswith("XAUUSD") and resn == WANT_TF):
        c.stop(); print(json.dumps({"HARD_STOP": f"chart não confirmou 240: {sym}/{resn}"})); sys.exit(1)
    chart["used"] = {"symbol": sym, "tf": resn}
    for p in plan:
        r1 = c.call("draw_shape", {"shape": "long_position",
            "point": {"time": p["entry_time"], "price": p["entry"]},
            "point2": {"time": p["exit_time"], "price": p["target"]},
            "overrides": json.dumps({"stopLevel": ticks(p["entry"], p["sl"]), "profitLevel": ticks(p["entry"], p["target"])})})
        if r1.get("success"): drawn += 1
        else: p["draw_error"] = r1
        c.call("draw_shape", {"shape": "text",
            "point": {"time": p["entry_time"], "price": round(p["sl"] - 0.6*p["atr"], 2)},
            "text": f"#cut dp={p['dp']:.2f}", "overrides": json.dumps({"color": "#d32f2f", "bold": True, "fontsize": 10})})
finally:
    try: c.stop()
    except Exception: pass
res = {"planned": len(plan), "drawn_long_position": drawn, "skipped": skipped, "sl": "structural OB/swing -0.1ATR",
       "target": "3R", "chart": chart, "trades": [{k: p[k] for k in ("ts","entry","sl","target","dp")} for p in plan]}
(RES / "l1_poc_cut8_plot_result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
print(json.dumps({k: res[k] for k in ["planned","drawn_long_position","skipped","chart","trades"]}, indent=2, ensure_ascii=False))
