#!/usr/bin/env python3
"""DA follow-up: is LBB's 38% runner carried by the demand_defended+acceptance_above pair, and is
that pair itself outcome-correlated by construction across the WHOLE base (Q9b)? Diagnostic only.
Reconstructs raw evidence booleans from path/engine/decision CSVs (same logic as main evidence())
to test factor-outcome correlation independent of state assignment. Outcome EVAL-only."""
import csv, math
from collections import Counter
D="results"
dspa={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
EP=sorted(dspa); N=len(EP)
MFE={b:float(unc[b]['mfe_R']) for b in EP}
def run(b): return MFE[b]>=5
baseR=sum(1 for b in EP if run(b))/N

# raw booleans (mirror main evidence(), no outcome)
def demand_defended(b):
    d=dec[b]; e=eng[b]; return d.get('demand')=='DEMAND_DEFENDED' or e.get('demand')=='DEMAND_DEFENDED'
def acceptance_above(b):
    p=dspa[b]; return p.get('f3_acceptance_state')=='ACCEPTED_ABOVE_RES' or p.get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE'
def bear_ctx(b):
    d=dec[b]; e=eng[b]; p=dspa[b]; leg=d.get('macro_reader_leg','')
    return leg=='MACRO_BEAR_LEG' or e.get('regime') in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or p.get('f7_regime_traj') in('REGIME_STABLE_BEAR','REGIME_DETERIORATING')

def cell(pred, universe=None):
    bs=[b for b in (universe or EP) if pred(b)]
    if not bs: return (0,0,0.0)
    r=sum(1 for b in bs if run(b)); return (len(bs),r,r/len(bs))

print(f"base N={N} runner_rate={100*baseR:.1f}%\n")
print("=== Q9b: are demand_defended / acceptance_above outcome-correlated BY CONSTRUCTION (whole base)? ===")
for nm,pr in [('demand_defended',demand_defended),('acceptance_above',acceptance_above),
              ('BOTH(dd&aa)',lambda b:demand_defended(b) and acceptance_above(b))]:
    n,r,rp=cell(pr)
    n0,r0,rp0=cell(lambda b: not pr(b))
    print(f"  {nm:18} WITH n={n:>3} run%={100*rp:>3.0f} lift={rp/baseR:4.2f}  | WITHOUT n={n0:>3} run%={100*rp0:>3.0f} lift={rp0/baseR:4.2f}")

print("\n=== same, RESTRICTED to bear_context universe (where LBB lives) ===")
BU=[b for b in EP if bear_ctx(b)]; bbase=sum(1 for b in BU if run(b))/len(BU)
print(f"  bear_context universe: n={len(BU)} runner_rate={100*bbase:.1f}%")
for nm,pr in [('demand_defended',demand_defended),('acceptance_above',acceptance_above),
              ('BOTH(dd&aa)',lambda b:demand_defended(b) and acceptance_above(b))]:
    n,r,rp=cell(pr,BU); n0,r0,rp0=cell(lambda b: not pr(b),BU)
    print(f"  {nm:18} WITH n={n:>3} run%={100*rp:>3.0f} lift={rp/bbase:4.2f}  | WITHOUT n={n0:>3} run%={100*rp0:>3.0f} lift={rp0/bbase:4.2f}")

# de-facto gate test: in bear_context, does (dd & aa) ALONE already reproduce ~LBB separation,
# i.e. are the OTHER 8 LBB supports cosmetic?
print("\n=== de-facto 2-factor gate: bear_context & demand_defended & acceptance_above ===")
g=[b for b in BU if demand_defended(b) and acceptance_above(b)]
gr=sum(1 for b in g if run(b))
print(f"  n={len(g)} runner%={100*gr/len(g) if g else 0:.0f} lift_vs_bearbase={gr/len(g)/bbase if g else 0:.2f}")
print("  (compare to LBB n=37 38% — if ~equal, the 8 extra supports add little; the pair IS the axis)")

# hypergeometric for this pair-gate
def hyper_sf(k,Npop,K,n):
    def logC(a,b):
        if b<0 or b>a: return -math.inf
        return math.lgamma(a+1)-math.lgamma(b+1)-math.lgamma(a-b+1)
    tot=logC(Npop,n)
    return sum(math.exp(logC(K,x)+logC(Npop-K,n-x)-tot) for x in range(k,min(K,n)+1))
K=sum(1 for b in EP if run(b))
print(f"  hypergeometric P(>= {gr} runners | n={len(g)}, base universe={N}) = {hyper_sf(gr,N,K,len(g)):.4f}")
print("\nDONE _DA_dspa_agg_carrier_test.")
