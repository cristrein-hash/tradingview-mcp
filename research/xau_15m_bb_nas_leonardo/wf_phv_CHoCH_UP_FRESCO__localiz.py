#!/usr/bin/env python3
"""STRICT-CAUSAL re-implementation of candidate 'CHoCH-UP FRESCO V2_hl_nochase'.
Adversarial audit: recompute swing structure from SCRATCH truncated at bar j (never touch bars>j),
independent of kit's causal_swings_upto. Rule = higher_low AND NOT chase_top.
NO reference to any target-n list anywhere in the decision logic.
"""
import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,N,ENTRIES,score,causal_swings_upto

def zz_truncated(jmax, r):
    """Zigzag computed using ONLY bars index<=jmax, from scratch. Returns confirmed pivots
    (tp,idx,price,conf_bar) with conf_bar<=jmax. This is the honest causal structure at j."""
    piv=[]; d=0; ehi=elo=0
    for i in range(1, jmax+1):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i:
            piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i:
            piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv

def strict_feats(e, r=3, W=32):
    j=e["j"]
    sw=zz_truncated(j, r)                     # STRICT: recomputed from scratch, bars<=j only
    H=[pr for tp,i,pr,ci in sw if tp=="H"]
    L=[pr for tp,i,pr,ci in sw if tp=="L"]
    lastL=L[-1] if L else CL[j]; prevL=L[-2] if len(L)>=2 else lastL
    lastH=H[-1] if H else CL[j]
    higher_low=int(lastL>prevL)
    # chase_top: close crossed above lastH within last W bars (closes k<=j only)
    brk=99
    for k in range(j, max(1,j-W)-1, -1):
        if CL[k]>lastH and CL[k-1]<=lastH: brk=j-k; break
    chase_top=int(brk<=W)
    return higher_low, chase_top

# ---- cross-check: does kit's causal_swings_upto == truncated-from-scratch? (leak detector) ----
mism=0
for e in ENTRIES:
    j=e["j"]
    a=[(tp,i,round(pr,2)) for tp,i,pr,ci in causal_swings_upto(j,3)]
    b=[(tp,i,round(pr,2)) for tp,i,pr,ci in zz_truncated(j,3)]
    if a!=b: mism+=1
print(f"CAUSALITY CROSS-CHECK: kit causal_swings_upto vs truncated-from-scratch mismatches={mism}/{len(ENTRIES)}")

# ---- strict keep set ----
keep=set()
for e in ENTRIES:
    hl,ch=strict_feats(e)
    if hl and not ch: keep.add(e["n"])

sc=score(keep)
print("STRICT V2_hl_nochase (higher_low AND NOT chase_top):")
print(sc)
print("KEEP_NS:", sorted(keep))

# sanity post-hoc ONLY (never in logic)
LOSER_TGT=[21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94]
WIN_KEY  =[1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96]
lc=sum(1 for n in LOSER_TGT if n not in keep); wk=sum(1 for n in WIN_KEY if n in keep)
print(f"SANITY post-hoc: loser-tgt cut {lc}/{len(LOSER_TGT)} · win-key kept {wk}/{len(WIN_KEY)}")
