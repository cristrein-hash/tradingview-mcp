#!/usr/bin/env python3
"""DA part 3: the brute-force surfaced svp_acc (n=132 lift1.28 p=0.0064) and st_up+svp_acc (n=41 lift1.5 p=0.035)
as separating axes that the 18 declared rules under-weighted. Is this a REAL missed lead or a chance/correlation artifact?
Checks: (1) P1/P2 temporal stability of svp_acc & st_up+svp_acc; (2) does svp_acc survive Bonferroni over the 56-cell brute space (alpha 0.00089)?
(3) is svp_acc just re-expressing 'accept' (collinear) or adding signal; (4) monumental coverage & loser behaviour.
Note: main script's A4_bear_svp_accept_struct REQUIRED bear -> that gating KILLED the svp_acc signal (n35 lift0.99).
The unconditional/bull-inclusive svp_acc is what separates. This is the candidate missed lead."""
import csv, math
D="/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
path={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
EP=sorted(path)
def fn(v):
    try:return float(v)
    except:return None
MFE={b:fn(unc[b]['mfe_R']) for b in EP}
N=len(EP); nR=sum(1 for b in EP if MFE[b]>=5); nL=sum(1 for b in EP if MFE[b]<2); baseR=nR/N; baseL=nL/N
def comb(n,k): return math.comb(n,k) if 0<=k<=n else 0
def hyper_R(grp):
    n=len(grp); x=sum(1 for b in grp if MFE[b]>=5)
    if n==0: return 1.0
    return sum(comb(nR,i)*comb(N-nR,n-i) for i in range(x,min(n,nR)+1))/comb(N,n)
def win(b): return 'P1' if path[b]['datetime']<'2023-01-01' else 'P2'
def svp_acc(b): return path[b].get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE'
def accept(b): return path[b].get('f3_acceptance_state')=='ACCEPTED_ABOVE_RES' or path[b].get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE'
def st_up(b): return path[b].get('f4_structure_state')=='STRUCTURE_UP'
def bear(b):
    e=eng[b];p=path[b];d=dec.get(b,{})
    return d.get('macro_reader_leg','')=='MACRO_BEAR_LEG' or e.get('regime') in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or p.get('f7_regime_traj') in('REGIME_STABLE_BEAR','REGIME_DETERIORATING')

def report(nm,pred):
    grp=[b for b in EP if pred(b)]; n=len(grp)
    r=sum(1 for b in grp if MFE[b]>=5); l=sum(1 for b in grp if MFE[b]<2); m=sum(1 for b in grp if MFE[b]>=10)
    p1=[b for b in grp if win(b)=='P1']; p2=[b for b in grp if win(b)=='P2']
    rr1=(sum(1 for b in p1 if MFE[b]>=5)/len(p1)*100) if p1 else 0
    rr2=(sum(1 for b in p2 if MFE[b]>=5)/len(p2)*100) if p2 else 0
    print(f"  {nm:30} n={n:3} run%={100*r/n:4.0f} lift={r/n/baseR:4.2f} los%={100*l/n:4.0f} mon={m:2} p={hyper_R(grp):.4f} | P1run%={rr1:4.0f}(n{len(p1)}) P2run%={rr2:4.0f}(n{len(p2)})")
    return n,r,l,m,rr1,rr2

print("[1] svp_acc lead anatomy + temporal stability")
report("svp_acc (unconditional)",svp_acc)
report("st_up + svp_acc",lambda b: st_up(b) and svp_acc(b))
report("accept (broad, incl svp)",accept)
report("accept WITHOUT svp_acc",lambda b: accept(b) and not svp_acc(b))
report("svp_acc WITHOUT plain-accept",lambda b: svp_acc(b) and not(path[b].get('f3_acceptance_state')=='ACCEPTED_ABOVE_RES'))
print("\n[2] why main script MISSED it: A4 GATED svp_acc behind bear")
report("A4: bear & svp_acc & (st_up|holds)",lambda b: bear(b) and svp_acc(b) and (st_up(b) or path[b].get('f3_acceptance_state')=='HOLDING_SUPPORT'))
report("svp_acc & NOT bear (bull/neutral)",lambda b: svp_acc(b) and not bear(b))
print("    => the bear-gate in A4 destroyed the svp_acc edge; the signal lives OUTSIDE bear legs.")

print("\n[3] Bonferroni over brute 56-cell space: alpha=0.00089")
p_svp=hyper_R([b for b in EP if svp_acc(b)])
print(f"    svp_acc p={p_svp:.4f} vs alpha_eff 0.00089 -> {'PASS' if p_svp<0.00089 else 'FAIL (sub-significant under honest correction)'}")
print(f"    vs declared-18 Bonferroni 0.0028 -> {'PASS' if p_svp<0.0028 else 'FAIL'}")
print(f"    vs NOMINAL 0.05 -> {'PASS' if p_svp<0.05 else 'FAIL'}")
print("\n[VERDICT INPUT] svp_acc separates nominally (p~0.006) and is P1/P2-checkable, but does NOT survive honest")
print("multiple-testing correction. It is a stronger CONDITIONAL lead than A2/A5, MISSED only because A4 over-gated it with bear.")
print("DONE svp_probe.")
