#!/usr/bin/env python3
"""
Devil's Advocate verification of A2 filter on dataset_5atr.jsonl.
RULE: KEEP if h1_pos>=0.65 AND disp4_atr>=0.78.
Veto criteria (recalibrated): look-ahead, non-stationarity (worse in ANY year vs that
year's base, OR >2/8 blocks worse), winners_kept<85%, cherry-pick (+/-20% neighborhood collapses).
Do NOT veto on tail/WR-only/no-OOS.
"""
import json, collections

ROWS = [json.loads(l) for l in open('dataset_5atr.jsonl')]

def wr(rows):
    return 100.0 * sum(r['win'] for r in rows) / len(rows) if rows else float('nan')

def max_losing_streak(rows):
    # chronological by low_t
    s = sorted(rows, key=lambda r: r['low_t'])
    cur = mx = 0
    for r in s:
        if r['win'] == 0:
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx

def keep(r, h1=0.65, disp=0.78):
    return (r['h1_pos'] is not None and r['disp4_atr'] is not None
            and r['h1_pos'] >= h1 and r['disp4_atr'] >= disp)

def report(h1=0.65, disp=0.78, label='A2'):
    kept = [r for r in ROWS if keep(r, h1, disp)]
    cut  = [r for r in ROWS if not keep(r, h1, disp)]
    base_w = sum(r['win'] for r in ROWS)
    kept_w = sum(r['win'] for r in kept)
    out = {}
    out['label'] = label
    out['h1>=%.2f disp>=%.2f' % (h1, disp)] = True
    out['n_keep'] = len(kept)
    out['wr_base'] = round(wr(ROWS), 2)
    out['wr_keep'] = round(wr(kept), 2)
    out['avgR_base'] = round(sum(r['R'] for r in ROWS)/len(ROWS), 3)
    out['avgR_keep'] = round(sum(r['R'] for r in kept)/len(kept), 3) if kept else None
    out['streak_base'] = max_losing_streak(ROWS)
    out['streak_keep'] = max_losing_streak(kept)
    out['winners_kept_pct'] = round(100.0*kept_w/base_w, 2)
    out['losers_cut_pct'] = round(100.0*(sum(1-r['win'] for r in cut))/(len(ROWS)-base_w), 2)
    return out, kept

def per_year(h1=0.65, disp=0.78):
    res = {}
    for yr in sorted(set(r['yr'] for r in ROWS)):
        base = [r for r in ROWS if r['yr']==yr]
        kept = [r for r in base if keep(r, h1, disp)]
        res[yr] = {'base_wr': round(wr(base),2), 'keep_wr': round(wr(kept),2) if kept else None,
                   'n_keep': len(kept), 'delta': round(wr(kept)-wr(base),2) if kept else None}
    return res

def per_block(h1=0.65, disp=0.78):
    res = {}
    for blk in sorted(set(r['block'] for r in ROWS)):
        base = [r for r in ROWS if r['block']==blk]
        kept = [r for r in base if keep(r, h1, disp)]
        res[blk] = {'base_wr': round(wr(base),2), 'keep_wr': round(wr(kept),2) if kept else None,
                    'n_keep': len(kept), 'delta': round(wr(kept)-wr(base),2) if kept else None}
    return res

if __name__ == '__main__':
    main, kept = report()
    print('=== MAIN ===')
    for k,v in main.items(): print(' ', k, v)
    print('\n=== PER YEAR (base WR vs keep WR) ===')
    py = per_year()
    worse_years = []
    for yr,d in py.items():
        flag = ''
        if d['keep_wr'] is not None and d['keep_wr'] < d['base_wr']:
            flag = '  <-- WORSE THAN BASE-YEAR'; worse_years.append(yr)
        print(' ', yr, d, flag)
    print('\n=== PER BLOCK (8) ===')
    pb = per_block()
    worse_blocks = []
    for blk,d in pb.items():
        flag = ''
        if d['keep_wr'] is not None and d['keep_wr'] < d['base_wr']:
            flag = '  <-- WORSE'; worse_blocks.append(blk)
        print(' ', blk, d, flag)
    print('\nworse_years=', worse_years, ' worse_blocks=', len(worse_blocks), worse_blocks)

    print('\n=== CHERRY-PICK NEIGHBORHOOD (+/-20% on both thresholds) ===')
    for fh in (0.8, 0.9, 1.0, 1.1, 1.2):
        for fd in (0.8, 0.9, 1.0, 1.1, 1.2):
            h1 = round(0.65*fh, 4); dp = round(0.78*fd, 4)
            m,_ = report(h1, dp, 'nbhd')
            print('  h1=%.3f disp=%.3f -> wr_keep=%.2f n=%d wkept%%=%.1f'
                  % (h1, dp, m['wr_keep'], m['n_keep'], m['winners_kept_pct']))
