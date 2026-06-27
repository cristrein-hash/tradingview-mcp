#!/usr/bin/env python3
"""R2 lapidation - explore orthogonal feature distributions and base rates (R2-KEPT only)."""
import json
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]

ORTHO = ['low_vol_rel','low_closepos','bars_since_lowest','absorption','sell_decel',
         'flow_accel','bars_since_sell','bars_since_buycross','buy_sell_ratio4','max_silence',
         'smc_lag_bars','buy_after_smc','naslong_after_smc','sell_skew_mig','buy_L_recent',
         'regime_age_h','is_london_open','is_ny_overlap','is_deadzone']

def base_year():
    yr = defaultdict(lambda: [0, 0])
    for r in KEPT:
        yr[r['yr']][0] += 1; yr[r['yr']][1] += r['win']
    return {y: 100*w/n for y, (n, w) in yr.items()}

def main():
    n = len(KEPT); wins = sum(r['win'] for r in KEPT)
    print('KEPT n', n, 'WR', round(100*wins/n, 3))
    yb = base_year()
    for y in sorted(yb): print('  base year', y, round(yb[y], 2))
    print('--- feature win-rate by quantile / value ---')
    for f in ORTHO:
        vals = sorted(r[f] for r in KEPT)
        uniq = sorted(set(vals))
        if len(uniq) <= 4:
            # categorical
            cat = defaultdict(lambda: [0, 0])
            for r in KEPT:
                cat[r[f]][0] += 1; cat[r[f]][1] += r['win']
            s = ' '.join(f'{v}:n{c}wr{round(100*w/c,1)}' for v, (c, w) in sorted(cat.items()))
            print(f'{f:20s} CAT {s}')
        else:
            # quartile buckets, skip sentinel -1e7
            clean = [r for r in KEPT if r[f] > -1e6]
            cv = sorted(x[f] for x in clean)
            import statistics
            qs = [cv[int(len(cv)*p)] for p in (0.25, 0.5, 0.75)]
            buck = defaultdict(lambda: [0, 0])
            for r in clean:
                v = r[f]
                b = 0 if v <= qs[0] else 1 if v <= qs[1] else 2 if v <= qs[2] else 3
                buck[b][0] += 1; buck[b][1] += r['win']
            s = ' '.join(f'Q{b}:n{c}wr{round(100*w/c,1)}' for b, (c, w) in sorted(buck.items()))
            sent = sum(1 for r in KEPT if r[f] <= -1e6)
            print(f'{f:20s} q={[round(q,3) for q in qs]} sentinel={sent}')
            print(f'{"":20s} {s}')

if __name__ == '__main__':
    main()
