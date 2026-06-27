#!/usr/bin/env python3
"""DA POINT 6 — RECONCILE. Is BOT-FRACO 9% WR just a relabel of known loser clusters?
Cross the FRACO entries (and UNMATCHED losers) with macro_bear, h1_eff (anti-range), and
the 170 vs 267 difference. Check whether the entries the 170-filter already removes are the
same FRACO/loser entries — i.e. the cross adds nothing new the approved filter doesn't catch."""
import csv, bisect
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
ids170={int(r["entry_t"]) for r in csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv"))}
FRACO=[r for r in base if group_of(r)=="BOT-FRACO"]
print(f"BOT-FRACO n={len(FRACO)}; wins={sum(r['win'] for r in FRACO)}")
print(f"{'low_t':>12}{'R':>7}{'win':>4}{'mbear':>6}{'h1eff':>7}{'h1pos':>7}{'in170':>6}")
for r in sorted(FRACO,key=lambda x:x['low_t']):
    print(f"{r['low_t']:>12}{r['R']:>+7.2f}{r['win']:>4}{r.get('macro_bear',0):>6}{r.get('h1_eff') if r.get('h1_eff') is not None else -9:>7.2f}{r.get('h1_pos',0):>7.2f}{'Y' if r['t'] in ids170 else '-':>6}")
nb=sum(1 for r in FRACO if r.get('macro_bear'))
inr=sum(1 for r in FRACO if (r.get('h1_eff') is not None and r['h1_eff']<0.15))
in170=sum(1 for r in FRACO if r['t'] in ids170)
print(f"\nFRACO that are macro_bear: {nb}/{len(FRACO)}")
print(f"FRACO that are anti-range h1_eff<0.15 (already cut by approved base): {inr}/{len(FRACO)}")
print(f"FRACO that SURVIVE into the 170-final filter: {in170}/{len(FRACO)}")
print("If most FRACO losers are already removed by h1_eff/regime, the tier cross adds nothing new.")
# whole-base: how many losers does the approved 170 filter already remove?
losers=[r for r in base if not r['win']]
loser_in170=sum(1 for r in losers if r['t'] in ids170)
print(f"\nwhole base losers n={len(losers)}; surviving into 170 = {loser_in170} (approved filter already cut {len(losers)-loser_in170})")
