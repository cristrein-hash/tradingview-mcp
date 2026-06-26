#!/usr/bin/env python3
"""
_disc8_combo_hunter.py
Investigative combo hunter for the 8ATR confirmation entry.
Goal: find a CAUSAL contextual combo (2-3 features across families) that RAISES WR
above base (66%) AND lowers max-losing-streak, STABLE across 3 years + 8 blocks,
keeping >=85% winners.

RAW-causal: all features as-of confirmation bar. win = R>0. R/win NEVER used as input.
Order by low_t for streak. Greedy forward selection over single-condition predicates,
then 2-3 way combos. Report n_keep, wr_keep, streak_keep, winners_kept_pct,
losers_cut_pct, WR per year, robustness.
"""
import json
from itertools import combinations

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])
N = len(ROWS)
TOTW = sum(r['win'] for r in ROWS)
TOTL = N - TOTW
BASE_WR = TOTW / N
YEARS = [2024, 2025, 2026]
BASE_WR_YR = {}
for y in YEARS:
    sub = [r for r in ROWS if r['yr'] == y]
    BASE_WR_YR[y] = sum(x['win'] for x in sub) / len(sub)


def max_losing_streak(rows):
    """rows must be time-ordered. consecutive losers (win==0)."""
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


BASE_STREAK = max_losing_streak(ROWS)


def evaluate(mask_fn, rows=ROWS):
    """mask_fn(r)->bool means KEEP the trade. Returns metrics dict or None if too small."""
    kept = [r for r in rows if mask_fn(r)]
    if len(kept) < 30:
        return None
    nk = len(kept)
    wk = sum(r['win'] for r in kept)
    wr = wk / nk
    streak = max_losing_streak(kept)
    winners_kept = wk / TOTW
    losers_cut = (TOTL - (nk - wk)) / TOTL
    # per year
    wr_yr = {}
    for y in YEARS:
        sub = [r for r in kept if r['yr'] == y]
        wr_yr[y] = (sum(x['win'] for x in sub) / len(sub), len(sub)) if sub else (None, 0)
    # per block stability
    blocks = {}
    for r in kept:
        blocks.setdefault(r['block'], [0, 0])
        blocks[r['block']][0] += 1
        blocks[r['block']][1] += r['win']
    blk_wr = {b: (v[1] / v[0], v[0]) for b, v in blocks.items()}
    return dict(nk=nk, wr=wr, streak=streak, winners_kept=winners_kept,
                losers_cut=losers_cut, wr_yr=wr_yr, blk_wr=blk_wr, kept=kept)


def robust(m, min_winners_kept=0.85):
    """robust = WR rises overall AND >= base in ALL 3 years AND winners kept >= threshold
       AND not carried by few (each year n>=40 and WR>=base)."""
    if m is None:
        return False
    if m['wr'] <= BASE_WR:
        return False
    if m['winners_kept'] < min_winners_kept:
        return False
    for y in YEARS:
        wr_y, n_y = m['wr_yr'][y]
        if wr_y is None or n_y < 40:
            return False
        if wr_y < BASE_WR_YR[y]:
            return False
    return True


# ---- Build candidate single-condition predicates (causal reads) ----
# Each predicate: (name, fn). fn returns True=KEEP. Handle nulls -> exclude only if used.
def safe(v):
    return v is not None


PREDS = []


def addp(name, fn):
    PREDS.append((name, fn))


# Multi-TF reads
for tf in ['h1', 'h4', 'hd']:
    addp(f'{tf}_trend_up', lambda r, tf=tf: r[f'{tf}_trend'] == 1)
    addp(f'{tf}_trend_notdown', lambda r, tf=tf: safe(r[f'{tf}_trend']) and r[f'{tf}_trend'] >= 0)
    addp(f'{tf}_pos_lo', lambda r, tf=tf: safe(r[f'{tf}_pos']) and r[f'{tf}_pos'] < 0.4)
    addp(f'{tf}_pos_hi', lambda r, tf=tf: safe(r[f'{tf}_pos']) and r[f'{tf}_pos'] > 0.6)
    addp(f'{tf}_pos_mid', lambda r, tf=tf: safe(r[f'{tf}_pos']) and 0.3 <= r[f'{tf}_pos'] <= 0.7)
    addp(f'{tf}_eff_hi', lambda r, tf=tf: safe(r[f'{tf}_eff']) and r[f'{tf}_eff'] > 0.4)
    addp(f'{tf}_eff_lo', lambda r, tf=tf: safe(r[f'{tf}_eff']) and r[f'{tf}_eff'] < 0.2)
    addp(f'{tf}_dist_lo', lambda r, tf=tf: safe(r[f'{tf}_dist']) and r[f'{tf}_dist'] < 1.0)
    addp(f'{tf}_dist_hi', lambda r, tf=tf: safe(r[f'{tf}_dist']) and r[f'{tf}_dist'] > 2.0)

