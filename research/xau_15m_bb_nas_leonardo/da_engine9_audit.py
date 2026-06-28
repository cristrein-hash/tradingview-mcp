#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit of engine9_full_gatilho.py confluence-stack frontier.
Reproduces the base (3120 LONG BULL/RANGE knife-gated), then runs 5 adversarial tests:
 1. NULL-OF-MAX: random scoring -> empirical p-value for observed avgR at N209 / N580.
 2. CONCENTRATION: top-trade stripping + year split at conv>=14.
 3. BOOTSTRAP CI on avgR at conv>=14 vs base 0.13.
 4. PREDICATE DIRECTION VALIDITY: per-predicate TRUE vs FALSE avgR (wrong-signed?).
 5. REDUNDANCY: conv vs single dominant features (h4_up,h1d_up,in_demand).
Deterministic seed. Saved/committed for reproducibility.
"""
import json, statistics as st, random
from pathlib import Path
import engine9_full_gatilho as E  # reuse exact base + preds

base = E.base
preds = E.preds
NP = E.NP
random.seed(1234)

def metr(rs):
    n=len(rs)
    if not n: return None
    sm=sum(rs); w=sum(1 for x in rs if x>0)
    eq=pk=dd=0
    for x in rs:
        eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return n, 100*w/n, sm, sm/n, dd

# Precompute per-trade predicate boolean vectors + R
PV=[list(preds(r).values()) for r in base]      # list of bool lists (len 20)
PNAMES=list(preds(base[0]).keys())
RS=[r["R"] for r in base]
YR=[r["yr"] for r in base]
conv=[sum(v) for v in PV]
base_avgR=sum(RS)/len(RS)
print(f"BASE N={len(base)} avgR={base_avgR:.4f} sumR={sum(RS):.1f}")

# observed frontier avgR by threshold (for reference)
obs={}
for k in range(0,NP+1):
    idx=[i for i in range(len(base)) if conv[i]>=k]
    if idx:
        obs[k]=(len(idx), sum(RS[i] for i in idx)/len(idx))

# ----- TEST 1: NULL-OF-MAX via random scoring -----
# Method A: per-feature column shuffle (preserve each predicate's marginal TRUE-rate,
# destroy its association with R). Recompute conv, take same N (top-conv slice) -> avgR.
# We target N209 (conv>=14) and N580 (conv>=13).
print("\n=== TEST 1: NULL-OF-MAX (per-feature column shuffle) ===")
ncol=len(PV[0]); nrow=len(PV)
cols=[[PV[i][j] for i in range(nrow)] for j in range(ncol)]
targets={"N209":209,"N580":580}
NREP=500
nulldist={t:[] for t in targets}
for rep in range(NREP):
    sh=[c[:] for c in cols]
    for c in sh: random.shuffle(c)
    sc=[sum(sh[j][i] for j in range(ncol)) for i in range(nrow)]
    order=sorted(range(nrow), key=lambda i:(-sc[i],))  # highest conv first
    for tname,Ntgt in targets.items():
        sel=order[:Ntgt]
        nulldist[tname].append(sum(RS[i] for i in sel)/Ntgt)
obs_avg={"N209":obs[14][1],"N580":obs[13][1]}
for tname,Ntgt in targets.items():
    d=sorted(nulldist[tname]); m=st.mean(d); sd=st.pstdev(d)
    ge=sum(1 for x in d if x>=obs_avg[tname])
    p=(ge+1)/(NREP+1)
    q95=d[int(0.95*len(d))]
    print(f"{tname} (N={Ntgt}): observed avgR={obs_avg[tname]:.4f} | "
          f"null mean={m:.4f} sd={sd:.4f} 95pct={q95:.4f} | "
          f"#null>=obs={ge}/{NREP} p={p:.4f}")

# Method B: pure random conv assignment matched to N (sanity on top-slice variance)
print("\n--- Method B: pure random N-slice (variance baseline) ---")
for tname,Ntgt in targets.items():
    ds=[]
    for rep in range(NREP):
        sel=random.sample(range(nrow),Ntgt)
        ds.append(sum(RS[i] for i in sel)/Ntgt)
    ds.sort(); ge=sum(1 for x in ds if x>=obs_avg[tname]); p=(ge+1)/(NREP+1)
    print(f"{tname}: obs={obs_avg[tname]:.4f} | randslice mean={st.mean(ds):.4f} "
          f"sd={st.pstdev(ds):.4f} 95pct={ds[int(0.95*len(ds))]:.4f} p={p:.4f}")

# ----- TEST 2: CONCENTRATION at conv>=14 -----
print("\n=== TEST 2: CONCENTRATION at conv>=14 (N=209) ===")
idx14=[i for i in range(len(base)) if conv[i]>=14]
r14=sorted(((RS[i],YR[i]) for i in idx14), key=lambda x:-x[0])
sm14=sum(x[0] for x in r14)
print(f"N={len(r14)} sumR={sm14:.1f} avgR={sm14/len(r14):.4f}")
for topn in (1,3,5,10):
    top=sum(x[0] for x in r14[:topn])
    rest=r14[topn:]
    print(f" top{topn} sumR={top:.1f} ({100*top/sm14:.1f}% of total) | "
          f"strip-top{topn}: N={len(rest)} sumR={sm14-top:.1f} avgR={(sm14-top)/len(rest):.4f}")
# year split
for y in (2024,2025,2026):
    ry=[x[0] for x in r14 if x[1]==y]
    if ry:
        print(f" {y}: N={len(ry)} sumR={sum(ry):.1f} avgR={sum(ry)/len(ry):.4f} WR={100*sum(1 for x in ry if x>0)/len(ry):.1f}")
# ex-2025
non25=[x[0] for x in r14 if x[1]!=2025]
print(f" ex-2025: N={len(non25)} sumR={sum(non25):.1f} avgR={sum(non25)/len(non25):.4f}")

# ----- TEST 3: BOOTSTRAP CI on avgR at conv>=14 -----
print("\n=== TEST 3: BOOTSTRAP CI avgR conv>=14 vs base 0.13 ===")
r14v=[RS[i] for i in idx14]
NB=5000; boots=[]
for _ in range(NB):
    samp=[random.choice(r14v) for _ in range(len(r14v))]
    boots.append(sum(samp)/len(samp))
boots.sort()
lo,hi=boots[int(0.025*NB)],boots[int(0.975*NB)]
below_base=sum(1 for x in boots if x<=base_avgR)/NB
print(f"avgR={sum(r14v)/len(r14v):.4f} | 95% CI [{lo:.4f}, {hi:.4f}] | "
      f"P(boot<=base 0.13)={below_base:.4f}")

# ----- TEST 4: PREDICATE DIRECTION VALIDITY -----
print("\n=== TEST 4: PREDICATE DIRECTION (TRUE avgR vs FALSE avgR) ===")
rows=[]
for j,name in enumerate(PNAMES):
    tr=[RS[i] for i in range(nrow) if PV[i][j]]
    fa=[RS[i] for i in range(nrow) if not PV[i][j]]
    ta=sum(tr)/len(tr) if tr else float('nan')
    fb=sum(fa)/len(fa) if fa else float('nan')
    rows.append((name,len(tr),ta,fb,ta-fb))
rows.sort(key=lambda x:x[4])
print(f"{'predicate':<20}{'nTRUE':>6}{'avgR_T':>9}{'avgR_F':>9}{'delta':>9}  flag")
for name,nt,ta,fb,d in rows:
    flag="WRONG-SIGN" if d<0 else ("~zero" if abs(d)<0.02 else "")
    print(f"{name:<20}{nt:>6}{ta:>9.4f}{fb:>9.4f}{d:>9.4f}  {flag}")

# ----- TEST 5: REDUNDANCY conv vs single features -----
print("\n=== TEST 5: REDUNDANCY (conv vs dominant single features) ===")
# correlation of conv with each single predicate (point-biserial-ish)
import math
def corr(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    va=sum((x-ma)**2 for x in a); vb=sum((x-mb)**2 for x in b)
    return cov/math.sqrt(va*vb) if va>0 and vb>0 else 0
convf=[float(c) for c in conv]
for name in ("h4_up","h1d_up","in_demand","h4_demanda","clean_sky","perto_demanda","sem_supply_acima","downleg_grind"):
    j=PNAMES.index(name)
    col=[1.0 if PV[i][j] else 0.0 for i in range(nrow)]
    print(f" corr(conv, {name:<16})={corr(convf,col):+.3f}")
# does requiring just {h4_up & h1d_up & in_demand} reproduce conv>=14 performance?
print("\n single-stack comparisons:")
def sel_pred(fn):
    idx=[i for i in range(nrow) if fn(i)]
    if not idx: return None
    rs=[RS[i] for i in idx]
    py={y:round(sum(RS[i] for i in idx if YR[i]==y),1) for y in (2024,2025,2026)}
    return len(idx),100*sum(1 for x in rs if x>0)/len(idx),sum(rs),sum(rs)/len(rs),py
def gi(name): return PNAMES.index(name)
combos={
 "h4_up&h1d_up&in_demand": lambda i: PV[i][gi("h4_up")] and PV[i][gi("h1d_up")] and PV[i][gi("in_demand")],
 "h4_up&h1d_up": lambda i: PV[i][gi("h4_up")] and PV[i][gi("h1d_up")],
 "h4_up&h1d_up&h4_demanda": lambda i: PV[i][gi("h4_up")] and PV[i][gi("h1d_up")] and PV[i][gi("h4_demanda")],
 "conv>=14": lambda i: conv[i]>=14,
}
for nm,fn in combos.items():
    r=sel_pred(fn)
    if r: print(f" {nm:<26} N={r[0]:>4} WR={r[1]:.1f} sumR={r[2]:.1f} avgR={r[3]:.4f} yr={r[4]}")
# overlap: of conv>=14, how many also satisfy h4_up&h1d_up&in_demand?
i14=set(idx14)
core=set(i for i in range(nrow) if PV[i][gi("h4_up")] and PV[i][gi("h1d_up")] and PV[i][gi("in_demand")])
print(f"\n overlap: conv>=14 ∩ core = {len(i14&core)}/{len(i14)} of conv>=14 trades are in the 3-feature core")
print(f" of conv>=14, fraction with h4_up=TRUE: {sum(1 for i in idx14 if PV[i][gi('h4_up')])/len(idx14):.2f}, "
      f"h1d_up=TRUE: {sum(1 for i in idx14 if PV[i][gi('h1d_up')])/len(idx14):.2f}, "
      f"in_demand=TRUE: {sum(1 for i in idx14 if PV[i][gi('in_demand')])/len(idx14):.2f}")
