#!/usr/bin/env python3
"""
_disc8_multitf.py — Multi-TF aggregated contextual combo discovery for the 8ATR
confirmation entry (n=2615, base WR 66.1%, base max-losing-streak 28).

LENS: Multi-TF agregado. Combine h1/h4/hd trend/dist/pos/eff.
Hypothesis: LOSER when timeframes DISAGREE, or hd/h4 in RANGE (eff low),
or near TOP of HTF range (pos high). WINNER when 4H+1D aligned-with and
there is SPACE (pos low).

RULES:
 - win = R>0. R/win NEVER used as a feature.
 - order by low_t, compute MAX-LOSING-STREAK before/after.
 - report n_keep, wr_keep, streak_keep, winners_kept_pct, losers_cut_pct, WR per year.
 - robust=True only if WR up AND >= base in ALL 3 years AND not carried by few.
 - RAW-causal: HTF only closed bars; nulls handled explicitly.
"""
import json, statistics as st

ROWS = [json.loads(l) for l in open('dataset_8atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
TOT_WIN = sum(r['win'] for r in ROWS)
TOT_LOSE = N - TOT_WIN
YEARS = [2024, 2025, 2026]
BASE_WR_YR = {}
for y in YEARS:
    sub = [r for r in ROWS if r['yr'] == y]
    BASE_WR_YR[y] = sum(r['win'] for r in sub) / len(sub)


def max_losing_streak(rows):
    """rows already time-ordered; longest consecutive R<=0 run (win==0)."""
    mx = cur = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


BASE_STREAK = max_losing_streak(ROWS)


def block_breakdown(kept):
    """WR per block; return (n_blocks_with_data, min_block_wr, n_blocks_below_base)."""
    from collections import defaultdict
    bw = defaultdict(lambda: [0, 0])
    for r in kept:
        bw[r['block']][0] += r['win']
        bw[r['block']][1] += 1
    res = {}
    for b, (w, n) in bw.items():
        res[b] = (w / n if n else None, n)
    return res


def evaluate(name, pred, desc, min_keep=200):
    """pred(r)->bool means KEEP (trade taken). Report drop of the rest."""
    kept = [r for r in ROWS if pred(r)]
    nk = len(kept)
    if nk < min_keep:
        return None
    wins_kept = sum(r['win'] for r in kept)
    wr_keep = wins_kept / nk
    streak_keep = max_losing_streak(kept)
    winners_kept_pct = wins_kept / TOT_WIN
    losers_cut = TOT_LOSE - (nk - wins_kept)
    losers_cut_pct = losers_cut / TOT_LOSE
    wr_yr = {}
    for y in YEARS:
        sub = [r for r in kept if r['yr'] == y]
        wr_yr[y] = (sum(r['win'] for r in sub) / len(sub), len(sub)) if sub else (None, 0)
    # robust check
    yrs_ok = all(wr_yr[y][0] is not None and wr_yr[y][0] >= BASE_WR_YR[y] for y in YEARS)
    wr_up = wr_keep > BASE_WR
    # not carried by few: every year keeps >=30 trades and >=85% winners overall
    enough = all(wr_yr[y][1] >= 30 for y in YEARS) and winners_kept_pct >= 0.85
    # block stability: WR >= base in at least 7/8 blocks
    bb = block_breakdown(kept)
    blocks_below = sum(1 for b,(w,n) in bb.items() if w is not None and n>=15 and w < BASE_WR)
    block_ok = blocks_below <= 1
    robust = bool(wr_up and yrs_ok and enough and block_ok)
    return {
        'name': name, 'desc': desc,
        'n_keep': nk, 'wr_keep': round(wr_keep, 4),
        'streak_keep': streak_keep,
        'winners_kept_pct': round(winners_kept_pct, 4),
        'losers_cut_pct': round(losers_cut_pct, 4),
        'y24': round(wr_yr[2024][0], 4) if wr_yr[2024][0] is not None else None,
        'y25': round(wr_yr[2025][0], 4) if wr_yr[2025][0] is not None else None,
        'y26': round(wr_yr[2026][0], 4) if wr_yr[2026][0] is not None else None,
        'y24n': wr_yr[2024][1], 'y25n': wr_yr[2025][1], 'y26n': wr_yr[2026][1],
        'blocks_below': blocks_below,
        'robust': robust,
    }


# ---- helpers for null-safe HTF access ----
def g(r, k, default=None):
    v = r.get(k)
    return default if v is None else v


# =========================================================================
# PHASE 1: build candidate predicates (KEEP = take the trade)
# =========================================================================
CANDS = []

# --- A. HTF alignment (4H + 1D agree with up). pos low = space.
def htf_align_up(r):
    h4 = r.get('h4_trend'); hd = r.get('hd_trend')
    if h4 is None or hd is None: return False
    return h4 >= 0 and hd >= 0 and not (h4 == 0 and hd == 0)
CANDS.append(('A_htf_align_up', htf_align_up,
    'h4_trend>=0 AND hd_trend>=0 (both 4H+1D non-down, not both range)'))

# --- B. drop the contradiction: h4 and hd DISAGREE in trend sign
def no_htf_disagree(r):
    h4 = r.get('h4_trend'); hd = r.get('hd_trend')
    if h4 is None or hd is None: return True  # keep warmup
    return not (h4 * hd < 0)  # cut only when signs strictly opposite
CANDS.append(('B_no_htf_disagree', no_htf_disagree,
    'NOT (h4_trend and hd_trend strictly opposite sign)'))

# --- C. avoid TOP of HTF range: hd_pos and h4_pos not both high
def not_htf_top(r, thr=0.85):
    h4p = r.get('h4_pos'); hdp = r.get('hd_pos')
    cond = True
    if h4p is not None and h4p > thr: cond = False
    if hdp is not None and hdp > thr: cond = False
    return cond
CANDS.append(('C_not_htf_top', not_htf_top,
    'h4_pos<=0.85 AND hd_pos<=0.85 (not at top of HTF range)'))

# --- D. HTF has trend (eff not range): h4_eff or hd_eff above floor
def htf_has_trend(r, thr=0.15):
    h4e = r.get('h4_eff'); hde = r.get('hd_eff')
    vals = [v for v in (h4e, hde) if v is not None]
    if not vals: return True
    return max(vals) >= thr
CANDS.append(('D_htf_has_trend', htf_has_trend,
    'max(h4_eff,hd_eff)>=0.15 (HTF not pure range)'))

# --- E. space above: not near supply, room to run
def room_above(r, thr=1.0):
    ds = r.get('dist_supply_atr')
    if ds is None: return True
    return ds >= thr
CANDS.append(('E_room_above', room_above, 'dist_supply_atr>=1.0'))

# Evaluate singles first
print('=== BASE ===')
print('N', N, 'WR', round(BASE_WR,4), 'streak', BASE_STREAK)
print('WR/yr', {y: round(BASE_WR_YR[y],4) for y in YEARS})
print()
print('=== SINGLES ===')
for nm, pr, ds in CANDS:
    res = evaluate(nm, pr, ds)
    if res:
        print(f"{nm:22} n={res['n_keep']:4} wr={res['wr_keep']} strk={res['streak_keep']:2} "
              f"wkept={res['winners_kept_pct']} lcut={res['losers_cut_pct']} "
              f"y={res['y24']}/{res['y25']}/{res['y26']} robust={res['robust']}")

# =========================================================================
# PHASE 2: contextual combos (the real target)
# =========================================================================
print()
print('=== COMBOS ===')

COMBOS = []

# 1. Aligned-up AND not at HTF top
COMBOS.append(('combo1_alignup_nottop',
    lambda r: htf_align_up(r) and not_htf_top(r),
    'h4>=0 & hd>=0 (not both range) AND h4_pos<=.85 & hd_pos<=.85'))

# 2. No disagreement AND not HTF top AND room above
COMBOS.append(('combo2_agree_room',
    lambda r: no_htf_disagree(r) and not_htf_top(r) and room_above(r),
    'no h4/hd sign-conflict AND not HTF top AND dist_supply>=1.0'))

# 3. HTF trend present AND aligned up
COMBOS.append(('combo3_trend_align',
    lambda r: htf_has_trend(r) and htf_align_up(r),
    'max(h4_eff,hd_eff)>=.15 AND h4>=0 & hd>=0'))

# 4. Full structural: aligned up + space (pos low) + room above
COMBOS.append(('combo4_full_long',
    lambda r: htf_align_up(r) and not_htf_top(r, 0.75) and room_above(r, 0.75),
    'aligned-up AND h4/hd_pos<=.75 AND dist_supply>=0.75'))

# 5. Drop the worst: HTF top OR HTF disagree => skip
COMBOS.append(('combo5_drop_top_or_disagree',
    lambda r: not_htf_top(r, 0.85) and no_htf_disagree(r),
    'NOT(HTF top>.85) AND NOT(h4/hd disagree)'))

# 6. 3-TF concord: h1 also up with 4H+1D
COMBOS.append(('combo6_3tf_up',
    lambda r: r.get('h1_trend',0) >= 0 and htf_align_up(r),
    'h1_trend>=0 AND h4>=0 & hd>=0'))

# 7. macro retr + h4 up (pullback-in-uptrend) + not HTF top
COMBOS.append(('combo7_pullback_uptrend',
    lambda r: r.get('h4_trend') is not None and r['h4_trend'] >= 1
              and g(r,'macro_retr',0) >= 0.5 and not_htf_top(r,0.9),
    'h4_trend==up AND macro_retr>=0.5 AND not HTF top>.9'))

for nm, pr, ds in COMBOS:
    res = evaluate(nm, pr, ds)
    if res:
        print(f"{nm:28} n={res['n_keep']:4} wr={res['wr_keep']} strk={res['streak_keep']:2} "
              f"wkept={res['winners_kept_pct']} lcut={res['losers_cut_pct']} "
              f"y={res['y24']}/{res['y25']}/{res['y26']} blk_below={res['blocks_below']} robust={res['robust']}")

import pickle
with open('/tmp/_disc8_ctx.pkl','wb') as f:
    pickle.dump({'evaluate_doc':'see script'}, f)
