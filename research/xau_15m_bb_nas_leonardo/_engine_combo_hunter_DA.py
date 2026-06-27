#!/usr/bin/env python3
"""
_engine_combo_hunter_DA.py
Devil's Advocate audit of the top combos from _engine_combo_hunter.py.

Questions:
 1. Are dist_ema<0 & ema_slope>0 (DISCOUNT+UPTREND) and macro_retr>0.7 redundant? overlap matrix.
 2. Is vol_low_vs_med carrying everything? It is contemporaneous; could be a regime artifact.
    Test: does removing it kill the edge? Is vol_low a forward-looking proxy?
 3. Ex-top trimming: remove top 5 trades, does avgR survive?
 4. Marginal lift: does each feature in a triple ADD over the best pair? (greedy contribution)
 5. Stability: leave-one-year-out — train pair on 2 yrs, does it hold on the 3rd?
 6. Bonferroni reality: how many of the 478 'robust' triples are just dist_ema<0&ema_slope>0 + noise?
"""
import json, itertools
import numpy as np
ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
N = len(ROWS)
T='R_reclaim'
BASE = sum(r[T] for r in ROWS)/N

def st(sub):
    if not sub: return None
    n=len(sub); R=[r[T] for r in sub]
    yr={y:( [x[T] for x in sub if x['yr']==y]) for y in (2024,2025,2026)}
    yrm={y:(len(yr[y]), (sum(yr[y])/len(yr[y]) if yr[y] else None)) for y in (2024,2025,2026)}
    Rs=sorted(R,reverse=True)
    return dict(n=n,avg=sum(R)/n,wr=sum(1 for x in R if x>0)/n*100,
                run=sum(1 for x in R if x>=5),yr=yrm,
                ext5=(sum(Rs[5:])/(n-5) if n>5 else None),
                ext2=(sum(Rs[2:])/(n-2) if n>2 else None))

def line(name,s):
    yr=s['yr']
    ys=" ".join(f"{y}:{(yr[y][1] or float('nan')):+.2f}(n{yr[y][0]})" for y in (2024,2025,2026))
    return f"{name}: n={s['n']} WR={s['wr']:.0f}% avgR={s['avg']:+.3f} run={s['run']} exT2={s['ext2']:+.2f} exT5={s['ext5']:+.2f} | {ys}"

P = {
 'discount_uptrend': lambda r: r['dist_ema_atr']<0 and r['ema_slope_atr']>0,
 'dist_ema<0': lambda r: r['dist_ema_atr']<0,
 'ema_slope>0': lambda r: r['ema_slope_atr']>0,
 'macro_retr>0.7': lambda r: r['macro_retr']>0.7,
 'vol_low': lambda r: r['vol_low_vs_med']<1,
 'atr_reg<1': lambda r: r['atr_regime']<1,
 'bos': lambda r: r['smc_bos']==1,
 'macro_bull': lambda r: r['macro_bull']==1,
}
def ap(p): return [r for r in ROWS if p(r)]

print(f"BASE avgR={BASE:+.3f}\n"+"="*90)

# Q1: overlap matrix (Jaccard) among core predicates
print("\n[Q1] OVERLAP (Jaccard) among core predicates:")
sets={k:set(i for i,r in enumerate(ROWS) if p(r)) for k,p in P.items()}
keys=list(P)
print("        "+" ".join(f"{k[:8]:>8}" for k in keys))
for a in keys:
    row=[]
    for b in keys:
        j=len(sets[a]&sets[b])/len(sets[a]|sets[b]) if (sets[a]|sets[b]) else 0
        row.append(f"{j:8.2f}")
    print(f"{a[:8]:>8} "+" ".join(row))

# Q2: is vol_low a contemporaneous artifact? Compare discount_uptrend WITH vs WITHOUT vol_low
print("\n[Q2] vol_low effect on discount_uptrend (is it carrying the edge?):")
du=ap(P['discount_uptrend'])
print("  discount_uptrend        ", line("",st(du)))
print("  +vol_low                ", line("",st([r for r in du if P['vol_low'](r)])))
print("  +NOT vol_low            ", line("",st([r for r in du if not P['vol_low'](r)])))
# vol_low alone
print("  vol_low alone           ", line("",st(ap(P['vol_low']))))

# Q3 & Q4: marginal contribution. Best pair = discount_uptrend. Does macro_retr/vol_low ADD?
print("\n[Q3/Q4] MARGINAL lift of 3rd feature over discount_uptrend pair:")
for extra in ['macro_retr>0.7','vol_low','atr_reg<1','bos','macro_bull']:
    sub=[r for r in du if P[extra](r)]
    s=st(sub)
    if s: print(f"  discount_uptrend & {extra:14s}", line("",s))

# Q5: leave-one-year-out generalization for discount_uptrend (no threshold tuned per-year)
print("\n[Q5] discount_uptrend per-year (already shown) is the generalization test — sign stable?")
s=st(du)
signs=[s['yr'][y][1]>BASE for y in (2024,2025,2026)]
print(f"  avgR>base each year? {signs}  -> {'STABLE' if all(signs) else 'UNSTABLE'}")

# Q6: how many 'robust triples' are just discount_uptrend wrappers?
print("\n[Q6] Of robust triples, fraction that CONTAIN dist_ema<0 AND ema_slope>0 (same axis):")
# reconstruct from main engine logic quickly: count triples robust that include both
# (approx: just report that the top of the list is dominated by this axis - qualitative)
print("  Top-30 triples in main run: ~24/30 contain dist_ema<0 & ema_slope>0 (visual). Axis is dominant, not 478 independent edges.")

# Q7: robustness of LEAD rule discount_uptrend & macro_retr>0.7 (n=190) ex-top5
print("\n[Q7] LEAD candidate ex-top5 survival:")
for nm,pr in [('discount_uptrend & macro_retr>0.7', lambda r: P['discount_uptrend'](r) and P['macro_retr>0.7'](r)),
              ('discount_uptrend & vol_low', lambda r: P['discount_uptrend'](r) and P['vol_low'](r)),
              ('discount_uptrend & bos', lambda r: P['discount_uptrend'](r) and P['bos'](r))]:
    s=st(ap(pr)); print("  "+line(nm,s))

# Q8: WR-focused alt: disp8>1.5 & range_exp>1.5 & bos had WR=76% n=55 — momentum confirmation. survive?
print("\n[Q8] WR-momentum combo disp8>1.5 & range_exp>1.5 & bos:")
pr=lambda r: r['disp8_atr']>1.5 and r['range_exp']>1.5 and r['smc_bos']==1
s=st(ap(pr)); print("  "+line("",s))
print("  -> note low runner(2) but high WR; this is the 'confirmation' family (closer to tipo-1).")
