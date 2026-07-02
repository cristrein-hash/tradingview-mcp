#!/usr/bin/env python3
"""Cris: TESTAR CADA correção ISOLADA (não o agregado) com exit NEUTRO-AO-BETA (target+2R) vs random do MESMO regime.
Componentes: BULL-reteste(#1), BULL-fallback(#3), BEAR-capit(#5), RANGE-fundo(#2). Cada um vs 200 draws de entradas
aleatórias no mesmo tipo de regime, mesmo N. Se um componente bate random-p95 com target+2R = edge de entrada real isolado.
custo 0.35."""
import json,io,contextlib,sys,bisect,random
from pathlib import Path
random.seed(20260701)
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
def tgt2(bi,entry,sl):
    risk=entry-sl
    if risk<=0: return None
    tgt=entry+2*risk;end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
        if H[j]>=tgt: return 2.0
    return (C[end]-entry)/risk
# componentes estruturais isolados
comp={'BULL-reteste':[], 'BULL-fallback':[], 'BEAR-capit':[], 'RANGE-fundo':[]}
for idx in range(1,len(segs)):
    s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo']
    i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
    if i1-i0<3: continue
    if s['regime']=='BULL':
        niv=prev['hi'];zlo=niv-amp/3
        k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
        if k is None: continue
        rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
        if rj is not None: comp['BULL-reteste'].append((rj,C[rj],zlo-0.5*atr(rj)))
        else: comp['BULL-fallback'].append((i0,C[i0],min(L[i0:k+1])-0.5*atr(i0)))
    elif s['regime']=='BEAR':
        zd=bear_deep(idx)
        if zd:
            j=next((j for j in range(i0,i1+1) if L[j]<=zd[1]),None)
            if j is not None: comp['BEAR-capit'].append((j,C[j],zd[0]-0.5*atr(j)))
    else:
        for j in range(i0+2,i1+1):
            rmin=min(L[i0:j+1]);rmax=max(H[i0:j+1])
            if rmax>rmin and (C[j]-rmin)/(rmax-rmin)<0.34: comp['RANGE-fundo'].append((j,C[j],rmin-0.5*atr(j)));break
# random pools por regime
def rand_pool(regs,N):
    boxes=[(bisect.bisect_left(T,s['start']),bisect.bisect_right(T,s['end'])-1) for s in segs if s['regime'] in regs and s['bars']>=3]
    out=[]
    for _ in range(N):
        i0,i1=random.choice(boxes)
        if i1-i0<3: continue
        j=random.randint(i0,i1-1);e=C[j];out.append((j,e,e-1.5*atr(j)))
    return out
def summ(ents):
    rs=[round((tgt2(bi,e,sl) or 0)-COST,2) for bi,e,sl in ents if e-sl>0]
    return sum(rs),(sum(rs)/len(rs) if rs else 0),(100*sum(1 for r in rs if r>0)/len(rs) if rs else 0),len(rs)
REGMAP={'BULL-reteste':{'BULL'},'BULL-fallback':{'BULL'},'BEAR-capit':{'BEAR'},'RANGE-fundo':{'RANGE'}}
print("EDGE ISOLADO por correção — exit target+2R (neutro-ao-beta) vs random do MESMO regime (200 draws)\n")
print(f"{'componente':16} {'estrut sumR/avgR/WR/N':30} {'random med/p95':20} veredito")
for name,ents in comp.items():
    if not ents: print(f"{name:16} N=0");continue
    ssum,savg,swr,sn=summ(ents)
    rsums=[]
    for _ in range(200):
        rs,_,_,_=summ(rand_pool(REGMAP[name],sn));rsums.append(rs)
    rsums.sort();rmed=rsums[100];rp95=rsums[190]
    verd="EDGE (>p95)" if ssum>rp95 else ("~random (<=med)" if ssum<=rmed else "meio-termo")
    print(f"{name:16} {f'{ssum:+6.1f}/{savg:+5.2f}/{swr:3.0f}%/n{sn}':30} {f'{rmed:+5.1f}/{rp95:+5.1f}':20} {verd}")
