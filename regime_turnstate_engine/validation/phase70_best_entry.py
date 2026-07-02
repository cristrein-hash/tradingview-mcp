#!/usr/bin/env python3
"""Existe entrada MELHOR que bull-reteste? Compara 3 famílias de entrada da V2, cada uma com exit-NEUTRO (target+2R, isola
timing do beta) E let-run, contra random do MESMO contexto (200 draws): (A) CAPITULAÇÃO = fundos profundos (BEAR bear_deep
OU RANGE pos<0.25); (B) BULL-reteste; (C) baseline. Se capitulação bate random-p95 com target+2R = edge de entrada real
(a melhor). custo 0.35."""
import json,io,contextlib,sys,bisect,csv,random,datetime as dt
from pathlib import Path
random.seed(20260701);COST=0.35;HZ=120
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for config import (robust, no daemon/global sys.path)
from config import paths as CP
VAL=CP.repo("regime_turnstate_engine","validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open(CP.causal_segments())),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
def tp2(bi,entry,sl):
    risk=entry-sl;tp=entry+2*risk;end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
        if H[j]>=tp: return 2.0
    return (C[end]-entry)/risk
def letrun(bi,entry,sl):
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
# entradas V2
Dr=CP.ruler("XAU_4H_L2_BPT_BOS_CHOCH","v1","results")
capit=[];v2bars=set()
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];entry=float(r["entry"]);sl=float(r["sl"]);amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3,prev['hi']);zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    keep=(s['regime']=='BULL' and ztop[0]<=entry<=ztop[1]) or (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.34)
    if keep and entry-sl>0:
        v2bars.add(bi)
        if (s['regime']=='BEAR') or (s['regime']=='RANGE' and pos<0.25):
            capit.append((bi,entry,sl))
# bull-reteste
bull=[]
for idx in range(1,len(segs)):
    s=segs[idx]
    if s['regime']!='BULL': continue
    prev=segs[idx-1];amp=prev['hi']-prev['lo'];niv=prev['hi'];zlo=niv-amp/3
    i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
    if i1-i0<3: continue
    k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
    if k is None: continue
    rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
    if rj is None or any(abs(rj-b)<=1 for b in v2bars): continue
    bull.append((rj,C[rj],zlo-0.5*atr(rj)))
def ev(ents,fn):
    rs=[round(fn(bi,e,sl)-COST,2) for bi,e,sl in ents if e-sl>0]
    n=len(rs);w=sum(1 for x in rs if x>0);s=sum(rs)
    cum=peak=dd=0;st=mx=0
    for x in rs:
        cum+=x;peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x<=0 else 0;mx=max(mx,st)
    return s,(s/n if n else 0),(100*w/n if n else 0),n,dd,mx
# random em RANGE+BEAR (contexto dos fundos) e em BULL (contexto reteste)
def rpool(regs,N):
    br=[(bisect.bisect_left(T,s['start']),bisect.bisect_right(T,s['end'])-1) for s in segs if s['regime'] in regs and s['bars']>=3]
    return [ (lambda a,b:(random.randint(a,b-1),))(a,b)[0] for a,b in [random.choice(br) for _ in range(N)] ]
def rand_sum(regs,N,fn):
    bis=[];br=[(bisect.bisect_left(T,s['start']),bisect.bisect_right(T,s['end'])-1) for s in segs if s['regime'] in regs and s['bars']>=3]
    for _ in range(N):
        a,b=random.choice(br);j=random.randint(a,b-1);bis.append(j)
    rs=[round(fn(j,C[j],C[j]-1.5*atr(j))-COST,2) for j in bis]
    return sum(rs)
print("FAMÍLIA           exit        sumR  avgR   WR   N   DD  strk | random med/p95     veredito")
for name,ents,regs in (("CAPITULAÇÃO",capit,{'RANGE','BEAR'}),("BULL-reteste",bull,{'BULL'})):
    for lbl,fn in (("target+2R",tp2),("let-run",letrun)):
        s,a,wr,n,dd,mx=ev(ents,fn)
        rs=sorted(rand_sum(regs,n,fn) for _ in range(200));rmed=rs[100];rp95=rs[190]
        verd="EDGE(>p95)" if s>rp95 else ("~beta(<=med)" if s<=rmed else "meio-termo")
        print(f"{name:16} {lbl:11}{s:+6.1f} {a:+5.2f} {wr:3.0f}% {n:3} {dd:5.1f} {mx:4} | {rmed:+6.1f}/{rp95:+6.1f}   {verd}")
