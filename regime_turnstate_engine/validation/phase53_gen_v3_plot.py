#!/usr/bin/env python3
# LEGACY_PRE_CANON / DO_NOT_USE_AS_CANONICAL — convencao pre-canon (width 12 / label R). PLOTTING_CANON_MASTER_REQUIRED: docs/project_authority/PLOTTING_CANON_MASTER.md e a autoridade para novos plots (R2 2026-07-02).
"""Gera os 31 trades V3 GATILHO-DE-ZONA em formato de plotagem canónico (long_position, TICKS, largura 12 barras).
Regras = phase50: BULL toque-zona-top OU fallback-demanda · BEAR toque-zona-capitulação-profunda · RANGE fundo pos<0.34.
SL=fundo-zona−0.5ATR. Exit real=let-run HZ120 (cor win/loss). Emite /tmp/v3_zona_trades.json + linhas pipe p/ desenho."""
import json,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
MT=0.01;COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def letrun(bi,entry,sl):
    if entry-sl<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
def entries():
    out=[]
    for idx in range(1,len(segs)):
        s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo']
        i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<3: continue
        if s['regime']=='BULL':
            niv=prev['hi'];zlo=niv-amp/3
            k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
            if k is None: continue
            rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
            if rj is not None: out.append((rj,C[rj],zlo-0.5*atr(rj),'BULL','reteste'))
            else: out.append((i0,C[i0],min(L[i0:k+1])-0.5*atr(i0),'BULL','fallback'))
        elif s['regime']=='BEAR':
            zd=bear_deep(idx)
            if not zd: continue
            j=next((j for j in range(i0,i1+1) if L[j]<=zd[1]),None)
            if j is not None: out.append((j,C[j],zd[0]-0.5*atr(j),'BEAR','capit'))
        else:
            for j in range(i0+2,i1+1):
                rmin=min(L[i0:j+1]);rmax=max(H[i0:j+1])
                if rmax>rmin and (C[j]-rmin)/(rmax-rmin)<0.34: out.append((j,C[j],rmin-0.5*atr(j),'RANGE','fundo'));break
    return out
out=[]
for j,entry,sl,rg,typ in entries():
    R=letrun(j,entry,sl)
    if R is None: continue
    risk=entry-sl
    out.append({"bi":j,"date":dt.datetime.utcfromtimestamp(T[j]).strftime("%Y-%m-%d"),"reg":rg,"typ":typ,
        "entry_time":T[j],"exit_time":T[j]+12*14400,"entry":round(entry,2),"target":round(entry+3*risk,2),
        "stopLevel":int(round(risk/MT)),"profitLevel":int(round(3*risk/MT)),"R":round(R-COST,2),"win":(R-COST)>0})
out.sort(key=lambda x:x['entry_time'])
json.dump(out,open("/tmp/v3_zona_trades.json","w"))
w=sum(1 for x in out if x['win'])
print(f"V3 GATILHO-DE-ZONA — {len(out)} trades (win {w}/loss {len(out)-w}) sumR {sum(x['R'] for x in out):+.1f}")
print(f"período {out[0]['date']} -> {out[-1]['date']}  regimes "+str({rg:sum(1 for x in out if x['reg']==rg) for rg in ('BULL','RANGE','BEAR')}))
for i,x in enumerate(out,1): print(f'{i:2}|{x["date"]}|{x["reg"]:5}|{x["typ"]:8}|entry {x["entry"]}|SL {x["stopLevel"]}tk|R {x["R"]:+.1f}|{"W" if x["win"] else "L"}')
