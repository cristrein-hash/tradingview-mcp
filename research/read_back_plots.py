#!/usr/bin/env python3
"""Le de volta as caixas desenhadas (pontos reais + tempo) p/ diagnosticar o erro de plotagem. Read-only."""
import os, sys, json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
HERE = "/Users/cristrein/tradingview-mcp/my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient
tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
def hm(t):
    try: return dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")
    except Exception: return str(t)
try:
    dl = c.call_tool("draw_list") or {}
    print(f"tab {tid[:8]} · total {dl.get('count')} shapes")
    for s in dl.get("shapes", []):
        if s.get("name") in ("long_position", "short_position"):
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            p = pr.get("properties", {})
            print(f"  {s['name']}: pontos={[(round(x.get('price',0),1), hm(x.get('time'))) for x in pts]} "
                  f"stopLevel={p.get('stopLevel')} profitLevel={p.get('profitLevel')}")
finally:
    c.stop()
