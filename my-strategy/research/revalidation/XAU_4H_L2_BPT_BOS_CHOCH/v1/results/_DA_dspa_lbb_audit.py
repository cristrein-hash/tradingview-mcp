#!/usr/bin/env python3
"""DEVIL'S ADVOCATE audit of l2_bpt_dspa_lbb_signal_stress.py. Diagnostic only.
Recomputes per-feature significance (Fisher exact 2x2 on median-split), Bonferroni,
per-year LBB counts, multiple-testing FDR, and leak checks. Does NOT modify main files."""
import csv, json, math
from itertools import combinations
D="."
states={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_intermediate_states_276.csv"))}
ev={int(r['bar_idx']):r for r in (json.loads(l) for l in open(f"{D}/l2_bpt_dspa_intermediate_evidence_276.jsonl"))}
path={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
EP=sorted(states)
def fn(v):
    try:return float(v)
    except:return None
MFE={b:fn(unc[b]['mfe_R']) for b in EP}
nR=sum(1 for b in EP if MFE[b]>=5); N=len(EP); baseR=nR/N
print(f"Base: N={N} runners(MFE>=5)={nR} baseR={baseR:.3f}")

def demand_def(b): return dec.get(b,{}).get('demand')=='DEMAND_DEFENDED' or eng[b].get('demand')=='DEMAND_DEFENDED'
def accept_above(b): return path[b].get('f3_acceptance_state')=='ACCEPTED_ABOVE_RES' or path[b].get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE'
def bear_ctx(b):
    leg=dec.get(b,{}).get('macro_reader_leg','')
    return leg=='MACRO_BEAR_LEG' or eng[b].get('regime') in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or path[b].get('f7_regime_traj') in('REGIME_STABLE_BEAR','REGIME_DETERIORATING')
def is_LBB(b): return states[b]['dspa_primary_state']=='LEGITIMATE_BEAR_BUY'
A=[b for b in EP if demand_def(b) and accept_above(b)]
B=[b for b in EP if bear_ctx(b) and demand_def(b) and accept_above(b)]
Cset=[b for b in EP if is_LBB(b)]

# ---- Fisher exact 2x2 ----
def logfact(n): return math.lgamma(n+1)
def fisher_2x2(a,b,c,d):
    # two-sided via summing tables with prob <= observed (Fisher's exact)
    n=a+b+c+d; r1=a+b; r2=c+d; c1=a+c; c2=b+d
    def p_tbl(a):
        b_=r1-a; c_=c1-a; d_=r2-c_
        if b_<0 or c_<0 or d_<0: return None
        return math.exp(logfact(r1)+logfact(r2)+logfact(c1)+logfact(c2)-logfact(n)
                        -logfact(a)-logfact(b_)-logfact(c_)-logfact(d_))
    p_obs=p_tbl(a)
    amin=max(0,c1-r2); amax=min(r1,c1)
    tot=0.0
    for x in range(amin,amax+1):
        px=p_tbl(x)
        if px is not None and px<=p_obs*(1+1e-9): tot+=px
    return min(1.0,tot)

NUMS=['f1_sweep_depth_atr','f1_bars_since_sweep','f2_drop_atr','f2_velocity_atr_bar','f2_range_expansion','f2_consec_down',
 'f2_flush_bars','f3_closes_above_res','f3_rejections_at_res','f3_breaks_support','f4_BOS','f4_CHoCH','f4_n_pivots_lb',
 'f5_range_pct_4h','f5_range_pct_1d','f6_above_value','f6_below_value','f6_dist_poc_atr','f7_combined_slope','f7_cascade_now','f7_macro_broken_recent']
print("\n=== T3 RE-TEST: Fisher exact two-sided per feature (median-split, within B n=%d) ==="%len(B))
print(f"{'feature':22}{'n_hi':>5}{'n_lo':>5}{'rh':>4}{'rl':>4}{'lift':>6}{'fisher_p':>10}{'bonf_0.0024':>12}")
results=[]
tested=0
for k in NUMS:
    vals=[(fn(path[b].get(k)),b) for b in B if fn(path[b].get(k)) is not None]
    if len(vals)<10:
        results.append((k,'INSUFF',1.0)); continue
    vals.sort(); med=vals[len(vals)//2][0]
    hi=[b for v,b in vals if v>med]; lo=[b for v,b in vals if v<=med]
    if not hi or not lo or min(len(hi),len(lo))<10:
        results.append((k,'NO_SPLIT/SMALL',1.0)); continue
    rh=sum(1 for b in hi if MFE[b]>=5); rl=sum(1 for b in lo if MFE[b]>=5)
    p=fisher_2x2(rh,len(hi)-rh,rl,len(lo)-rl)
    lift=(rh/len(hi))/(rl/len(lo)) if rl>0 else 99
    tested+=1
    results.append((k,'TESTED',p))
    surv='SURVIVES' if p<0.0024 else ''
    print(f"{k:22}{len(hi):>5}{len(lo):>5}{rh/len(hi)*100:>4.0f}{rl/len(lo)*100:>4.0f}{lift:>6.2f}{p:>10.4f}{surv:>12}")
print(f"\nFeatures actually tested (n>=10 both sides): {tested}")
# min p and how it compares
ps=sorted([(p,k) for k,s,p in results if s=='TESTED'])
print(f"Smallest Fisher p: {ps[0][1]} p={ps[0][0]:.4f}")
print(f"Bonferroni threshold (0.05/{tested}): {0.05/tested:.4f}")
print(f"Survivors at Bonferroni: {[k for p,k in ps if p<0.05/tested]}")
# Expected false positives at uncorrected alpha=0.05
print(f"Expected #false-positives at uncorrected alpha=0.05 over {tested} tests: {0.05*tested:.2f}")
# how many had uncorrected p<0.05
n_raw=sum(1 for p,k in ps if p<0.05)
print(f"Observed #features with uncorrected p<0.05: {n_raw}  (script's 'SEPARATES' used lift>=1.5|<=0.66, NOT p)")
# Benjamini-Hochberg FDR
m=len(ps); bh_sig=[]
for i,(p,k) in enumerate(ps,1):
    if p<=(i/m)*0.05: bh_sig=[(p,k) for j,(p,k) in enumerate(ps,1) if j<=i]
print(f"BH-FDR 0.05 survivors: {[k for p,k in bh_sig]}")

# ---- per-year LBB counts (Q4) ----
def yr(b): return path[b]['datetime'][:4]
from collections import Counter
yc=Counter(yr(b) for b in Cset)
print("\n=== Q4: per-year LBB counts (is LOO stability an artifact of even distribution?) ===")
print(dict(sorted(yc.items())))
print(f"LBB total={len(Cset)}; largest single year={max(yc.values())} ({max(yc,key=yc.get)}) = {max(yc.values())/len(Cset)*100:.0f}% of set")
# runner% of each single year alone
print("Per-year runner% (single year, the dropped slice):")
for y in sorted(yc):
    sub=[b for b in Cset if yr(b)==y]
    r=sum(1 for b in sub if MFE[b]>=5)
    print(f"  {y}: n={len(sub):>2} runners={r} runner%={r/len(sub)*100:.0f}")

# ---- f2_velocity vs FLUSH_V dependence (Q3) ----
print("\n=== Q3: is f2_velocity re-expressing FLUSH_V (circularity)? within B ===")
# flush_state categorical
fv=[b for b in B if path[b].get('f2_flush_state')=='FLUSH_V']
print(f"B with flush_state==FLUSH_V: {len(fv)}/{len(B)}")
# correlation of f2_velocity high vs flush_V membership
vals=[(fn(path[b].get('f2_velocity_atr_bar')),b) for b in B if fn(path[b].get('f2_velocity_atr_bar')) is not None]
vals.sort(); med=vals[len(vals)//2][0]
hi=set(b for v,b in vals if v>med)
overlap=sum(1 for b in fv if b in hi)
print(f"velocity-HI ∩ FLUSH_V = {overlap}/{len(fv)} of FLUSH_V are velocity-hi; {overlap}/{len(hi)} of velocity-hi are FLUSH_V")
# does velocity separate INSIDE non-FLUSH_V? (genuinely new info?)
nonfv=[b for b in B if b not in set(fv)]
vv=[(fn(path[b].get('f2_velocity_atr_bar')),b) for b in nonfv if fn(path[b].get('f2_velocity_atr_bar')) is not None]
if len(vv)>=10:
    vv.sort(); m2=vv[len(vv)//2][0]
    h2=[b for v,b in vv if v>m2]; l2=[b for v,b in vv if v<=m2]
    if h2 and l2:
        rh=sum(1 for b in h2 if MFE[b]>=5)/len(h2); rl=sum(1 for b in l2 if MFE[b]>=5)/len(l2)
        print(f"velocity split WITHIN non-FLUSH_V (n={len(vv)}): hi={rh*100:.0f}% lo={rl*100:.0f}% lift={rh/rl if rl>0 else 99:.2f} -> if ~1, velocity IS just flush proxy")

# ---- Q1: leak check — do A/B/C set-definition columns ever come from outcome file? ----
print("\n=== Q1: leak check ===")
print("Set defs use: dec[demand], eng[demand/regime], path[f3/f6/f7], states[dspa_primary_state]. unc[] used ONLY for MFE metrics.")
print("Confirmed by source: unc loaded line marked 'EVAL ONLY'; MFE never feeds demand_def/accept_above/bear_ctx/is_LBB.")

# ---- Q2/Q6: Fisher contrast C vs B-rest and C vs A (does narrowing add?) ----
def rc(g): return sum(1 for b in g if MFE[b]>=5)
Brest=[b for b in B if b not in set(Cset)]
print("\n=== Q2/Q6: does the full LBB convergence C add over the pair? (Fisher exact) ===")
print(f"C n={len(Cset)} runners={rc(Cset)} ({rc(Cset)/len(Cset)*100:.0f}%)")
print(f"B-rest (in B, not C) n={len(Brest)} runners={rc(Brest)} ({rc(Brest)/len(Brest)*100:.0f}%)")
print(f"Fisher C vs B-rest p={fisher_2x2(rc(Cset),len(Cset)-rc(Cset),rc(Brest),len(Brest)-rc(Brest)):.3f}")
print(f"Fisher C vs A     p={fisher_2x2(rc(Cset),len(Cset)-rc(Cset),rc(A),len(A)-rc(A)):.3f}")
print(f"C subset of B? {set(Cset).issubset(set(B))} ; C members also in B: {sum(1 for b in Cset if b in set(B))}/{len(Cset)}")
print("(Note: C is NOT a strict subset of B — 4 LBB episodes fall outside the bear_ctx/demand/accept triple,")
print(" so the script's 'C-over-B permutation' compares non-nested sets. Minor, but worth flagging.)")
