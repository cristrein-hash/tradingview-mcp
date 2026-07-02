#!/usr/bin/env python3
"""DA repro: measure the ROBUST SKELETON of phase39 book WITHOUT the fitted BEAR thresholds.
Skeleton BEAR = keep ALL dist<=-2 capitulations (drop nearest_below/RSI filter). BULL cap-tardias. RANGE keep.
Also isolate: bear-faca-skip ALONE (no bull-cap). Claim to verify: skeleton ~+54R, causal.
Orphan-guard: exits if inputs missing."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
from collections import defaultdict
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation")
if not VAL.exists(): sys.exit("orphan: VAL dir missing")
sys.path.insert(0,str(VAL))
SEGP=Path("/tmp/causal_segments_v10.json")
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
RAWP=Dr/"repro_recovery/raw_features_2020_2026.jsonl"
CSVP=Dr/"results/l2_bpt_regua_structural.csv"
for p in (SEGP,RAWP,CSVP):
    if not p.exists(): sys.exit(f"orphan: missing {p}")
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def atrb(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open(SEGP)),key=lambda s:s['start'])
raw={int(json.loads(l)["ts_epoch"]):json.loads(l) for l in open(RAWP)}
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
tr=[]
for r in csv.DictReader(open(CSVP)):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];a=atrb(bi);entry=float(r["entry"])
    niv=prev['hi'] if s['regime']=='BULL' else prev['lo']
    dist=(entry-niv)/a
    los_below=[segs[j]['lo'] for j in range(idx) if segs[j]['lo']<entry]
    nearest_below=(entry-max(los_below))/a if los_below else 99
    rsi=(raw.get(int(t)) or {}).get("rsi") or 50
    R=round(float(r["letrun_struct"])-0.35,2)
    tr.append({"bi":bi,"t":t,"yr":dt.datetime.utcfromtimestamp(t).year,
               "ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),
               "reg":s['regime'],"segkey":idx,"dist":dist,"nb":nearest_below,"rsi":rsi,"R":R})
tr.sort(key=lambda x:x['bi'])
byseg=defaultdict(list)
for x in tr: byseg[x['segkey']].append(x)
for k,g in byseg.items():
    g.sort(key=lambda z:z['bi'])
    for i,z in enumerate(g): z['first']=(i==0)
def panel(keepfn,lab):
    k=[x for x in tr if keepfn(x)];k.sort(key=lambda z:z['bi'])
    if not k: print(f"  {lab:46} N=0");return
    n=len(k);w=sum(1 for x in k if x['R']>0);s=sum(x['R'] for x in k);big=sum(1 for x in k if x['R']>=3)
    cum=peak=dd=0;streak=mx=0;runs=[]
    for x in k:
        cum+=x['R'];peak=max(peak,cum);dd=min(dd,cum-peak)
        if x['R']<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak: runs.append(streak)
            streak=0
    if streak: runs.append(streak)
    r5=sum(1 for q in runs if q>=5)
    mth=defaultdict(float)
    for x in k: mth[x['ym']]+=x['R']
    posm=sum(1 for v in mth.values() if v>0);tot=len(mth)
    print(f"  {lab:46} N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:6.1f} streak={mx:2} runs>=5:{r5} big={big:2} meses{posm}/{tot}({100*posm/tot:.0f}%+)")
# capitulacao skeleton: dist<=-2, NO nb/rsi
def bear_skel_capit(x): return x['reg']=='BEAR' and x['dist']<=-2
# fitted version for reference
NB,RS=14,60
def bear_fit_capit(x): return x['reg']=='BEAR' and x['dist']<=-2 and x['nb']<=NB and x['rsi']<=RS
print(f"BOOK SKELETON (no BEAR fitting). {len(tr)} trades total.\n")
panel(lambda x:True,"BASE (todos)")
print("--- SKELETON: BEAR keep ALL dist<=-2 (drop NB/RS), BULL cap, RANGE keep ---")
panel(lambda x: not(x['reg']=='BEAR' and not bear_skel_capit(x)),"+ BEAR skel-capit (keep all dist<=-2)")
def skel_full(x):
    if x['reg']=='BEAR': return bear_skel_capit(x)
    if x['reg']=='BULL': return x['first']
    return True
panel(skel_full,"SKELETON FULL (BEAR-skel + BULL-cap + RANGE)")
print("--- ISOLATE: bear-faca-skip ALONE (BEAR keep dist<=-2, NO bull-cap, RANGE keep) ---")
def bearfaca_only(x):
    if x['reg']=='BEAR': return bear_skel_capit(x)
    return True  # BULL keep all + RANGE keep
panel(bearfaca_only,"bear-faca-skip only (no bull-cap)")
print("--- reference: FITTED FULL (NB<=14 RS<=60) ---")
def fit_full(x):
    if x['reg']=='BEAR': return bear_fit_capit(x)
    if x['reg']=='BULL': return x['first']
    return True
panel(fit_full,"FITTED FULL")
print("\n--- per-year SKELETON FULL vs FITTED FULL ---")
for y in (2020,2021,2022,2023,2024,2025,2026):
    sk=[x for x in tr if x['yr']==y and skel_full(x)]
    ft=[x for x in tr if x['yr']==y and fit_full(x)]
    by=[x for x in tr if x['yr']==y]
    if by: print(f"  {y}: BASE {sum(x['R'] for x in by):+6.1f}(n{len(by):2}) SKEL {sum(x['R'] for x in sk):+6.1f}(n{len(sk):2}) FIT {sum(x['R'] for x in ft):+6.1f}(n{len(ft):2})")
# how much is the +8R refinement: skeleton bear-capit set vs fitted bear-capit set
bs=[x for x in tr if bear_skel_capit(x)]; bf=[x for x in tr if bear_fit_capit(x)]
print(f"\nBEAR capit sets: skel dist<=-2 -> N{len(bs)} sumR{sum(x['R'] for x in bs):+.1f} | fitted NB/RS -> N{len(bf)} sumR{sum(x['R'] for x in bf):+.1f} | refinement Δ={sum(x['R'] for x in bf)-sum(x['R'] for x in bs):+.1f}R")
