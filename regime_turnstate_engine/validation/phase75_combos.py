#!/usr/bin/env python3
"""Combinar CAPITULAÇÃO(10) com cada variante deep_pull_bull → qual maximiza N mantendo STREAK baixo e avgR alto.
+ valida deep_pull base por-ano e jackknife-drop-ano (é edge robusto ou depende de 1 ano?). exit let-run, custo 0.35."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
from statistics import mean
from collections import defaultdict
COST=0.35;HZ=120
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for config import (robust, no daemon/global sys.path)
from config import paths as CP
VAL=CP.repo("regime_turnstate_engine","validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
segs=sorted(json.load(open(CP.causal_segments())),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def regime_at(bi):
    idx=seg_idx(T[bi]);return segs[idx]['regime'] if idx is not None else '?'
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
TR=[0.0]*n4
for i in range(1,n4): TR[i]=max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1]))
ATR=[0.0]*n4
for i in range(14,n4): ATR[i]=mean(TR[i-13:i+1])
def rsi(i,k=14):
    g=l=0
    for j in range(i-k+1,i+1):
        d=C[j]-C[j-1]
        if d>0:g+=d
        else:l-=d
    return 50 if g+l==0 else 100-100/(1+(g/k)/((l/k) if l>0 else 1e-9))
def dpos(i,n):
    lo=min(L[i-n+1:i+1]);hi=max(H[i-n+1:i+1]);return (C[i]-lo)/(hi-lo) if hi>lo else .5
def SL(i): return min(L[max(0,i-4):i+1])-0.5*ATR[i]
def letrun(bi,entry,sl):
    if entry-sl<=0:return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl:return -1.0
    return (C[end]-entry)/(entry-sl)
def base(i): return regime_at(i)=='BULL' and dpos(i,40)<0.30 and C[i]>C[i-1]
VAR={"base":lambda i:base(i),
 "+swept":lambda i:base(i) and L[i]<min(L[i-20:i]),
 "+rsi_turn":lambda i:base(i) and rsi(i-1)<40 and rsi(i)>rsi(i-1),
 "+deep20":lambda i:regime_at(i)=='BULL' and dpos(i,40)<0.20 and C[i]>C[i-1]}
def gen(pred):
    out=[];last=-99
    for i in range(60,n4-HZ-1):
        if i-last<5: continue
        try:
            if pred(i):
                sl=SL(i)
                if C[i]-sl>0:
                    r=letrun(i,C[i],sl)
                    if r is not None: out.append((i,round(r-COST,2)));last=i
        except: pass
    return out
def stats(rows):
    rows=sorted(rows);n=len(rows)
    if n==0: return None
    w=sum(1 for _,r in rows if r>0);s=sum(r for _,r in rows)
    cum=peak=dd=0;st=mx=0
    for _,r in rows:
        cum+=r;peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if r<=0 else 0;mx=max(mx,st)
    return n,100*w/n,s,s/n,dd,mx,sum(1 for _,r in rows if r>=3)
# capitulação V2 (10)
Dr=CP.ruler("XAU_4H_L2_BPT_BOS_CHOCH","v1","results")
capit=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);entry=float(r["entry"]);sl=float(r["sl"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0 or entry-sl<=0: continue
    s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo'];zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    if (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.25):
        rr=letrun(bi,entry,sl)
        if rr is not None: capit.append((bi,round(rr-COST,2)))
capbars=set(b for b,_ in capit)
print("COMBINAÇÕES capitulação(10) + variante deep_pull (só trades novos, dedup ±2b):")
print(f"  {'CAPIT só':22} N={len(capit):3} WR={stats(capit)[1]:3.0f}% sumR={stats(capit)[2]:+6.1f} avgR={stats(capit)[3]:+.2f} DD={stats(capit)[4]:5.1f} STREAK={stats(capit)[5]}")
for name,pred in VAR.items():
    add=[(b,r) for b,r in gen(pred) if not any(abs(b-cb)<=2 for cb in capbars)]
    comb=capit+add;st=stats(comb)
    n,wr,s,avg,dd,mx,big=st
    print(f"  CAPIT+deep{name:12} N={n:3} WR={wr:3.0f}% sumR={s:+6.1f} avgR={avg:+.2f} DD={dd:5.1f} STREAK={mx} big={big}  (+{len(add)} novos)")
print("\nVALIDAÇÃO deep_pull base — por-ano + jackknife (drop-ano):")
b=gen(VAR['base'])
by=defaultdict(list)
for bi,r in b: by[dt.datetime.utcfromtimestamp(T[bi]).year].append(r)
for y in sorted(by): print(f"  {y}: n={len(by[y]):2} sumR={sum(by[y]):+6.1f} avgR={mean(by[y]):+.2f}")
tot=sum(r for _,r in b)
print("  jackknife (sumR removendo cada ano):")
for y in sorted(by): print(f"    sem {y}: sumR={tot-sum(by[y]):+6.1f} avgR={(tot-sum(by[y]))/(len(b)-len(by[y])):+.2f}")
