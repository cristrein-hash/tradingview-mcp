#!/usr/bin/env python3
"""PLOT canónico dos sinais MATERIAIS de hoje que chegaram ao leitor E2 (maior chance de sinal).
Aditivo (NO_CLEAR). 15M (sinais de hoje, dentro do histórico carregado). long/short_position + label T1..T3
neutro (skipados, sem outcome). stopLevel/profitLevel ticks 0.01. Read-back no fim. Daemons pausados pelo caller."""
import os, sys, json, time, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
HERE = R + "my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, R + "alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
BAR = 900; WIDTH = 10
hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")

# 3 sinais materiais de hoje (bar_time UTC epoch), extraídos dos verdicts/e1
SIG = [
    {"t": 1785109500, "dir": "SHORT", "entry": 4089.38, "sl": 4097.67, "tgt": 4058.08, "lab": "T1"},
    {"t": 1785110400, "dir": "SHORT", "entry": 4084.64, "sl": 4091.15, "tgt": 4058.08, "lab": "T2"},
    {"t": 1785157200, "dir": "LONG",  "entry": 4087.45, "sl": 4082.82, "tgt": 4096.93, "lab": "T3"},
]
NEUTRO = "#1565c0"   # canon: azul = neutro (skipado, sem outcome)

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
try:
    c.call_tool("chart_set_timeframe", {"timeframe": "15"})
    time.sleep(4)
    dl0 = c.call_tool("draw_list") or {}
    print(f"tab {tid[:8]} · desenhos ANTES: {dl0.get('count')} (aditivo, NO_CLEAR)")
    drawn = 0
    for s in SIG:
        shape = "long_position" if s["dir"] == "LONG" else "short_position"
        r1 = c.call_tool("draw_shape", {"shape": shape,
            "point": {"time": s["t"], "price": s["entry"]},
            "point2": {"time": s["t"] + WIDTH * BAR, "price": s["tgt"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(s["entry"], s["sl"]),
                                     "profitLevel": price_to_ticks_offset(s["entry"], s["tgt"])})})
        ok = bool(r1.get("success")); drawn += ok
        Rr = abs(s["entry"] - s["sl"])
        yoff = s["entry"] + (0.6 * Rr if s["dir"] == "SHORT" else -0.6 * Rr)
        c.call_tool("draw_shape", {"shape": "text", "point": {"time": s["t"], "price": yoff},
                    "text": s["lab"], "overrides": json.dumps({"color": NEUTRO, "bold": True, "fontsize": 13})})
        print(f"  {s['lab']} {hm(s['t'])} {s['dir']} entry {s['entry']} SL {s['sl']} alvo {s['tgt']} : {'OK' if ok else 'FALHOU'}")
    print(f"\nplotados {drawn}/3")
    print("VERIFICAÇÃO (read-back):")
    dl = c.call_tool("draw_list") or {}
    okw = 0
    for sh in dl.get("shapes", []):
        if sh.get("name") in ("long_position", "short_position"):
            pr = c.call_tool("draw_get_properties", {"entity_id": sh["id"]}) or {}
            pts = pr.get("points", [])
            if len(pts) >= 2 and pts[0].get("time") != pts[1].get("time"):
                okw += 1
    print(f"  posições no chart: {sum(1 for x in dl.get('shapes',[]) if x.get('name') in ('long_position','short_position'))} · com largura: {okw}")
finally:
    c.stop()
