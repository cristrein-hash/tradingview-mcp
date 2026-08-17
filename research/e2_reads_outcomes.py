#!/usr/bin/env python3
"""Junta as leituras shadow do E2 (tese) com os outcomes resolvidos (e2_outcomes.jsonl, TP/SL/OPEN) por
candidate_id. Display read-only p/ revisao humana — mostra se o juizo do E2 (convergencia+fit) bate com o
que o mercado fez. Nao pontua/nao gate. Horas Lisboa."""
import json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
L = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/"
shadow = [json.loads(x) for x in open(L + "e2_shadow.jsonl") if x.strip()]
outs = {}
for x in open(L + "e2_outcomes.jsonl"):
    if not x.strip(): continue
    r = json.loads(x)
    cid = r.get("candidate_id") or r.get("id")
    if cid: outs[cid] = r

def hm(ts):
    try: return dt.datetime.fromisoformat(ts).astimezone(LX).strftime("%d/%m %H:%M")
    except Exception: return (ts or "")[:16]

def favorable(t):
    return t.get("candidate_fit") == "aligned" and t.get("convergence") in ("high", "moderate")

print("=== E2 READS × OUTCOMES (candidato: TP=bateu alvo · SL=bateu stop · OPEN=nao resolvido) ===\n")
rowsj = []
for r in shadow:
    t = r.get("thesis") or {}
    if not t.get("convergence"): continue                 # ignora os 4 branco (dia-1, erro transitorio)
    c = r.get("candidate") or {}
    o = outs.get(c.get("id")) or {}
    oc = o.get("outcome", "?")
    rowsj.append((r.get("ts"), c, t, oc, o))
rowsj.sort(key=lambda z: z[0] or "")
for ts, c, t, oc, o in rowsj:
    fav = "FAVORÁVEL" if favorable(t) else "desfavorável"
    print(f"{hm(ts)} {c.get('direction')} {c.get('rule')}@{c.get('tf')} {c.get('entry')}->{c.get('target')} "
          f"| E2: conv={t.get('convergence')} fit={t.get('candidate_fit')} ctx={t.get('context_direction')} [{fav}] "
          f"| OUTCOME: {oc}")

# resumo honesto: o juizo do E2 bate com o outcome? (candidato tomado)
print("\n=== o juízo do E2 vs o que o mercado fez (candidatos RESOLVIDOS) ===")
for lbl, sel in [("E2 FAVORÁVEL (aligned + conv moderate/high)", favorable),
                 ("E2 desfavorável (against/orthogonal ou conv low/incoherent)", lambda t: not favorable(t))]:
    g = [(oc) for ts, c, t, oc, o in rowsj if sel(t) and oc in ("TP", "SL")]
    tp = g.count("TP"); sl = g.count("SL")
    opn = sum(1 for ts, c, t, oc, o in rowsj if sel(t) and oc == "OPEN")
    n = len(g)
    print(f"  {lbl}: resolvidos {n} → TP {tp} / SL {sl}" + (f"  (WR {100*tp//n}%)" if n else "") + f"  · +{opn} OPEN")
print("\nNOTA: 'FAVORÁVEL' = o E2 diria para tomar; 'desfavorável' = diria para skipar. Se o E2 lê bem,")
print("os FAVORÁVEIS tendem a TP e os desfavoráveis a SL (skip correto). Amostra pequena/1 semana — indicativo.")
