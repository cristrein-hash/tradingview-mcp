#!/usr/bin/env python3
"""
DEVIL'S ADVOCATE verification of R_B lapidation filter on dataset_r2refine.jsonl (r2_keep==1 only).

Rule R_B = CUT when:
  (absorption==1 AND sell_decel==0)
  OR (buy_sell_ratio4>7 AND low_vol_rel>1.37)
  OR (regime_age_h<=25.2 AND sell_skew_mig>0)

KEEP = NOT CUT.

Régua: do NOT veto by tail / WR-only / no-OOS.
VETO only for:
  - look-ahead (feature uses future/outcome)
  - stationarity gate: per-year WR-after must be >= base-of-year (within r2_keep);
    per-block: <=2/8 blocks worse than block-base allowed
  - cuts too many winners (<85% winners kept)
  - combo cherry-picked (neighborhood collapses under +-20% threshold perturbation)
"""
import json

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]


def is_cut(r, t_ratio=7.0, t_vol=1.37, t_age=25.2):
    c1 = (r['absorption'] == 1 and r['sell_decel'] == 0)
    c2 = (r['buy_sell_ratio4'] > t_ratio and r['low_vol_rel'] > t_vol)
    c3 = (r['regime_age_h'] <= t_age and r['sell_skew_mig'] > 0)
    return c1 or c2 or c3


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

    print('=== TOTAL ===')
    print('n_base %d  WR_base %.2f' % (len(base), wr(base)))
    print('n_cut  %d  WR_cut  %.2f' % (len(cut), wr(cut)))
    print('n_keep %d  WR_keep %.2f' % (len(keep), wr(keep)))
    print('winners_kept_pct %.2f' % (100.0 * winners_kept / total_winners))
    print('losers_cut_pct   %.2f' % (100.0 * losers_cut / total_losers))
    print('streak_base %d  streak_keep %d' % (max_loss_streak(base), max_loss_streak(keep)))

    print('\n=== PER YEAR (stationarity gate: WR_keep >= base-of-year) ===')
    year_fail = []
    for yr in sorted(set(r['yr'] for r in base)):
        yb = [r for r in base if r['yr'] == yr]
        yk = [r for r in keep if r['yr'] == yr]
        ywin = sum(r['win'] for r in yb)
        ywin_k = sum(r['win'] for r in yk)
        wk_pct = 100.0 * ywin_k / ywin if ywin else float('nan')
        worse = wr(yk) < wr(yb)
        if worse:
            year_fail.append(yr)
        print('  yr %d  base %.2f (n%d) -> keep %.2f (n%d)  winners_kept %.1f%%  %s'
              % (yr, wr(yb), len(yb), wr(yk), len(yk), wk_pct,
                 'WORSE!' if worse else 'ok'))

    print('\n=== PER BLOCK (gate: <=2/8 blocks worse than block-base) ===')
    block_worse = 0
    for blk in sorted(set(r['block'] for r in base)):
        bb = [r for r in base if r['block'] == blk]
        bk = [r for r in keep if r['block'] == blk]
        worse = wr(bk) < wr(bb)
        if worse:
            block_worse += 1
        print('  %s  base %.2f (n%d) -> keep %.2f (n%d)  %s'
              % (blk, wr(bb), len(bb), wr(bk), len(bk), 'WORSE' if worse else 'ok'))
    print('  blocks worse: %d / 8' % block_worse)

    print('\n=== COMPONENT-ISOLATED (loser-density claim) ===')
    for name, fn in [
        ('c1 absorb&decel0', lambda r: r['absorption'] == 1 and r['sell_decel'] == 0),
        ('c2 ratio4>7&vol>1.37', lambda r: r['buy_sell_ratio4'] > 7 and r['low_vol_rel'] > 1.37),
        ('c3 age<=25.2&skew>0', lambda r: r['regime_age_h'] <= 25.2 and r['sell_skew_mig'] > 0),
    ]:
        s = [r for r in base if fn(r)]
        # winners kept if ONLY this component cut
        keep_only = [r for r in base if not fn(r)]
        wk = 100.0 * sum(r['win'] for r in keep_only) / total_winners
        print('  %s : n_cut %d  WR %.2f  winners_kept_if_only %.1f%%'
              % (name, len(s), wr(s), wk))

    print('\n=== THRESHOLD PERTURBATION +-20% (cherry-pick / neighborhood) ===')
    import itertools
    base_w = wr(keep)
    for fr, fv, fa in itertools.product([0.8, 1.0, 1.2], repeat=3):
        tk = [r for r in base if not is_cut(r, 7.0 * fr, 1.37 * fv, 25.2 * fa)]
        wkp = 100.0 * sum(r['win'] for r in tk) / total_winners
        print('  ratio*%.1f vol*%.1f age*%.1f : WR_keep %.2f  n %d  winners_kept %.1f%%'
              % (fr, fv, fa, wr(tk), len(tk), wkp))

    print('\n=== LEAVE-ONE-BLOCK-OUT (edge distributed?) ===')
    for name, fn in [
        ('c1', lambda r: r['absorption'] == 1 and r['sell_decel'] == 0),
        ('c2', lambda r: r['buy_sell_ratio4'] > 7 and r['low_vol_rel'] > 1.37),
        ('c3', lambda r: r['regime_age_h'] <= 25.2 and r['sell_skew_mig'] > 0),
    ]:
        others = [c for n, c in [
            ('c1', lambda r: r['absorption'] == 1 and r['sell_decel'] == 0),
            ('c2', lambda r: r['buy_sell_ratio4'] > 7 and r['low_vol_rel'] > 1.37),
            ('c3', lambda r: r['regime_age_h'] <= 25.2 and r['sell_skew_mig'] > 0),
        ] if n != name]
        keep_minus = [r for r in base if not (others[0](r) or others[1](r))]
        lift = wr(keep_minus) - wr(base)
        print('  drop %s : WR_keep %.2f  lift %+.2f' % (name, wr(keep_minus), lift))

    print('\n=== VERDICT INPUTS ===')
    print('year_fail:', year_fail)
    print('block_worse:', block_worse)
    print('winners_kept_pct: %.2f' % (100.0 * winners_kept / total_winners))


if __name__ == '__main__':
    report()
