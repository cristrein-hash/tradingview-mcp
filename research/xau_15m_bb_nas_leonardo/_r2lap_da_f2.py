"""Devil's Advocate confirm on F2 = cut chop_score>=3.
chop_score = sum of 5 orthogonal chop-symptoms (all univ WR<66):
  one-sided buying bsr4>=7, flat flow_accel[-2,0], absorption==1,
  high-vol-noise low_vol_rel>1.5, young-regime regime_age_h<25.2.
Cut only when >=3 co-occur (contextual, not single hand-picked clause).
No look-ahead/no R in predicate. R used only for winner-cut COST audit.
"""
from _r2lap_lib import load, blocks, wr

k = load()

def score(r):
    return ((r['buy_sell_ratio4'] >= 7) + (-2 <= r['flow_accel'] <= 0) +
            (r['absorption'] == 1) + (r['low_vol_rel'] > 1.5) +
            (r['regime_age_h'] < 25.2))

F2 = lambda r: score(r) < 3

# LOBO stability
bl = blocks(k)
worst = 99
print("F2 leave-one-block-out:")
for i in range(8):
    sub = [r for j, b in enumerate(bl) if j != i for r in b]
    kept = [r for r in sub if F2(r)]
    lift = wr(kept) - wr(sub)
    worst = min(worst, lift)
    print(f"  drop blk{i}: lift {lift:+.2f}pp")
print(f"  worst LOBO lift = {worst:+.2f}pp")

# winner-cut cost
cut = [r for r in k if not F2(r)]
cw = [r for r in cut if r['win'] == 1]
allw = [r for r in k if r['win'] == 1]
print(f"\nwinners cut = {len(cw)} avgR={sum(r['R'] for r in cw)/len(cw):.2f} "
      f"R>=2:{sum(1 for r in cw if r['R']>=2)} maxR={max(r['R'] for r in cw):.2f}")
print(f"all winners avgR={sum(r['R'] for r in allw)/len(allw):.2f} "
      f"(cut winners are {'cheap' if sum(r['R'] for r in cw)/len(cw) < sum(r['R'] for r in allw)/len(allw) else 'pricey'})")
