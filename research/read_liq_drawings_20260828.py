#!/usr/bin/env python3
"""LER as marcações MANUAIS do Cris na tab 15M via MCP pinado (procedimento tab_pin salvo):
liquidez nos pavios (linhas/rays horizontais) + diagonais de liquidez construída (trend lines) +
posições. Dump completo com pontos (t, preço) para estudo. Read-only. py3.9."""
import os
import sys
import json

HERE = "/Users/cristrein/tradingview-mcp/my-strategy/core"
sys.path.insert(0, HERE)
sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin  # noqa: E402
from draw_xau_4h_trades import MCPClient  # noqa: E402

OUT = "/Users/cristrein/tradingview-mcp/research/liq_drawings_15m_20260828.json"

tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
if not tid:
    print("sem tab 15M"); sys.exit(1)
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
try:
    dl = c.call_tool("draw_list") or {}
    shapes = dl.get("shapes", [])
    print(f"tab {tid[:8]} · {len(shapes)} desenhos · tipos:", sorted({s.get("name") for s in shapes}))
    out = []
    for s in shapes:
        pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
        pts = [{"t": p.get("time"), "price": p.get("price")} for p in (pr.get("points") or [])]
        out.append({"id": s["id"], "name": s.get("name"), "points": pts,
                    "text": (pr.get("properties") or {}).get("text"),
                    "props": {k: v for k, v in (pr.get("properties") or {}).items()
                              if k in ("stopLevel", "profitLevel", "linecolor", "linestyle", "linewidth")}})
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"gravado {OUT} ({len(out)} desenhos)")
finally:
    try: c.stop()
    except Exception: pass
