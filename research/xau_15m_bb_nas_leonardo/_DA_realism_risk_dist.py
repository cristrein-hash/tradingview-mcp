#!/usr/bin/env python3
"""
Deep-dive on the 8ATR risk-distance problem and what R actually means here.

If entry is 8ATR above the fractal low and SL = low-0.1ATR, then risk distance
~= 8.1 ATR ~= 8.1 * 4.67 ~= $37.8 per trade on XAU 15m. A +1R winner = +$37.8.
But the MOVE captured to make +1R is only ~8ATR of favorable excursion measured
from an already-extended entry. Median winner is +0.95R.

Realism question: is this 'edge' just mean structure of XAU drift, where after an
8ATR pop off a low, price tends to push a bit more before retrace? And critically,
with such a wide stop, the fixed-fractional-risk position size is TINY, so absolute
$ throughput per unit time is low despite high trade count.

Also: cap is 20R but max observed R is 3.76 and 0 trades >=5R. That means the
trailing let-run NEVER produces a convex tail -> winners are clipped early by the
trail OR the 8ATR entry is so late that there is no room left to run. Confirm by
checking R distribution shape.
"""
import json, statistics as st
ROWS=[json.loads(l) for l in open('dataset_r2refine.jsonl')]
def rb_cut(d):
    return ((d.get('absorption')==1 and d.get('sell_decel')==0)
            or (d.get('buy_sell_ratio4',0)>7 and d.get('low_vol_rel',0)>1.37)
            or (d.get('regime_age_h',1e9)<=25.2 and d.get('sell_skew_mig',0)>0))
final=[d for d in ROWS if d['r2_keep']==1 and not rb_cut(d)]
Rs=[d['R'] for d in final]

print("CONVEXITY CHECK:")
print(f"  cap=20R, observed max R={max(Rs):.2f}, #trades>=3R={sum(1 for r in Rs if r>=3)}, "
      f">=2R={sum(1 for r in Rs if r>=2)}, >=1.5R={sum(1 for r in Rs if r>=1.5)}")
print(f"  -> trail+8ATR-entry produces NO tail. Profile is bounded ~[-1, +3.8], mass at +0.5..+1.5.")
print(f"  This is a high-WR mean-reversion-continuation SCALP, NOT a convex runner strategy.")

# Expectancy stability if WR drops 20% (power / robustness narrative)
n=len(Rs); wr=sum(1 for r in Rs if r>0)/n
aw=st.mean([r for r in Rs if r>0]); al=st.mean([r for r in Rs if r<=0])
print("\nEXPECTANCY FRAGILITY (avg_win small, payoff ~1.1):")
for dwr in (0.0,0.05,0.10):
    w=wr-dwr
    exp=w*aw+(1-w)*al
    print(f"  WR {w*100:.1f}% -> expectancy {exp:+.3f}R/trade")
print(f"  Breakeven WR = {-al/(aw-al)*100:.1f}%  (current {wr*100:.1f}%). "
      f"Cushion = {(wr-(-al/(aw-al)))*100:.1f}pp -> THIN given payoff~1.1.")

# Cost in R if risk distance were the CONFIRMATION-BAR stop (tight), not 8ATR.
# A realistic intrabar/scalp stop ~1-2 ATR would make cost-in-R 4-8x larger.
atr=4.666
print("\nCOST SENSITIVITY UNDER ALT RISK ASSUMPTIONS (cost=$0.22, spread0.18+2tick):")
for mult,label in [(8.1,'as-spec 8.1ATR stop (huge)'),(2.0,'2ATR stop'),(1.0,'1ATR stop')]:
    rd=mult*atr; costR=0.22/rd
    print(f"  {label}: riskdist=${rd:.1f} cost={costR:.4f}R -> avgR {0.423-costR:+.3f}")
print("  Edge survives cost ONLY because the 8ATR stop makes R-units enormous. The high")
print("  trade count + tiny per-trade $ throughput is the real deployability concern, not cost.")
