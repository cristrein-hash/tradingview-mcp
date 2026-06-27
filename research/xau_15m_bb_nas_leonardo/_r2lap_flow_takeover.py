#!/usr/bin/env python3
"""
_r2lap_flow_takeover.py
Lapidate R2 over R2-KEPT subset (r2_keep==1) on dataset_r2refine.jsonl.

Goal: find ONE orthogonal filter/combo (cut-when or keep-when) that RAISES WR
above base (68.54%) AND lowers max-losing-streak, keeping >=85% of winners,
STABLE (>= per-year base each of 2024/2025/2026 AND >=6/8 blocks not-worse).

Lens: FLOW TAKEOVER. Recent confirmed SELL->BUY cross.
Features (orthogonal, causal): bars_since_buycross, buy_sell_ratio4, buy_L_recent,
plus context: sell_decel, flow_accel, bars_since_sell, sell_skew_mig, absorption,
low_closepos, regime_age_h, is_london_open, is_ny_overlap, is_deadzone.

NEVER use h1_eff/h4_pos (define R2) or R/win as a feature.
RAW-causal: features are read as-of-bar; entry at close. Stable = robust gate.
"""
import json, itertools
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = sorted([r for r in ROWS if r['r2_keep'] == 1], key=lambda r: r['low_t'])

N = len(KEPT)
WINS = sum(r['win'] for r in KEPT)
WR_BASE = 100 * WINS / N
BLOCKS = sorted(set(r['block'] for r in KEPT))

def max_losing_streak(rows):
    """rows must be time-ordered by low_t."""
    s = m = 0
    for r in rows:
        if r['win'] == 0:
            s += 1; m = max(m, s)
        else:
            s = 0
    return m

# per-year base WR (within R2-KEPT)
YEAR_BASE = {}
for yr in (2024, 2025, 2026):
    g = [r for r in KEPT if r['yr'] == yr]
    YEAR_BASE[yr] = 100 * sum(x['win'] for x in g) / len(g) if g else 0.0

# per-block base WR
BLOCK_BASE = {}
for b in BLOCKS:
    g = [r for r in KEPT if r['block'] == b]
    BLOCK_BASE[b] = 100 * sum(x['win'] for x in g) / len(g) if g else 0.0

STREAK_BASE = max_losing_streak(KEPT)

def evaluate(keep_fn, desc):
    """keep_fn(r)->True means trade is KEPT after filter."""
    kept = [r for r in KEPT if keep_fn(r)]
    if not kept:
        return None
    n_keep = len(kept)
    wins_keep = sum(r['win'] for r in kept)
    wr_keep = 100 * wins_keep / n_keep
    streak_keep = max_losing_streak(kept)  # already time-ordered (KEPT is sorted)
    winners_kept = wins_keep
    winners_kept_pct = 100 * winners_kept / WINS
    losers_total = N - WINS
    losers_kept = n_keep - wins_keep
    losers_cut_pct = 100 * (losers_total - losers_kept) / losers_total if losers_total else 0.0

    yr_wr = {}
    yr_ok = True
    for yr in (2024, 2025, 2026):
        g = [r for r in kept if r['yr'] == yr]
        if g:
            w = 100 * sum(x['win'] for x in g) / len(g)
            yr_wr[yr] = w
            if w < YEAR_BASE[yr] - 1e-9:
                yr_ok = False
        else:
            yr_wr[yr] = None
            yr_ok = False  # losing a whole year's coverage = fail stability

    # blocks not-worse
    nb_ok = 0
    nb_total = 0
    for b in BLOCKS:
        g = [r for r in kept if r['block'] == b]
        nb_total += 1
        if g:
            w = 100 * sum(x['win'] for x in g) / len(g)
            if w >= BLOCK_BASE[b] - 1e-9:
                nb_ok += 1
        # empty block = worse (lost coverage)
    blocks_not_worse = nb_ok

    robust = (wr_keep > WR_BASE + 1e-9
              and yr_ok
              and winners_kept_pct >= 85.0
              and blocks_not_worse >= 6
              and streak_keep < STREAK_BASE)

    return dict(desc=desc, n_keep=n_keep, wr_keep=round(wr_keep, 2),
                streak_keep=streak_keep,
                winners_kept_pct=round(winners_kept_pct, 2),
                losers_cut_pct=round(losers_cut_pct, 2),
                y24=round(yr_wr[2024], 2) if yr_wr[2024] is not None else None,
                y25=round(yr_wr[2025], 2) if yr_wr[2025] is not None else None,
                y26=round(yr_wr[2026], 2) if yr_wr[2026] is not None else None,
                blocks_not_worse=blocks_not_worse,
                robust=robust)

