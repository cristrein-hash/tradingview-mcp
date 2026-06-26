#!/usr/bin/env python3
"""Streak honesty check: max consecutive losses, both global-time-sorted and per-block,
for R2-kept base vs R_B-keep."""
import json
ROWS=[json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT=[r for r in ROWS if r['r2_keep']==1]
def is_cut(r):
    return ((r['absorption']==1 and r['sell_decel']==0)
            or (r['buy_sell_ratio4']>7 and r['low_vol_rel']>1.37)
            or (r['regime_age_h']<=25.2 and r['sell_skew_mig']>0))
def streak_global(sub):
    s=sorted(sub,key=lambda r:r['low_t']); cur=best=0
    for r in s:
        if r['win']==0: cur+=1; best=max(best,cur)
        else: cur=0
    return best
def streak_perblock(sub):
    best=0
    for blk in sorted(set(r['block'] for r in sub)):
        bs=sorted([r for r in sub if r['block']==blk],key=lambda r:r['low_t']); cur=0
        for r in bs:
            if r['win']==0: cur+=1; best=max(best,cur)
            else: cur=0
    return best
keep=[r for r in KEPT if not is_cut(r)]
print('base streak global %d  per-block %d'%(streak_global(KEPT),streak_perblock(KEPT)))
print('keep streak global %d  per-block %d'%(streak_global(keep),streak_perblock(keep)))
