#!/usr/bin/env python3
"""LÊ (read-only) as posições no 1H após edição do Cris: extrai entry/SL/target reais de cada caixa
(pontos + stopLevel/profitLevel em ticks) p/ capturar os SLs ESTENDIDOS dele nos S2/S4/S5 = ground-truth
do SL estrutural. Também diagnostica S3 (não encontrada por ele). Procedimento tab_pin salvo."""
import os, sys, json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
HERE = R + "my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, R + "alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient
hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M") if t else "?"

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
try:
    dl = c.call_tool("draw_list") or {}
    print(f"tab {tid[:8]} · {dl.get('count')} shapes")
    for s in dl.get("shapes", []):
        nm = s.get("name")
        if nm in ("long_position", "short_position"):
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            p = pr.get("properties", {}) or {}
            if not pts: continue
            e = pts[0].get("price"); t0 = pts[0].get("time")
            stop_ticks = p.get("stopLevel"); prof_ticks = p.get("profitLevel")
            TICK = 0.01
            if nm == "long_position":
                sl = e - (stop_ticks or 0) * TICK; tg = e + (prof_ticks or 0) * TICK
            else:
                sl = e + (stop_ticks or 0) * TICK; tg = e - (prof_ticks or 0) * TICK
            risk = abs(e - sl); rr = abs(tg - e) / risk if risk else None
            print(f"  {nm} @ {hm(t0)}  entry {e:.2f}  SL {sl:.2f} (risco {risk:.2f} pts)  "
                  f"alvo {tg:.2f}  RxR {rr:.2f}" if rr else f"  {nm} @ {hm(t0)} entry {e} SEM stop")
        elif nm == "text":
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            txt = (pr.get("properties") or {}).get("text")
            if pts:
                print(f"  label '{txt}' @ {hm(pts[0].get('time'))} price {pts[0].get('price')}")
finally:
    c.stop()
