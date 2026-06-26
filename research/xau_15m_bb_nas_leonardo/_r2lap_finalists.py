#!/usr/bin/env python3
"""R2 lapidation - FINALIST verification. Full diagnostics for top robust CUT combos,
plus an attempt to jointly maximize WR and minimize streak by unioning the two best
families. Reports per-year, per-block, streak, Wilson lower bound. RAW-causal, R2-KEPT.
"""
import json, math
from collections import defaultdict

ROWS=[json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT=sorted([r for r in ROWS if r['r2_keep']==1], key=lambda r:r['low_t'])
N=len(KEPT); WINS=sum(r['win'] for r in KEPT); LOSERS=N-WINS; WR_BASE=100*WINS/N

def grp_base(key):
    g=defaultdict(lambda:[0,0])
    for r in KEPT: g[r[key]][0]+=1; g[r[key]][1]+=r['win']
    return {k:100*w/n for k,(n,w) in g.items()}
YR_BASE=grp_base('yr'); BL_BASE=grp_base('block')

def max_streak(rows):
    s=mx=0
    for r in rows:
        if r['win']==0: s+=1; mx=max(mx,s)
        else: s=0
    return mx
STREAK_BASE=max_streak(KEPT)

def wilson_lo(k,n,z=1.96):
    if n==0: return 0
    p=k/n; d=1+z*z/n
    c=p+z*z/(2*n); m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return 100*(c-m)/d

def report(keep_fn,desc):
    kept=[r for r in KEPT if keep_fn(r)]
    nk=len(kept); wk=sum(r['win'] for r in kept); wr=100*wk/nk
    winners_kept=100*wk/WINS; losers_cut=100*(LOSERS-(nk-wk))/LOSERS
    streak=max_streak(kept)
    yk=defaultdict(lambda:[0,0]); bk=defaultdict(lambda:[0,0])
    for r in kept:
        yk[r['yr']][0]+=1; yk[r['yr']][1]+=r['win']
        bk[r['block']][0]+=1; bk[r['block']][1]+=r['win']
    yr_wr={y:100*w/n for y,(n,w) in yk.items()}
    yr_ok=all(yr_wr[y]>=YR_BASE[y] for y in YR_BASE)
    nb=sum(1 for b in BL_BASE if 100*bk[b][1]/bk[b][0]>=BL_BASE[b]-1e-9)
    robust=(wr>WR_BASE and yr_ok and winners_kept>=85.0 and nb>=6 and streak<STREAK_BASE)
    print(f'\n### {desc}')
    print(f'  n_keep={nk} wr_keep={wr:.2f} (Wilson_lo={wilson_lo(wk,nk):.1f}) streak={streak} (base {STREAK_BASE})')
    print(f'  winners_kept={winners_kept:.1f}% losers_cut={losers_cut:.1f}% robust={robust}')
    print(f'  year: ' + ' '.join(f'{y}={yr_wr[y]:.1f}(b{YR_BASE[y]:.1f}){"+" if yr_wr[y]>=YR_BASE[y] else "-"}' for y in sorted(YR_BASE)))
    print(f'  blocks nb={nb}/8: ' + ' '.join(f'{b[-5:]}={100*bk[b][1]/bk[b][0]:.1f}{"+" if 100*bk[b][1]/bk[b][0]>=BL_BASE[b]-1e-9 else "-"}' for b in sorted(BL_BASE)))
    return dict(desc=desc,n_keep=nk,wr_keep=round(wr,2),streak_keep=streak,
                winners_kept_pct=round(winners_kept,1),losers_cut_pct=round(losers_cut,1),
                y24=round(yr_wr[2024],1),y25=round(yr_wr[2025],1),y26=round(yr_wr[2026],1),robust=robust)

# atoms
A_flow_flat   = lambda r: -2<r['flow_accel']<=0
A_lowest_fresh= lambda r: r['bars_since_lowest']<=44
A_ratio_gt5   = lambda r: r['buy_sell_ratio4']>5
A_buyL_recent = lambda r: r['buy_L_recent']==1
A_no_buysmc   = lambda r: r['buy_after_smc']==0
A_ny          = lambda r: r['is_ny_overlap']==1

print(f'BASE n={N} WR={WR_BASE:.3f} streak={STREAK_BASE} yr_base={{2024:{YR_BASE[2024]:.1f},2025:{YR_BASE[2025]:.1f},2026:{YR_BASE[2026]:.1f}}}')

fin=[]
# F1: highest WR robust
fin.append(report(lambda r: not (A_flow_flat(r) and A_lowest_fresh(r)), 'F1 CUT[flow_flat & lowest_fresh]'))
# F2: high WR + good streak
fin.append(report(lambda r: not (A_ratio_gt5(r) and A_flow_flat(r)), 'F2 CUT[ratio_gt5 & flow_flat]'))
# F3: lens, lowest streak (21)
fin.append(report(lambda r: not (A_no_buysmc(r) and A_buyL_recent(r)), 'F3 CUT[no_buyaftersmc & buyL_recent] (LENS)'))
# F4: lens variant streak 21
fin.append(report(lambda r: not (A_buyL_recent(r) and A_ny(r)), 'F4 CUT[buyL_recent & ny_overlap]'))

# JOINT: union the WR-king (F1) with the streak-helper (F3) to chase both
fin.append(report(lambda r: not ((A_flow_flat(r) and A_lowest_fresh(r)) or (A_no_buysmc(r) and A_buyL_recent(r))),
                  'JOINT CUT[(flow_flat&lowest_fresh) | (no_buyaftersmc&buyL_recent)]'))
fin.append(report(lambda r: not ((A_ratio_gt5(r) and A_flow_flat(r)) or (A_no_buysmc(r) and A_buyL_recent(r))),
                  'JOINT CUT[(ratio_gt5&flow_flat) | (no_buyaftersmc&buyL_recent)]'))

import json as J
print('\nJSON_FINALISTS=' + J.dumps(fin))
