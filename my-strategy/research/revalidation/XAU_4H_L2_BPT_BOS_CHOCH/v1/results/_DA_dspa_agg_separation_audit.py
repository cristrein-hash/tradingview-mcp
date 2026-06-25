#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit of DSPA Camada 4 aggregation (XAU 4H L2/BPT, base 276).
DIAGNOSTIC ONLY. Does NOT modify main files. Tests:
 (Q7) single-axis collapse — per primary state: distribution of #supports and #sources; LBB episode-level.
 (Q9a) Fisher exact / hypergeometric null on LEGITIMATE_BEAR_BUY runner concentration (n=37 vs base).
 (Q9b) single-support-removal sensitivity: which support, removed, collapses the LBB runner lift?
       + leave-one-out on the SEPARATION (LBB runner% - BPT runner%).
 (Q9c) P1/P2 temporal split of LBB vs BPT.
 outcome read for EVAL ONLY (mfe_R), never feeds state assignment (states already assigned in CSV).
Run from .../v1/  ->  python3 results/_DA_dspa_agg_separation_audit.py"""
import csv, json, math, random
from collections import Counter
D="results"

states={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_intermediate_states_276.csv"))}
ev={int(r['bar_idx']):json.loads(l) for r in [None] for l in []}  # placeholder
ev={}
for line in open(f"{D}/l2_bpt_dspa_intermediate_evidence_276.jsonl"):
    j=json.loads(line); ev[j['bar_idx']]=j
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
dspa={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
EP=sorted(states)
MFE={b:float(unc[b]['mfe_R']) for b in EP}
N=len(EP)
def is_run(b): return MFE[b]>=5
baseR=sum(1 for b in EP if is_run(b))/N

def grp(s): return [b for b in EP if states[b]['dspa_primary_state']==s]
def runpct(bs): return (sum(1 for b in bs if is_run(b))/len(bs)) if bs else 0.0

print("="*84)
print(f"DA AUDIT — base N={N} runner(mfe>=5) base_rate={100*baseR:.1f}% ({sum(1 for b in EP if is_run(b))} runners)")
print("="*84)

# ---- Q7: single-axis collapse check per state (uses #supports, #sources from evidence) ----
print("\n[Q7] CONVERGENCE MULTIPLICITY per primary state (supports & sources are pre-outcome):")
print(f"{'state':28}{'n':>4}{'minSup':>7}{'medSup':>7}{'minSrc':>7}{'medSrc':>7}{'%>=3src':>8}")
def med(xs):
    xs=sorted(xs); m=len(xs)//2
    return xs[m] if len(xs)%2 else (xs[m-1]+xs[m])/2
for s in sorted(set(states[b]['dspa_primary_state'] for b in EP)):
    bs=grp(s)
    sup=[len(ev[b]['supports']) for b in bs]
    src=[len(ev[b]['source_layers']) for b in bs]
    pct3=100*sum(1 for v in src if v>=3)/len(bs)
    print(f"{s:28}{len(bs):>4}{min(sup):>7}{med(sup):>7.1f}{min(src):>7}{med(src):>7.1f}{pct3:>8.0f}")

# ---- Q7 deep: LBB episode-level support composition ----
print("\n[Q7-deep] LEGITIMATE_BEAR_BUY (n=37) — per-episode support set (is any ONE factor universal?):")
lbb=grp('LEGITIMATE_BEAR_BUY')
supcnt=Counter()
for b in lbb:
    for f in ev[b]['supports']: supcnt[f]+=1
print(f"  support frequency across {len(lbb)} LBB episodes:")
for f,c in supcnt.most_common():
    print(f"    {f:24} {c:>3}/{len(lbb)}  ({100*c/len(lbb):.0f}%)")
# any single support present in 100%? that would be a de-facto single axis gate
universal=[f for f,c in supcnt.items() if c==len(lbb)]
print(f"  universal (100%) supports: {universal if universal else 'NONE'}")

# ---- Q9a: hypergeometric null on LBB runner concentration ----
def hyper_sf(k,Npop,K,n):
    # P(X>=k) hypergeometric; K=total runners in pop, n=group size, Npop=pop
    def logC(a,b):
        if b<0 or b>a: return -math.inf
        return math.lgamma(a+1)-math.lgamma(b+1)-math.lgamma(a-b+1)
    tot=logC(Npop,n); p=0.0
    for x in range(k,min(K,n)+1):
        p+=math.exp(logC(K,x)+logC(Npop-K,n-x)-tot)
    return p
Krun=sum(1 for b in EP if is_run(b))
lbb_run=sum(1 for b in lbb if is_run(b))
p_lbb=hyper_sf(lbb_run,N,Krun,len(lbb))
print(f"\n[Q9a] LBB runner concentration: {lbb_run}/{len(lbb)} = {100*lbb_run/len(lbb):.0f}% vs base {100*baseR:.0f}%")
print(f"  hypergeometric P(X>={lbb_run} runners in n={len(lbb)} draw) = {p_lbb:.4f}")
# vs BEAR_PULLBACK_TRAP directly (2x2 Fisher)
bpt=grp('BEAR_PULLBACK_TRAP')
a=lbb_run; b_=len(lbb)-lbb_run; c=sum(1 for x in bpt if is_run(x)); d=len(bpt)-c
def fisher2x2(a,b,c,d):
    n=a+b+c+d
    def logC(N,k): return math.lgamma(N+1)-math.lgamma(k+1)-math.lgamma(N-k+1)
    r1,r2,c1=a+b,c+d,a+c
    def pval_tbl(aa):
        bb=r1-aa; cc=c1-aa; dd=r2-cc
        if bb<0 or cc<0 or dd<0: return 0.0
        return math.exp(logC(r1,aa)+logC(r2,cc)-logC(n,c1))
    p0=pval_tbl(a); tot=0.0
    for aa in range(0,min(r1,c1)+1):
        pp=pval_tbl(aa)
        if pp<=p0*(1+1e-9): tot+=pp
    return tot
p_fish=fisher2x2(a,b_,c,d)
print(f"  LBB vs BPT 2x2 [{a},{b_};{c},{d}] Fisher two-sided p = {p_fish:.4f}")

# ---- Q9b: leave-one-support-out — does removing one support destroy the separation? ----
# We cannot re-run assignment without main code; instead test: drop episodes whose support set
# would empty/fall below convergence if support X removed -> proxy for fragility.
# Concrete proxy: for each support f, recompute LBB runner% on the SUBSET of LBB episodes that
# still satisfy convergence (>=2 supports from >=2 sources) WITHOUT f.
src_of={  # support -> source tag (mirror of main evidence sources)
 'sweep_low_reclaim':'dspa','swept_high_reject':'dspa','flush_V':'dspa','grind_down':'dspa','no_flush':'dspa',
 'acceptance_above':'dspa','rejected_at_res':'dspa','holding_support':'dspa','broke_support':'dspa',
 'structure_up':'dspa','structure_down':'dspa','structure_range':'dspa','svp_below':'dspa','premium':'dspa','discount':'dspa',
 'regime_deteriorating':'dspa','capit_climax':'macro','falling_knife':'macro','demand_defended':'macro',
 'supply_markup':'macro','supply_reject':'macro','fuel_low':'macro','momentum_exhaustion':'macro','momentum_strong':'macro',
 'bub_climax_bull':'ind','smc_choch_bull':'ind','nas_long':'ind','bull_div':'ind',
 'bottom_turn':'prior','clean_sky':'prior','macro_phase_bullrun':'prior','bl_refined_preserve':'prior','bl_refined_block':'prior'}
print("\n[Q9b] LEAVE-ONE-SUPPORT-OUT fragility on LBB (subset still convergent w/o factor f):")
print(f"{'drop_factor':24}{'n_remain':>9}{'run%':>7}{'lift':>7}")
lbb_supports=sorted(supcnt)
for f in lbb_supports:
    remain=[]
    for b in lbb:
        s=[x for x in ev[b]['supports'] if x!=f]
        srcs=set(src_of.get(x,'?') for x in s)
        if len(s)>=2 and len(srcs)>=2: remain.append(b)
    if remain:
        rp=runpct(remain)
        print(f"{f:24}{len(remain):>9}{100*rp:>7.0f}{rp/baseR if baseR else 0:>7.2f}")
    else:
        print(f"{f:24}{0:>9}{'--':>7}{'--':>7}")

# ---- Q9b-2: which support, ALONE among LBB, is most outcome-correlated? (is one factor the carrier?) ----
print("\n[Q9b-2] Within-LBB: runner% of episodes WITH vs WITHOUT each support (is one factor the carrier?):")
print(f"{'factor':24}{'n_with':>7}{'run%w':>7}{'n_wo':>6}{'run%wo':>8}")
for f in lbb_supports:
    wi=[b for b in lbb if f in ev[b]['supports']]; wo=[b for b in lbb if f not in ev[b]['supports']]
    print(f"{f:24}{len(wi):>7}{100*runpct(wi):>7.0f}{len(wo):>6}{100*runpct(wo):>8.0f}")

# ---- Q9c: P1/P2 split LBB vs BPT ----
def win(b): return 'P1' if dspa[b]['datetime']<'2023-01-01' else 'P2'
print("\n[Q9c] TEMPORAL SPLIT (P1 < 2023-01-01, P2 >=):")
for nm,g in [('LEGITIMATE_BEAR_BUY',lbb),('BEAR_PULLBACK_TRAP',bpt)]:
    p1=[b for b in g if win(b)=='P1']; p2=[b for b in g if win(b)=='P2']
    print(f"  {nm:24} P1 n={len(p1):>2} run%={100*runpct(p1):>3.0f}  |  P2 n={len(p2):>2} run%={100*runpct(p2):>3.0f}")

# ---- aggregate value of prior layers: how often did each SOURCE contribute the decisive 2nd source? ----
print("\n[extra] SOURCE contribution across ALL primary states (which layers actually aggregated):")
src_use=Counter()
for b in EP:
    for s in ev[b]['source_layers']: src_use[s]+=1
for s,c in src_use.most_common(): print(f"    {s:24} {c:>4}/{N}")
print("\nDONE _DA_dspa_agg_separation_audit. Diagnostic only.")