print(f"BASE: n={N} WR={WR_BASE:.2f} streak={STREAK_BASE} "
      f"y24={YEAR_BASE[2024]:.2f} y25={YEAR_BASE[2025]:.2f} y26={YEAR_BASE[2026]:.2f}")
print(f"BLOCK_BASE: " + " ".join(f"{b}={BLOCK_BASE[b]:.1f}" for b in BLOCKS))
print()

# ---- distributions of key flow features (sanity) ----
def dist(name):
    vals = [r[name] for r in KEPT]
    nums = [v for v in vals if isinstance(v, (int, float))]
    if nums:
        s = sorted(nums)
        q = lambda p: s[int(p*(len(s)-1))]
        print(f"  {name}: min={s[0]} p25={q(.25)} med={q(.5)} p75={q(.75)} max={s[-1]}")
for f in ['bars_since_buycross','buy_sell_ratio4','buy_L_recent','sell_decel',
          'flow_accel','bars_since_sell','sell_skew_mig','absorption',
          'low_closepos','regime_age_h']:
    dist(f)
print()

results = []

# ---------- SINGLE-FEATURE PROBES (flow takeover lens) ----------
# bars_since_buycross: recent SELL->BUY cross. Test "recent" windows.
for thr in (2, 3, 4, 6, 8, 10, 12, 16, 20):
    results.append(evaluate(lambda r, t=thr: r['bars_since_buycross'] <= t,
                            f"buycross<= {thr} (recent takeover)"))
# late-too-far cut already in above; also test a band (not too early, not too late)
for lo, hi in [(1,6),(1,8),(2,10),(2,12),(3,12)]:
    results.append(evaluate(lambda r, a=lo, b=hi: a <= r['bars_since_buycross'] <= b,
                            f"buycross in [{lo},{hi}]"))

# buy_sell_ratio4
for thr in (1.5, 2.0, 2.5, 3.0, 4.0):
    results.append(evaluate(lambda r, t=thr: r['buy_sell_ratio4'] >= t,
                            f"buy_sell_ratio4>= {thr}"))

# buy_L_recent
results.append(evaluate(lambda r: r['buy_L_recent'] == 1, "buy_L_recent==1"))

# context single
results.append(evaluate(lambda r: r['absorption'] == 1, "absorption==1"))
results.append(evaluate(lambda r: r['is_deadzone'] == 0, "not deadzone"))
results.append(evaluate(lambda r: r['is_london_open'] == 1, "london_open"))
results.append(evaluate(lambda r: r['is_ny_overlap'] == 1, "ny_overlap"))
results.append(evaluate(lambda r: r['sell_skew_mig'] > 0, "sell_skew_mig>0 (exhaustion)"))
results.append(evaluate(lambda r: r['sell_decel'] > 0, "sell_decel>0 (selling decel)"))
results.append(evaluate(lambda r: r['low_closepos'] >= 0.5, "low_closepos>=0.5"))

# ---------- COMBOS 2-feature (flow takeover) ----------
# recent cross + strong buy ratio
for bc in (4, 6, 8, 10, 12):
    for br in (1.5, 2.0, 2.5, 3.0):
        results.append(evaluate(
            lambda r, b=bc, q=br: r['bars_since_buycross'] <= b and r['buy_sell_ratio4'] >= q,
            f"buycross<= {bc} AND ratio4>= {br}"))

