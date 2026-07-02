#!/usr/bin/env python3
"""Cris: B8/B9/B10 são entradas perfeitas em bull-run (MFE alto). Testar se um TP FIXO (causal, não adivinha topo)
captura o movimento antes do giveback. Para os 10 bull-reteste: MFE/MAE em R (SL zona-bottom, mais largo), e resultado
com target +2R e +3R (TP-first vs SL-first). Vê se as boas (B8/B9/B10) se realizam e o painel. custo 0.35."""
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
def target(bi,entry,sl,m):
    risk=entry-sl;tp=entry+m*risk;end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
        if H[j]>=tp: return float(m)
    return (C[end]-entry)/risk
def mfe_mae(bi,entry,sl):
    risk=entry-sl;end=min(bi+HZ,n4-1);mfe=mae=0
    for j in range(bi+1,end+1):
        mfe=max(mfe,(H[j]-entry)/risk);mae=min(mae,(L[j]-entry)/risk)
        if L[j]<=sl: break
    return mfe,mae
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
    mfe,mae=mfe_mae(rj,entry,sl)
    base.append({"bi":rj,"date":dt.datetime.utcfromtimestamp(T[rj]).strftime("%Y-%m-%d"),"entry":entry,"sl":sl,
        "mfe":round(mfe,2),"mae":round(mae,2),"t2":round(target(rj,entry,sl,2)-COST,2),"t3":round(target(rj,entry,sl,3)-COST,2)})
base.sort(key=lambda x:x['bi'])
print(f"{'#':4}{'date':11}{'MFE_R':7}{'MAE_R':7}{'TP+2R':7}{'TP+3R':7}")
for i,x in enumerate(base,1):
    star=" <<" if x['date'][:4] in ('2025','2026') else ""
    print(f"B{i:<3}{x['date']:11}{x['mfe']:+7.2f}{x['mae']:+7.2f}{x['t2']:+7.2f}{x['t3']:+7.2f}{star}")
def pan(key,tag,rows):
    n=len(rows);w=sum(1 for x in rows if x[key]>0);s=sum(x[key] for x in rows)
    cum=peak=dd=0;st=mx=0
    for x in rows:
        cum+=x[key];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x[key]<=0 else 0;mx=max(mx,st)
    print(f"{tag:26} N={n} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:5.1f} streak={mx}")
print("\n== TODAS as 10 ==")
pan("t2","TP+2R (todas)",base);pan("t3","TP+3R (todas)",base)
print("== só as B8/B9/B10 (bull-run 2025-26) ==")
sub=[x for x in base if x['date'][:4] in ('2025','2026')]
pan("t2","TP+2R (2025-26)",sub);pan("t3","TP+3R (2025-26)",sub)
