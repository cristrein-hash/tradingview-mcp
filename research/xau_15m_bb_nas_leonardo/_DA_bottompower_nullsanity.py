#!/usr/bin/env python3
"""DA null-sanity + tier-gradient audit for bottom-power separability (Cris 2026-06-27).
Verifies the permutation null is honest using ABSOLUTE rate (not lift, which moves with shuffled base),
and audits whether tier is a monotonic function of leg-shallowness features (= continuation/beta axis).
Companion to _DA_bottompower_controls.py. -> _DA_bottompower_nullsanity.txt"""
import json,statistics as st,random,math
from itertools import combinations
from pathlib import Path
from collections import Counter
HERE=Path(__file__).parent
R=[json.loads(l) for l in (HERE/"bottom_features.jsonl").read_text().splitlines()]
META={'block','t','yr','tier','tier_clean','leg_atr','power_score','session'}
NUMF=[k for k in R[0] if k not in META and isinstance(R[0][k],(int,float))]
def s3(r): return 0 if r["tier"]=="FRACO" else 1
BASE3=sum(s3(r) for r in R)/len(R)
def auc(rows,f):
    vv=[(r[f],s3(r)) for r in rows if r.get(f) is not None]
    pos=[v for v,y in vv if y]; neg=[v for v,y in vv if not y]
    if not pos or not neg: return None
    sv=sorted(vv); vals=[v for v,_ in sv]; ranks=[0]*len(vals); j=0
    while j<len(vals):
        k=j
        while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
        for m in range(j,k+1): ranks[m]=(j+k)/2+1
        j=k+1
    rs=sum(ranks[m] for m in range(len(sv)) if sv[m][1]); n1=len(pos); n0=len(neg)
    return (rs-n1*(n1+1)/2)/(n1*n0)
out=[]; P=out.append
res=sorted(((abs(auc(R,f)-.5),f) for f in NUMF if auc(R,f) is not None),reverse=True)
TOP=[f for _,f in res[:14]]
med={f:st.median([r[f] for r in R if r.get(f) is not None]) for f in TOP}
dirn={f:(1 if auc(R,f)>=.5 else -1) for f in TOP}
def sel(rows,c):
    o=[]
    for r in rows:
        ok=True
        for f in c:
            v=r.get(f)
            if v is None or (dirn[f]>0 and v<med[f]) or (dirn[f]<0 and v>med[f]): ok=False; break
        if ok: o.append(r)
    return o

P("=== NULL SANITY (absolute rate3, immune to base-shift under shuffle) ===")
best=[]
for sz in (2,3):
    for c in combinations(TOP,sz):
        s=sel(R,c)
        if len(s)>=25: best.append((sum(s3(r) for r in s)/len(s),c,len(s)))
best.sort(reverse=True)
obs=best[0][0]
P(f"observed best abs rate3={obs:.3f} combo={best[0][1]} n={best[0][2]} base={BASE3:.3f}")
random.seed(1); tiers=[r["tier"] for r in R]; nullabs=[]
for _ in range(300):
    p=tiers[:]; random.shuffle(p)
    sh=[dict(r) for r in R]
    for r,t in zip(sh,p): r["tier"]=t
    bb=0
    for sz in (2,3):
        for c in combinations(TOP,sz):
            s=sel(sh,c)
            if len(s)>=25:
                rr=sum((0 if r["tier"]=="FRACO" else 1) for r in s)/len(s)
                if rr>bb: bb=rr
    nullabs.append(bb)
nullabs.sort()
P(f"null best abs rate3: p50={nullabs[150]:.3f} p95={nullabs[284]:.3f} max={max(nullabs):.3f} p(>=obs)={sum(1 for x in nullabs if x>=obs)/300:.4f}")

P("\n=== TIER GRADIENT (is tier a monotonic fn of leg-shallowness = continuation/beta axis?) ===")
for tier in ["MONSTRO","FORTE","MEDIO","FRACO"]:
    g=[r for r in R if r["tier"]==tier]
    P(f"{tier:8} n={len(g):>3} legpos90={st.mean([r['legpos90'] for r in g]):.3f} "
      f"h1_pos={st.mean([r['h1_pos'] for r in g if r['h1_pos'] is not None]):.3f} "
      f"rsi_min8={st.mean([r['rsi_min8'] for r in g]):.1f} atr_regime={st.mean([r['atr_regime'] for r in g]):.2f} "
      f"h1_trend_up%={sum(1 for r in g if r.get('h1_trend')==1)/len(g):.2f} macro_bull%={sum(r['macro_bull'] for r in g)/len(g):.2f}")
xs=[r["legpos90"] for r in R]; ys=[r["leg_atr"] for r in R]
mx=st.mean(xs); my=st.mean(ys)
cov=sum((a-mx)*(b-my) for a,b in zip(xs,ys))
sx=math.sqrt(sum((a-mx)**2 for a in xs)); sy=math.sqrt(sum((b-my)**2 for b in ys))
P(f"Pearson legpos90 vs leg_atr(label source) r={cov/(sx*sy):.3f}")

P("\n=== BLOCK STRUCTURE (leave-block folds are ~quarterly, span year boundaries) ===")
bs={}
for r in R:
    bs.setdefault(r["block"],{"yrs":Counter(),"tiers":Counter()})
    bs[r["block"]]["yrs"][r["yr"]]+=1; bs[r["block"]]["tiers"][r["tier"]]+=1
for b in sorted(bs):
    P(f"  {b}: n={sum(bs[b]['yrs'].values()):>3} yrs={dict(bs[b]['yrs'])} tiers={dict(bs[b]['tiers'])}")
rep="\n".join(out); print(rep)
(HERE/"_DA_bottompower_nullsanity.txt").write_text(rep)
print("\n-> _DA_bottompower_nullsanity.txt")
