#!/usr/bin/env python3
"""
DA verification of R2-refine lapidation filter R_D (SELL-exhaustion-into-overheat/vol).
Operates ONLY on r2_keep==1 rows of dataset_r2refine.jsonl.

RULE R_D (CUT when any holds):
  (buy_sell_ratio4>7  AND sell_skew_mig>0)
  OR (regime_age_h<=25.2 AND sell_skew_mig>0)
  OR (flow_accel==0    AND low_vol_rel>1.37)

Verdict gate (régua DA recalibrada):
  - look-ahead: features must be known at entry (audited separately/structurally here).
  - stationarity: kept-WR-after must be >= base-of-year (within r2_keep) for EVERY year,
    and <=2/8 blocks worse than block base.
  - winners kept >= 85%.
  - combo not cherry-picked (neighborhood collapse check).
"""
import json, os

PATH = os.path.join(os.path.dirname(__file__), 'dataset_r2refine.jsonl')

def load():
    rows = [json.loads(l) for l in open(PATH)]
    return [r for r in rows if r.get('r2_keep') == 1]

def cut(r):
    return ((r['buy_sell_ratio4'] > 7 and r['sell_skew_mig'] > 0)
            or (r['regime_age_h'] <= 25.2 and r['sell_skew_mig'] > 0)
            or (r['flow_accel'] == 0 and r['low_vol_rel'] > 1.37))

def wr(rows):
    return 100.0 * sum(x['win'] for x in rows) / len(rows) if rows else float('nan')

def streak(rows):
    # longest run of consecutive wins, ordered by low_t
    s = sorted(rows, key=lambda r: r['low_t'])
    best = cur = 0
    for r in s:
        if r['win']:
            cur += 1; best = max(best, cur)
        else:
            cur = 0
    return best

def main():
    kept = load()
    base = [r for r in kept if not cut(r)]   # KEPT after applying cut-rule
    removed = [r for r in kept if cut(r)]

    print('=== TOTAL ===')
    print('R2-kept n', len(kept), 'WR %.2f' % wr(kept), 'streak', streak(kept))
    print('after R_D n', len(base), 'WR %.2f' % wr(base), 'streak', streak(base))
    print('removed n', len(removed), 'WR %.2f' % wr(removed))

    tot_winners = sum(r['win'] for r in kept)
    kept_winners = sum(r['win'] for r in base)
    tot_losers = sum(1 - r['win'] for r in kept)
    cut_losers = sum(1 - r['win'] for r in removed)
    wkept = 100.0 * kept_winners / tot_winners
    lcut = 100.0 * cut_losers / tot_losers
    print('winners_kept_pct %.2f' % wkept, 'losers_cut_pct %.2f' % lcut)

    print('\n=== BY YEAR (base-of-year within r2_keep) ===')
    year_fail = []
    for y in sorted(set(r['yr'] for r in kept)):
        ky = [r for r in kept if r['yr'] == y]
        by = [r for r in base if r['yr'] == y]
        worse = wr(by) < wr(ky)
        if worse: year_fail.append(y)
        print(y, 'base_yr %.2f' % wr(ky), '-> after %.2f' % wr(by),
              'WORSE' if worse else 'ok', 'n', len(by))

    print('\n=== BY BLOCK ===')
    block_worse = 0
    for b in sorted(set(r['block'] for r in kept)):
        kb = [r for r in kept if r['block'] == b]
        bb = [r for r in base if r['block'] == b]
        worse = wr(bb) < wr(kb)
        if worse: block_worse += 1
        print(b, 'base %.2f' % wr(kb), '-> after %.2f' % wr(bb),
              'WORSE' if worse else 'ok', 'n', len(bb))
    print('blocks worse:', block_worse, '/ 8')

    print('\n=== NEIGHBORHOOD / CHERRY-PICK PROBE (each disjunct alone) ===')
    def probe(name, fn):
        rem = [r for r in kept if fn(r)]
        keptn = [r for r in kept if not fn(r)]
        print('%-30s removed n %4d remWR %.2f -> keptWR %.2f' %
              (name, len(rem), wr(rem) if rem else float('nan'), wr(keptn)))
    probe('A buy_sell_ratio4>7&skew>0', lambda r: r['buy_sell_ratio4'] > 7 and r['sell_skew_mig'] > 0)
    probe('B regime_age<=25.2&skew>0', lambda r: r['regime_age_h'] <= 25.2 and r['sell_skew_mig'] > 0)
    probe('C flow_accel==0&lowvol>1.37', lambda r: r['flow_accel'] == 0 and r['low_vol_rel'] > 1.37)
    # threshold jitter on the main knobs
    print('\n--- threshold jitter (full rule, perturb one knob) ---')
    variants = {
        'ratio>6': lambda r: ((r['buy_sell_ratio4']>6 and r['sell_skew_mig']>0) or (r['regime_age_h']<=25.2 and r['sell_skew_mig']>0) or (r['flow_accel']==0 and r['low_vol_rel']>1.37)),
        'ratio>8': lambda r: ((r['buy_sell_ratio4']>8 and r['sell_skew_mig']>0) or (r['regime_age_h']<=25.2 and r['sell_skew_mig']>0) or (r['flow_accel']==0 and r['low_vol_rel']>1.37)),
        'age<=20': lambda r: ((r['buy_sell_ratio4']>7 and r['sell_skew_mig']>0) or (r['regime_age_h']<=20 and r['sell_skew_mig']>0) or (r['flow_accel']==0 and r['low_vol_rel']>1.37)),
        'age<=30': lambda r: ((r['buy_sell_ratio4']>7 and r['sell_skew_mig']>0) or (r['regime_age_h']<=30 and r['sell_skew_mig']>0) or (r['flow_accel']==0 and r['low_vol_rel']>1.37)),
        'vol>1.2': lambda r: ((r['buy_sell_ratio4']>7 and r['sell_skew_mig']>0) or (r['regime_age_h']<=25.2 and r['sell_skew_mig']>0) or (r['flow_accel']==0 and r['low_vol_rel']>1.2)),
        'vol>1.5': lambda r: ((r['buy_sell_ratio4']>7 and r['sell_skew_mig']>0) or (r['regime_age_h']<=25.2 and r['sell_skew_mig']>0) or (r['flow_accel']==0 and r['low_vol_rel']>1.5)),
    }
    for nm, fn in variants.items():
        kn = [r for r in kept if not fn(r)]
        print('%-10s after n %4d WR %.2f' % (nm, len(kn), wr(kn)))

    print('\n=== WORSE-BLOCK MAGNITUDE (high-WR blocks losing a few wins) ===')
    for b in sorted(set(r['block'] for r in kept)):
        kb = [r for r in kept if r['block'] == b]
        bb = [r for r in base if r['block'] == b]
        if wr(bb) < wr(kb):
            rem = [r for r in kb if cut(r)]
            print(b, 'delta %.2f' % (wr(bb) - wr(kb)),
                  'cut_n', len(rem), 'cut_WR %.1f' % wr(rem))

    print('\n=== LOSING-STREAK (rule streak metric) ===')
    def lose_streak(rows):
        s = sorted(rows, key=lambda r: r['low_t']); best = cur = 0
        for x in s:
            if not x['win']: cur += 1; best = max(best, cur)
            else: cur = 0
        return best
    print('lose_streak kept', lose_streak(kept), '-> after', lose_streak(base))

    print('\n=== VERDICT INPUTS ===')
    print('year_fail', year_fail, 'block_worse', block_worse, 'winners_kept %.2f' % wkept)

if __name__ == '__main__':
    main()
