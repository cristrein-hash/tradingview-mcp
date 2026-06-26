#!/usr/bin/env python3
"""
R2 lapidation — LENS: regime-age / session.
Operate ONLY on r2_keep==1 (n=2355, WR base 68.54%, max-losing-streak base 24).
win = R>0. Find ONE orthogonal filter/combo (cut-when or keep-when) that:
  - raises WR > 68.54
  - lowers max-losing-streak
  - keeps >= 85% of winners
  - STABLE: >= per-year base in EACH of 2024/2025/2026 AND >= 6/8 blocks not-worse

ORTHOGONAL features ONLY (causal; NOT h1_eff/h4_pos which define R2; NOT R/win):
  low_vol_rel, low_closepos, bars_since_lowest, absorption, sell_decel, flow_accel,
  bars_since_sell, bars_since_buycross, buy_sell_ratio4, max_silence, smc_lag_bars,
  buy_after_smc, naslong_after_smc, sell_skew_mig, buy_L_recent, regime_age_h,
  is_london_open, is_ny_overlap, is_deadzone.

Hypothesis (my lens): fresh post-turn 8ATR / London-open / NY-overlap = winner;
old regime / deadzone = loser.
"""
import json
from itertools import combinations

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]
KEPT.sort(key=lambda r: r['low_t'])  # chronological for streak

N0 = len(KEPT)
W0 = sum(r['win'] for r in KEPT)
WR0 = 100 * W0 / N0
YEARS = sorted(set(r['yr'] for r in KEPT))
BLOCKS = sorted(set(r['block'] for r in KEPT))

# per-year base WR
YR_BASE = {}
for y in YEARS:
    sub = [r for r in KEPT if r['yr'] == y]
    YR_BASE[y] = 100 * sum(s['win'] for s in sub) / len(sub)
# per-block base WR
BL_BASE = {}
for b in BLOCKS:
    sub = [r for r in KEPT if r['block'] == b]
    BL_BASE[b] = 100 * sum(s['win'] for s in sub) / len(sub)


def max_streak(rows):
    cur = mx = 0
    for r in rows:  # rows already chronological
        if r['win'] == 0:
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx


STREAK0 = max_streak(KEPT)


def evaluate(name, pred):
    """pred(row)->True means KEEP the row."""
    kept = [r for r in KEPT if pred(r)]
    if not kept:
        return None
    nk = len(kept)
    wk = sum(r['win'] for r in kept)
    wr = 100 * wk / nk
    streak = max_streak(kept)
    winners_kept = 100 * wk / W0
    losers_total = N0 - W0
    losers_cut = losers_total - (nk - wk)
    losers_cut_pct = 100 * losers_cut / losers_total
    # per year
    yr_after = {}
    yr_ok = True
    for y in YEARS:
        sub = [r for r in kept if r['yr'] == y]
        if not sub:
            yr_after[y] = None; yr_ok = False; continue
        a = 100 * sum(s['win'] for s in sub) / len(sub)
        yr_after[y] = a
        if a < YR_BASE[y] - 1e-9:
            yr_ok = False
    # per block not-worse
    blocks_notworse = 0
    for b in BLOCKS:
        sub = [r for r in kept if r['block'] == b]
        if not sub:
            continue
        a = 100 * sum(s['win'] for s in sub) / len(sub)
        if a >= BL_BASE[b] - 1e-9:
            blocks_notworse += 1
    robust = (wr > WR0 and yr_ok and winners_kept >= 85.0
              and blocks_notworse >= 6 and streak < STREAK0)
    return dict(name=name, n_keep=nk, wr_keep=round(wr, 2), streak_keep=streak,
                winners_kept_pct=round(winners_kept, 2),
                losers_cut_pct=round(losers_cut_pct, 2),
                y24=round(yr_after.get(2024, 0), 2), y25=round(yr_after.get(2025, 0), 2),
                y26=round(yr_after.get(2026, 0), 2),
                blocks_notworse=blocks_notworse, robust=robust)


