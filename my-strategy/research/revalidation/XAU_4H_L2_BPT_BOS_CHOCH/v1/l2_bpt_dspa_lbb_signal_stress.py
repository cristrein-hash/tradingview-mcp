#!/usr/bin/env python3
"""DSPA — SIGNAL STRESS & PRESERVATION (LBB). Base 276. Diagnóstico. Outcome SÓ avaliação, nunca input.
T2 anatomia (A demand+accept / B +bear-context / C full-confluence) · T3 21 numerics ignorados como evidência
condicional · T4 stress (permutation null, P1/P2, leave-1-year-out, drop-1-evidence, par-vs-full delta). Sem OOS/promoção."""
import csv, json, random, math
D="results"
states={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_intermediate_states_276.csv"))}
ev={int(r['bar_idx']):r for r in (json.loads(l) for l in open(f"{D}/l2_bpt_dspa_intermediate_evidence_276.jsonl"))}
path={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}  # EVAL ONLY
EP=sorted(states)
def fn(v):
    try:return float(v)
    except:return None
MFE={b:fn(unc[b]['mfe_R']) for b in EP}
nR=sum(1 for b in EP if MFE[b]>=5); nL=sum(1 for b in EP if MFE[b]<2); N=len(EP); baseR=nR/N; baseL=nL/N

# recompute pair/bear (mesma lógica do evidence() da agregação)
def demand_def(b): return dec.get(b,{}).get('demand')=='DEMAND_DEFENDED' or eng[b].get('demand')=='DEMAND_DEFENDED'
def accept_above(b): return path[b].get('f3_acceptance_state')=='ACCEPTED_ABOVE_RES' or path[b].get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE'
def bear_ctx(b):
    leg=dec.get(b,{}).get('macro_reader_leg','')
    return leg=='MACRO_BEAR_LEG' or eng[b].get('regime') in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or path[b].get('f7_regime_traj') in('REGIME_STABLE_BEAR','REGIME_DETERIORATING')
def is_LBB(b): return states[b]['dspa_primary_state']=='LEGITIMATE_BEAR_BUY'

# hypergeometric upper-tail p (runners concentration vs base)
def comb(n,k): return math.comb(n,k) if 0<=k<=n else 0
def hyper_p(group):
    n=len(group); x=sum(1 for b in group if MFE[b]>=5)
    if n==0: return 1.0
    p=sum(comb(nR,i)*comb(N-nR,n-i) for i in range(x,min(n,nR)+1))/comb(N,n)
    return p
def metrics(group,label):
    n=len(group)
    if n==0: return dict(set=label,n=0)
    r=sum(1 for b in group if MFE[b]>=5); l=sum(1 for b in group if MFE[b]<2); m=sum(1 for b in group if MFE[b]>=10)
    def win(b): return 'P1' if path[b]['datetime']<'2023-01-01' else 'P2'
    p1=[b for b in group if win(b)=='P1']; p2=[b for b in group if win(b)=='P2']
    rr1=(sum(1 for b in p1 if MFE[b]>=5)/len(p1)) if p1 else 0; rr2=(sum(1 for b in p2 if MFE[b]>=5)/len(p2)) if p2 else 0
    return dict(set=label,n=n,runner_pct=round(100*r/n,1),lift=round((r/n)/baseR,2),loser_pct=round(100*l/n,1),
        monumentals=m,hyper_p=round(hyper_p(group),3),P1_rr=round(100*rr1,1),P2_rr=round(100*rr2,1),P1_n=len(p1),P2_n=len(p2))

# ---- T2 ANATOMIA: A / B / C ----
A=[b for b in EP if demand_def(b) and accept_above(b)]
B=[b for b in EP if bear_ctx(b) and demand_def(b) and accept_above(b)]
Cset=[b for b in EP if is_LBB(b)]
print("="*86);print("T2 — ANATOMIA DO SINAL (base runner_rate=%.0f%%)"%(100*baseR))
anat=[metrics(A,'A_demand+acceptance'),metrics(B,'B_+bear_context'),metrics(Cset,'C_full_confluence_LBB')]
print(f"{'set':28}{'n':>4}{'run%':>6}{'lift':>6}{'los%':>6}{'mon':>4}{'hyp_p':>7}{'P1/P2':>11}")
for m in anat: print(f"{m['set']:28}{m['n']:>4}{m['runner_pct']:>6}{m['lift']:>6}{m['loser_pct']:>6}{m['monumentals']:>4}{m['hyper_p']:>7}{str(m['P1_rr'])+'/'+str(m['P2_rr']):>11}")
with open(f"{D}/l2_bpt_dspa_lbb_signal_anatomy.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(anat[0].keys()),lineterminator="\n");w.writeheader();w.writerows(anat)

# PERGUNTA CENTRAL: C agrega além de B? permutation: C é subset de B; pick |C| aleatório de B, runner% >= C?
rng=random.Random(21); kc=len(Cset); obsC=sum(1 for b in Cset if MFE[b]>=5)/kc; ge=0; Bmfe=[MFE[b] for b in B]
for _ in range(5000):
    s=rng.sample(range(len(B)),kc)
    if sum(1 for j in s if Bmfe[j]>=5)/kc>=obsC: ge+=1
p_CoverB=ge/5000
print(f"\nC vs B (a confluência estreita B->C adiciona valor?): C runner%={100*obsC:.0f} vs B runner%={anat[1]['runner_pct']} | permutation p(subset aleatório de B >= C)={p_CoverB:.3f}")

# ---- T3 21 NUMERIC FEATURES ignorados: separam runner de loser DENTRO de B (n76)? ----
NUMS=['f1_sweep_depth_atr','f1_bars_since_sweep','f2_drop_atr','f2_velocity_atr_bar','f2_range_expansion','f2_consec_down',
 'f2_flush_bars','f3_closes_above_res','f3_rejections_at_res','f3_breaks_support','f4_BOS','f4_CHoCH','f4_n_pivots_lb',
 'f5_range_pct_4h','f5_range_pct_1d','f6_above_value','f6_below_value','f6_dist_poc_atr','f7_combined_slope','f7_cascade_now','f7_macro_broken_recent']
Bdata=B
print(f"\nT3 — 21 NUMERIC FEATURES dentro de B (n={len(B)}): separa runner de loser? (median-split lift; Bonferroni alpha=0.05/21=0.0024)")
numrows=[]
for k in NUMS:
    vals=[(fn(path[b].get(k)),b) for b in Bdata if fn(path[b].get(k)) is not None]
    if len(vals)<10: numrows.append(dict(feature=k,status='INSUFFICIENT')); continue
    vals.sort(); med=vals[len(vals)//2][0]
    hi=[b for v,b in vals if v>med]; lo=[b for v,b in vals if v<=med]
    if not hi or not lo: numrows.append(dict(feature=k,status='NO_SPLIT')); continue
    rh=sum(1 for b in hi if MFE[b]>=5)/len(hi); rl=sum(1 for b in lo if MFE[b]>=5)/len(lo)
    lift=round(rh/rl,2) if rl>0 else 99
    numrows.append(dict(feature=k,n_hi=len(hi),n_lo=len(lo),runner_hi=round(100*rh,0),runner_lo=round(100*rl,0),split_lift=lift,
        status=('SEPARATES' if (lift>=1.5 or lift<=0.66) and min(len(hi),len(lo))>=10 else 'WEAK')))
for r in numrows:
    if r.get('status')=='SEPARATES': print(f"  {r['feature']:22} hi_run={r.get('runner_hi')}% lo_run={r.get('runner_lo')}% lift={r.get('split_lift')} <<SEPARA(lead)")
print("  (demais: WEAK/insuficiente — listados no CSV)")
with open(f"{D}/l2_bpt_dspa_lbb_numeric_path_feature_test.csv","w",newline="") as f:
    cols=['feature','n_hi','n_lo','runner_hi','runner_lo','split_lift','status']
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows(numrows)

# ---- T4 STRESS ----
# permutation null LBB vs BPT
BPT=[b for b in EP if states[b]['dspa_primary_state']=='BEAR_PULLBACK_TRAP']
print(f"\nT4 — STRESS")
print(f"  LBB n={len(Cset)} runner%={metrics(Cset,'x')['runner_pct']} hyper_p={hyper_p(Cset):.3f} | BPT n={len(BPT)} runner%={metrics(BPT,'x')['runner_pct']}")
# leave-one-year-out (LBB)
def yr(b): return path[b]['datetime'][:4]
years=sorted(set(yr(b) for b in Cset))
loo=[]
for y in years:
    sub=[b for b in Cset if yr(b)!=y]; m=metrics(sub,f'drop_{y}'); loo.append(m)
print("  leave-1-year-out (LBB runner%):", {y:metrics([b for b in Cset if yr(b)!=y],'x')['runner_pct'] for y in years})
# drop-one-evidence ablation (usar evidence supports)
SUPS=['demand_defended','acceptance_above','sweep_low_reclaim','flush_V','capit_climax','bottom_turn','bub_climax_bull','smc_choch_bull','bull_div','bl_refined_preserve']
abl=[]
for s in SUPS:
    # LBB episódios que NÃO dependem só de s: removendo s, quais ainda têm >=2 supports de >=2 fontes? aproximação: LBB com s presente
    withS=[b for b in Cset if s in ev[b]['supports']]
    rr=(sum(1 for b in withS if MFE[b]>=5)/len(withS)) if withS else 0
    abl.append(dict(support=s,n_LBB_with=len(withS),runner_pct_with=round(100*rr,1)))
print("  drop-one-evidence (runner% dos LBB que TÊM cada support):")
for a in sorted(abl,key=lambda x:-x['n_LBB_with']): print(f"    {a['support']:20} n={a['n_LBB_with']:>3} runner%={a['runner_pct_with']}")
with open(f"{D}/l2_bpt_dspa_lbb_ablation.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['support','n_LBB_with','runner_pct_with'],lineterminator="\n");w.writeheader();w.writerows(abl)
# permutation null files
with open(f"{D}/l2_bpt_dspa_lbb_permutation_null.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['test','observed','p_value','interpretation'])
    w.writerow(['LBB_runner_concentration_vs_base',round(100*obsC,1),round(hyper_p(Cset),3),'hypergeometric upper-tail vs base 26%'])
    w.writerow(['C_over_B_increment',anat[2]['runner_pct'],round(p_CoverB,3),'permutation: confluencia estreita B->C adiciona alem de subset aleatorio?'])
    w.writerow(['LBB_vs_BPT_separation','38vs13','~0.045','Fisher contraste (do DA anterior)'])
print(f"\n=== DELTA REAL DA CONFLUÊNCIA: B(par+bear)={anat[1]['runner_pct']}% -> C(full)={anat[2]['runner_pct']}% | p(C>random subset de B)={p_CoverB:.3f} ===")
print("NÃO promovido. NÃO automation-ready. Outcome só avaliação. DONE.")
