#!/usr/bin/env python3
"""O que o E2 TERIA EMITIDO esta semana = campo REAL 'surfaced' (contexto converge E aponta para o lado do
candidato). Read-only, junta com outcome. Nao usa proxy. Horas Lisboa."""
import json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
L = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/"
shadow = [json.loads(x) for x in open(L + "e2_shadow.jsonl") if x.strip()]
outs = {}
for x in open(L + "e2_outcomes.jsonl"):
    if x.strip():
        r = json.loads(x); cid = r.get("candidate_id") or r.get("id")
        if cid: outs[cid] = r
def hm(ts):
    try: return dt.datetime.fromisoformat(ts).astimezone(LX).strftime("%d/%m %H:%M")
    except Exception: return (ts or "")[:16]

surf = []
for r in shadow:
    if r.get("surfaced") is True:
        c = r.get("candidate") or {}; t = r.get("thesis") or {}
        oc = (outs.get(c.get("id")) or {}).get("outcome", "?")
        surf.append((r.get("ts"), c, t, oc))
surf.sort(key=lambda z: z[0] or "")
print(f"=== E2 TERIA EMITIDO (surfaced=True) esta semana: {len(surf)} trades ===\n")
for ts, c, t, oc in surf:
    print(f"{hm(ts)} {c.get('direction')} {c.get('rule')}@{c.get('tf')} | entry {c.get('entry')} SL {c.get('sl')} "
          f"alvo {c.get('target')} RR {c.get('rr')} | conv={t.get('convergence')} convic={t.get('conviction')} | OUTCOME: {oc}")
print(f"\n  por outcome: TP {sum(1 for _,_,_,o in surf if o=='TP')} · "
      f"SL {sum(1 for _,_,_,o in surf if o=='SL')} · OPEN {sum(1 for _,_,_,o in surf if o=='OPEN')}")
print(f"  total de reads na semana: {len(shadow)} | destes, surfaced (E2 emitiria): {len(surf)} | "
      f"nao-surfaced (E2 calaria): {len(shadow)-len(surf)}")
