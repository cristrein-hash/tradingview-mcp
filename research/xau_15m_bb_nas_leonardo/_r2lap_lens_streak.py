#!/usr/bin/env python3
"""R2 lapidation - refine robust CUT combos toward STREAK reduction + lens (struct->flow).
Lens hypothesis: SMC structure UNCONFIRMED by later buy flow (buy_after_smc==0),
and/or weak-flow / late-buy pockets, are loser-dense -> cut them.
Targets: wr_keep>68.535, >=year-base each year, winners_kept>=85%, >=6/8 blocks non-worse,
and we additionally RANK by streak reduction. Also locate where the 24-streak sits.
RAW-causal, R2-KEPT only.
"""
import json
from collections import defaultdict
from itertools import combinations

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = sorted([r for r in ROWS if r['r2_keep'] == 1], key=lambda r: r['low_t'])
N = len(KEPT); WINS = sum(r['win'] for r in KEPT); LOSERS = N - WINS
WR_BASE = 100*WINS/N

def grp_base(key):
    g = defaultdict(lambda:[0,0])
    for r in KEPT: g[r[key]][0]+=1; g[r[key]][1]+=r['win']
    return {k:100*w/n for k,(n,w) in g.items()}
YR_BASE=grp_base('yr'); BL_BASE=grp_base('block')

def max_streak(rows):
    s=mx=0; loc=-1; best_end=-1
    for i,r in enumerate(rows):
        if r['win']==0:
            s+=1
            if s>mx: mx=s; best_end=i
        else: s=0
    return mx,best_end
STREAK_BASE,STREAK_END = max_streak(KEPT)

def evaluate(keep_fn, desc):
    kept=[r for r in KEPT if keep_fn(r)]
    nk=len(kept)
    if nk<100: return None
    wk=sum(r['win'] for r in kept); wr=100*wk/nk
    winners_kept=100*wk/WINS; losers_cut=100*(LOSERS-(nk-wk))/LOSERS
    streak,_=max_streak(kept)
    yk=defaultdict(lambda:[0,0]); bk=defaultdict(lambda:[0,0])
    for r in kept:
        yk[r['yr']][0]+=1; yk[r['yr']][1]+=r['win']
        bk[r['block']][0]+=1; bk[r['block']][1]+=r['win']
    yr_wr={y:100*w/n for y,(n,w) in yk.items()}
    yr_ok=all(y in yr_wr and yr_wr[y]>=YR_BASE[y] for y in YR_BASE)
    nb=sum(1 for b in BL_BASE if b in bk and bk[b][0]>0 and 100*bk[b][1]/bk[b][0]>=BL_BASE[b]-1e-9)
    robust=(wr>WR_BASE and yr_ok and winners_kept>=85.0 and nb>=6 and streak<STREAK_BASE)
    return dict(desc=desc,n_keep=nk,wr_keep=round(wr,2),streak_keep=streak,
                winners_kept_pct=round(winners_kept,1),losers_cut_pct=round(losers_cut,1),
                y24=round(yr_wr.get(2024,0),1),y25=round(yr_wr.get(2025,0),1),
                y26=round(yr_wr.get(2026,0),1),nb=nb,robust=robust)

CUT = {
    'absorb1':       lambda r: r['absorption']==1,
    'ratio_gt5':     lambda r: r['buy_sell_ratio4']>5,
    'ratio_gt7':     lambda r: r['buy_sell_ratio4']>7,
    'buyL_recent':   lambda r: r['buy_L_recent']==1,
    'flow_flat':     lambda r: -2<r['flow_accel']<=0,
    'sell_stale':    lambda r: 40<r['bars_since_sell']<=99,
    'vol_hi':        lambda r: r['low_vol_rel']>1.37,
    'age_young':     lambda r: 10.5<r['regime_age_h']<=25.2,
    'lowest_fresh':  lambda r: r['bars_since_lowest']<=44,
    'ny_overlap':    lambda r: r['is_ny_overlap']==1,
    'no_buyaftersmc':lambda r: r['buy_after_smc']==0,
    'smc_old':       lambda r: r['smc_lag_bars']>10,
}

def main():
    print(f'BASE n={N} WR={WR_BASE:.3f} streak={STREAK_BASE} ends_at_idx={STREAK_END}')
    # context of the base streak: print the streak window block/year
    win=KEPT[STREAK_END-STREAK_BASE+1:STREAK_END+1]
    bl=defaultdict(int)
    for r in win: bl[r['block']]+=1
    print('base 24-streak spans blocks:', dict(bl))

    print('\n=== LENS: structure->flow targeted cuts ===')
    LENS = {
        'no_buyaftersmc & flow_flat': lambda r: not (r['buy_after_smc']==0 and -2<r['flow_accel']<=0),
        'no_buyaftersmc & buyL_recent': lambda r: not (r['buy_after_smc']==0 and r['buy_L_recent']==1),
        'no_buyaftersmc & ratio_gt5': lambda r: not (r['buy_after_smc']==0 and r['buy_sell_ratio4']>5),
        'smc_old & no_buyaftersmc': lambda r: not (r['smc_lag_bars']>10 and r['buy_after_smc']==0),
        'no_buyaftersmc & age_young': lambda r: not (r['buy_after_smc']==0 and 10.5<r['regime_age_h']<=25.2),
    }
    for n,f in LENS.items():
        d=evaluate(f,'CUT['+n+']')
        if d: print(f"  {d['robust']!s:5s} wr{d['wr_keep']:5.2f} strk{d['streak_keep']:2d} nk{d['n_keep']} "
                    f"wk{d['winners_kept_pct']} lc{d['losers_cut_pct']} y[{d['y24']}/{d['y25']}/{d['y26']}] nb{d['nb']} :: {n}")

    print('\n=== TRIPLE-UNION cuts ranked by (robust, low streak, wr) ===')
    res=[]
    names=list(CUT)
    for a,b,c in combinations(names,3):
        f=lambda r,a=a,b=b,c=c: not (CUT[a](r) or CUT[b](r) or CUT[c](r))
        d=evaluate(f,f'CUT[{a}|{b}|{c}]')
        if d and d['winners_kept_pct']>=85.0 and d['wr_keep']>WR_BASE: res.append(d)
    res.sort(key=lambda r:(r['robust'], -r['streak_keep'], r['wr_keep']) ,reverse=True)
    rob=[r for r in res if r['robust']]
    rob.sort(key=lambda r:(r['streak_keep'], -r['wr_keep']))
    print(f'robust triples: {len(rob)} (showing lowest-streak first)')
    for r in rob[:15]:
        print(f"  wr{r['wr_keep']:5.2f} strk{r['streak_keep']:2d} nk{r['n_keep']:4d} wk{r['winners_kept_pct']:4.1f} "
              f"lc{r['losers_cut_pct']:4.1f} y[{r['y24']}/{r['y25']}/{r['y26']}] nb{r['nb']} :: {r['desc']}")

if __name__=='__main__':
    main()
