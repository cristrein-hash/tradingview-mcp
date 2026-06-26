#!/usr/bin/env python3
"""
_disc8_combo_search.py — contextual 2-3 feature COMBO search, RANGE vs TREND lens.

Reuses metric machinery. win=R>0 (PROHIBITED to use R/win as feature).
Ordered by low_t for max-losing-streak. Reports n_keep, wr_keep, streak_keep,
winners_kept_pct, losers_cut_pct, per-year WR, robust flag, and per-block stability.

Findings from _disc8_range_vs_trend.py (univariate):
  - hd_eff>=0.1 -> WR .697 (strongest single)
  - bars_to_8atr<=25 (FAST) -> WR ~.60 LOSER ; slow grind better
  - path_eff HIGH -> LOSER (.586) ; counter to naive impulse hypothesis
  - h4_eff mid good
INVERTED HYPOTHESIS: slow grind (low path_eff, high bars_to_8atr) WITH daily-trend
backing = WINNER ; fast impulsive spike (high path_eff, low bars) = mean-revert LOSER.

This script enumerates structured combos and reports robust ones. RAW-causal.
"""
import json, itertools

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
YEARS = [2024, 2025, 2026]
SORTED = sorted(ROWS, key=lambda r: r['low_t'])
TOTAL_WINNERS = sum(r['win'] for r in ROWS)
TOTAL_LOSERS = N - TOTAL_WINNERS


def max_losing_streak(rows):
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx


BASE_STREAK = max_losing_streak(SORTED)


def wr(rows):
    return sum(r['win'] for r in rows) / len(rows) if rows else 0.0


def g(r, k, d):
    v = r.get(k)
    return d if v is None else v


def block_stab(kept):
    blocks = {}
    for r in kept:
        blocks.setdefault(r['block'], []).append(r)
    bw = {b: (round(wr(v), 3), len(v)) for b, v in blocks.items()}
    valid = [(w, n) for w, n in bw.values() if n >= 12]
    minw = min((w for w, n in valid), default=None)
    n_above = sum(1 for w, n in valid if w >= BASE_WR)
    return bw, minw, n_above, len(valid)


def evaluate(pred, desc):
    kept = [r for r in SORTED if pred(r)]
    if len(kept) < 150:
        return None
    n_keep = len(kept)
    wr_keep = wr(kept)
    streak_keep = max_losing_streak(kept)
    winners_kept = sum(r['win'] for r in kept)
    losers_kept = n_keep - winners_kept
    winners_kept_pct = winners_kept / TOTAL_WINNERS
    losers_cut_pct = (TOTAL_LOSERS - losers_kept) / TOTAL_LOSERS
    yvals = {}
    for yy in YEARS:
        sub = [r for r in kept if r['yr'] == yy]
        yvals[yy] = (wr(sub), len(sub))
    bw, minblock, n_above, n_valid = block_stab(kept)
    robust = (wr_keep > BASE_WR
              and all(yvals[yy][0] >= BASE_WR and yvals[yy][1] >= 30 for yy in YEARS)
              and winners_kept_pct >= 0.50
              and streak_keep < BASE_STREAK
              and (minblock is not None and minblock >= BASE_WR - 0.03)
              and n_above >= n_valid - 1)
    return dict(desc=desc, n_keep=n_keep, wr_keep=round(wr_keep, 4),
                streak_keep=streak_keep,
                winners_kept_pct=round(winners_kept_pct, 4),
                losers_cut_pct=round(losers_cut_pct, 4),
                y24=round(yvals[2024][0], 4), y25=round(yvals[2025][0], 4),
                y26=round(yvals[2026][0], 4),
                n24=yvals[2024][1], n25=yvals[2025][1], n26=yvals[2026][1],
                minblock=minblock, blocks_above=f"{n_above}/{n_valid}",
                robust=robust)


# ---------- atomic predicates (RANGE vs TREND ingredients) ----------
P = {
    'hd_up':        lambda r: g(r, 'hd_trend', 0) == 1,
    'hd_eff_hi':    lambda r: g(r, 'hd_eff', 0) >= 0.1,
    'hd_eff_hi2':   lambda r: g(r, 'hd_eff', 0) >= 0.2,
    'h4_eff_mid':   lambda r: 0.1 <= g(r, 'h4_eff', 0) <= 0.45,
    'h4_eff_hi':    lambda r: g(r, 'h4_eff', 0) >= 0.2,
    'h1_eff_hi':    lambda r: g(r, 'h1_eff', 0) >= 0.2,
    'slow_grind':   lambda r: g(r, 'bars_to_8atr', 0) >= 25,
    'not_fast':     lambda r: g(r, 'bars_to_8atr', 0) >= 20,
    'low_patheff':  lambda r: g(r, 'path_eff', 1) <= 0.4,
    'low_patheff3': lambda r: g(r, 'path_eff', 1) <= 0.3,
    'atr_hi':       lambda r: g(r, 'atr_regime', 1) >= 1.2,
    'h4_up':        lambda r: g(r, 'h4_trend', 0) == 1,
    'h1_up':        lambda r: g(r, 'h1_trend', 0) == 1,
    'macro_bull':   lambda r: r.get('macro_bull', 0) == 1,
    'not_climax':   lambda r: g(r, 'vol_climax', 0) < 1.5,
    'rsi_not_hot':  lambda r: g(r, 'rsi', 50) <= 70,
}


def AND(*ks):
    fns = [P[k] for k in ks]
    return lambda r: all(f(r) for f in fns)


# ---------- enumerate 2-combos and 3-combos ----------
keys = list(P.keys())
results = []
for combo in itertools.combinations(keys, 2):
    res = evaluate(AND(*combo), ' & '.join(combo))
    if res:
        results.append(res)
for combo in itertools.combinations(keys, 3):
    res = evaluate(AND(*combo), ' & '.join(combo))
    if res:
        results.append(res)

# rank: robust first, then WR, then losers_cut
results.sort(key=lambda d: (d['robust'], d['wr_keep'], d['losers_cut_pct']), reverse=True)

print(f"BASE WR={BASE_WR:.4f} streak={BASE_STREAK} winners={TOTAL_WINNERS} losers={TOTAL_LOSERS}")
print(f"{'robust':6} {'wr':6} {'strk':4} {'nkeep':5} {'wkpt':5} {'lcut':5} "
      f"{'y24':5} {'y25':5} {'y26':5} {'minblk':6} {'blks':5}  desc")
for d in results[:40]:
    print(f"{str(d['robust']):6} {d['wr_keep']:.3f} {d['streak_keep']:4d} {d['n_keep']:5d} "
          f"{d['winners_kept_pct']:.2f}  {d['losers_cut_pct']:.2f}  "
          f"{d['y24']:.3f} {d['y25']:.3f} {d['y26']:.3f} "
          f"{str(d['minblock']):6} {d['blocks_above']:5}  {d['desc']}")

print(f"\nTOTAL combos passing min-n: {len(results)}  robust: {sum(d['robust'] for d in results)}")
