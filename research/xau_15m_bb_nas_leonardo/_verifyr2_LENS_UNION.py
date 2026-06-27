#!/usr/bin/env python3
"""
DEVIL'S ADVOCATE verification of LENS UNION lapidation filter on r2_keep==1.

Rule = CUT when:
  regime_age_h < 24 AND (absorption==1 OR low_vol_rel >= 1.5)
KEEP = NOT CUT.

Régua: no veto by tail / WR-only / no-OOS. Veto only for:
  - look-ahead
  - stationarity gate: per-year WR_keep < base-of-year; per-block >2/8 worse
  - cuts winners (<85% kept)
  - combo cherry-picked (neighborhood collapses under +-20% perturbation)
"""
import json, itertools

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]


def is_cut(r, t_age=24.0, t_vol=1.5):
    return r['regime_age_h'] < t_age and (r['absorption'] == 1 or r['low_vol_rel'] >= t_vol)


def wr(sub):
    return 100.0 * sum(x['win'] for x in sub) / len(sub) if sub else float('nan')


def max_loss_streak(sub):
    s = sorted(sub, key=lambda r: r['low_t'])
    cur = best = 0
    for r in s:
        if r['win'] == 0:
            cur += 1; best = max(best, cur)
        else:
            cur = 0
    return best


def report():
    base = KEPT
    cut = [r for r in base if is_cut(r)]
    keep = [r for r in base if not is_cut(r)]
    total_winners = sum(r['win'] for r in base)
    total_losers = len(base) - total_winners
    winners_kept = sum(r['win'] for r in keep)
    losers_cut = total_losers - (len(keep) - winners_kept)

    print('=== TOTAL ===')
    print('n_base %d  WR_base %.2f  streak_base %d' % (len(base), wr(base), max_loss_streak(base)))
    print('n_cut  %d  WR_cut  %.2f' % (len(cut), wr(cut)))
    print('n_keep %d  WR_keep %.2f  streak_keep %d' % (len(keep), wr(keep), max_loss_streak(keep)))
    print('winners_kept_pct %.2f' % (100.0 * winners_kept / total_winners))
    print('losers_cut_pct   %.2f' % (100.0 * losers_cut / total_losers))

    print('\n=== PER YEAR (gate: WR_keep >= base-of-year) ===')
    year_fail = []
    for yr in sorted(set(r['yr'] for r in base)):
        yb = [r for r in base if r['yr'] == yr]
        yk = [r for r in keep if r['yr'] == yr]
        worse = wr(yk) < wr(yb)
        if worse: year_fail.append(yr)
        print('  yr %d base %.2f (n%d) -> keep %.2f (n%d) %s'
              % (yr, wr(yb), len(yb), wr(yk), len(yk), 'WORSE!' if worse else 'ok'))

    print('\n=== PER BLOCK (gate: <=2/8 worse) ===')
    block_worse = 0
    for blk in sorted(set(r['block'] for r in base)):
        bb = [r for r in base if r['block'] == blk]
        bk = [r for r in keep if r['block'] == blk]
        worse = wr(bk) < wr(bb)
        if worse: block_worse += 1
        print('  %s base %.2f (n%d) -> keep %.2f (n%d) %s'
              % (blk, wr(bb), len(bb), wr(bk), len(bk), 'WORSE' if worse else 'ok'))
    print('  blocks worse: %d / 8' % block_worse)

    print('\n=== COMPONENT ISOLATION ===')
    for name, fn in [
        ('young&absorb', lambda r: r['regime_age_h'] < 24 and r['absorption'] == 1),
        ('young&volchaos', lambda r: r['regime_age_h'] < 24 and r['low_vol_rel'] >= 1.5),
    ]:
        s = [r for r in base if fn(r)]
        print('  %s : n_cut %d  WR %.2f' % (name, len(s), wr(s)))

    print('\n=== THRESHOLD PERTURBATION +-20% ===')
    for fa, fv in itertools.product([0.8, 1.0, 1.2], repeat=2):
        tk = [r for r in base if not is_cut(r, 24.0 * fa, 1.5 * fv)]
        wkp = 100.0 * sum(r['win'] for r in tk) / total_winners
        print('  age*%.1f vol*%.1f : WR_keep %.2f  n %d  winners_kept %.1f%%'
              % (fa, fv, wr(tk), len(tk), wkp))

    print('\n=== VERDICT INPUTS ===')
    print('year_fail:', year_fail)
    print('block_worse:', block_worse)
    print('winners_kept_pct: %.2f' % (100.0 * winners_kept / total_winners))
    print('wr_keep: %.2f  streak_keep: %d' % (wr(keep), max_loss_streak(keep)))


if __name__ == '__main__':
    report()
