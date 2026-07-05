#!/usr/bin/env python3
"""Extrai TODOS os círculos do chart via MCP (rodada Layer 2, 2026-07-05).
Leitura MCP pura (não análise) — Cris adicionou fundos após os 61 do GT v4.
Grava results/cris_bottom_circles_all2_20260705.json e reporta o diff."""
import sys, json
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
from draw_xau_4h_trades import MCPClient
from collections import Counter
c = MCPClient(); c.start()
rows = []
try:
    st = c.call_tool("chart_get_state")
    dl = c.call_tool("draw_list")
    print("CHART", st.get("symbol"), st.get("resolution"),
          "| tipos:", dict(Counter(s.get("name") for s in dl["shapes"])))
    for s in dl["shapes"]:
        if s.get("name") != "circle":
            continue
        p = c.call_tool("draw_get_properties", {"entity_id": s["id"]})
        pts = p.get("points") or (p.get("properties") or {}).get("points")
        if not pts:
            continue
        ts = [q.get("time") for q in pts if q.get("time")]
        pr = [q.get("price") for q in pts if q.get("price") is not None]
        if ts and pr:
            rows.append((int(sum(ts) / len(ts)), round(sum(pr) / len(pr), 2)))
finally:
    c.stop()
rows.sort()
old = json.load(open(HERE / "results" / "cris_bottom_circles_all_20260705.json"))
json.dump(rows, open(HERE / "results" / "cris_bottom_circles_all2_20260705.json", "w"))
new = [r for r in rows if tuple(r) not in {tuple(x) for x in old}]
print(f"círculos agora: {len(rows)} (antes {len(old)}) · novos por tuple-diff (jitter incluso): {len(new)}")
for t, pr in new:
    print(" ", dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M"), f"{pr:.2f}")
