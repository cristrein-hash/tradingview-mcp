#!/usr/bin/env python3
"""DA POINT 1 — MATCH VALIDITY. Is ±3 bars arbitrary? Re-run match at W=1,3,6,12,24
and report (a) match rate, (b) median Δ to nearest reversal, (c) how the BOT-tier WR
pattern moves. If the cross is 90% UNMATCHED, the 5ATR entries do NOT trade the M8
reversals — they are micro-lows mid-leg. Saved/reproducible (no inline)."""
import csv, bisect, statistics as st
from pathlib import Path
from filter_harness import ROWS, dedup, stats
HERE=Path(__file__).parent; BAR=900
REV=[{**r,"t":int(r["t"]),"leg_atr":float(r["leg_atr"])} for r in csv.DictReader(open(HERE/"reversal_power.csv"))]
REVt=sorted(REV,key=lambda r:r["t"]); RT=[r["t"] for r in REVt]
def nearest_rev(t):
    k=bisect.bisect_left(RT,t); best=None
    for j in (k-1,k,k+1):
        if 0<=j<len(REVt):
            d=abs(REVt[j]["t"]-t)
            if best is None or d<best[0]: best=(d,REVt[j])
    return best
def group_of(r,W):
    nb=nearest_rev(r["low_t"])
    if nb is None or nb[0] > W*BAR: return "UNMATCHED"
    rev=nb[1]
    return "TOP" if rev["kind"]=="TOP" else "BOT-"+rev["tier"]

base=dedup(ROWS)
b=stats(base)
print(f"BASE A2 dedup N={b['n']} WR={b['wr']}% sumR={b['sumr']}")
# distribution of Δ in bars
dts=sorted(nearest_rev(r["low_t"])[0]/BAR for r in base)
print(f"\nΔ-to-nearest-reversal (bars): min {dts[0]:.0f}  p10 {dts[int(.1*len(dts))]:.0f}  median {st.median(dts):.0f}  p90 {dts[int(.9*len(dts))]:.0f}  max {dts[-1]:.0f}")
print(f"fraction within 1/3/6/12/24 bars: "+" ".join(f"{w}b={sum(1 for d in dts if d<=w)}/{len(dts)}({100*sum(1 for d in dts if d<=w)/len(dts):.0f}%)" for w in (1,3,6,12,24)))

order=["BOT-MONSTRO","BOT-FORTE","BOT-MEDIO","BOT-FRACO","TOP","UNMATCHED"]
for W in (1,3,6,12,24):
    from collections import defaultdict
    g=defaultdict(list)
    for r in base: g[group_of(r,W)].append(r)
    matched=b['n']-len(g.get("UNMATCHED",[]))
    print(f"\n--- W=±{W} bars | matched {matched}/{b['n']} ({100*matched/b['n']:.0f}%) ---")
    print(f"{'grupo':<14}{'n':>4}{'WR%':>7}{'sumR':>8}{'avgR':>7}")
    for k in order:
        rs=g.get(k,[])
        if not rs: continue
        n=len(rs); w=sum(x['win'] for x in rs); sm=sum(x['R'] for x in rs)
        print(f"{k:<14}{n:>4}{100*w/n:>7.1f}{sm:>8.1f}{sm/n:>+7.2f}")
