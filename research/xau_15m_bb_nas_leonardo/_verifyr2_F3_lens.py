#!/usr/bin/env python3
"""
DEVIL'S ADVOCATE verification of F3 LENS lapidation filter on dataset_r2refine.jsonl (r2_keep==1 only).

Rule F3 = CUT when:  buy_after_smc==0 AND buy_L_recent==1
  (SMC structure NOT confirmed by later buy flow, combined with a recent large buy)
KEEP = NOT CUT.

Gate: per-year WR_keep >= base-of-year (within r2_keep); per-block <=2/8 worse;
winners_kept >= 85%; combo not cherry-picked (does AND collapse to one voice?).
NO veto by tail/WR-only/no-OOS.
"""
import json

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]


def is_cut(r):
    return r['buy_after_smc'] == 0 and r['buy_L_recent'] == 1


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

print('\n=== PER YEAR (gate: WR_keep >= base-of-year) ===')
year_fail = []
for yr in sorted(set(r['yr'] for r in base)):
    yb = [r for r in base if r['yr'] == yr]
    yk = [r for r in keep if r['yr'] == yr]
    ywin = sum(r['win'] for r in yb); ywin_k = sum(r['win'] for r in yk)
    wk_pct = 100.0 * ywin_k / ywin if ywin else float('nan')
    n_cut_y = len([r for r in yb if is_cut(r)])
    worse = wr(yk) < wr(yb)
    if worse: year_fail.append(yr)
    print('  yr %d  base %.2f (n%d) -> keep %.2f (n%d)  cut %d  winners_kept %.1f%%  %s'
          % (yr, wr(yb), len(yb), wr(yk), len(yk), n_cut_y, wk_pct, 'WORSE!' if worse else 'ok'))

print('\n=== PER BLOCK (gate: <=2/8 worse) ===')
block_worse = 0; blocks = sorted(set(r['block'] for r in base))
for blk in blocks:
    bb = [r for r in base if r['block'] == blk]
    bk = [r for r in keep if r['block'] == blk]
    n_cut_b = len([r for r in bb if is_cut(r)])
    worse = wr(bk) < wr(bb)
    if worse and n_cut_b > 0: block_worse += 1
    print('  %s  base %.2f (n%d) -> keep %.2f (n%d)  cut %d  %s'
          % (blk, wr(bb), len(bb), wr(bk), len(bk), n_cut_b,
             ('WORSE' if worse else 'ok') + (' [no cut]' if n_cut_b == 0 else '')))
print('  blocks worse (with cuts): %d / %d' % (block_worse, len(blocks)))

print('\n=== COMPONENT ISOLATION (does AND collapse to one voice?) ===')
for name, fn in [
    ('buy_after_smc==0 alone', lambda r: r['buy_after_smc'] == 0),
    ('buy_L_recent==1 alone', lambda r: r['buy_L_recent'] == 1),
    ('AND (F3)', is_cut),
]:
    s = [r for r in base if fn(r)]
    print('  %-24s n_cut %4d  WR_cut %.2f' % (name, len(s), wr(s)))

# overlap: how much of each component is the other? cherry-pick = one dominates
a = [r for r in base if r['buy_after_smc'] == 0]
b = [r for r in base if r['buy_L_recent'] == 1]
print('  buy_after_smc==0: n=%d  WR=%.2f   buy_L_recent==1: n=%d  WR=%.2f'
      % (len(a), wr(a), len(b), wr(b)))
print('  F3 cut n=%d  (smc0=%d, Lrec=%d) -> AND tightens both: %s'
      % (len(cut), len(a), len(b), 'real conjunction' if len(cut) < min(len(a), len(b)) else 'redundant'))

print('\n=== VERDICT INPUTS ===')
print('year_fail:', year_fail)
print('block_worse:', block_worse)
print('winners_kept_pct: %.2f' % (100.0 * winners_kept / total_winners))
print('wr_keep: %.2f  streak_keep: %d  n_keep: %d' % (wr(keep), max_loss_streak(keep), len(keep)))
