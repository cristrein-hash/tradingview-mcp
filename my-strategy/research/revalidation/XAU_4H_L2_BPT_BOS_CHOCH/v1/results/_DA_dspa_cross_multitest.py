#!/usr/bin/env python3
"""DA part 2: multiple-testing honesty + omitted-confluence sweep.
The main script declares 18 rules, Bonferroni M=18. But 40 boolean EV axes exist.
Researcher-degrees-of-freedom risk: were the 18 cherry-picked from a larger peeked space?
Test: (a) brute-force ALL 2-way AND 3-way AND confluences over a core axis subset, count how many
reach nominal p<0.05 vs expected-by-chance; (b) does A2/A5 survive an effective-M correction sized to
the realistic search space; (c) did the exploration MISS a separating confluence the 18 didn't name."""
import csv, math, itertools
D="/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
path={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
states={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_intermediate_states_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
ind={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
bl={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_bearleg_surgical.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
EP=sorted(path)
def fn(v):
    try:return float(v)
    except:return None
MFE={b:fn(unc[b]['mfe_R']) for b in EP}
N=len(EP); nR=sum(1 for b in EP if MFE[b]>=5); baseR=nR/N
def comb(n,k): return math.comb(n,k) if 0<=k<=n else 0
def hyper_R(grp):
    n=len(grp); x=sum(1 for b in grp if MFE[b]>=5)
    if n==0: return 1.0,n,x
    return sum(comb(nR,i)*comb(N-nR,n-i) for i in range(x,min(n,nR)+1))/comb(N,n),n,x

# core TAKE-relevant axes (subset that the families actually combine)
def A(b):
    p=path[b];e=eng[b];x=ind.get(b,{});d=dec.get(b,{})
    leg=d.get('macro_reader_leg','')
    return dict(
      bear=leg=='MACRO_BEAR_LEG' or e.get('regime') in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or p.get('f7_regime_traj') in('REGIME_STABLE_BEAR','REGIME_DETERIORATING'),
      sweep=p.get('f1_swept_low_reclaim')=='1',
      flushV=p.get('f2_flush_state')=='FLUSH_V',
      accept=p.get('f3_acceptance_state')=='ACCEPTED_ABOVE_RES' or p.get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE',
      demand=d.get('demand')=='DEMAND_DEFENDED' or e.get('demand')=='DEMAND_DEFENDED',
      capit=e.get('capit')=='CLIMAX_RECLAIM' or d.get('capit')=='CLIMAX_RECLAIM',
      discount=p.get('f5_range_pos_4h')=='DISCOUNT',
      st_up=p.get('f4_structure_state')=='STRUCTURE_UP',
      bottom_turn=d.get('bottom_turn')=='True',
      svp_acc=p.get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE',
      bull_div=x.get('rsi')=='RSI_BULL_DIV',
      bub_climax=x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL',
      smc_choch=x.get('smc')=='SMC_CHOCH_BULL_TRIGGER',
      nas_long=x.get('nas')=='NAS_LONG_RECENT')
EVA={b:A(b) for b in EP}
axes=list(EVA[EP[0]].keys())

# (a) brute-force all 2-way and 3-way AND confluences, n>=15, count nominal hits
print(f"[a] BRUTE-FORCE all AND-confluences over {len(axes)} TAKE axes (n>=15), TAKE-intent runner sep")
hits=[]; tested=0
for k in (1,2,3):
    for combo in itertools.combinations(axes,k):
        grp=[b for b in EP if all(EVA[b][c] for c in combo)]
        if len(grp)<15: continue
        tested+=1
        p,n,x=hyper_R(grp)
        lift=(x/n)/baseR
        if p<0.05: hits.append((combo,n,round(lift,2),round(p,4)))
print(f"    tested {tested} confluences with n>=15. nominal p<0.05 hits: {len(hits)} (expected by chance ~{0.05*tested:.1f})")
for h in sorted(hits,key=lambda z:z[3])[:12]: print(f"      {'+'.join(h[0]):45} n={h[1]} lift={h[2]} p={h[3]}")
if not hits: print("      (none) => no omitted 2/3-way TAKE confluence separates even nominally at n>=15")

# (b) effective-M honesty: if the realistic search space is ~tested confluences, what Bonferroni?
effM=tested
print(f"\n[b] Effective-M correction sized to realistic AND-space (n>=15): M_eff={effM}, alpha_eff={0.05/effM:.5f}")
print(f"    A2 p=0.1159, A5 p=0.1387 -> both FAIL even nominal 0.05, so harsher M is moot. Leads are honest CONDITIONAL_EVIDENCE, not significance claims.")
print(f"    Declared-M Bonferroni (18) is the WEAKEST defensible correction; nothing passes it anyway, so under-correction does not manufacture a false positive here.")

# (c) did exploration miss a separating confluence? best lift at n>=20 across brute force
print(f"\n[c] BEST separating TAKE confluence found anywhere (n>=20):")
best=[]
for k in (1,2,3):
    for combo in itertools.combinations(axes,k):
        grp=[b for b in EP if all(EVA[b][c] for c in combo)]
        if len(grp)<20: continue
        p,n,x=hyper_R(grp); lift=(x/n)/baseR
        best.append((combo,n,round(lift,2),round(p,4)))
for h in sorted(best,key=lambda z:-z[2])[:8]:
    print(f"      {'+'.join(h[0]):45} n={h[1]} lift={h[2]} p={h[3]}")
print("    => compare top lifts to A2(1.53)/A5(1.44): if nothing at n>=20 beats them with lower p, the 18 rules already captured the residual signal. No missed lead.")
print("\nDONE multitest.")