# recent cross + buy_L_recent
for bc in (4, 6, 8, 10, 12):
    results.append(evaluate(
        lambda r, b=bc: r['bars_since_buycross'] <= b and r['buy_L_recent'] == 1,
        f"buycross<= {bc} AND buy_L_recent"))

# recent cross + sell exhaustion
for bc in (6, 8, 10, 12):
    results.append(evaluate(
        lambda r, b=bc: r['bars_since_buycross'] <= b and r['sell_decel'] > 0,
        f"buycross<= {bc} AND sell_decel>0"))
    results.append(evaluate(
        lambda r, b=bc: r['bars_since_buycross'] <= b and r['sell_skew_mig'] > 0,
        f"buycross<= {bc} AND sell_skew>0"))

# ratio + buy_L_recent
for br in (1.5, 2.0, 2.5):
    results.append(evaluate(
        lambda r, q=br: r['buy_sell_ratio4'] >= q and r['buy_L_recent'] == 1,
        f"ratio4>= {br} AND buy_L_recent"))

# takeover + clean low (closepos)
for bc in (6, 8, 10, 12):
    results.append(evaluate(
        lambda r, b=bc: r['bars_since_buycross'] <= b and r['low_closepos'] >= 0.4,
        f"buycross<= {bc} AND closepos>=0.4"))

# takeover + session
for bc in (6, 8, 10, 12):
    results.append(evaluate(
        lambda r, b=bc: r['bars_since_buycross'] <= b and r['is_deadzone'] == 0,
        f"buycross<= {bc} AND not deadzone"))

# CUT-WHEN late cross + weak ratio (loser signature: too late / before cross weak)
for bc in (12, 16, 20, 24):
    results.append(evaluate(
        lambda r, b=bc: not (r['bars_since_buycross'] > b and r['buy_sell_ratio4'] < 2.0),
        f"CUT (buycross>{bc} AND ratio4<2.0)"))

# ---------- COMBOS 3-feature ----------
for bc in (8, 10, 12):
    for br in (1.5, 2.0):
        results.append(evaluate(
            lambda r, b=bc, q=br: r['bars_since_buycross'] <= b and r['buy_sell_ratio4'] >= q and r['low_closepos'] >= 0.4,
            f"buycross<= {bc} AND ratio4>= {br} AND closepos>=0.4"))
        results.append(evaluate(
            lambda r, b=bc, q=br: r['bars_since_buycross'] <= b and r['buy_sell_ratio4'] >= q and r['is_deadzone'] == 0,
            f"buycross<= {bc} AND ratio4>= {br} AND not deadzone"))
        results.append(evaluate(
            lambda r, b=bc, q=br: r['bars_since_buycross'] <= b and r['buy_sell_ratio4'] >= q and r['sell_decel'] > 0,
            f"buycross<= {bc} AND ratio4>= {br} AND sell_decel>0"))

results = [r for r in results if r]

# ---- rank: robust first, then by (winners_kept_pct gate) wr_keep ----
def sortkey(r):
    return (r['robust'], r['wr_keep'], r['winners_kept_pct'])
results.sort(key=sortkey, reverse=True)

print("=== TOP RESULTS (robust first, then WR) ===")
hdr = f"{'desc':<48}{'n':>5}{'WR':>7}{'strk':>5}{'wkept%':>8}{'lcut%':>7}{'y24':>7}{'y25':>7}{'y26':>7}{'blk':>4}{'rob':>5}"
print(hdr)
for r in results[:30]:
    print(f"{r['desc']:<48}{r['n_keep']:>5}{r['wr_keep']:>7}{r['streak_keep']:>5}"
          f"{r['winners_kept_pct']:>8}{r['losers_cut_pct']:>7}"
          f"{str(r['y24']):>7}{str(r['y25']):>7}{str(r['y26']):>7}"
          f"{r['blocks_not_worse']:>4}{str(r['robust']):>5}")

print()
robust = [r for r in results if r['robust']]
print(f"ROBUST count: {len(robust)}")
for r in robust:
    print(json.dumps(r))
