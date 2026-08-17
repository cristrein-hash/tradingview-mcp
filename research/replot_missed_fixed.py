#!/usr/bin/env python3
"""FIX do erro de plotagem: as caixas colapsavam (largura 0, mesmo ponto) porque os tempos 16-20/07 estavam FORA
do range de barras 15M carregado. Solucao: carregar o range (set_visible_range 15->25/07) ANTES de plotar, depois
draw_clear + re-plotar os 9 + LER DE VOLTA para confirmar largura/tempo corretos. Canon 15M."""
import os, sys, json, time, datetime as dt
from zoneinfo import ZoneInfo
UTC = dt.timezone.utc; LX = ZoneInfo("Europe/Lisbon")
HERE = "/Users/cristrein/tradingview-mcp/my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
BAR = 900; WIDTH = 10
mw = json.load(open("/Users/cristrein/tradingview-mcp/research/.e2_missed_winners.json"))
FROM = int(dt.datetime(2026, 7, 15, 0, 0, tzinfo=UTC).timestamp())
TO = int(dt.datetime(2026, 7, 25, 12, 0, tzinfo=UTC).timestamp())
hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M") if t else "?"

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
try:
    rv = c.call_tool("chart_set_visible_range", {"from": FROM, "to": TO})
    print(f"set_visible_range 15->25/07: {rv.get('success')}")
    time.sleep(3)                                       # deixar carregar as barras historicas
    c.call_tool("draw_clear")
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
                    "text": f"#{k+1}", "overrides": json.dumps({"color": "#1a8917", "bold": True, "fontsize": 12})})
    print(f"plotados {drawn}/{len(mw)}")
    # LER DE VOLTA p/ confirmar que agora tem largura e tempos distintos
    print("\nVERIFICAÇÃO (pontos reais apos fix):")
    dl = c.call_tool("draw_list") or {}
    okw = 0
    for s in dl.get("shapes", []):
        if s.get("name") in ("long_position", "short_position"):
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            if len(pts) >= 2:
                t0, t1 = pts[0].get("time"), pts[1].get("time")
                width_ok = t0 != t1
                okw += width_ok
                print(f"  {pts[0].get('price'):.1f} @ {hm(t0)} -> {hm(t1)}  largura={'OK' if width_ok else 'ZERO!'}")
    print(f"\ncom largura: {okw}/9")
finally:
    c.stop()
