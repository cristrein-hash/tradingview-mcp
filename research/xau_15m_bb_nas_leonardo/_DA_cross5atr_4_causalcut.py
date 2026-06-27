#!/usr/bin/env python3
"""DA POINT 4 — CAUSAL-CUT FEASIBILITY (the real question).
Can the loser-dense BOT-FRACO group be separated from BOT-MEDIO/winners using ONLY
features available AT ENTRY (causal)? Beyond medians: for every causal feature, test
whether FRACO entries occupy a separable range vs MEDIO. Also vs ALL winners. Report
per-feature AUC-like separation (Mann-Whitney rank fraction) and best single-threshold
accuracy. If best separation is near chance / overlaps, declare NO causal signature."""
import csv, bisect, statistics as st
from pathlib import Path
from filter_harness import ROWS, dedup
HERE=Path(__file__).parent; BAR=900; W=3
REV=[{**r,"t":int(r["t"])} for r in csv.DictReader(open(HERE/"reversal_power.csv"))]
REVt=sorted(REV,key=lambda r:r["t"]); RT=[r["t"] for r in REVt]
def nearest_rev(t):
    k=bisect.bisect_left(RT,t); best=None
    for j in (k-1,k,k+1):
        if 0<=j<len(REVt):
            d=abs(REVt[j]["t"]-t)
            if best is None or d<best[0]: best=(d,REVt[j])
    return best
def group_of(r):
    nb=nearest_rev(r["low_t"])
    if nb is None or nb[0]>W*BAR: return "UNMATCHED"
    return "TOP" if nb[1]["kind"]=="TOP" else "BOT-"+nb[1]["tier"]
base=dedup(ROWS)
from collections import defaultdict
g=defaultdict(list)
for r in base: g[group_of(r)].append(r)
FRACO=g["BOT-FRACO"]; MEDIO=g["BOT-MEDIO"]
ALL_WIN=[r for r in base if r["win"]]; ALL_LOSE=[r for r in base if not r["win"]]
feats=["leg_ext_atr","disp4_atr","h1_pos","h1_eff","dist_demand_atr","room_above_atr",
       "rsi","rsi_low","dist_ema_atr","path_eff","atr_regime","vol_climax","vpnode_dist_atr",
       "bars_to_base","macro_drop_atr","h1_dist","flow_accel","dist_supply_atr"]
def auc(pos,neg,f):
    a=[r[f] for r in pos if r.get(f) is not None]
    b=[r[f] for r in neg if r.get(f) is not None]
    if not a or not b: return None
    c=sum((1 if x>y else 0.5 if x==y else 0) for x in a for y in b)/(len(a)*len(b))
    return c
print(f"FRACO n={len(FRACO)} (loser-dense, WR {100*sum(r['win'] for r in FRACO)/len(FRACO):.0f}%)  vs  MEDIO n={len(MEDIO)} (WR 100%)")
print("AUC near 0.5 = no separation. |AUC-0.5|>~0.25 with these tiny n is unstable anyway.")
print(f"\n{'feature':<18}{'AUC F>M':>9}{'medFRACO':>10}{'medMEDIO':>10}")
rows=[]
for f in feats:
    a=auc(FRACO,MEDIO,f)
    if a is None: continue
    mf=st.median([r[f] for r in FRACO if r.get(f) is not None])
    mm=st.median([r[f] for r in MEDIO if r.get(f) is not None])
    rows.append((abs(a-0.5),a,f,mf,mm))
for _,a,f,mf,mm in sorted(rows,reverse=True):
    print(f"{f:<18}{a:>9.2f}{mf:>10.2f}{mm:>10.2f}")
# the harder, fairer test: separate ALL losers from ALL winners in whole base
print(f"\n=== broader: ALL winners n={len(ALL_WIN)} vs ALL losers n={len(ALL_LOSE)} (whole base) ===")
print(f"{'feature':<18}{'AUC win>lose':>13}")
rows2=[]
for f in feats:
    a=auc(ALL_WIN,ALL_LOSE,f)
    if a is None: continue
    rows2.append((abs(a-0.5),a,f))
for _,a,f in sorted(rows2,reverse=True):
    print(f"{f:<18}{a:>13.2f}")
print("\nIf no feature reaches meaningful, stable separation -> losers NOT causally cleanable via this cross.")
