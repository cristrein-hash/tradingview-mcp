"""Devil's Advocate on K5 + refinements.
K5 = cut (bsr4>=7 & flow_accel in[-2,0]) OR (absorption==1 & low_vol_rel>1.5).
Checks:
 (1) selection count: ~30 rules tried -> is +2.08pp lift real vs noise band?
 (2) leave-one-block-out stability of lift.
 (3) winner-cut audit: are cut winners small-R (cheap) or runners (expensive)?
 (4) each clause standalone contribution.
 (5) refinement search for higher winners_kept while staying robust.
No look-ahead: all features are pre-entry state at low_t bar. No R/win used in pred.
"""
from _r2lap_lib import load, evaluate, report, wr, max_losing_streak, blocks, BASE_WR

k = load()

def K5(r):
    return not ((r['buy_sell_ratio4']>=7 and -2<=r['flow_accel']<=0) or
                (r['absorption']==1 and r['low_vol_rel']>1.5))

# (1) noise band: binomial SE of WR at n~1957
import math
p=0.6854; n=1957
se=100*math.sqrt(p*(1-p)/n)
print(f"(1) WR SE at n={n}: {se:.2f}pp. K5 lift=+2.08pp = {2.08/se:.2f} sigma (raw, pre-selection)")
print(f"    With ~30 rules tried, Bonferroni-ish need ~+{se*math.sqrt(2*math.log(30)):.2f}pp. Borderline.")

# (2) leave-one-block-out: recompute K5 WR over 7/8 blocks each time
bl=blocks(k)
print("\n(2) leave-one-block-out K5 WR (drop each block):")
worst=99
for i in range(8):
    sub=[r for j,b in enumerate(bl) if j!=i for r in b]
    kept=[r for r in sub if K5(r)]
    base_sub=wr(sub); kw=wr(kept)
    worst=min(worst,kw-base_sub)
    print(f"   drop blk{i}: base={base_sub:.2f} K5={kw:.2f} lift={kw-base_sub:+.2f}")
print(f"   worst lift across LOBO = {worst:+.2f}pp (should stay >0)")

# (3) winner-cut audit
cut=[r for r in k if not K5(r)]
cw=[r for r in cut if r['win']==1]
print(f"\n(3) winners cut by K5: {len(cw)} of 1614 ({100*len(cw)/1614:.1f}%)")
print(f"    avg R of cut winners = {sum(r['R'] for r in cw)/len(cw):.2f}")
print(f"    max R cut winner = {max(r['R'] for r in cw):.2f}; #cut winners with R>=2: {sum(1 for r in cw if r['R']>=2)}")
allw=[r for r in k if r['win']==1]
print(f"    avg R all winners = {sum(r['R'] for r in allw)/len(allw):.2f} (cut winners {'cheaper' if sum(r['R'] for r in cw)/len(cw)<sum(r['R'] for r in allw)/len(allw) else 'pricier'})")

# (4) clause standalone
print("\n(4) clause contribution:")
report(evaluate(k, lambda r: not (r['buy_sell_ratio4']>=7 and -2<=r['flow_accel']<=0), "A: cut bsr4>=7&flat"))
report(evaluate(k, lambda r: not (r['absorption']==1 and r['low_vol_rel']>1.5), "B: cut absorb&lowvol"))

# (5) refinement: try to RAISE winners_kept while robust. Tighten clauses.
print("\n(5) refinements:")
refs=[
  ("R5a tighten: bsr4>=8&flat OR absorb&lowvol>1.8",
     lambda r: not ((r['buy_sell_ratio4']>=8 and -2<=r['flow_accel']<=0) or (r['absorption']==1 and r['low_vol_rel']>1.8))),
  ("R5b add 3rd clause buy_L_recent&bsr4>=7",
     lambda r: not ((r['buy_sell_ratio4']>=7 and -2<=r['flow_accel']<=0) or (r['absorption']==1 and r['low_vol_rel']>1.5) or (r['buy_L_recent']==1 and r['buy_sell_ratio4']>=7))),
  ("R5c flat-flow widened [-3,1]",
     lambda r: not ((r['buy_sell_ratio4']>=7 and -3<=r['flow_accel']<=1) or (r['absorption']==1 and r['low_vol_rel']>1.5))),
  ("R5d bsr4>=6&flat OR absorb&lowvol>1.5",
     lambda r: not ((r['buy_sell_ratio4']>=6 and -2<=r['flow_accel']<=0) or (r['absorption']==1 and r['low_vol_rel']>1.5))),
]
for d,f in refs:
    report(evaluate(k,f,d)); print()
