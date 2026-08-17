#!/usr/bin/env python3
"""FIX: remove SÓ as 3 caixas T1/T2/T3 mal-datadas (+1h) que acabei de desenhar + labels T1/T2/T3, e re-plota
nos bar_time EXATOS. Preserva tudo o resto (S1-S5 do Cris etc). Read-back no fim. Daemons pausados pelo caller."""
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
WRONG_T = {1785109500, 1785110400, 1785157200}          # epochs errados (+1h)
NEUTRO = "#1565c0"
SIG = [
    {"t": 1785105900, "dir": "SHORT", "entry": 4089.38, "sl": 4097.67, "tgt": 4058.08, "lab": "T1"},
    {"t": 1785106800, "dir": "SHORT", "entry": 4084.64, "sl": 4091.15, "tgt": 4058.08, "lab": "T2"},
    {"t": 1785153600, "dir": "LONG",  "entry": 4087.45, "sl": 4082.82, "tgt": 4096.93, "lab": "T3"},
]

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
try:
    dl = c.call_tool("draw_list") or {}
    removed = 0
    for s in dl.get("shapes", []):
        nm = s.get("name")
        pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
        pts = pr.get("points", []); props = pr.get("properties", {}) or {}
        rm = False
        if nm in ("long_position", "short_position") and pts:
            if int(pts[0].get("time") or 0) in WRONG_T: rm = True
        if nm == "text" and props.get("text") in ("T1", "T2", "T3"):
            if pts and int(pts[0].get("time") or 0) in WRONG_T: rm = True
        if rm:
            c.call_tool("draw_remove_one", {"entity_id": s["id"]}); removed += 1
    print(f"removidas {removed} formas mal-datadas")
    time.sleep(1)
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
    print(f"re-plotados {drawn}/3 nos tempos corretos")
    print("VERIFICAÇÃO T1/T2/T3 (read-back):")
    dl2 = c.call_tool("draw_list") or {}
    for s in dl2.get("shapes", []):
        if s.get("name") in ("long_position", "short_position"):
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            if pts and int(pts[0].get("time") or 0) in {x["t"] for x in SIG}:
                w = len(pts) >= 2 and pts[0].get("time") != pts[1].get("time")
                print(f"  {s['name']} @ {hm(pts[0].get('time'))} px {pts[0].get('price')} largura={'OK' if w else 'ZERO'}")
finally:
    c.stop()
