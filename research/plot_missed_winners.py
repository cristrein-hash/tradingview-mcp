#!/usr/bin/env python3
"""CLEAR autorizado (Cris 2026-07-25: 'apaga fui eu quem mexi') + plota os 9 WINNERS SKIPADOS (verde outcome-mode,
teriam batido TP). Canon 15M: long/short_position + label #id, width 10, tick 0.01. Via tab_pin 15M."""
import os, sys, json
HERE = "/Users/cristrein/tradingview-mcp/my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
BAR = 900; WIDTH = 10
mw = json.load(open("/Users/cristrien/tradingview-mcp/research/.e2_missed_winners.json".replace("cristrien", "cristrein")))

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
try:
    r = c.call_tool("draw_clear")
    print(f"CLEAR (autorizado): {r.get('success')}")
    CLR = "#1a8917"   # verde winner (outcome-mode TP)
    drawn = 0
    for k, m in enumerate(mw):
        shape = "long_position" if m["dir"] == "LONG" else "short_position"
        r1 = c.call_tool("draw_shape", {"shape": shape,
            "point": {"time": m["t"], "price": m["entry"]},
            "point2": {"time": m["t"] + WIDTH * BAR, "price": m["tgt"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(m["entry"], m["sl"]),
                                     "profitLevel": price_to_ticks_offset(m["entry"], m["tgt"])})})
        drawn += bool(r1.get("success"))
        R = m["entry"] - m["sl"]
        c.call_tool("draw_shape", {"shape": "text", "point": {"time": m["t"], "price": m["entry"] + 0.5 * R},
                    "text": f"#{k+1}", "overrides": json.dumps({"color": CLR, "bold": True, "fontsize": 12})})
        print(f"  #{k+1} {m['dir']} {m['entry']} -> TP {m['tgt']} : {'OK' if r1.get('success') else 'FALHOU'}")
    dl2 = c.call_tool("draw_list") or {}
    print(f"\nPlotados {drawn}/{len(mw)} winners verdes · draw_list total: {dl2.get('count')}")
finally:
    c.stop()
