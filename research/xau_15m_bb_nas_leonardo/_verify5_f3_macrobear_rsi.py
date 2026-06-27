#!/usr/bin/env python3
"""
DEVIL'S ADVOCATE verification of F3 5ATR filter.
RULE: macro_bear <= 0 AND rsi >= 50.7
Dataset: dataset_5atr.jsonl  (base WR = 60.49%, 3047 rows, 8 blocks)

Regua (recalibrated DA):
- DO NOT veto for tail-trim / WR-only / no-OOS.
- VETO only for: look-ahead, non-stationarity (WR worse in any YEAR vs that year's base,
  OR worse in >2/8 blocks vs that block's base), cutting winners <85%, cherry-pick
  (neighborhood +/-20% collapses).
"""
import json
from math import sqrt

ROWS = [json.loads(l) for l in open('dataset_5atr.jsonl')]


def predicate(r, mb_thr=0.0, rsi_thr=50.7):
    return (r['macro_bear'] <= mb_thr) and (r['rsi'] >= rsi_thr)


def wr(rows):
    if not rows:
        return None, 0, 0
    w = sum(r['win'] for r in rows)
    return 100.0 * w / len(rows), w, len(rows)


def max_losing_streak(rows):
    """rows must be in chronological order; loss = win==0."""
    cur = mx = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


def wilson_lb(w, n, z=1.96):
    if n == 0:
        return 0.0
    p = w / n
    denom = 1 + z*z/n
    centre = p + z*z/(2*n)
    margin = z*sqrt((p*(1-p) + z*z/(4*n))/n)
    return 100.0*(centre - margin)/denom


def report(mb_thr=0.0, rsi_thr=50.7, label="F3"):
    # chronological order: sort by low_t for honest streak
    rows = sorted(ROWS, key=lambda r: r['low_t'])
    kept = [r for r in rows if predicate(r, mb_thr, rsi_thr)]
    cut = [r for r in rows if not predicate(r, mb_thr, rsi_thr)]

    base_wr, base_w, base_n = wr(rows)
    k_wr, k_w, k_n = wr(kept)
    c_wr, c_w, c_n = wr(cut)

    total_winners = sum(r['win'] for r in rows)
    kept_winners = sum(r['win'] for r in kept)
    winners_kept_pct = 100.0 * kept_winners / total_winners if total_winners else 0

    base_streak = max_losing_streak(rows)
    keep_streak = max_losing_streak(kept)

    print(f"=== {label}: macro_bear<={mb_thr} AND rsi>={rsi_thr} ===")
    print(f"BASE   n={base_n} WR={base_wr:.2f}  winners={total_winners}  maxLossStreak={base_streak}")
    print(f"KEEP   n={k_n} WR={k_wr:.2f} (Wilson95 LB={wilson_lb(k_w,k_n):.2f})  maxLossStreak={keep_streak}")
    print(f"CUT    n={c_n} WR={c_wr:.2f}")
    print(f"delta WR keep-base = {k_wr-base_wr:+.2f}pp")
    print(f"winners_kept = {kept_winners}/{total_winners} = {winners_kept_pct:.1f}%")
    print(f"losers_cut = {(c_n-c_w)}/{base_n-total_winners} = {100.0*(c_n-c_w)/(base_n-total_winners):.1f}%")

    # sumR
    sumR_base = sum(r['R'] for r in rows)
    sumR_keep = sum(r['R'] for r in kept)
    print(f"sumR base={sumR_base:.1f}  keep={sumR_keep:.1f}")

    # ---- STATIONARITY: by YEAR (year-base vs year-keep) ----
    print("\n-- by YEAR (keep WR vs that year's base WR) --")
    year_fail = []
    for yr in sorted(set(r['yr'] for r in rows)):
        yrows = [r for r in rows if r['yr'] == yr]
        ykept = [r for r in yrows if predicate(r, mb_thr, rsi_thr)]
        ybw, _, ybn = wr(yrows)
        ykw, _, ykn = wr(ykept)
        worse = (ykw is not None) and (ykw < ybw)
        if worse:
            year_fail.append(yr)
        print(f"  {yr}: base WR={ybw:.2f} (n={ybn})  keep WR={ykw:.2f} (n={ykn})  delta={ykw-ybw:+.2f}  {'WORSE!' if worse else 'ok'}")

    # ---- STATIONARITY: by BLOCK ----
    print("\n-- by BLOCK (keep WR vs that block's base WR) --")
    block_fail = []
    for b in sorted(set(r['block'] for r in rows)):
        brows = [r for r in rows if r['block'] == b]
        bkept = [r for r in brows if predicate(r, mb_thr, rsi_thr)]
        bbw, _, bbn = wr(brows)
        bkw, _, bkn = wr(bkept)
        worse = (bkw is not None) and (bkw < bbw)
        if worse:
            block_fail.append(b)
        print(f"  {b}: base={bbw:.2f}(n={bbn})  keep={bkw:.2f}(n={bkn})  delta={bkw-bbw:+.2f}  {'WORSE!' if worse else 'ok'}")

    print(f"\nYEARS worse: {year_fail}")
    print(f"BLOCKS worse: {len(block_fail)}/8 -> {block_fail}")
    return {
        'wr_keep': round(k_wr, 2),
        'streak_keep': keep_streak,
        'base_streak': base_streak,
        'winners_kept_pct': round(winners_kept_pct, 1),
        'n_keep': k_n,
        'year_fail': year_fail,
        'block_fail': block_fail,
    }


def cherry_pick_neighborhood():
    """+/-20% on both thresholds -> does the edge collapse?"""
    print("\n========== CHERRY-PICK / NEIGHBORHOOD (+/-20%) ==========")
    base_wr, _, _ = wr(ROWS)
    for mb in [0.0]:  # macro_bear<=0 is structural (0/negative); +/-20% meaningless on 0 -> test -0.2,0,0.2
        for mb_t in [-0.2, 0.0, 0.2]:
            for rsi_t in [50.7*0.8, 50.7*0.9, 50.7, 50.7*1.1, 50.7*1.2]:
                kept = [r for r in ROWS if predicate(r, mb_t, rsi_t)]
                k_wr, _, k_n = wr(kept)
                if k_wr is None:
                    print(f"  mb<={mb_t:+.2f} rsi>={rsi_t:.1f}: n=0 (empty)")
                    continue
                print(f"  mb<={mb_t:+.2f} rsi>={rsi_t:.1f}: n={k_n} WR={k_wr:.2f} delta={k_wr-base_wr:+.2f}")


if __name__ == '__main__':
    res = report(0.0, 50.7, "F3")
    cherry_pick_neighborhood()
    print("\nSUMMARY:", json.dumps(res))
