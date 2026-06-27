#!/usr/bin/env python3
"""
_engine_DA_audit.py — Devil's Advocate audit of the candidate robust rules.

Checks per rule:
  1. ex-top2 AND ex-top5 avgR (carried by few trades?)
  2. WR per year + n per year (stability of sign)
  3. median R (not just mean) -> is the edge in the body or tail?
  4. threshold neighborhood (perturb +-20% the numeric threshold; sign stays?)
  5. causality sanity: in_demand uses zones born_t<=low_t; sweep2 uses swing lows < i; retest uses k<=i-10 -> all causal.

Selection-bias note: ~60 single thresholds + ~14 combos scanned. These are NOT Bonferroni-survivors
in a hard sense; the defense is sign-stability across 3 disjoint years (out-of-period within-asset),
which is the project's accepted validation (no OOS/cross-asset).
"""
import json, os
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in open(os.path.join(HERE,'entry_dataset_novel.jsonl'))]
BASE=0.727

def stats(sel,label):
    n=len(sel); R=[r['R_reclaim'] for r in sel]
    avg=sum(R)/n; med=sorted(R)[n//2]
    wr=100*sum(1 for x in R if x>0)/n
    Rs=sorted(R,reverse=True)
    ex2=sum(Rs[2:])/(n-2); ex5=sum(Rs[5:])/(n-5)
    print('%-34s n=%4d WR=%4.1f%% avgR=%+.3f med=%+.2f exT2=%+.3f exT5=%+.3f'%(label,n,wr,avg,med,ex2,ex5))
    for y in (2024,2025,2026):
        ys=[r for r in sel if r['yr']==y]; Ry=[r['R_reclaim'] for r in ys]
        if Ry:
            print('     y%d n=%3d WR=%4.1f%% avgR=%+.3f'%(y,len(ys),100*sum(1 for x in Ry if x>0)/len(ys),sum(Ry)/len(ys)))

RULES={
 'disp4<=-0.65 & in_demand': lambda r: r['disp4_atr']<=-0.649 and r.get('in_demand')==1,
 'drop<=3.6 & in_demand'   : lambda r: r['macro_drop_atr']<=3.606 and r.get('in_demand')==1,
 'drop<=3.6 & retest_lo'   : lambda r: r['macro_drop_atr']<=3.606 and r.get('retest_lo')==1,
 'drop<=3.6 & sweep2'      : lambda r: r['macro_drop_atr']<=3.606 and r.get('sweep2')==1,
 'macro_drop_atr<=3.606'   : lambda r: r['macro_drop_atr']<=3.606,
 'disp4_atr<=-0.649'       : lambda r: r['disp4_atr']<=-0.649,
}
print('=== DA: per-rule deep stats ===')
for lab,m in RULES.items():
    stats([r for r in rows if m(r)],lab)
    print()

print('=== threshold neighborhood perturbation (+-20%) ===')
for d in (0.8*3.606, 3.606, 1.2*3.606):
    sel=[r for r in rows if r['macro_drop_atr']<=d and r.get('in_demand')==1]
    R=[r['R_reclaim'] for r in sel]
    yy={y:np.mean([r['R_reclaim'] for r in sel if r['yr']==y]) for y in (2024,2025,2026)}
    print('drop<=%.2f & in_demand  n=%d avgR=%+.3f  y24=%+.2f y25=%+.2f y26=%+.2f'%(d,len(sel),np.mean(R),yy[2024],yy[2025],yy[2026]))
for d in (1.2*-0.649,-0.649,0.8*-0.649):
    sel=[r for r in rows if r['disp4_atr']<=d and r.get('in_demand')==1]
    R=[r['R_reclaim'] for r in sel]
    yy={y:np.mean([r['R_reclaim'] for r in sel if r['yr']==y]) for y in (2024,2025,2026)}
    print('disp4<=%.3f & in_demand n=%d avgR=%+.3f  y24=%+.2f y25=%+.2f y26=%+.2f'%(d,len(sel),np.mean(R),yy[2024],yy[2025],yy[2026]))

print()
print('=== combined triple: discount + structure ===')
# the convergent reading: discount (disp4 negative) AND structure (in_demand) AND not-overextended drop
tri=lambda r: r['disp4_atr']<=-0.649 and r.get('in_demand')==1 and r['macro_drop_atr']<=5.165
stats([r for r in rows if tri(r)],'disp4<=-0.65 & in_demand & drop<=5.2')
print()
# proportion of universe that in_demand covers (is it just "almost everything"?)
print('in_demand coverage: %d/%d = %.0f%%'%(sum(1 for r in rows if r.get('in_demand')==1),len(rows),100*sum(1 for r in rows if r.get('in_demand')==1)/len(rows)))
print('disp4<=-0.649 coverage: %d/%d = %.0f%%'%(sum(1 for r in rows if r['disp4_atr']<=-0.649),len(rows),100*sum(1 for r in rows if r['disp4_atr']<=-0.649)/len(rows)))
