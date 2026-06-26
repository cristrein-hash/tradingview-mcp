#!/usr/bin/env python3
"""R2 lapidation - search keep-when combos (2-3 features) for stable WR lift + streak reduction.
RAW-causal, R2-KEPT only. win=R>0. Streak = max consecutive losers ordered by low_t.
robust=true iff: wr_keep>68.535 AND wr_keep_year>=base_year for ALL years
                 AND winners_kept>=85% AND >=6/8 blocks not-worse.
"""
import json
from collections import defaultdict
from itertools import combinations

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = sorted([r for r in ROWS if r['r2_keep'] == 1], key=lambda r: r['low_t'])
N = len(KEPT)
WINS = sum(r['win'] for r in KEPT)
WR_BASE = 100 * WINS / N

# base per year / block
def grp_base(key):
    g = defaultdict(lambda: [0, 0])
    for r in KEPT:
        g[r[key]][0] += 1; g[r[key]][1] += r['win']
    return {k: 100*w/n for k, (n, w) in g.items()}
YR_BASE = grp_base('yr')
BL_BASE = grp_base('block')

def max_streak(rows):
    s = mx = 0
    for r in rows:  # rows already time-ordered
        if r['win'] == 0:
            s += 1; mx = max(mx, s)
        else:
            s = 0
    return mx

STREAK_BASE = max_streak(KEPT)

def evaluate(mask_fn, desc):
    kept = [r for r in KEPT if mask_fn(r)]
    nk = len(kept)
    if nk == 0:
        return None
    wk = sum(r['win'] for r in kept)
    wr = 100 * wk / nk
    win_total = WINS
    winners_kept = 100 * wk / win_total
    losers_total = N - WINS
    losers_cut = 100 * ((N - WINS) - (nk - wk)) / losers_total
    streak = max_streak(kept)
    # per year
    yk = defaultdict(lambda: [0, 0])
    for r in kept:
        yk[r['yr']][0] += 1; yk[r['yr']][1] += r['win']
    yr_wr = {y: 100*w/n for y, (n, w) in yk.items()}
    yr_ok = all(y in yr_wr and yr_wr[y] >= YR_BASE[y] for y in YR_BASE)
    # per block not-worse
    bk = defaultdict(lambda: [0, 0])
    for r in kept:
        bk[r['block']][0] += 1; bk[r['block']][1] += r['win']
    nb_notworse = 0
    for b in BL_BASE:
        if b in bk and bk[b][0] > 0:
            if 100*bk[b][1]/bk[b][0] >= BL_BASE[b] - 1e-9:
                nb_notworse += 1
    robust = (wr > WR_BASE and yr_ok and winners_kept >= 85.0 and nb_notworse >= 6)
    return dict(desc=desc, n_keep=nk, wr_keep=round(wr, 2), streak_keep=streak,
                winners_kept_pct=round(winners_kept, 1), losers_cut_pct=round(losers_cut, 1),
                y24=round(yr_wr.get(2024, 0), 1), y25=round(yr_wr.get(2025, 0), 1),
                y26=round(yr_wr.get(2026, 0), 1), nb_notworse=nb_notworse, robust=robust)

# ---- candidate predicates (keep-when = cut the complementary losers) ----
# Each predicate keeps rows satisfying it.
P = {
    'sell_recent':      lambda r: r['bars_since_sell'] <= 40,
    'ratio_le5':        lambda r: r['buy_sell_ratio4'] <= 5.0,
    'ratio_le4':        lambda r: r['buy_sell_ratio4'] <= 4.0,
    'flow_ne0':         lambda r: r['flow_accel'] != 0,
    'flow_neg_or_hi':   lambda r: r['flow_accel'] < 0 or r['flow_accel'] >= 7,
    'no_absorb':        lambda r: r['absorption'] == 0,
    'buycross_old':     lambda r: r['bars_since_buycross'] > 272,
    'regime_mid':       lambda r: 25.2 < r['regime_age_h'] <= 61.8,
    'lowvol_lo':        lambda r: r['low_vol_rel'] <= 1.37,
    'low_closepos_lo':  lambda r: r['low_closepos'] <= 0.39,
    'lowest_old':       lambda r: r['bars_since_lowest'] > 91,
    'smc_recent':       lambda r: r['smc_lag_bars'] <= 1,
    'buyL_no':          lambda r: r['buy_L_recent'] == 0,
    'decel_pos':        lambda r: r['sell_decel'] > 0,
    'not_buyaftersmc':  lambda r: True,  # placeholder
}
del P['not_buyaftersmc']

def main():
    print(f'BASE n={N} WR={WR_BASE:.3f} streak={STREAK_BASE}')
    print(f'YR_BASE {YR_BASE}')
    print('BL_BASE', {k: round(v,1) for k,v in sorted(BL_BASE.items())})
    print('=== SINGLES ===')
    res = []
    for name, fn in P.items():
        r = evaluate(fn, name)
        if r: res.append(r)
    print('=== PAIRS ===')
    names = list(P)
    for a, b in combinations(names, 2):
        fn = lambda r, a=a, b=b: P[a](r) and P[b](r)
        rr = evaluate(fn, f'{a}+{b}')
        if rr: res.append(rr)
    print('=== TRIPLES ===')
    for a, b, c in combinations(names, 3):
        fn = lambda r, a=a, b=b, c=c: P[a](r) and P[b](r) and P[c](r)
        rr = evaluate(fn, f'{a}+{b}+{c}')
        if rr: res.append(rr)
    # diagnostic: best WR regardless of winners_kept, to see frontier
    allc = [r for r in res if r['wr_keep'] > WR_BASE]
    allc.sort(key=lambda r: r['wr_keep'], reverse=True)
    print(f'\n=== FRONTIER: highest WR (any winners_kept), wr>{WR_BASE:.1f} ===')
    for r in allc[:15]:
        print(f"wr{r['wr_keep']} strk{r['streak_keep']} nk{r['n_keep']} "
              f"wkeep{r['winners_kept_pct']} lcut{r['losers_cut_pct']} "
              f"y[{r['y24']}/{r['y25']}/{r['y26']}] nb{r['nb_notworse']} :: {r['desc']}")
    # filter: keep winners>=85
    cand = [r for r in res if r['winners_kept_pct'] >= 85.0 and r['wr_keep'] > WR_BASE]
    cand.sort(key=lambda r: (r['robust'], r['wr_keep'], -r['streak_keep']), reverse=True)
    print(f'\n=== TOP CANDIDATES (winners_kept>=85, wr>{WR_BASE:.1f}) n={len(cand)} ===')
    for r in cand[:30]:
        print(f"{r['robust']!s:5s} wr{r['wr_keep']} strk{r['streak_keep']} "
              f"nk{r['n_keep']} wkeep{r['winners_kept_pct']} lcut{r['losers_cut_pct']} "
              f"y[{r['y24']}/{r['y25']}/{r['y26']}] nb{r['nb_notworse']} :: {r['desc']}")
    robust = [r for r in cand if r['robust']]
    print(f'\n=== ROBUST n={len(robust)} ===')
    for r in robust[:20]:
        print(f"wr{r['wr_keep']} strk{r['streak_keep']} nk{r['n_keep']} "
              f"wkeep{r['winners_kept_pct']} lcut{r['losers_cut_pct']} "
              f"y[{r['y24']}/{r['y25']}/{r['y26']}] nb{r['nb_notworse']} :: {r['desc']}")

if __name__ == '__main__':
    main()
