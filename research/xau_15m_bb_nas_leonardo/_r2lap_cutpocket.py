#!/usr/bin/env python3
"""R2 lapidation - find a LOSER-DENSE pocket to CUT (keep>=85% winners) that
lifts WR>68.535 stably across years/blocks and lowers max-losing-streak.
The binding constraint is winners_kept>=85%: we can only remove ~small slices,
so we want pockets with WR far below base (loser-dense) but modest winner count.
RAW-causal, R2-KEPT only. Lens: structure->flow (smc + buy_after_smc).
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

def evaluate(keep_fn, desc):
    kept = [r for r in KEPT if keep_fn(r)]
    nk = len(kept)
    if nk < 100: return None
    wk = sum(r['win'] for r in kept)
    wr = 100*wk/nk
    winners_kept = 100*wk/WINS
    losers_cut = 100*(LOSERS - (nk-wk))/LOSERS
    streak = max_streak(kept)
    yk = defaultdict(lambda: [0,0]); bk = defaultdict(lambda: [0,0])
    for r in kept:
        yk[r['yr']][0]+=1; yk[r['yr']][1]+=r['win']
        bk[r['block']][0]+=1; bk[r['block']][1]+=r['win']
    yr_wr = {y: 100*w/n for y,(n,w) in yk.items()}
    yr_ok = all(y in yr_wr and yr_wr[y] >= YR_BASE[y] for y in YR_BASE)
    nb = sum(1 for b in BL_BASE if b in bk and bk[b][0]>0 and 100*bk[b][1]/bk[b][0] >= BL_BASE[b]-1e-9)
    robust = (wr>WR_BASE and yr_ok and winners_kept>=85.0 and nb>=6 and streak<STREAK_BASE)
    return dict(desc=desc, n_keep=nk, wr_keep=round(wr,2), streak_keep=streak,
                winners_kept_pct=round(winners_kept,1), losers_cut_pct=round(losers_cut,1),
                y24=round(yr_wr.get(2024,0),1), y25=round(yr_wr.get(2025,0),1),
                y26=round(yr_wr.get(2026,0),1), nb=nb, robust=robust)

# CUT predicates: True => this row is in the loser-dense pocket to REMOVE.
# keep_fn = not cut. Designed loser-dense slices from univariate + lens.
CUT = {
    'absorb1':        lambda r: r['absorption'] == 1,           # 0.640
    'ratio_gt7':      lambda r: r['buy_sell_ratio4'] > 7,       # 0.610
    'ratio_gt5':      lambda r: r['buy_sell_ratio4'] > 5,       # 5..7 0.624 +>7
    'buyL_recent':    lambda r: r['buy_L_recent'] == 1,         # 0.661
    'flow_flat':      lambda r: -2 < r['flow_accel'] <= 0,      # q1 0.599
    'sell_stale':     lambda r: 40 < r['bars_since_sell'] <= 99,# 0.633
    'vol_hi':         lambda r: r['low_vol_rel'] > 1.37,        # 0.643
    'age_young':      lambda r: 10.5 < r['regime_age_h'] <= 25.2,# 0.632
    'lowest_fresh':   lambda r: r['bars_since_lowest'] <= 44,   # 0.648
    'ny_overlap':     lambda r: r['is_ny_overlap'] == 1,        # 0.674
    # lens: structure stale / unconfirmed
    'smc_old_nobuy':  lambda r: r['smc_lag_bars'] > 10 and r['buy_after_smc'] == 0,
    'smc_old':        lambda r: r['smc_lag_bars'] > 10,
    'no_buyaftersmc': lambda r: r['buy_after_smc'] == 0,
}

def cut_wr(cutfn):
    pocket = [r for r in KEPT if cutfn(r)]
    if not pocket: return 0,0,0
    w = sum(r['win'] for r in pocket)
    return len(pocket), 100*w/len(pocket), w

def main():
    print(f'BASE n={N} WR={WR_BASE:.3f} streak={STREAK_BASE} losers={LOSERS} winners={WINS}')
    print('YR_BASE', {k:round(v,2) for k,v in YR_BASE.items()})
    print('\n=== single CUT-pocket profiles (pocket WR / size / winners in pocket) ===')
    for n,f in CUT.items():
        sz,wr,w = cut_wr(f)
        print(f'  {n:16s} pocket n={sz:4d} WR={wr:5.1f} winners_in_pocket={w}')

    print('\n=== single CUT -> keep complement ===')
    res=[]
    for n,f in CUT.items():
        d = evaluate(lambda r,f=f: not f(r), f'CUT[{n}]')
        if d: res.append(d)
    # pairs (cut union) and (cut intersection)
    names=list(CUT)
    for a,b in combinations(names,2):
        d = evaluate(lambda r,a=a,b=b: not (CUT[a](r) or CUT[b](r)), f'CUT[{a}|{b}]')
        if d: res.append(d)
    for a,b in combinations(names,2):
        d = evaluate(lambda r,a=a,b=b: not (CUT[a](r) and CUT[b](r)), f'CUT[{a}&{b}]')
        if d: res.append(d)
    for a,b,c in combinations(names,3):
        d = evaluate(lambda r,a=a,b=b,c=c: not (CUT[a](r) or CUT[b](r) or CUT[c](r)), f'CUT[{a}|{b}|{c}]')
        if d: res.append(d)

    cand=[r for r in res if r['winners_kept_pct']>=85.0 and r['wr_keep']>WR_BASE]
    cand.sort(key=lambda r:(r['robust'], r['wr_keep']), reverse=True)
    print(f'\n=== CANDIDATES winners_kept>=85 & wr>base: n={len(cand)} ===')
    for r in cand[:40]:
        print(f"{r['robust']!s:5s} wr{r['wr_keep']:5.2f} strk{r['streak_keep']:2d} nk{r['n_keep']:4d} "
              f"wkeep{r['winners_kept_pct']:4.1f} lcut{r['losers_cut_pct']:4.1f} "
              f"y[{r['y24']}/{r['y25']}/{r['y26']}] nb{r['nb']} :: {r['desc']}")
    robust=[r for r in cand if r['robust']]
    print(f'\n=== ROBUST n={len(robust)} ===')
    for r in robust:
        print(f"  wr{r['wr_keep']} strk{r['streak_keep']} nk{r['n_keep']} wkeep{r['winners_kept_pct']} "
              f"lcut{r['losers_cut_pct']} y[{r['y24']}/{r['y25']}/{r['y26']}] nb{r['nb']} :: {r['desc']}")

if __name__=='__main__':
    main()
