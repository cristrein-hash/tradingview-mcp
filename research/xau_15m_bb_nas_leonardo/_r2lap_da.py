#!/usr/bin/env python3
"""R2 lapidation - DEVIL'S ADVOCATE audit of top cut candidates.
Checks: (1) per-block detail, (2) winners actually cut, (3) selection-bias context,
(4) is lift within binomial noise, (5) leave-one-block-out stability.
RAW-causal, R2-KEPT only.
"""
import json, math
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = sorted([r for r in ROWS if r['r2_keep'] == 1], key=lambda r: r['low_t'])
N = len(KEPT); WINS = sum(r['win'] for r in KEPT); LOSERS = N - WINS
WR_BASE = 100 * WINS / N

def grp_base(key):
    g = defaultdict(lambda: [0, 0])
    for r in KEPT: g[r[key]][0]+=1; g[r[key]][1]+=r['win']
    return {k: 100*w/n for k,(n,w) in g.items()}
YR_BASE = grp_base('yr'); BL_BASE = grp_base('block')

def max_streak(rows):
    s=mx=0
    for r in rows:
        if r['win']==0: s+=1; mx=max(mx,s)
        else: s=0
    return mx
STREAK_BASE = max_streak(KEPT)

# The most stable / highest winners-kept robust candidates worth a real look:
CANDS = {
    # widest losers-cut + nb8 (every block not-worse) + decent winners
    'A_absorb_sellstale': lambda r: r['absorption']==1 and r['bars_since_sell']>40,
    # highest WR robust
    'B_ratio_sell_regime': lambda r: r['buy_sell_ratio4']>5.0 and r['bars_since_sell']>40 and r['regime_age_h']<=25.2,
    # nb8 flow+lowest
    'C_flow0_lowestfresh': lambda r: r['flow_accel']==0 and r['bars_since_lowest']<=44,
    # ratio+flow simple 2-feat
    'D_ratio_flow0': lambda r: r['buy_sell_ratio4']>5.0 and r['flow_accel']==0,
    # lowvol+regime young (my-lens vacuum)
    'E_lowvol_regimeyng': lambda r: r['low_vol_rel']>1.37 and r['regime_age_h']<=25.2,
}

def binom_z(k, n, p):
    # normal-approx z-score of observed wins k vs base p
    mu = n*p; sd = math.sqrt(n*p*(1-p))
    return (k-mu)/sd if sd>0 else 0.0

def audit(name, cut):
    kept = [r for r in KEPT if not cut(r)]
    cutr = [r for r in KEPT if cut(r)]
    nk=len(kept); wk=sum(r['win'] for r in kept); wr=100*wk/nk
    n_cut=len(cutr); w_cut=sum(r['win'] for r in cutr); wr_cut=100*w_cut/n_cut if n_cut else 0
    winners_kept=100*wk/WINS; losers_cut=100*(LOSERS-(nk-wk))/LOSERS
    streak=max_streak(kept)
    print(f'\n### {name}')
    print(f'  KEPT n{nk} wr{wr:.2f} (base{WR_BASE:.2f}) streak{streak}(base{STREAK_BASE}) '
          f'winners_kept{winners_kept:.1f}% losers_cut{losers_cut:.1f}%')
    print(f'  CUT  n{n_cut} wr{wr_cut:.1f} (winners cut={w_cut}, losers cut={n_cut-w_cut})')
    # DA4: is the CUT pocket genuinely loser-dense vs noise?
    # P(observing this many losers in cut pocket under base WR)
    p_lose_base = 1-WR_BASE/100
    exp_losers = n_cut*p_lose_base; obs_losers=n_cut-w_cut
    print(f'  CUT-pocket loser-enrichment: obs_losers={obs_losers} exp@base={exp_losers:.1f} '
          f'lift={obs_losers/exp_losers:.2f}x')
    # z-score of kept-WR vs base (how surprising; small => within noise)
    z = binom_z(wk, nk, WR_BASE/100)
    print(f'  kept-WR z vs base = {z:.2f} (|z|<1.96 => within noise)')
    # per block
    bk=defaultdict(lambda:[0,0])
    for r in kept: bk[r['block']][0]+=1; bk[r['block']][1]+=r['win']
    line=[]
    nb_worse=0
    for b in sorted(BL_BASE):
        if b in bk and bk[b][0]>0:
            w=100*bk[b][1]/bk[b][0]; d=w-BL_BASE[b]
            if d < -1e-9: nb_worse+=1
            line.append(f'{b[2:]}:{w:.0f}({d:+.1f})')
    print('  blocks ' + ' '.join(line) + f'  [worse={nb_worse}/8]')
    # per year
    yk=defaultdict(lambda:[0,0])
    for r in kept: yk[r['yr']][0]+=1; yk[r['yr']][1]+=r['win']
    print('  years ' + ' '.join(f'{y}:{100*yk[y][1]/yk[y][0]:.1f}(base{YR_BASE[y]:.1f})' for y in sorted(yk)))
    # DA: leave-one-block-out -- does lift survive removing each block?
    los=[]
    for drop in sorted(BL_BASE):
        sub=[r for r in KEPT if r['block']!=drop]
        base_sub=100*sum(x['win'] for x in sub)/len(sub)
        ks=[r for r in sub if not cut(r)]
        wr_s=100*sum(x['win'] for x in ks)/len(ks)
        los.append(wr_s-base_sub)
    print(f'  LOBO lift range: min{min(los):+.2f} max{max(los):+.2f} '
          f'(all>0={all(x>0 for x in los)})')

def main():
    print(f'BASE n={N} WR={WR_BASE:.3f} streak={STREAK_BASE} W={WINS} L={LOSERS}')
    print('DA context: ~250+ combos scanned (2&3-feat AND, OR). Bonferroni-aware: '
          'best raw WR=70.9 = +2.4pp. Selection over ~250 tests => need lift robust to LOBO.')
    for name, cut in CANDS.items():
        audit(name, cut)

if __name__ == '__main__':
    main()
