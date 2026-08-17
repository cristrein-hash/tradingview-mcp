#!/usr/bin/env python3
"""Plota os 5 trades que o E2 TERIA EMITIDO (surfaced=True) esta semana, no canon 15M (PLOTTING_CANON_MASTER):
long/short_position + label #id, width 10 barras (bar 900s), tick 0.01 (stopLevel/profitLevel=offsets em ticks),
cor outcome-mode (vermelho=SL loser) + AZUL neutro p/ OPEN (sem outcome). NO_CLEAR (nao apaga nada). Via tab_pin 15M."""
import os, sys, json
HERE = "/Users/cristrein/tradingview-mcp/my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
L = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/"
BAR = 900; WIDTH = 10  # 15M canon

outs = {}
for x in open(L + "e2_outcomes.jsonl"):
    if x.strip():
        r = json.loads(x); cid = r.get("candidate_id") or r.get("id")
        if cid: outs[cid] = r
surf = []
for r in (json.loads(x) for x in open(L + "e2_shadow.jsonl") if x.strip()):
    if r.get("surfaced") is True:
        c = r.get("candidate") or {}
        surf.append({"dir": c["direction"], "entry": c["entry"], "sl": c["sl"], "tgt": c["target"],
                     "t": c.get("bar_time"), "oc": (outs.get(c.get("id")) or {}).get("outcome", "OPEN")})
surf.sort(key=lambda z: z["t"] or 0)

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
CLR = {"SL": "#cc0000", "TP": "#1a8917", "OPEN": "#1565c0"}
drawn = 0
try:
    for k, s in enumerate(surf):
        shape = "long_position" if s["dir"] == "LONG" else "short_position"
        r1 = c.call_tool("draw_shape", {
            "shape": shape,
            "point": {"time": s["t"], "price": s["entry"]},
            "point2": {"time": s["t"] + WIDTH * BAR, "price": s["tgt"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(s["entry"], s["sl"]),
                                     "profitLevel": price_to_ticks_offset(s["entry"], s["tgt"])})})
        ok = r1.get("success")
        drawn += bool(ok)
        R = s["entry"] - s["sl"]
        c.call_tool("draw_shape", {"shape": "text", "point": {"time": s["t"], "price": s["entry"] + 0.5 * R},
                    "text": f"#{k+1}", "overrides": json.dumps({"color": CLR.get(s["oc"], "#1565c0"), "bold": True, "fontsize": 12})})
        print(f"  #{k+1} {s['dir']} {s['entry']} SL{s['sl']} TP{s['tgt']} [{s['oc']}] -> {'OK' if ok else 'FALHOU '+str(r1)[:80]}")
    dl = c.call_tool("draw_list") or {}
    print(f"\nDesenhados {drawn}/{len(surf)} · draw_list total agora: {dl.get('count')}")
finally:
    c.stop()
