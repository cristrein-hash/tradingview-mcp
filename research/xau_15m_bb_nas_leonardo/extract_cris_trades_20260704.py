#!/usr/bin/env python3
"""Extrai as operações plotadas MANUALMENTE pelo Cris no chart 15M (2026-07-04) via MCP read-only.
Objetivo: dataset das operações que ELE faria, para engenharia reversa causal (sem lookahead).
Só leitura: chart_get_state + draw_list + draw_get_properties. Zero draw/remove/clear.
Output: results/cris_manual_trades_20260704.json (raw completo + resumo por shape)."""
import sys, json
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path("/Users/cristrein/tradingview-mcp/alert-bridge")))
from draw_xau_4h_trades import MCPClient

c = MCPClient(); c.start()
out = {"extracted_at": dt.datetime.utcnow().isoformat()}
try:
    st = c.call_tool("chart_get_state")
    out["chart"] = {"symbol": st.get("symbol"), "resolution": str(st.get("resolution"))}
    print(f"CHART: {out['chart']['symbol']}/{out['chart']['resolution']}")
    dl = c.call_tool("draw_list")
    shapes = dl.get("shapes") or []
    out["count"] = dl.get("count")
    print(f"drawings: {out['count']}")
    det = []
    for e in shapes:
        eid = e.get("id")
        rec = {"id": eid, "name": e.get("name")}
        try:
            pr = c.call_tool("draw_get_properties", {"entity_id": eid})
            rec["props"] = pr
        except Exception as ex:
            rec["props_error"] = str(ex)[:120]
        det.append(rec)
    out["shapes"] = det
finally:
    try: c.stop()
    except Exception: pass

(HERE / "results" / "cris_manual_trades_20260704.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
# resumo legível
for r in out.get("shapes", []):
    p = r.get("props") or {}
    pts = p.get("points") or p.get("point") or []
    print(f"  {r['name']:<18} id={r['id']} pts={json.dumps(pts)[:140]}")
print("OK → results/cris_manual_trades_20260704.json")
