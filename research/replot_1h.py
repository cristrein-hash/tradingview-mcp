#!/usr/bin/env python3
"""FIX definitivo: plota os 9 winners no 1H (tem a semana toda carregada -> ancora bem), pois o 15M so tem ~2
dias em memoria e colapsava as caixas antigas. Exceção declarada ao canon 15M/4H (motivo: histórico). Largura ~6h,
verde. LE DE VOLTA para confirmar largura/tempos distintos."""
import os, sys, json, time, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
HERE = "/Users/cristrein/tradingview-mcp/my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
WIDTH_S = 6 * 3600
mw = json.load(open("/Users/cristrein/tradingview-mcp/research/.e2_missed_winners.json"))
hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M") if t else "?"

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
try:
    c.call_tool("chart_set_timeframe", {"timeframe": "60"})   # 1H tem a semana carregada
    time.sleep(4)
    c.call_tool("draw_clear")
    drawn = 0
    for k, m in enumerate(mw):
        shape = "long_position" if m["dir"] == "LONG" else "short_position"
        r1 = c.call_tool("draw_shape", {"shape": shape,
            "point": {"time": m["t"], "price": m["entry"]},
            "point2": {"time": m["t"] + WIDTH_S, "price": m["tgt"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(m["entry"], m["sl"]),
                                     "profitLevel": price_to_ticks_offset(m["entry"], m["tgt"])})})
        drawn += bool(r1.get("success"))
        R = m["entry"] - m["sl"]
        c.call_tool("draw_shape", {"shape": "text", "point": {"time": m["t"], "price": m["entry"] + 0.5 * R},
                    "text": f"#{k+1}", "overrides": json.dumps({"color": "#1a8917", "bold": True, "fontsize": 12})})
    print(f"plotados {drawn}/{len(mw)} no 1H")
    print("\nVERIFICAÇÃO (pontos reais):")
    dl = c.call_tool("draw_list") or {}
    okw = 0
    for s in dl.get("shapes", []):
        if s.get("name") in ("long_position", "short_position"):
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            if len(pts) >= 2:
                t0, t1 = pts[0].get("time"), pts[1].get("time")
                w = t0 != t1; okw += w
                print(f"  {pts[0].get('price'):.1f} @ {hm(t0)} -> {hm(t1)}  largura={'OK' if w else 'ZERO!'}")
    print(f"\ncom largura: {okw}/9")
finally:
    c.stop()
