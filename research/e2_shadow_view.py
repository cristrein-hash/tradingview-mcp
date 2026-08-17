#!/usr/bin/env python3
"""Display read-only das leituras shadow do E2 (tese + raciocinio) para revisao humana. Nao computa nada."""
import json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
F = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/e2_shadow.jsonl"
rows = [json.loads(l) for l in open(F) if l.strip()]
rows.sort(key=lambda r: r.get("ts", ""))

def hm(ts):
    try: return dt.datetime.fromisoformat(ts).astimezone(LX).strftime("%d/%m %H:%M")
    except Exception: return (ts or "")[:16]

print(f"=== {len(rows)} leituras shadow do E2 (tese; outcome ainda nao backfilled) ===\n")
for i, r in enumerate(rows):
    c = r.get("candidate") or {}; t = r.get("thesis") or {}
    th = (t.get("thesis") or "")[:140]
    print(f"[{i:2}] {hm(r.get('ts'))} {c.get('direction')} {c.get('rule')}@{c.get('tf')} "
          f"{c.get('entry')}->{c.get('target')} RR{c.get('rr')} | conv={t.get('convergence')} "
          f"convic={t.get('conviction')} ctx={t.get('context_direction')} fit={t.get('candidate_fit')}")
    print(f"     {th}\n")