# OB
addp('in_demand', lambda r: r['in_demand'] == 1)
addp('not_in_demand', lambda r: r['in_demand'] == 0)
addp('demand_fresh', lambda r: r['demand_fresh'] == 1)
addp('dist_supply_far', lambda r: r['dist_supply_atr'] > 2.0)
addp('dist_supply_near', lambda r: r['dist_supply_atr'] < 1.0)
addp('dist_demand_near', lambda r: r['dist_demand_atr'] < 1.0)
addp('dist_demand_far', lambda r: r['dist_demand_atr'] > 2.0)
addp('n_demand_ge2', lambda r: r['n_demand_near'] >= 2)
addp('n_demand_0', lambda r: r['n_demand_near'] == 0)

# VOL
addp('atr_regime_hi', lambda r: r['atr_regime'] > 1.2)
addp('atr_regime_lo', lambda r: r['atr_regime'] < 0.9)
addp('atr_expand_hi', lambda r: r['atr_expand'] > 1.2)
addp('atr_expand_lo', lambda r: r['atr_expand'] < 1.0)
addp('vol_low', lambda r: r['vol_low_vs_med'] < 1.0)
addp('vol_high', lambda r: r['vol_low_vs_med'] > 1.5)
addp('vol_climax_hi', lambda r: r['vol_climax'] > 1.5)
addp('vol_climax_lo', lambda r: r['vol_climax'] < 1.0)
addp('vpnode_above', lambda r: r['vpnode_dist_atr'] > 0)   # close above POC
addp('vpnode_below', lambda r: r['vpnode_dist_atr'] < 0)
addp('vpnode_far_above', lambda r: r['vpnode_dist_atr'] > 2.0)
addp('vpnode_near', lambda r: abs(r['vpnode_dist_atr']) < 1.0)

# PERNA (leg)
addp('macro_bull', lambda r: r['macro_bull'] == 1)
addp('macro_bear', lambda r: r['macro_bear'] == 1)
addp('macro_notbear', lambda r: r['macro_bear'] == 0)
addp('macro_retr_hi', lambda r: r['macro_retr'] > 1.0)
addp('macro_retr_lo', lambda r: r['macro_retr'] < 0.6)
addp('macro_drop_lo', lambda r: r['macro_drop_atr'] < 6.0)
addp('macro_drop_hi', lambda r: r['macro_drop_atr'] > 9.0)
addp('path_eff_hi', lambda r: r['path_eff'] > 0.6)
addp('path_eff_lo', lambda r: r['path_eff'] < 0.3)
addp('bars_fast', lambda r: r['bars_to_8atr'] < 20)
addp('bars_slow', lambda r: r['bars_to_8atr'] > 40)

# 15M
addp('rsi_hi', lambda r: r['rsi'] > 60)
addp('rsi_lo', lambda r: r['rsi'] < 45)
addp('rsi_mid', lambda r: 45 <= r['rsi'] <= 65)
addp('rsi_low_hi', lambda r: r['rsi_low'] > 40)
addp('rsi_low_lo', lambda r: r['rsi_low'] < 30)
addp('disp4_hi', lambda r: r['disp4_atr'] > 2.0)
addp('disp4_lo', lambda r: r['disp4_atr'] < 1.0)
addp('killzone', lambda r: r['killzone'] == 1)
addp('not_killzone', lambda r: r['killzone'] == 0)

PRED_MAP = dict(PREDS)

print(f"Base: N={N} WR={BASE_WR:.4f} streak={BASE_STREAK} winners={TOTW} losers={TOTL}")
print(f"Base WR/yr: " + " ".join(f"{y}={BASE_WR_YR[y]:.3f}" for y in YEARS))
print(f"#predicates={len(PREDS)}\n")

# ---- Stage 1: single predicate scan ----
print("=== STAGE 1: single predicates (sorted by wr, winners_kept>=0.85) ===")
single = []
for name, fn in PREDS:
    m = evaluate(fn)
    if m is None:
        continue
    single.append((name, m))
