#!/usr/bin/env python3
"""
_disc8_range_vs_trend.py — RANGE vs TREND structural lens on 8ATR confirmation entries.

Target: dataset_8atr.jsonl, n=2615, base WR=66%, base max-losing-streak=28.
win = R>0. PROHIBITED: using R/win as a feature.
Goal: find CAUSAL contextual COMBO (2-3 features) that raises WR above 66% AND
lowers max-losing-streak, STABLE across 2024/2025/2026 and 8 blocks, cutting losers
while keeping >=85% of winners.

LENS: RANGE vs TREND.
  - eff (h1/h4/hd): efficiency 0=range .. 1=trend
  - atr_regime, atr_expand
  - path_eff: impulse vs grind of the leg into the 8ATR
  - bars_to_8atr: how fast the 8ATR move developed
Hypothesis: 8ATR formed in RANGE (mean-reverting chop) = loser;
            8ATR formed in real TREND (impulse, high path_eff, high HTF eff) = winner.

All features are as-of the confirmation bar (HTF only closed bars). RAW-causal.
"""
import json, itertools

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
YEARS = [2024, 2025, 2026]


def max_losing_streak(rows):
    """rows must already be sorted by low_t. Returns longest run of win==0."""
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


SORTED = sorted(ROWS, key=lambda r: r['low_t'])
BASE_STREAK = max_losing_streak(SORTED)


def wr(rows):
    return sum(r['win'] for r in rows) / len(rows) if rows else 0.0


def yr_wr(rows, y):
    sub = [r for r in rows if r['yr'] == y]
    return (wr(sub), len(sub))


TOTAL_WINNERS = sum(r['win'] for r in ROWS)
TOTAL_LOSERS = N - TOTAL_WINNERS


def evaluate(pred, desc):
    """pred(r)->bool means KEEP the trade (passes filter). Returns metrics dict."""
    kept_sorted = [r for r in SORTED if pred(r)]
    if not kept_sorted:
        return None
    n_keep = len(kept_sorted)
    wr_keep = wr(kept_sorted)
    streak_keep = max_losing_streak(kept_sorted)
    winners_kept = sum(r['win'] for r in kept_sorted)
    losers_kept = n_keep - winners_kept
    winners_kept_pct = winners_kept / TOTAL_WINNERS
    losers_cut_pct = (TOTAL_LOSERS - losers_kept) / TOTAL_LOSERS
    y = {yy: yr_wr(kept_sorted, yy) for yy in YEARS}
    # robust: WR up overall AND >= base in ALL 3 years AND each year has reasonable n
    robust = (wr_keep > BASE_WR and
              all(y[yy][0] >= BASE_WR and y[yy][1] >= 30 for yy in YEARS) and
              winners_kept_pct >= 0.50)
    return dict(desc=desc, n_keep=n_keep, wr_keep=round(wr_keep, 4),
                streak_keep=streak_keep,
                winners_kept_pct=round(winners_kept_pct, 4),
                losers_cut_pct=round(losers_cut_pct, 4),
                y24=round(y[2024][0], 4), n24=y[2024][1],
                y25=round(y[2025][0], 4), n25=y[2025][1],
                y26=round(y[2026][0], 4), n26=y[2026][1],
                robust=robust)


def block_stability(pred):
    """WR per block for kept trades; returns min block WR and count of blocks >= base."""
    blocks = {}
    for r in ROWS:
        if pred(r):
            blocks.setdefault(r['block'], []).append(r)
    bw = {b: (wr(v), len(v)) for b, v in blocks.items()}
    valid = [w for w, n in bw.values() if n >= 15]
    return bw, (min(valid) if valid else None), sum(1 for w, n in bw.values() if n >= 15 and w >= BASE_WR)


# ---- helpers for null-safe access ----
def g(r, k, default):
    v = r.get(k)
    return default if v is None else v


print(f"BASE: N={N} WR={BASE_WR:.4f} max_losing_streak={BASE_STREAK} "
      f"winners={TOTAL_WINNERS} losers={TOTAL_LOSERS}")
print()

# ============================================================
# STEP 1 — single-feature directional probe (sanity / to confirm univariate is weak)
# Build the RANGE vs TREND ingredients, see marginal WR by threshold.
# ============================================================
def quantile_probe(key, default_for_null, grid):
    print(f"-- {key} marginal WR (keep >= thr) --")
    for thr in grid:
        sub = [r for r in ROWS if g(r, key, default_for_null) >= thr]
        if len(sub) >= 100:
            print(f"   >= {thr:6}: n={len(sub):4d} WR={wr(sub):.3f}")
    print(f"-- {key} marginal WR (keep <= thr) --")
    for thr in grid:
        sub = [r for r in ROWS if g(r, key, default_for_null) <= thr]
        if len(sub) >= 100:
            print(f"   <= {thr:6}: n={len(sub):4d} WR={wr(sub):.3f}")


for key, dflt, grid in [
    ('path_eff', 0.0, [0.3, 0.4, 0.5, 0.6, 0.7]),
    ('h1_eff', 0.0, [0.1, 0.2, 0.3, 0.4, 0.5]),
    ('h4_eff', 0.0, [0.1, 0.2, 0.3, 0.4, 0.5]),
    ('hd_eff', 0.0, [0.1, 0.2, 0.3, 0.4, 0.5]),
    ('atr_regime', 1.0, [0.8, 1.0, 1.2, 1.4]),
    ('bars_to_8atr', 999, [15, 20, 25, 30, 40]),
]:
    quantile_probe(key, dflt, grid)
    print()
