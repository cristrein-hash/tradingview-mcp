#!/usr/bin/env python3
"""R2 lapidacao - FINAL verification of best contextual cut-unions.
RAW-causal. Only r2_keep==1. win=R>0. Sort by low_t. Independent recompute.
Reports full block table + winners-cut audit (which winners lost) per rule.
"""
import json
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]
KEPT.sort(key=lambda r: r['low_t'])
N = len(KEPT); W_TOT = sum(r['win'] for r in KEPT); WR_BASE = 100*W_TOT/N
LOS_TOT = N - W_TOT

def year_wr(rows):
    yr = defaultdict(lambda: [0,0])
    for r in rows: yr[r['yr']][0]+=1; yr[r['yr']][1]+=r['win']
    return {y:100*w/n for y,(n,w) in yr.items()}
YBASE = year_wr(KEPT)
def block_stat(rows):
    bl = defaultdict(lambda: [0,0])
    for r in rows: bl[r['block']][0]+=1; bl[r['block']][1]+=r['win']
    return {b:(n,100*w/n) for b,(n,w) in bl.items()}
BBASE = block_stat(KEPT); BLOCKS = sorted(BBASE)
def streak(rows):
    s=mx=0
    for r in rows:
        if r['win']==0: s+=1; mx=max(mx,s)
        else: s=0
    return mx
STREAK_BASE = streak(KEPT)

def C(name, r):
    if name=='absorb&sd_zero':   return r['absorption']==1 and r['sell_decel']==0.0
    if name=='reg_young&skew':   return r['regime_age_h']<=25.2 and r['sell_skew_mig']>0
    if name=='bsr4_vhot&vol_hi': return r['buy_sell_ratio4']>7 and r['low_vol_rel']>1.37
    if name=='vol_hi&sd_zero':   return r['low_vol_rel']>1.37 and r['sell_decel']==0.0
    if name=='buyL&skew':        return r['buy_L_recent']==1 and r['sell_skew_mig']>0
    if name=='flow_zero&vol_hi': return r['flow_accel']==0 and r['low_vol_rel']>1.37
    if name=='bsr4_vhot&skew':   return r['buy_sell_ratio4']>7 and r['sell_skew_mig']>0
    if name=='flow_dead&absorb': return (-2 < r['flow_accel'] <= 0) and r['absorption']==1
    raise KeyError(name)

# Final candidate rules (representatives of the robust family, distinct emphasis)
RULES = {
    'R_A (overheat+vol+young-exhaust)': ['bsr4_vhot&vol_hi','vol_hi&sd_zero','reg_young&skew'],
    'R_B (absorb+overheat+young-exhaust, 8/8)': ['absorb&sd_zero','bsr4_vhot&vol_hi','reg_young&skew'],
    'R_C (absorb+vol+buyL-exhaust, 8/8)': ['absorb&sd_zero','vol_hi&sd_zero','buyL&skew'],
    'R_D (skew-trio: vhot/young/vol)': ['bsr4_vhot&skew','reg_young&skew','flow_zero&vol_hi'],
}

def keep_after(parts):
    return [r for r in KEPT if not any(C(p,r) for p in parts)]

print(f"BASE n={N} WR={WR_BASE:.3f} streak={STREAK_BASE}")
print(f"  year base: 2024={YBASE[2024]:.2f} 2025={YBASE[2025]:.2f} 2026={YBASE[2026]:.2f}")
print("  block base: " + " ".join(f"{b}:{BBASE[b][1]:.1f}(n{BBASE[b][0]})" for b in BLOCKS))

for nm, parts in RULES.items():
    keep = keep_after(parts)
    nk=len(keep); wk=sum(r['win'] for r in keep); wr=100*wk/nk
    winK=100*wk/W_TOT; losC=100*(LOS_TOT-(nk-wk))/LOS_TOT
    yk=year_wr(keep); bk=block_stat(keep)
    sk=streak(keep)
    nw=sum(1 for b in BLOCKS if bk[b][1]>=BBASE[b][1]-1e-9)
    # winners cut
    cut = [r for r in KEPT if any(C(p,r) for p in parts)]
    win_cut = sum(r['win'] for r in cut); los_cut = len(cut)-win_cut
    robust=(wr>WR_BASE and all(yk[y]>=YBASE[y]-1e-9 for y in YBASE)
            and winK>=85.0 and nw>=6 and sk<STREAK_BASE)
    print(f"\n### {nm}")
    print(f"  parts: {parts}")
    print(f"  n_keep={nk} wr_keep={wr:.2f} streak_keep={sk} winners_kept_pct={winK:.1f} losers_cut_pct={losC:.1f}")
    print(f"  cut total={len(cut)} (winners_cut={win_cut} losers_cut={los_cut} => purity {100*los_cut/len(cut):.0f}% losers)")
    print(f"  WR by year: 2024={yk[2024]:.2f}(b{YBASE[2024]:.2f}) 2025={yk[2025]:.2f}(b{YBASE[2025]:.2f}) 2026={yk[2026]:.2f}(b{YBASE[2026]:.2f})")
    print(f"  blocks not-worse: {nw}/8")
    for b in BLOCKS:
        d = bk[b][1]-BBASE[b][1]
        print(f"    {b}: {bk[b][1]:.1f} (base {BBASE[b][1]:.1f}, d{d:+.1f}, n{bk[b][0]})")
    print(f"  ROBUST={robust}")