single.sort(key=lambda x: -x[1]['wr'])
for name, m in single[:20]:
    wk85 = m['winners_kept'] >= 0.85
    print(f"{name:22s} n={m['nk']:4d} wr={m['wr']:.3f} strk={m['streak']:2d} "
          f"wkept={m['winners_kept']:.2f} lcut={m['losers_cut']:.2f} "
          f"y24={m['wr_yr'][2024][0] if m['wr_yr'][2024][0] else 0:.2f} "
          f"y25={m['wr_yr'][2025][0] if m['wr_yr'][2025][0] else 0:.2f} "
          f"y26={m['wr_yr'][2026][0] if m['wr_yr'][2026][0] else 0:.2f} "
          f"{'WK85' if wk85 else ''} {'ROBUST' if robust(m) else ''}")

# ---- Stage 2: 2-way combos (AND). Only combine predicates that individually keep>=92% sample
#      OR are conceptually orthogonal. Require combined winners_kept>=0.85. ----
print("\n=== STAGE 2: 2-way AND combos (winners_kept>=0.85, wr>base, streak<base) ===")
names = [n for n, _ in PREDS]
two = []
for a, b in combinations(names, 2):
    fa, fb = PRED_MAP[a], PRED_MAP[b]
    m = evaluate(lambda r: fa(r) and fb(r))
    if m is None:
        continue
    if m['winners_kept'] >= 0.85 and m['wr'] > BASE_WR and m['streak'] < BASE_STREAK:
        two.append(((a, b), m))
two.sort(key=lambda x: -x[1]['wr'])
for (a, b), m in two[:25]:
    print(f"{a}+{b:30s} n={m['nk']:4d} wr={m['wr']:.3f} strk={m['streak']:2d} "
          f"wkept={m['winners_kept']:.2f} lcut={m['losers_cut']:.2f} "
          f"y24={m['wr_yr'][2024][0] or 0:.2f}({m['wr_yr'][2024][1]}) "
          f"y25={m['wr_yr'][2025][0] or 0:.2f}({m['wr_yr'][2025][1]}) "
          f"y26={m['wr_yr'][2026][0] or 0:.2f}({m['wr_yr'][2026][1]}) "
          f"{'ROBUST' if robust(m) else ''}")

# ---- Stage 3: 3-way combos seeded from robust/near-robust 2-way ----
print("\n=== STAGE 3: 3-way AND combos (seeded, robust focus) ===")
# seed pool = top 2-way bases + all single names
seed_pairs = [pair for pair, m in two[:30]]
three = []
seen = set()
for (a, b) in seed_pairs:
    for c in names:
        if c in (a, b):
            continue
        key = tuple(sorted([a, b, c]))
        if key in seen:
            continue
        seen.add(key)
        fa, fb, fc = PRED_MAP[a], PRED_MAP[b], PRED_MAP[c]
        m = evaluate(lambda r: fa(r) and fb(r) and fc(r))
        if m is None:
            continue
        if m['winners_kept'] >= 0.85 and m['wr'] > BASE_WR and m['streak'] < BASE_STREAK:
            three.append((key, m))
three.sort(key=lambda x: -x[1]['wr'])
for key, m in three[:25]:
    print(f"{'+'.join(key):48s} n={m['nk']:4d} wr={m['wr']:.3f} strk={m['streak']:2d} "
          f"wkept={m['winners_kept']:.2f} lcut={m['losers_cut']:.2f} "
          f"y24={m['wr_yr'][2024][0] or 0:.2f} y25={m['wr_yr'][2025][0] or 0:.2f} "
          f"y26={m['wr_yr'][2026][0] or 0:.2f} {'ROBUST' if robust(m) else ''}")

# ---- Stage 4: detailed report on robust candidates (all stages) ----
print("\n=== STAGE 4: ROBUST candidates full detail ===")
robust_all = []
for name, m in single:
    if robust(m):
        robust_all.append((name, m))
for (a, b), m in two:
    if robust(m):
        robust_all.append((f"{a}+{b}", m))
for key, m in three:
    if robust(m):
        robust_all.append(("+".join(key), m))
# dedup by description
robust_all.sort(key=lambda x: -x[1]['wr'])
for desc, m in robust_all[:15]:
    print(f"\n--- {desc} ---")
    print(f"  n_keep={m['nk']} wr_keep={m['wr']:.4f} streak_keep={m['streak']} "
          f"(base streak {BASE_STREAK})")
    print(f"  winners_kept={m['winners_kept']:.3f} losers_cut={m['losers_cut']:.3f}")
    print(f"  WR/yr: " + " ".join(f"{y}={m['wr_yr'][y][0]:.3f}(n{m['wr_yr'][y][1]})"
                                   for y in YEARS if m['wr_yr'][y][0] is not None))
    print(f"  blocks: " + " ".join(f"{b}:{v[0]:.2f}(n{v[1]})" for b, v in sorted(m['blk_wr'].items())))

print(f"\nTotal robust candidates: {len(robust_all)}")
