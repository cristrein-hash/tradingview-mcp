#!/usr/bin/env python3
"""AVALIACAO E2 da FONTE UNICA e2_shadow.jsonl (candidato+surfaced+reasoning juntos; ordem Cris 28/08).
Cada sinal: aprovado/skip + razao textual do proprio reader + resultado SL-first 3R. Materializado."""
import json,datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); LX=dt.timezone(dt.timedelta(hours=1))
def jl(p):
    try: return [json.loads(l) for l in open(p) if l.strip()]
    except: return []
bars=jl(REPO/"my-strategy/core/bar_store/store/bars_15m.jsonl")
T=[b['t'] for b in bars];H=[b['h'] for b in bars];L=[b['l'] for b in bars]
def resolve(t0,e,sl,tgt,lng):
    if not(t0 and e and sl): return "?",None
    i0=next((i for i,t in enumerate(T) if t>t0),None)
    if i0 is None: return "FUT",None
    risk=(e-sl) if lng else (sl-e)
    if risk<=0: return "R<=0",None
    tgt=tgt or (e+3*risk if lng else e-3*risk)
    for i in range(i0,len(T)):
        if lng:
            if L[i]<=sl: return "LOSS",-1.0
            if H[i]>=tgt: return "WIN",3.0
        else:
            if H[i]>=sl: return "LOSS",-1.0
            if L[i]<=tgt: return "WIN",3.0
    return "OPEN",0.0
def hm(t): return dt.datetime.fromtimestamp(int(t),LX).strftime('%d/%m %H:%M') if t else '?'
sh=jl(REPO/"alert-bridge/logs/e2_shadow.jsonl")
rows=[]
for s in sh:
    c=s.get('candidate') or {}; th=s.get('thesis') or {}
    t=c.get('bar_time'); lng=(c.get('direction') or '').upper()=='LONG'
    o,R=resolve(t,c.get('entry'),c.get('sl'),c.get('target'),lng)
    rows.append(dict(t=t,dir=c.get('direction'),rule=c.get('rule'),surf=bool(s.get('surfaced')),
                     o=o,R=R,fit=th.get('candidate_fit'),conv=th.get('conviction'),
                     reason=str(th.get('reasoning') or '').replace('\n',' ')))
rows=[r for r in rows if r['t']]
rows.sort(key=lambda x:x['t'])
out=Path(REPO/"my-strategy/research/revalidation/e2_reader_reasoning_eval_20260828.json")
out.write_text(json.dumps(rows,ensure_ascii=False,indent=1))
ap=[r for r in rows if r['surf']]; sk=[r for r in rows if not r['surf']]
apw=sum(1 for r in ap if r['R']==3);apl=sum(1 for r in ap if r['R']==-1)
skg=sum(1 for r in sk if r['R']==-1);skb=sum(1 for r in sk if r['R']==3)
print(f"FONTE: e2_shadow.jsonl · {len(rows)} leituras · APROVADOS {len(ap)} ({apw}W-{apl}L) · SKIPS {len(sk)} ({skg} evitaram perda, {skb} perderam WIN)")
print(f"gravado {out.name} (todos os {len(rows)} com razao textual completa)")
