#!/usr/bin/env python3
"""
_reopt5_da_audit.py — Devil's Advocate audit of the top robust 5ATR cut-stacks.

Questions interrogated EMPIRICALLY (no chart access here; classifier-level audit):
  1. Look-ahead: features used are MULTI-TF h*/OB/VOL/PERNA/15M/FLOW. None of the
     cut predicates here use forward info — all are state-at-bar (dist_supply_atr,
     vpnode_dist_atr, disp4_atr, h1_dist, demand fields). Documented, not look-ahead.
  2. In-sample contamination: thresholds (-0.28, 1.07, 0.78, 1.43) were taken from
     decile scan on THESE rows. So robustness must come from STABILITY across
     year+block, not from the in-sample WR. We test sensitivity to threshold jitter.
  3. Selection bias: ~100 combos tested -> 17 'robust'. We apply Bonferroni-style
     binomial test: is wr_keep significantly > base given n_keep? and threshold jitter.
  4. Power: n_keep ~2500, base 60.49 -> +2pp. We compute the binomial p and CI.
  5. Streak: report streak honestly (most barely move).
  6. The lift is small -> we report avgR too (economic, not just WR).

Verdict logic: a cut-stack 'survives DA' only if:
  - wr_keep CI lower bound (Wilson 90%) > base_wr (not just point estimate)  ... STRICT
    OR at minimum the +lift is stable under +/-20% threshold jitter on each numeric cut.
"""
import math, itertools
from _reopt5_harness import ROWS, BASE_WR, evaluate, BASE_YR

def g(r,k,d=None):
    v=r.get(k); return d if v is None else v

# numeric cut builders parameterized by threshold so we can jitter
def into_supply(t):   return lambda r: g(r,'dist_supply_atr',99) < t      # base -0.28
def at_node(t):       return lambda r: g(r,'vpnode_dist_atr',99) < t       # base 1.07
def no_disp(t):       return lambda r: g(r,'disp4_atr',99) < t             # base 0.78
def h1_compress(t):   return lambda r: g(r,'h1_dist',99) < t               # base 1.43
def rsi_weak(t):      return lambda r: g(r,'rsi',99) < t                   # base 55.9
def not_in_demand():  return lambda r: g(r,'in_demand',1)==0
def macro_bear():     return lambda r: g(r,'macro_bear',0)>=1
def not_fresh():      return lambda r: g(r,'demand_fresh',1)==0

def keep_not(preds):
    return lambda r: not any(p(r) for p in preds)

def wilson_low(k,n,z=1.645):  # 90% one-sided-ish lower bound
    if n==0: return 0.0
    p=k/n
    den=1+z*z/n
    centre=p+z*z/(2*n)
    adj=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)
    return 100*(centre-adj)/den

def binom_p_greater(k,n,p0):
    # one-sided normal approx: P(WR>=observed | base)
    mu=n*p0; sd=math.sqrt(n*p0*(1-p0))
    if sd==0: return 1.0
    z=(k-0.5-mu)/sd
    # survival of standard normal
    return 0.5*math.erfc(z/math.sqrt(2))

# Top candidates from _reopt5_ob.py (named), with parameterized numeric thresholds
CANDS = {
    'into_supply+no_disp':       lambda j=1.0: keep_not([into_supply(-0.28*j), no_disp(0.78*j)]),
    'at_node+no_disp':           lambda j=1.0: keep_not([at_node(1.07*j), no_disp(0.78*j)]),
    'into_supply+at_node':       lambda j=1.0: keep_not([into_supply(-0.28*j), at_node(1.07*j)]),
    'h1_compress+no_disp':       lambda j=1.0: keep_not([h1_compress(1.43*j), no_disp(0.78*j)]),
    'at_node+rsi_weak':          lambda j=1.0: keep_not([at_node(1.07*j), rsi_weak(55.9*j)]),
    'not_in_demand+macro_bear':  lambda j=1.0: keep_not([not_in_demand(), macro_bear()]),
}

print(f"BASE_WR={BASE_WR:.2f}  N_TESTS≈100 (Bonferroni alpha=0.05/100=0.0005)\n")
BONF = 0.05/100

for name, builder in CANDS.items():
    m = evaluate(builder(1.0), name)
    if not m:
        print(name,"EMPTY"); continue
    n=m['n_keep']; k=round(n*m['wr_keep']/100)
    wl=wilson_low(k,n)
    pv=binom_p_greater(k,n,BASE_WR/100)
    # threshold jitter +/-20%: re-evaluate, check still > base each year
    jit_ok=0; jit_tot=0; jit_wr=[]
    for j in (0.8,0.9,1.1,1.2):
        mj=evaluate(builder(j), name)
        if mj:
            jit_tot+=1
            jit_wr.append(round(mj['wr_keep'],2))
            if mj['wr_keep']>BASE_WR and all(mj['yr'][y]>=BASE_YR[y]-1e-9 for y in (2024,2025,2026)):
                jit_ok+=1
    print(f"{name}")
    print(f"  n={n} wr={m['wr_keep']} avgR={m['avgR']} streak30->{m['streak_keep']} winners_kept%={m['winners_kept_pct']} blocks={m['nonworse']}/8")
    print(f"  Wilson90 lower={wl:.2f} (>base? {wl>BASE_WR})  binom p(>base)={pv:.4f} (<Bonf {BONF}? {pv<BONF})")
    print(f"  jitter+/-20% wr={jit_wr}  stable_yr_ok={jit_ok}/{jit_tot}")
    survives = (wl>BASE_WR) or (jit_ok==jit_tot and m['robust'])
    print(f"  SURVIVES_DA={survives} (Wilson-lower>base OR full-jitter-stable+robust)\n")
