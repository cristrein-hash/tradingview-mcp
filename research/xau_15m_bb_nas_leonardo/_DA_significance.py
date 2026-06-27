#!/usr/bin/env python3
"""Significance / power for the finalists' WR lift.
(a) Wilson 95% CI on each finalist WR.
(b) Is B's WR (66.1, N189) distinguishable from the single-h1_eff WR (62.6, N211)?
    -> two-proportion z-test (NOT independent samples, overlapping pools; so treat as upper bound on signal).
(c) Power: with N~200 and base WR~58, what WR drop is detectable? min detectable effect at 80% power.
(d) Selection penalty: the prompt says 'dozens of combos tried'. Bonferroni-style: how many of B's
    incremental conditions survive if we demand p<0.05/K for K=20,40 tested combos.
All deterministic except bootstrap which is seeded."""
import json, math, random, importlib.util
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('fh',HERE/'filter_harness.py')
fh=importlib.util.module_from_spec(spec); spec.loader.exec_module(fh)

def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(100*(c-h),1),round(100*(c+h),1))

def run(e):
    s,taken=fh.run(eval('lambda r: ('+e+')')); return s,taken

E={'h1_eff':"r['h1_eff']>=0.15",
   'A':"r['h1_eff']>=0.15 and r['rsi']>50",
   'B':"r['h1_eff']>=0.15 and (r['buy_bub_w_leg']<=3*r['sell_bub_w_leg']+5) and r['rsi']>50",
   'C':"r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=3 and r['dist_ema_atr']<=4"}

print('### (a) Wilson 95% CI on WR ###')
print(f"BASE   N={fh.BASE['n']} WR={fh.BASE['wr']} CI={wilson(fh.BASE['winners'],fh.BASE['n'])}")
res={}
for k,e in E.items():
    s,taken=run(e); res[k]=(s,taken)
    print(f"{k:<6} N={s['n']} WR={s['wr']} CI={wilson(s['winners'],s['n'])} sumR={s['sumr']}")
print()

print('### (b) B vs single-h1_eff WR: two-proportion z (overlapping pools -> optimistic) ###')
sh,_=res['h1_eff']; sb,_=res['B']
p1=sh['winners']/sh['n']; p2=sb['winners']/sb['n']
pp=(sh['winners']+sb['winners'])/(sh['n']+sb['n'])
se=math.sqrt(pp*(1-pp)*(1/sh['n']+1/sb['n']))
z=(p2-p1)/se; from math import erf
pval=2*(1-0.5*(1+erf(abs(z)/math.sqrt(2))))
print(f"p1(h1_eff)={p1:.3f} p2(B)={p2:.3f} z={z:.2f} p={pval:.3f}  (samples overlap heavily -> this OVERSTATES signal)")
print()

print('### (c) Min detectable WR drop at 80% power, N=200, base p=0.584 ###')
# crude: effect size for two-prop at alpha .05, power .8 ~ (1.96+0.84)^2 * 2pq / n
p=0.584; n=200; za=1.96; zb=0.84
mde=(za+zb)*math.sqrt(2*p*(1-p)/n)
print(f"MDE(WR) ~ {100*mde:.1f} pp. -> a single year/block (N~25) cannot detect <~28pp swings; year-level WR noise is large.")
print()

print('### (d) Bootstrap: P(B-WR > h1_eff-WR) resampling trades within each kept set (seeded) ###')
random.seed(42)
_,tb=res['B']; _,th=res['h1_eff']
rb=[c['win'] for c in tb]; rh=[c['win'] for c in th]
def bwr(x):
    s=[x[random.randrange(len(x))] for _ in x]; return sum(s)/len(s)
cnt=sum(1 for _ in range(5000) if bwr(rb)>bwr(rh))
print(f"P(bootstrap B-WR > bootstrap h1_eff-WR) = {cnt/5000:.3f}  (50% = pure noise; high = consistent)")
print()

print('### Per-year Wilson CI for each finalist (does any year dip below base 58.4?) ###')
for k,e in E.items():
    _,taken=res[k]
    yr={}
    for c in taken: yr.setdefault(c['yr'],[0,0]); yr[c['yr']][0]+=1; yr[c['yr']][1]+=c['win']
    parts=[f"{y}:N{v[0]} WR{round(100*v[1]/v[0],1)} CI{wilson(v[1],v[0])}" for y,v in sorted(yr.items())]
    print(f"{k:<6} "+" | ".join(parts))
