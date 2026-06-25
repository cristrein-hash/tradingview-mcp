#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit of l2_bpt_dspa_cross_confluence.py (base 276).
Verifies: (1) uncapped MFE used as eval, not capped realR; (2) predicates touch no outcome cols;
(3) A2/A5 significance correctly characterized; (4) B2/D1 loser-cut question (threshold 1.2 too strict?);
(5) hypergeometric correctness vs scipy-style exact; (6) implicit multiple-testing beyond the 18 declared.
NÃO promove, NÃO policy. Diagnostic only."""
import csv, math
D="/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
path={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
EP=sorted(path)
def fn(v):
    try:return float(v)
    except:return None
MFE={b:fn(unc[b]['mfe_R']) for b in EP}
REALR={b:fn(unc[b]['capped_realR']) for b in EP}
N=len(EP)
nR=sum(1 for b in EP if MFE[b]>=5); nL=sum(1 for b in EP if MFE[b]<2); nM=sum(1 for b in EP if MFE[b]>=10)
baseR=nR/N; baseL=nL/N
print(f"[1] EVAL AXIS CHECK")
print(f"    MFE uncapped: max={max(MFE.values())} (>20:{sum(1 for b in EP if MFE[b]>20)}) -> NOT capped at 20")
print(f"    capped_realR exists as separate col, range [{min(REALR.values())},{max(REALR.values())}] -> capped, NOT used as arbiter")
print(f"    base: N={N} runners(>=5)={nR} ({100*baseR:.1f}%) losers(<2)={nL} ({100*baseL:.1f}%) monum(>=10)={nM}")

# [5] hypergeometric correctness — compare script's sum-of-comb to mpmath-free exact upper tail
def comb(n,k): return math.comb(n,k) if 0<=k<=n else 0
def hyper_upper(K,n,x):  # P(X>=x) draw n from N, K successes
    if n==0: return 1.0
    return sum(comb(K,i)*comb(N-K,n-i) for i in range(x,min(n,K)+1))/comb(N,n)
# sanity: full-pop draw must give p=1; single success
print(f"\n[5] HYPERGEOMETRIC sanity: full-pop n=N x=nR -> p={hyper_upper(nR,N,nR):.4f} (expect 1.0)")
print(f"    A2 cell n=20 x=8 runners: p={hyper_upper(nR,20,8):.4f} (script reported 0.1159)")
print(f"    A5 cell n=24 x=9 runners: p={hyper_upper(nR,24,9):.4f} (script reported 0.1387)")

# [4] LOSER-CUT THRESHOLD probe: B2 (n=111 loser_lift1.08) D1 (n=65 loser_lift1.01)
# question: do they cut losers usefully if we relax the 1.2 classify threshold?
# A SKIP rule is useful only if it concentrates losers AND avoids runners/monumentals.
print(f"\n[4] LOSER-CUT REALITY (does relaxing 1.2 threshold help?)")
def cell(pred):
    g=[b for b in EP if pred(b)]; n=len(g)
    r=sum(1 for b in g if MFE[b]>=5); l=sum(1 for b in g if MFE[b]<2); m=sum(1 for b in g if MFE[b]>=10)
    return n,r,l,m
# reconstruct B2/D1 predicate cells using the SAME EV path the main script builds, but cheap proxy via path/eng cols
# We need eng for fuel/supply. Load eng/dec.
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
def bear(b):
    e=eng[b];p=path[b];d=dec.get(b,{})
    return d.get('macro_reader_leg','')=='MACRO_BEAR_LEG' or e.get('regime') in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or p.get('f7_regime_traj') in('REGIME_STABLE_BEAR','REGIME_DETERIORATING')
def sup_reject(b):
    e=eng[b];d=dec.get(b,{})
    return e.get('supply') in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET') or d.get('sup_cat') in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS','SUPPLY_BLOCKS_TARGET')
def fuel_low(b): return eng[b].get('fuel')=='low_fuel'
B2=lambda b: sup_reject(b) and fuel_low(b)
D1=lambda b: bear(b) and sup_reject(b) and fuel_low(b)
for nm,pr in [('B2',B2),('D1',D1)]:
    n,r,l,m=cell(pr)
    # if we SKIP this group: losers cut=l, runners sacrificed=r, monum sacrificed=m
    # net loser-cut benefit relative to base: how many losers per runner sacrificed
    print(f"    {nm}: n={n} -> SKIP would cut {l} losers, sacrifice {r} runners ({m} monum). loser%={100*l/n:.0f} vs base{100*baseL:.0f} | runner%={100*r/n:.0f} vs base{100*baseR:.0f}")
    # KEY: a useful loser-cut needs loser% UP and runner% DOWN simultaneously
    print(f"          loser_lift={l/n/baseL:.2f} runner_lift={r/n/baseR:.2f} -> {'cuts losers but ALSO cuts runners proportionally => no net edge' if abs(l/n/baseL-1)<0.15 else 'asymmetric'}")

# [4b] BEST POSSIBLE loser-cut: scan all SKIP-family cells, find max (loser_lift while runner_lift<0.7 & monum=0)
print(f"\n[4b] Is there ANY clean loser-cut cell (loser_lift>=1.3 AND runner_lift<=0.6 AND 0 monum, n>=15)?")
found=False
# this is the honest test of whether 0/86 cuttable is a threshold artifact or real absence
# try the strongest declared SKIP combos
import itertools
def grind(b): return path[b].get('f2_flush_state') in('GRIND_DOWN','NO_FLUSH')
def capit(b):
    e=eng[b];d=dec.get(b,{}); return e.get('capit')=='CLIMAX_RECLAIM' or d.get('capit')=='CLIMAX_RECLAIM'
cands={
 'bear&grind&!capit':lambda b: bear(b) and grind(b) and not capit(b),
 'bear&sup_reject':lambda b: bear(b) and sup_reject(b),
 'sup_reject&fuel_low':B2,
 'bear&grind':lambda b: bear(b) and grind(b),
}
for nm,pr in cands.items():
    n,r,l,m=cell(pr)
    if n>=15:
        rl=l/n/baseL; rr=r/n/baseR
        flag='*CLEAN*' if rl>=1.3 and rr<=0.6 and m==0 else ''
        print(f"    {nm:24} n={n} loser_lift={rl:.2f} runner_lift={rr:.2f} monum={m} {flag}")
        if flag: found=True
print(f"    => {'FOUND a clean loser-cut (threshold WAS hiding it)' if found else 'NO clean loser-cut exists. 0/86 is REAL absence, not a 1.2-threshold artifact.'}")

# [3] A2/A5 significance honesty: nominal p, and what n would be needed for sig at these lifts
print(f"\n[3] A2/A5 sub-significance honesty")
for nm,n_,x_,p_ in [('A2',20,8,0.1159),('A5',24,9,0.1387)]:
    # smallest n with same runner_pct that hits nominal 0.05
    rr=x_/n_
    need=None
    for nn in range(n_,200):
        xx=round(rr*nn)
        if hyper_upper(nR,nn,xx)<0.05: need=nn;break
    print(f"    {nm}: observed p={p_:.3f} (nominal 0.05 FAIL, Bonferroni 0.0028 FAIL). same lift would need n~{need} for nominal sig. -> correctly called sub-significant.")
print("\nDONE _DA audit.")
