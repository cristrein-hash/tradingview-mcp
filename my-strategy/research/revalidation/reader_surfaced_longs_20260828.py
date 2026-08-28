#!/usr/bin/env python3
"""LONGs SURFACED pelo reader/E2 — histórico completo com resolução SL-first 3R (pergunta Cris 28/08).
Materializado (regra output-órfão). py3 stdlib."""
import json,datetime as dt
B='/Users/cristrein/tradingview-mcp/alert-bridge/logs/'
LX=dt.timezone(dt.timedelta(hours=1))
def ts(x):
    if isinstance(x,(int,float)): return x
    try: return dt.datetime.fromisoformat(str(x).replace('Z','+00:00')).timestamp()
    except: return 0
bars=[json.loads(l) for l in open('/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_15m.jsonl') if l.strip()]
T=[b['t'] for b in bars];H=[b['h'] for b in bars];L=[b['l'] for b in bars]
def resolve(t0,e,sl,lng):
    if not(e and sl): return "SEM-NUM",None,None
    r=(e-sl) if lng else (sl-e)
    if r<=0: return "RISK<=0",None,None
    tgt=e+3*r if lng else e-3*r
    i0=next((i for i,t in enumerate(T) if t>t0),None)
    if i0 is None: return "SEM-BARRAS",None,None
    mfe=0.0
    for i in range(i0,len(T)):
        mfe=max(mfe,(H[i]-e)/r if lng else (e-L[i])/r)
        if lng:
            if L[i]<=sl: return "LOSS",-1.0,round(mfe,2)
            if H[i]>=tgt: return "WIN",3.0,round(mfe,2)
        else:
            if H[i]>=sl: return "LOSS",-1.0,round(mfe,2)
            if L[i]<=tgt: return "WIN",3.0,round(mfe,2)
    return "OPEN",0.0,round(mfe,2)
verd=[json.loads(l) for l in open(B+'e2_verdicts.jsonl') if l.strip()]
cands=[json.loads(l) for l in open(B+'e1_candidates.jsonl') if l.strip()]
sh=[json.loads(l) for l in open(B+'e2_shadow.jsonl') if l.strip()]
surf_ts={ts(s.get('ts')) for s in sh if s.get('surfaced')}
rows=[]
for v in verd:
    if (v.get('direction') or '').upper()!='LONG': continue
    t=ts(v.get('bar_time') or v.get('ts'))
    sf=v.get('surfaced')
    if sf is None:
        sf=any(abs(x-ts(v.get('ts')))<=900 for x in surf_ts)
    if not sf: continue
    cc=[c for c in cands if c.get('rule')==v.get('rule') and c.get('direction')==v.get('direction')]
    best=min(cc,key=lambda c:abs(ts(c.get('t') or c.get('ts'))-t)) if cc else None
    e=sl=None
    if best and abs(ts(best.get('t') or best.get('ts'))-t)<=3600:
        e,sl=best.get('entry'),best.get('sl')
    o,R,mfe=resolve(t,e,sl,True)
    rows.append((t,v.get('rule'),o,R,mfe))
print(f"LONGs SURFACED pelo E2 ({len(verd)} vereditos no log):")
w=l=op=0
for t,rule,o,R,mfe in sorted(rows):
    print(f"  {dt.datetime.fromtimestamp(t,LX).strftime('%d/%m %H:%M')} {rule:<16} {o:<5} MFE {mfe}")
    w+=o=='WIN';l+=o=='LOSS';op+=o=='OPEN'
print(f"TOTAL: {len(rows)} · {w}W-{l}L-{op}open · sumR {3*w-l:+d}")
