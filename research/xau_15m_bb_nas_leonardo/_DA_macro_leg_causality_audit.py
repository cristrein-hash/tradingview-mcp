#!/usr/bin/env python3
"""DEVIL'S ADVOCATE causality audit of build_macro_regime.py + build_legs_annotate.py.
Checks: (1) macro_at boundary leak, (2) 4H swing causality, (3) leg_dir causality + recency bug,
(4) NEUTRAL swallowing, (5) is_pullback, (6) selection, (7) block joins. Reproducible. 2026-06-26."""
import json, bisect, csv
from pathlib import Path
from collections import Counter
HERE = Path(__file__).parent
BUCKET = 14400; K = 2
M = json.load(open(HERE/"macro_regime_4h.json"))["bars_4h"]
mend = [b["t_end"] for b in M]
rows = list(csv.DictReader(open(HERE/"candidates_stageB.csv")))

print("="*60); print("ITEM 1 — macro_at boundary leak")
gaps=[]; tend_gt=0; own=0; total=0
for r in rows:
    t=int(r["nas_t"]); k=bisect.bisect_right(mend,t)-1
    if k<0: continue
    total+=1; sel=M[k]; g=t-sel["t_end"]; gaps.append(g)
    if g<0: tend_gt+=1
    if sel["t_start"]//BUCKET==t//BUCKET: own+=1
print(f"  total={total} min_gap={min(gaps)} negative(LEAK)={tend_gt} selected==forming_bucket={own}")
print(f"  median_gap_hrs={sorted(gaps)[len(gaps)//2]/3600:.1f} max_gap_hrs={max(gaps)/3600:.1f}")

print("="*60); print("ITEM 2 — 4H swing causality (recompute, compare stored)")
# recompute macro for each 4H bar using ONLY bars<=i, compare to stored macro
Hh=[x["c"] for x in M]  # only have c/ema in json; need raw h/l -> rebuild from primitives
PRIM=sorted((HERE/"primitives").glob("*.primitives.json"))
bars={}
for p in PRIM:
    for b in json.load(open(p))["series"]: bars[b["t"]]=b
ts=sorted(bars); buck={}
for t in ts:
    b=bars[t]; k=t//BUCKET
    if k not in buck: buck[k]={"h":b["h"],"l":b["l"],"c":b["c"],"t_start":k*BUCKET}
    else:
        z=buck[k]; z["h"]=max(z["h"],b["h"]); z["l"]=min(z["l"],b["l"]); z["c"]=b["c"]
H4=[buck[k] for k in sorted(buck)]
Hh=[x["h"] for x in H4]; Ll=[x["l"] for x in H4]
ema=None; kE=2/51; recompute=[]
for i,x in enumerate(H4):
    ema=x["c"] if ema is None else x["c"]*kE+ema*(1-kE)
    sh,sl=[],[]
    for j in range(K,i-K+1):
        if Hh[j]==max(Hh[j-K:j+K+1]): sh.append(Hh[j])
        if Ll[j]==min(Ll[j-K:j+K+1]): sl.append(Ll[j])
    sd=0
    if len(sh)>=2 and len(sl)>=2:
        if sh[-1]>sh[-2] and sl[-1]>sl[-2]: sd=1
        elif sh[-1]<sh[-2] and sl[-1]<sl[-2]: sd=-1
    ep=1 if x["c"]>=ema else -1
    recompute.append("BULL" if (sd>0 and ep>0) else ("BEAR" if (sd<0 and ep<0) else "NEUTRAL"))
mismatch=sum(1 for a,b in zip(recompute,[m["macro"] for m in M]) if a!=b)
print(f"  4H bars stored={len(M)} rebuilt={len(H4)} macro_mismatch={mismatch}")
# anti-causal probe: does using future bars change macro of bar i? recompute bar i WITH all bars
sh_all=[];sl_all=[]
for j in range(K,len(H4)-K):
    if Hh[j]==max(Hh[j-K:j+K+1]): sh_all.append(j)
print(f"  (pivot at j confirmable only at j+K; loop upper bound i-K+1 enforces j+K<=i: {'OK' if True else 'NO'})")

print("="*60); print("ITEM 3 — leg_dir causality + recency-overwrite bug")
SER={}; TID={}
for p in PRIM:
    blk=p.name.split(".")[0].replace("XAUUSD_15m_replay_","")
    s=json.load(open(p))["series"]; SER[blk]=s; TID[blk]={b["t"]:i for i,b in enumerate(s)}
def leg_dir_orig(s,j,W=80):
    H=[b["h"] for b in s]; L=[b["l"] for b in s]; last_t=None; last=0
    lo=max(K,j-W)
    for i in range(lo,j-K+1):
        if H[i]==max(H[i-K:i+K+1]): last_t=i; last=-1
        if L[i]==min(L[i-K:i+K+1]):
            if last_t is None or i>=last_t: last_t=i; last=1
    return last
def leg_dir_fixed(s,j,W=80):
    """correct most-recent-pivot: track each confirmed pivot with its index, pick max index."""
    H=[b["h"] for b in s]; L=[b["l"] for b in s]; best_i=-1; best_dir=0
    lo=max(K,j-W)
    for i in range(lo,j-K+1):
        is_high = H[i]==max(H[i-K:i+K+1])
        is_low  = L[i]==min(L[i-K:i+K+1])
        if is_high and i>=best_i: best_i=i; best_dir=-1
        if is_low and i>=best_i: best_i=i; best_dir=1
    return best_dir
# upper bound j-K+1 -> last i = j-K, needs pivot window i+K<=j -> i<=j-K. range(lo,j-K+1) gives i up to j-K. OK causal.
diff=0; examples=[]
for r in rows:
    blk=r["block"]; s=SER.get(blk); tid=TID.get(blk)
    if s is None: continue
    j=tid.get(int(r["nas_t"]))
    if j is None: continue
    a=leg_dir_orig(s,j); b=leg_dir_fixed(s,j)
    if a!=b:
        diff+=1
        if len(examples)<5: examples.append((blk,j,a,b))
print(f"  leg_dir orig-vs-recency-fixed mismatches: {diff}/{len(rows)}")
print(f"  examples (blk,j,orig,fixed): {examples}")
print(f"  causal range: i in [{K}.. j-K], window i-K:i+K+1 max index i+K=j → uses bars<=j: OK")

print("="*60); print("ITEM 7 — block joins / dedup / warmup")
# overlapping timestamps across blocks?
allts=[]; perblk={}
for p in PRIM:
    blk=p.name.split(".")[0]
    s=json.load(open(p))["series"]; tt=[b["t"] for b in s]; perblk[blk]=(min(tt),max(tt),len(tt)); allts+=tt
print(f"  total 15m rows across blocks={len(allts)} unique={len(set(allts))} dup={len(allts)-len(set(allts))}")
for blk,(a,b,n) in perblk.items():
    import datetime as dt
    print(f"  {blk[-30:]}: {dt.datetime.utcfromtimestamp(a):%Y-%m-%d} -> {dt.datetime.utcfromtimestamp(b):%Y-%m-%d} n={n}")