def show(res):
    if res is None:
        return
    print(f"{res['name']:<48} n={res['n_keep']:<5} WR={res['wr_keep']:<6} "
          f"strk={res['streak_keep']:<3} winK%={res['winners_kept_pct']:<6} "
          f"losC%={res['losers_cut_pct']:<6} "
          f"y24={res['y24']:<6}({YR_BASE[2024]:.1f}) y25={res['y25']:<6}({YR_BASE[2025]:.1f}) "
          f"y26={res['y26']:<6}({YR_BASE[2026]:.1f}) blk={res['blocks_notworse']}/8 "
          f"{'ROBUST' if res['robust'] else ''}")


print("=== BASELINE (r2_keep==1) ===")
print(f"n={N0} WR={WR0:.2f} streak={STREAK0}")
print("yr base:", {y: round(v, 2) for y, v in YR_BASE.items()})
print("blk base:", {b: round(v, 1) for b, v in BL_BASE.items()})
print()

# ---------- SINGLE-FEATURE SCANS (context, find direction) ----------
print("=== SESSION / REGIME-AGE single ===")
results = []
results.append(evaluate("keep is_london_open==1", lambda r: r['is_london_open'] == 1))
results.append(evaluate("keep is_ny_overlap==1", lambda r: r['is_ny_overlap'] == 1))
results.append(evaluate("keep is_deadzone==0", lambda r: r['is_deadzone'] == 0))
results.append(evaluate("keep london OR ny_overlap", lambda r: r['is_london_open'] == 1 or r['is_ny_overlap'] == 1))
results.append(evaluate("cut deadzone (keep !=deadzone)", lambda r: r['is_deadzone'] == 0))

# regime_age thresholds
for thr in [24, 48, 72, 96, 120, 168, 240]:
    results.append(evaluate(f"keep regime_age_h<={thr}", lambda r, t=thr: r['regime_age_h'] <= t))
for thr in [12, 24, 48, 72, 96]:
    results.append(evaluate(f"keep regime_age_h>={thr}", lambda r, t=thr: r['regime_age_h'] >= t))
for res in results:
    show(res)

# Quartile look at regime_age_h vs win
print()
print("=== regime_age_h distribution vs win ===")
ages = sorted(r['regime_age_h'] for r in KEPT)
import statistics
qs = [ages[int(len(ages)*q)] for q in (0.25, 0.5, 0.75)]
print("quartiles regime_age_h:", [round(q, 1) for q in qs])
bins = [(-1, qs[0]), (qs[0], qs[1]), (qs[1], qs[2]), (qs[2], 1e9)]
for lo, hi in bins:
    sub = [r for r in KEPT if lo < r['regime_age_h'] <= hi]
    if sub:
        print(f"age ({lo:.1f},{hi:.1f}] n={len(sub)} WR={100*sum(s['win'] for s in sub)/len(sub):.2f}")

print()
print("=== other orthogonal singles (context) ===")
ctx = []
ctx.append(evaluate("keep absorption==1", lambda r: r['absorption'] == 1))
ctx.append(evaluate("keep absorption==0", lambda r: r['absorption'] == 0))
ctx.append(evaluate("keep buy_L_recent==1", lambda r: r['buy_L_recent'] == 1))
ctx.append(evaluate("keep buy_after_smc==1", lambda r: r['buy_after_smc'] == 1))
ctx.append(evaluate("keep naslong_after_smc==1", lambda r: r['naslong_after_smc'] == 1))
ctx.append(evaluate("keep low_closepos>=0.5", lambda r: r['low_closepos'] >= 0.5))
ctx.append(evaluate("keep low_closepos>=0.4", lambda r: r['low_closepos'] >= 0.4))
ctx.append(evaluate("keep sell_skew_mig>0", lambda r: r['sell_skew_mig'] > 0))
ctx.append(evaluate("keep sell_decel>0 (real)", lambda r: r['sell_decel'] > 0 and r['sell_decel'] > -1e6))
for thr in [1.0, 1.2, 1.5]:
    ctx.append(evaluate(f"keep low_vol_rel<={thr}", lambda r, t=thr: r['low_vol_rel'] <= t))
    ctx.append(evaluate(f"keep low_vol_rel>={thr}", lambda r, t=thr: r['low_vol_rel'] >= t))
for res in ctx:
    show(res)
