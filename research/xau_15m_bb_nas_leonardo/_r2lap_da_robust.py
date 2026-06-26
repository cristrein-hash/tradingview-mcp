#!/usr/bin/env python3
"""R2 lapidacao - DEVIL'S ADVOCATE robustness on R_B / R_C.
RAW-causal. Only r2_keep==1. win=R>0. Sort by low_t.
Checks: (1) threshold sensitivity +-20%; (2) leave-one-block-out WR lift;
(3) streak = does removing top block kill the WR gain.
"""
import json
from collections import defaultdict

ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT = [r for r in ROWS if r['r2_keep'] == 1]
KEPT.sort(key=lambda r: r['low_t'])
N=len(KEPT); W=sum(r['win'] for r in KEPT); WRB=100*W/N
BLOCKS=sorted(set(r['block'] for r in KEPT))

def wr(rows): return 100*sum(r['win'] for r in rows)/len(rows) if rows else 0
def streak(rows):
    s=mx=0
    for r in rows:
        if r['win']==0: s+=1; mx=max(mx,s)
        else: s=0
    return mx

def make_RB(va_thr, bsr_thr, vol_thr):
    def cut(r):
        return ((r['absorption']==1 and r['sell_decel']==0.0) or
                (r['buy_sell_ratio4']>bsr_thr and r['low_vol_rel']>vol_thr) or
                (r['regime_age_h']<=va_thr and r['sell_skew_mig']>0))
    return cut

print(f"BASE WR={WRB:.2f}")
print("\n=== R_B threshold sensitivity (reg_age, bsr, vol) ===")
base = (25.2, 7, 1.37)
for label, params in [
    ('base', (25.2,7,1.37)),
    ('reg-20%', (20.2,7,1.37)), ('reg+20%', (30.2,7,1.37)),
    ('bsr 6', (25.2,6,1.37)), ('bsr 8', (25.2,8,1.37)),
    ('vol-20%', (25.2,7,1.10)), ('vol+20%', (25.2,7,1.64)),
]:
    cut=make_RB(*params)
    keep=[r for r in KEPT if not cut(r)]
    wk=100*sum(r['win'] for r in keep)/len(keep)
    winK=100*sum(r['win'] for r in keep)/W
    print(f"  {label:10s} {params}: n={len(keep)} WR={wk:.2f} winK={winK:.1f}% strk={streak(keep)}")

print("\n=== R_B leave-one-block-out (WR lift on remaining blocks) ===")
cut=make_RB(*base)
for drop in BLOCKS:
    sub=[r for r in KEPT if r['block']!=drop]
    keep=[r for r in sub if not cut(r)]
    base_sub=wr(sub); keep_sub=wr(keep)
    print(f"  drop {drop}: base={base_sub:.2f} -> kept={keep_sub:.2f} (lift {keep_sub-base_sub:+.2f})")

print("\n=== component marginal contribution (R_B) ===")
comps={
 'absorb&sd_zero': lambda r: r['absorption']==1 and r['sell_decel']==0.0,
 'bsr4_vhot&vol_hi': lambda r: r['buy_sell_ratio4']>7 and r['low_vol_rel']>1.37,
 'reg_young&skew': lambda r: r['regime_age_h']<=25.2 and r['sell_skew_mig']>0,
}
for nm,fn in comps.items():
    keep=[r for r in KEPT if not fn(r)]
    g=[r for r in KEPT if fn(r)]
    print(f"  {nm}: alone cut_n={len(g)} cut_WR={wr(g):.1f} -> keep WR={wr(keep):.2f} winK={100*sum(r['win'] for r in keep)/W:.1f}%")
