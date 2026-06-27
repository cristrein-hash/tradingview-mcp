#!/usr/bin/env python3
"""R2 lapidation - CUT-WHEN search: find loser-dense pockets to remove while keeping >=85% winners.
A cut rule removes rows matching it. Goal: WR up, streak down, winners_kept>=85%, stable.
RAW-causal, R2-KEPT only. win=R>0. Ordered by low_t for streak.
robust=true iff: wr_keep>68.535 AND wr_keep_year>=base_year ALL years
                 AND winners_kept>=85% AND >=6/8 blocks not-worse.
"""
import json
from collections import defaultdict
from itertools import combinations

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = sorted([r for r in ROWS if r['r2_keep'] == 1], key=lambda r: r['low_t'])
N = len(KEPT); WINS = sum(r['win'] for r in KEPT); LOSERS = N - WINS
WR_BASE = 100 * WINS / N

def grp_base(key):
    g = defaultdict(lambda: [0, 0])
    for r in KEPT:
        g[r[key]][0] += 1; g[r[key]][1] += r['win']
    return {k: 100*w/n for k, (n, w) in g.items()}
YR_BASE = grp_base('yr'); BL_BASE = grp_base('block')

def max_streak(rows):
    s = mx = 0
    for r in rows:
        if r['win'] == 0:
            s += 1; mx = max(mx, s)
        else:
            s = 0
    return mx
STREAK_BASE = max_streak(KEPT)

def evaluate(cut_fn, desc):
    kept = [r for r in KEPT if not cut_fn(r)]
    nk = len(kept)
    if nk == 0: return None
    wk = sum(r['win'] for r in kept)
    wr = 100 * wk / nk
    winners_kept = 100 * wk / WINS
    losers_cut = 100 * (LOSERS - (nk - wk)) / LOSERS
    streak = max_streak(kept)
    yk = defaultdict(lambda: [0, 0])
    for r in kept: yk[r['yr']][0]+=1; yk[r['yr']][1]+=r['win']
    yr_wr = {y: 100*w/n for y, (n, w) in yk.items()}
    yr_ok = all(y in yr_wr and yr_wr[y] >= YR_BASE[y] for y in YR_BASE)
    bk = defaultdict(lambda: [0, 0])
    for r in kept: bk[r['block']][0]+=1; bk[r['block']][1]+=r['win']
    nb = sum(1 for b in BL_BASE if b in bk and bk[b][0]>0 and 100*bk[b][1]/bk[b][0] >= BL_BASE[b]-1e-9)
    robust = (wr > WR_BASE and yr_ok and winners_kept >= 85.0 and nb >= 6 and streak <= STREAK_BASE)
    return dict(desc=desc, n_keep=nk, wr_keep=round(wr,2), streak_keep=streak,
                winners_kept_pct=round(winners_kept,1), losers_cut_pct=round(losers_cut,1),
                y24=round(yr_wr.get(2024,0),1), y25=round(yr_wr.get(2025,0),1),
                y26=round(yr_wr.get(2026,0),1), nb=nb, yr_ok=yr_ok, robust=robust)

# ---- CUT predicates: remove rows where these are TRUE (loser-enriched pockets) ----
C = {
    'cut_ratio_hi':     lambda r: r['buy_sell_ratio4'] > 5.0,          # high buy ratio = chasing
    'cut_ratio_vhi':    lambda r: r['buy_sell_ratio4'] >= 7.0,
    'cut_flow0':        lambda r: r['flow_accel'] == 0,                # stagnant curvature
    'cut_absorb':       lambda r: r['absorption'] == 1,                # absorption=worse here
    'cut_sell_stale':   lambda r: r['bars_since_sell'] > 40,           # no recent sell
    'cut_lowvol_hi':    lambda r: r['low_vol_rel'] > 1.37,             # vacuum low
    'cut_closepos_hi':  lambda r: r['low_closepos'] > 0.85,           # weak close
    'cut_lowest_fresh': lambda r: r['bars_since_lowest'] <= 44,        # fresh new low
    'cut_buyL':         lambda r: r['buy_L_recent'] == 1,
    'cut_regime_yng':   lambda r: r['regime_age_h'] <= 25.2,          # young regime
    'cut_buycross_mid': lambda r: r['bars_since_buycross'] <= 99,
    'cut_decel_neg':    lambda r: r['sell_decel'] <= 0 and r['sell_decel'] > -1e6,
}

def report(res, title, top=25):
    res = [r for r in res if r is not None]
    print(f'\n=== {title} n={len(res)} ===')
    for r in res[:top]:
        print(f"{r['robust']!s:5s} wr{r['wr_keep']} strk{r['streak_keep']} nk{r['n_keep']} "
              f"wkeep{r['winners_kept_pct']} lcut{r['losers_cut_pct']} "
              f"y[{r['y24']}/{r['y25']}/{r['y26']}](ok{r['yr_ok']!s:5s}) nb{r['nb']} :: {r['desc']}")

def main():
    print(f'BASE n={N} WR={WR_BASE:.3f} streak={STREAK_BASE} winners={WINS} losers={LOSERS}')
    print(f'YR_BASE {{2024:{YR_BASE[2024]:.1f},2025:{YR_BASE[2025]:.1f},2026:{YR_BASE[2026]:.1f}}}')
    names = list(C)
    res = []
    for a in names:
        res.append(evaluate(C[a], a))
    # OR-pairs (cut if a OR b)
    for a, b in combinations(names, 2):
        res.append(evaluate(lambda r,a=a,b=b: C[a](r) or C[b](r), f'{a}|{b}'))
    # OR-triples
    for a, b, c in combinations(names, 3):
        res.append(evaluate(lambda r,a=a,b=b,c=c: C[a](r) or C[b](r) or C[c](r), f'{a}|{b}|{c}'))
    # AND-pairs (cut only where both true = tight loser pocket, spares winners)
    for a, b in combinations(names, 2):
        res.append(evaluate(lambda r,a=a,b=b: C[a](r) and C[b](r), f'{a}&{b}'))
    # AND-triples
    for a, b, c in combinations(names, 3):
        res.append(evaluate(lambda r,a=a,b=b,c=c: C[a](r) and C[b](r) and C[c](r), f'{a}&{b}&{c}'))
    res = [r for r in res if r]
    # candidates: keep>=85% winners and wr up
    cand = [r for r in res if r['winners_kept_pct'] >= 85.0 and r['wr_keep'] > WR_BASE]
    cand.sort(key=lambda r: (r['robust'], r['nb'], r['wr_keep']), reverse=True)
    report(cand, 'CUT CANDIDATES (winners>=85, wr up)', 30)
    robust = [r for r in res if r['robust']]
    robust.sort(key=lambda r: (r['wr_keep'], -r['streak_keep']), reverse=True)
    report(robust, 'ROBUST', 30)

if __name__ == '__main__':
    main()
