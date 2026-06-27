#!/usr/bin/env python3
"""Plotagem CANÔNICA dos trades do candidato v2 + screenshots de janelas-chave p/ inspecao visual (aprofundar, nao
concluir). long_position nativo (entry/sl do CSV, target=entry+3R, largura 10), label #N verde. Captura screenshots
de janelas (winning cluster vs losing) p/ comparar CARATER de mercado. Cris autorizou screenshot via MCP p/ esta engine.
Verified 2026-06-26."""
import sys, csv, json
from datetime import datetime, timezone
from pathlib import Path
REPO = Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
HERE = Path(__file__).parent
SYMBOL, TF, BARS = "PEPPERSTONE:XAUUSD", "15", 10
rows = [r for r in csv.DictReader(open(HERE / "candidates_v2_final.csv")) if r["t"] != "t"]
trades = []
for i, r in enumerate(sorted(rows, key=lambda x: int(x["t"])), 1):
    entry = float(r["entry"]); sl = float(r["sl"]); risk = entry - sl
    if risk <= 0: continue
    t = int(r["t"]); trades.append({"n": i, "t": t, "entry": round(entry, 2), "sl": round(sl, 2),
                                     "target": round(entry + 3 * risk, 2), "exit_t": t + BARS * 900, "win": r["win"], "ly": round(entry + 0.5 * risk, 2)})
# janelas de inspeção (winning cluster 2024-11 vs losing 2025-05 vs BULL 2026-01)
def ux(s): return int(datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
WINDOWS = [("win_2024-11", ux("2024-11-08"), ux("2024-11-30")), ("loss_2025-05", ux("2025-05-15"), ux("2025-06-08")),
           ("bull_2026-01", ux("2026-01-08"), ux("2026-01-25"))]
# plotar SÓ os trades dentro das janelas (rápido)
trades = [tr for tr in trades if any(a <= tr["t"] <= b for _, a, b in WINDOWS)]
print(f"trades nas janelas: {len(trades)}")
c = MCPClient(); c.start(); drawn = 0; shots = []
try:
    st = c.call_tool("chart_get_state")
    if st.get("symbol") != SYMBOL: c.call_tool("chart_set_symbol", {"symbol": SYMBOL})
    if str(st.get("resolution")) != TF: c.call_tool("chart_set_timeframe", {"timeframe": TF})
    for tr in trades:
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": tr["t"], "price": tr["entry"]}, "point2": {"time": tr["exit_t"], "price": tr["target"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(tr["entry"], tr["sl"]), "profitLevel": price_to_ticks_offset(tr["entry"], tr["target"])})})
        if r1.get("success"): drawn += 1
        c.call_tool("draw_shape", {"shape": "text", "point": {"time": tr["t"], "price": tr["ly"]},
            "text": f"#{tr['n']}", "overrides": json.dumps({"color": "#1a8917" if tr["win"] == "True" else "#cc0000", "bold": True, "fontsize": 10})})
    dl = c.call_tool("draw_list")
    for name, a, b in WINDOWS:
        c.call_tool("chart_set_visible_range", {"from_time": a, "to_time": b})
        ss = c.call_tool("capture_screenshot", {"region": "chart"})
        shots.append({"window": name, "shot": ss})
finally:
    try: c.stop()
    except Exception: pass
print(json.dumps({"trades": len(trades), "drawn_long_position": drawn, "draw_list": dl.get("count") if isinstance(dl, dict) else None, "screenshots": shots}, indent=2, ensure_ascii=False))
(HERE / "plot_v2_visual_result.json").write_text(json.dumps({"trades": len(trades), "drawn": drawn, "screenshots": shots}, indent=2, ensure_ascii=False))
