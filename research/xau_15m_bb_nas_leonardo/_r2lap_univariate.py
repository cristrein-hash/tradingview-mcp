"""Univariate signal scan on r2_keep==1. WR of win==0/1 across feature bins/flags.
Purpose: find which orthogonal features carry directional signal to inform combos.
Not a filter proposal — diagnostic.
"""
from _r2lap_lib import load, wr

k = load()
N = len(k)
print(f"n={N} overall WR={wr(k):.2f}")

# binary flags
print("\n== BINARY FLAGS (WR | n) ==")
for f in ['absorption', 'buy_after_smc', 'naslong_after_smc', 'buy_L_recent',
          'is_london_open', 'is_ny_overlap', 'is_deadzone']:
    for v in (0, 1):
        sub = [r for r in k if r[f] == v]
        print(f"  {f}=={v}: WR={wr(sub):6.2f} n={len(sub)}")

# continuous -> quartile WR
print("\n== CONTINUOUS quartile WR ==")
import statistics
for f in ['low_vol_rel', 'low_closepos', 'bars_since_lowest', 'sell_decel',
          'flow_accel', 'bars_since_sell', 'bars_since_buycross', 'buy_sell_ratio4',
          'smc_lag_bars', 'sell_skew_mig', 'regime_age_h']:
    vals = sorted(r[f] for r in k if abs(r[f]) < 1e6)
    if not vals:
        continue
    q = [vals[int(len(vals) * p)] for p in (0.25, 0.5, 0.75)]
    bins = {'Q1': [], 'Q2': [], 'Q3': [], 'Q4': []}
    for r in k:
        x = r[f]
        if abs(x) >= 1e6:
            continue
        if x <= q[0]:
            bins['Q1'].append(r)
        elif x <= q[1]:
            bins['Q2'].append(r)
        elif x <= q[2]:
            bins['Q3'].append(r)
        else:
            bins['Q4'].append(r)
    s = f"  {f:18s} cuts={[round(x,2) for x in q]}: "
    for b in ('Q1', 'Q2', 'Q3', 'Q4'):
        s += f"{b}={wr(bins[b]):5.1f}(n{len(bins[b])}) "
    print(s)
