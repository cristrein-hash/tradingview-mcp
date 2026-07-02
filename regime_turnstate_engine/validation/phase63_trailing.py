#!/usr/bin/env python3
"""TRAILING STOP causal (chandelier) nos 10 bull-reteste: stop = max(SL_inicial, highest_high_desde_entry − K*ATR),
sobe mas nunca desce. Captura parte do MFE sem adivinhar o topo. SL inicial = swing-low do reteste (regra causal Cris).
Testa K=2/2.5/3 ATR. Trade-a-trade (K=3) + painel por K. Compara com let-run, original, V2. custo 0.35."""
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
def letrun(bi,entry,sl):
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
def trail(bi,entry,sl0,K):
    risk=entry-sl0;peak=H[bi];stop=sl0
    for j in range(bi+1,n4):
        peak=max(peak,H[j]);stop=max(stop,peak-K*atr(j))
        if L[j]<=stop: return (stop-entry)/risk,j
    return (C[n4-1]-entry)/risk,n4-1
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
    entry=C[rj];a=atr(rj);sl0=min(L[max(i0,rj-4):rj+1])-0.1*a
    if entry-sl0<=0: continue
    base.append({"bi":rj,"date":dt.datetime.utcfromtimestamp(T[rj]).strftime("%Y-%m-%d"),"entry":entry,"sl0":sl0,
                 "R_let":round(letrun(rj,entry,sl0)-COST,2)})
base.sort(key=lambda x:x['bi'])
for K in (2,2.5,3):
    for x in base:
        r,ej=trail(x['bi'],x['entry'],x['sl0'],K);x[f'K{K}']=round(r-COST,2);x[f'K{K}bars']=ej-x['bi']
print(f"{'#':4}{'date':11}{'R_letrun':9}{'trailK2':8}{'trailK2.5':10}{'trailK3':8}")
for i,x in enumerate(base,1):
    print(f"B{i:<3}{x['date']:11}{x['R_let']:+9.2f}{x['K2']:+8.2f}{x['K2.5']:+10.2f}{x['K3']:+8.2f}")
def pan(key,tag):
    n=len(base);w=sum(1 for x in base if x[key]>0);s=sum(x[key] for x in base)
    cum=peak=dd=0;st=mx=0
    for x in base:
        cum+=x[key];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x[key]<=0 else 0;mx=max(mx,st)
    print(f"{tag:24} N={n} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:5.1f} streak={mx} big={sum(1 for x in base if x[key]>=3)}")
print()
pan("R_let","let-run120")
for K in (2,2.5,3): pan(f"K{K}",f"trailing K={K}ATR")
print("\nRef: V2-base pura +36,2R/17tr · ajustes manuais hindsight +17,5R · causal-v1 +0,5R")
print(f"\nB10 (2026-01-12) por método: letrun {base[-1]['R_let']:+.2f} | K2 {base[-1]['K2']:+.2f} | K2.5 {base[-1]['K2.5']:+.2f} | K3 {base[-1]['K3']:+.2f}  (MFE foi +8.5R)")
