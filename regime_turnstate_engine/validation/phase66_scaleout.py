#!/usr/bin/env python3
"""Cris: bull-reteste são NATOS p/ long run (MFE +10 a +22R). Exit que a estratégia quer = garante R + deixa runner correr.
SCALE-OUT: SL inicial=zona-bottom. Se atinge +2R -> tira 50% a +2R, move stop da outra metade p/ BREAKEVEN, runner corre
com trailing K=3 ATR (nunca desce). Se stopa antes de +2R -> −1R cheio. R_blend = 0.5*part + 0.5*runner.
Compara com TP+2R puro, let-run, e o MFE. Painel + trade-a-trade. custo 0.35 (aplicado no fecho de cada perna proporcional)."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
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
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
v2bars=set()
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];entry=float(r["entry"]);sl=float(r["sl"]);amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3,prev['hi']);zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    keep=(s['regime']=='BULL' and ztop[0]<=entry<=ztop[1]) or (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.34)
    if keep and entry-sl>0: v2bars.add(bi)
def tp_pure(bi,entry,sl,m):
    risk=entry-sl;tp=entry+m*risk;end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
        if H[j]>=tp: return float(m)
    return (C[end]-entry)/risk
def scaleout(bi,entry,sl,K=3.0):
    risk=entry-sl;tp1=entry+2*risk;end=min(bi+HZ,n4-1);hit=None
    # fase 1: até atingir +2R ou stop
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0     # stopou antes de +2R: perde 1R cheio
        if H[j]>=tp1: hit=j;break
    if hit is None: return (C[end]-entry)/risk   # nunca atingiu +2R nem stop: close
    part=2.0                                       # 50% realizado a +2R
    # fase 2: runner (50%) com stop em BE, trailing K ATR
    peak=H[hit];stop=entry
    run=None
    for j in range(hit+1,end+1):
        peak=max(peak,H[j]);stop=max(stop,peak-K*atr(j))
        if L[j]<=stop: run=(stop-entry)/risk;break
    if run is None: run=(C[end]-entry)/risk
    return 0.5*part+0.5*run
base=[]
for idx in range(1,len(segs)):
    s=segs[idx]
    if s['regime']!='BULL': continue
    prev=segs[idx-1];amp=prev['hi']-prev['lo'];niv=prev['hi'];zlo=niv-amp/3
    i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
    if i1-i0<3: continue
    k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
    if k is None: continue
    rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
    if rj is None: continue
    if any(abs(rj-b)<=1 for b in v2bars): continue
    entry=C[rj];sl=zlo-0.5*atr(rj)
    if entry-sl<=0: continue
    base.append({"date":dt.datetime.utcfromtimestamp(T[rj]).strftime("%Y-%m-%d"),
        "t2":round(tp_pure(rj,entry,sl,2)-COST,2),"scale":round(scaleout(rj,entry,sl)-COST,2)})
base.sort(key=lambda x:x['date'])
print(f"{'#':4}{'date':12}{'TP+2R':8}{'scale-out(2R+runner)':20}")
for i,x in enumerate(base,1): print(f"B{i:<3}{x['date']:12}{x['t2']:+8.2f}{x['scale']:+8.2f}")
def pan(key,tag,rows):
    n=len(rows);w=sum(1 for x in rows if x[key]>0);s=sum(x[key] for x in rows)
    cum=peak=dd=0;st=mx=0
    for x in rows:
        cum+=x[key];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x[key]<=0 else 0;mx=max(mx,st)
    print(f"{tag:28} N={n} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:5.1f} streak={mx} big={sum(1 for x in rows if x[key]>=3)}")
print()
pan("t2","TP+2R puro",base)
pan("scale","SCALE-OUT (2R+runner BE)",base)
sub=[x for x in base if x['date'][:4] in ('2025','2026')]
pan("scale","SCALE-OUT só 2025-26",sub)
