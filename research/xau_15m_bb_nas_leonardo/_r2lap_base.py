#!/usr/bin/env python3
"""R2-lapidation base stats + feature univariate scan on r2_keep==1 subset.
RAW-causal: only orthogonal NEW features. Reports base WR, per-year base, per-block base.
"""
import json
from collections import defaultdict

PATH = 'dataset_r2refine.jsonl'

def load():
    rows = [json.loads(l) for l in open(PATH)]
    kept = [r for r in rows if r['r2_keep'] == 1]
    kept.sort(key=lambda r: r['low_t'])  # chronological for streak
    return kept

def max_losing_streak(rows):
    """rows already sorted by low_t; loss = win==0."""
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx

def wr(rows):
    return sum(r['win'] for r in rows) / len(rows) if rows else 0.0

def per_year(rows):
    yr = defaultdict(lambda: [0, 0])
    for r in rows:
        yr[r['yr']][0] += 1
        yr[r['yr']][1] += r['win']
    return {y: (yr[y][0], yr[y][1] / yr[y][0]) for y in sorted(yr)}

def per_block(rows):
    bl = defaultdict(lambda: [0, 0])
    for r in rows:
        bl[r['block']][0] += 1
        bl[r['block']][1] += r['win']
    return {b: (bl[b][0], bl[b][1] / bl[b][0]) for b in sorted(bl)}

ORTHO = ['low_vol_rel','low_closepos','bars_since_lowest','absorption','sell_decel',
         'flow_accel','bars_since_sell','bars_since_buycross','buy_sell_ratio4','max_silence',
         'smc_lag_bars','buy_after_smc','naslong_after_smc','sell_skew_mig','buy_L_recent',
         'regime_age_h','is_london_open','is_ny_overlap','is_deadzone']

if __name__ == '__main__':
    kept = load()
    print('n_kept', len(kept))
    print('WR base %.4f' % wr(kept))
    print('streak base', max_losing_streak(kept))
    print('per-year base:')
    for y, (n, w) in per_year(kept).items():
        print('  ', y, 'n', n, 'WR %.4f' % w)
    print('per-block base:')
    for b, (n, w) in per_block(kept).items():
        print('  ', b, n, '%.4f' % w)

    # univariate: for binary feats show WR by value; for numeric show quartile WR
    print('\n=== UNIVARIATE WR by feature ===')
    for f in ORTHO:
        vals = sorted(set(r[f] for r in kept))
        if len(vals) <= 4:
            line = []
            for v in vals:
                sub = [r for r in kept if r[f] == v]
                line.append('%s=%g:n%d wr%.3f' % (f, v, len(sub), wr(sub)))
            print(f, '|', '  '.join(line))
        else:
            # quartiles (exclude sentinel -10000000 for sell_decel)
            clean = [r for r in kept if r[f] > -1e6]
            xs = sorted(r[f] for r in clean)
            qs = [xs[int(len(xs)*q)] for q in (0.25,0.5,0.75)]
            buckets = defaultdict(list)
            for r in clean:
                v = r[f]
                b = 0 if v<=qs[0] else 1 if v<=qs[1] else 2 if v<=qs[2] else 3
                buckets[b].append(r)
            line = ['q%d:n%d wr%.3f'%(b,len(buckets[b]),wr(buckets[b])) for b in range(4)]
            print(f,'cuts',[round(q,3) for q in qs],'|',' '.join(line))
