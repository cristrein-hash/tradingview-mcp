#!/usr/bin/env python3
"""STRICT-CAUSAL independent re-implementation of the 4-STATE CYCLE-PHASE MACHINE.
Adversarial audit: recomputes ALL features from scratch using ONLY bars index<=j.
NO reference to e['out'] in logic, NO reference to any target-n list anywhere.
Includes: (a) prefix-stability test (truncated zigzag vs filtered full zigzag),
          (b) label-shuffle null on the SAME classifier logic.
"""
import sys, random; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import (S,TS,HI,LO,CL,ATR,EMA,N,ENTRIES,score,causal_swings_upto)
from collections import Counter

# ---- independent truncated zigzag: run ONLY on bars [0..j], no future knowledge ----
def zz_upto(j, r=6):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,j+1):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv

# ---- prefix-stability: filtered-full must equal truncated-at-j (proves filter-after-compute is safe) ----
mismatch=0
for e in ENTRIES:
    j=e["j"]
    a=[(tp,idx,round(pr,3),ci) for tp,idx,pr,ci in causal_swings_upto(j)]
    b=[(tp,idx,round(pr,3),ci) for tp,idx,pr,ci in zz_upto(j)]
    if a!=b: mismatch+=1
print("prefix-stability mismatches (filtered-full vs truncated) — must be 0:", mismatch)

# ---- STRICT features recomputed from truncated zigzag; reclaim recomputed from i,j ----
def feats_strict(e):
    j=e["j"]; i=e["i"]; a=ATR[i] or 5.0
    sw=zz_upto(j)                                  # only bars <= j
    Hs=[pr for tp,idx,pr,ci in sw if tp=="H"]
    lh2=1 if (len(Hs)>=3 and Hs[-1]<Hs[-2]<Hs[-3]) else 0
    push=0
    for k in range(len(Hs)-1,0,-1):
        if Hs[k]>Hs[k-1]: push+=1
        else: break
    ent_vs_H=(CL[j]-Hs[-1])/a if Hs else 0.0       # CL[j] is close at decision bar (<=j)
    reclaim=j-i                                     # both <= j
    return dict(lh2=lh2,push=push,ent_vs_H=ent_vs_H,reclaim=reclaim)

FE={e["n"]:feats_strict(e) for e in ENTRIES}
P=dict(b_reclaim=4, a_push=2, a_entpos=-4.0)

def classify(f):
    if f["reclaim"]<=P["b_reclaim"]: return "B"
    if f["lh2"]==1: return "D"
    if f["push"]>=P["a_push"] and f["ent_vs_H"]<P["a_entpos"]: return "A"
    return "C"

PH={e["n"]:classify(FE[e["n"]]) for e in ENTRIES}
KEEP=sorted(n for n,p in PH.items() if p in ("A","B"))
SC=score(KEEP)
print("dist:", dict(Counter(PH.values())))
print("STRICT score:", SC)
print("KEEP_NS =", KEEP)

# ---- feature-diff vs candidate FE (did independent recompute change any classification?) ----
from wf_ph_combined_4state import PH as PH_CAND
diff=[n for n in PH if PH[n]!=PH_CAND[n]]
print("classification diffs vs candidate:", len(diff), diff)

# ---- LABEL-SHUFFLE NULL: same classifier keeps N_kept fixed; shuffle outcomes, measure hit3r_kept ----
outs=[e["out"] for e in ENTRIES]
keepset=set(KEEP); nk=len(keepset)
obs=SC["hit3r_kept"]
rnd=random.Random(42); ge=0; T=5000
for _ in range(T):
    sh=outs[:]; rnd.shuffle(sh)
    hk=sum(sh[idx] for idx,e in enumerate(ENTRIES) if e["n"] in keepset)/nk
    if hk>=obs: ge+=1
print(f"null(label-shuffle) P(hit3r_kept>=obs {obs}) = {ge/T:.4f}  over {T} perms")
