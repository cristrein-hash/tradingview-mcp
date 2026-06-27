#!/usr/bin/env python3
"""
DEVIL'S ADVOCATE verification of the R2 lapidation filter on dataset_r2refine.jsonl
(r2_keep==1 only).

Rule under test (R_C "absorb on fresh regime"):
  CUT when (absorption==1 AND regime_age_h < 24).
  KEEP = NOT CUT.

Claim from generator:
  n_keep=2117, wr_keep=69.25, streak_keep=21, winners_kept_pct=90.83,
  losers_cut_pct=12.15, y24=66.4, y25=71.5, y26=66.6, robust=True.

Base (r2_keep==1): WR=68.54, streak=24.

Régua (recalibrated DA): do NOT veto by tail / WR-only / no-OOS.
VETO only for:
  - look-ahead: feature uses future/outcome. absorption / regime_age_h must be
    known at trade time (t<=tc). Both are pre-entry microstructure/clock features.
  - stationarity gate: per-year WR_keep must be >= base-of-YEAR (within r2_keep),
    NOT global base. Any year worse => veto.
  - per-block gate: >2/8 blocks worse than that block's own base => veto.
  - cuts too many winners (winners_kept_pct < 85%).
  - combo cherry-picked: neighborhood collapses under threshold perturbation of
    the age cutoff (+-20%, and a sweep).
"""
import json

PATH = 'dataset_r2refine.jsonl'
ROWS = [json.loads(l) for l in open(PATH)]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]


def is_cut(r, t_age=24.0):
    return (r['absorption'] == 1 and r['regime_age_h'] < t_age)


def wr(sub):
    return 100.0 * sum(x['win'] for x in sub) / len(sub) if sub else float('nan')


def max_loss_streak(sub):
    """sub ordered by low_t; longest run of losses (win==0)."""
    s = sorted(sub, key=lambda r: r['low_t'])
    cur = best = 0
    for r in s:
        if r['win'] == 0:
            cur += 1
            best = max(best, cur)
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
    losers_kept = len(keep) - winners_kept
    losers_cut = total_losers - losers_kept

    wkp = 100.0 * winners_kept / total_winners
    lcp = 100.0 * losers_cut / total_losers

    print('=== TOTAL ===')
    print('n_base %d  WR_base %.2f  streak_base %d'
          % (len(base), wr(base), max_loss_streak(base)))
    print('n_cut  %d  WR_cut  %.2f' % (len(cut), wr(cut)))
    print('n_keep %d  WR_keep %.2f  streak_keep %d'
          % (len(keep), wr(keep), max_loss_streak(keep)))
    print('winners_kept_pct %.2f   losers_cut_pct %.2f' % (wkp, lcp))

    print('\n=== PER YEAR (gate: WR_keep >= base-of-year) ===')
    year_fail = []
    for yr in sorted(set(r['yr'] for r in base)):
        yb = [r for r in base if r['yr'] == yr]
        yk = [r for r in keep if r['yr'] == yr]
        worse = wr(yk) < wr(yb)
        if worse:
            year_fail.append(yr)
        print('  yr %d  base %.2f (n%d) -> keep %.2f (n%d)  delta %+.2f  %s'
              % (yr, wr(yb), len(yb), wr(yk), len(yk), wr(yk) - wr(yb),
                 'WORSE!' if worse else 'ok'))

    print('\n=== PER BLOCK (gate: <=2/8 blocks worse than block-base) ===')
    block_worse = 0
    for blk in sorted(set(r['block'] for r in base)):
        bb = [r for r in base if r['block'] == blk]
        bk = [r for r in keep if r['block'] == blk]
        worse = wr(bk) < wr(bb)
        if worse:
            block_worse += 1
        print('  %s  base %.2f (n%d) -> keep %.2f (n%d)  delta %+.2f  %s'
              % (blk, wr(bb), len(bb), wr(bk), len(bk), wr(bk) - wr(bb),
                 'WORSE' if worse else 'ok'))
    print('  blocks worse: %d / 8' % block_worse)

    print('\n=== WHAT IS CUT (loser-density of the cut set) ===')
    cw = sum(r['win'] for r in cut)
    print('  cut n=%d  winners_in_cut=%d  losers_in_cut=%d  WR_cut=%.2f'
          % (len(cut), cw, len(cut) - cw, wr(cut)))

    print('\n=== AGE-CUTOFF SWEEP (cherry-pick / neighborhood) ===')
    for t in [12, 18, 19.2, 21.6, 24, 26.4, 28.8, 30, 36, 48]:
        tk = [r for r in base if not is_cut(r, t)]
        twk = 100.0 * sum(r['win'] for r in tk) / total_winners
        print('  age<%-5.1f : WR_keep %.2f  n %d  streak %d  winners_kept %.1f%%'
              % (t, wr(tk), len(tk), max_loss_streak(tk), twk))

    print('\n=== ISOLATE COMPONENTS ===')
    only_absorb = [r for r in base if r['absorption'] == 1]
    only_fresh = [r for r in base if r['regime_age_h'] < 24]
    print('  absorption==1        : n %d  WR %.2f' % (len(only_absorb), wr(only_absorb)))
    print('  regime_age_h<24      : n %d  WR %.2f' % (len(only_fresh), wr(only_fresh)))
    print('  absorb & fresh (CUT) : n %d  WR %.2f' % (len(cut), wr(cut)))
    # interaction: is the edge from the PAIR or just from one leg?
    absorb_old = [r for r in base if r['absorption'] == 1 and r['regime_age_h'] >= 24]
    fresh_noabsorb = [r for r in base if r['absorption'] == 0 and r['regime_age_h'] < 24]
    print('  absorb & OLD regime  : n %d  WR %.2f' % (len(absorb_old), wr(absorb_old)))
    print('  fresh & NO absorb    : n %d  WR %.2f' % (len(fresh_noabsorb), wr(fresh_noabsorb)))

    print('\n=== VERDICT INPUTS ===')
    print('year_fail:', year_fail)
    print('block_worse:', block_worse)
    print('winners_kept_pct: %.2f' % wkp)
    print('wr_keep: %.2f  streak_keep: %d  n_keep: %d'
          % (wr(keep), max_loss_streak(keep), len(keep)))


if __name__ == '__main__':
    report()
