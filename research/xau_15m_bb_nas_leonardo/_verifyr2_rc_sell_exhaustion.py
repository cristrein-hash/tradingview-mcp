#!/usr/bin/env python3
"""
DA verification of R_C lapidation filter on R2-KEPT subset.

RULE (CUT when any pocket fires):
  (absorption==1 AND sell_decel==0)
  OR (low_vol_rel>1.37 AND sell_decel==0)
  OR (buy_L_recent==1 AND sell_skew_mig>0)

KEEP = NOT cut.

Regua DA: veto only for look-ahead, stationarity (per-year vs base-of-year within
r2_keep, or >2/8 blocks worse), cutting >15% winners (<85% kept), or cherry-picked
combo (neighborhood collapses).

Reports: WR before/after total+year+block, streak, winners_kept, cut composition.
"""
import json

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEEP = [r for r in ROWS if r['r2_keep'] == 1]


def is_cut(r):
    sd = r['sell_decel']
    p1 = (r['absorption'] == 1) and (sd == 0)
    p2 = (r['low_vol_rel'] > 1.37) and (sd == 0)
    p3 = (r['buy_L_recent'] == 1) and (r['sell_skew_mig'] > 0)
    return p1 or p2 or p3, (p1, p2, p3)


def wr(rs):
    return 100.0 * sum(x['win'] for x in rs) / len(rs) if rs else float('nan')


def max_streak(rs):
    """Max consecutive wins, ordered by low_t (chronological)."""
    s = sorted(rs, key=lambda x: x['low_t'])
    best = cur = 0
    for x in s:
        if x['win'] == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def main():
    cut = [r for r in KEEP if is_cut(r)[0]]
    kept = [r for r in KEEP if not is_cut(r)[0]]

    total_win = sum(r['win'] for r in KEEP)
    win_kept = sum(r['win'] for r in kept)
    loss_total = len(KEEP) - total_win
    loss_cut = sum(1 for r in cut if r['win'] == 0)

    print('=== TOTAL ===')
    print(f"base n={len(KEEP)} WR={wr(KEEP):.2f} streak={max_streak(KEEP)}")
    print(f"kept n={len(kept)} WR={wr(kept):.2f} streak={max_streak(kept)}")
    print(f"cut  n={len(cut)} WR={wr(cut):.2f}")
    print(f"winners_kept_pct={100.0*win_kept/total_win:.2f}")
    print(f"losers_cut_pct={100.0*loss_cut/loss_total:.2f}")
    print()

    # cut composition (overlap-aware)
    only = {'p1': 0, 'p2': 0, 'p3': 0}
    for r in KEEP:
        c, (p1, p2, p3) = is_cut(r)
        if p1:
            only['p1'] += 1
        if p2:
            only['p2'] += 1
        if p3:
            only['p3'] += 1
    print('=== POCKET FIRE COUNTS (overlapping) ===', only)
    print()

    print('=== BY YEAR (vs base-of-year within r2_keep) ===')
    year_fail = []
    for y in sorted(set(r['yr'] for r in KEEP)):
        sub = [r for r in KEEP if r['yr'] == y]
        subk = [r for r in sub if not is_cut(r)[0]]
        b, a = wr(sub), wr(subk)
        worse = a < b - 1e-9
        if worse:
            year_fail.append(y)
        print(f"{y}: base={b:.2f} after={a:.2f} delta={a-b:+.2f} "
              f"n_base={len(sub)} n_kept={len(subk)} {'WORSE' if worse else 'ok'}")
    print()

    print('=== BY BLOCK (vs base-of-block within r2_keep) ===')
    block_worse = 0
    for blk in sorted(set(r['block'] for r in KEEP)):
        sub = [r for r in KEEP if r['block'] == blk]
        subk = [r for r in sub if not is_cut(r)[0]]
        b, a = wr(sub), wr(subk)
        worse = a < b - 1e-9
        if worse:
            block_worse += 1
        print(f"{blk}: base={b:.2f} after={a:.2f} delta={a-b:+.2f} "
              f"n_base={len(sub)} n_cut={len(sub)-len(subk)} {'WORSE' if worse else 'ok'}")
    print(f"blocks worse: {block_worse}/8")
    print()

    # Neighborhood / cherry-pick probe: each pocket standalone on KEEP
    print('=== POCKET STANDALONE (cherry-pick probe) ===')
    for name, fn in [
        ('absorption==1 (all)', lambda r: r['absorption'] == 1),
        ('sell_decel==0 (all)', lambda r: r['sell_decel'] == 0),
        ('low_vol_rel>1.37 (all)', lambda r: r['low_vol_rel'] > 1.37),
        ('sell_skew_mig>0 (all)', lambda r: r['sell_skew_mig'] > 0),
        ('buy_L_recent==1 (all)', lambda r: r['buy_L_recent'] == 1),
        ('p1 absorp&decel0', lambda r: r['absorption'] == 1 and r['sell_decel'] == 0),
        ('p2 vol&decel0', lambda r: r['low_vol_rel'] > 1.37 and r['sell_decel'] == 0),
        ('p3 buyL&skew', lambda r: r['buy_L_recent'] == 1 and r['sell_skew_mig'] > 0),
    ]:
        grp = [r for r in KEEP if fn(r)]
        print(f"{name}: n={len(grp)} WR={wr(grp):.2f}")
    print()

    # neighborhood robustness on threshold low_vol_rel
    print('=== p2 THRESHOLD NEIGHBORHOOD (low_vol_rel) ===')
    for thr in [1.25, 1.3, 1.37, 1.45, 1.5]:
        grp = [r for r in KEEP if r['low_vol_rel'] > thr and r['sell_decel'] == 0]
        print(f"thr>{thr}: n={len(grp)} WR={wr(grp):.2f}")
    print()

    print('=== VERDICT INPUTS ===')
    print('year_fail:', year_fail)
    print('block_worse:', block_worse)
    print(f"winners_kept_pct={100.0*win_kept/total_win:.2f}")
    print(f"wr_keep={wr(kept):.2f} streak_keep={max_streak(kept)}")


if __name__ == '__main__':
    main()
