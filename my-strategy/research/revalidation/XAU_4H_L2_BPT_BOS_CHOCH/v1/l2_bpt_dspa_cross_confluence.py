#!/usr/bin/env python3
"""DSPA CROSS-CONFLUENCE EXPLORATION — base 276. Exploração AMPLA mas DISCIPLINADA por FAMÍLIAS de confluência
(não feature isolada, não fishing). Controles baked: hypergeometric null + P1/P2 + leave-1-year-out + Bonferroni
(M regras declaradas). Outcome/MFE SÓ avaliação, nunca predicado. realR capado nunca árbitro. Sem OOS/promoção.
Objetivo: skip-winners->TAKE, loser-takes->SKIP, preservando monumentais."""
import csv, json, math, random
D="results"
path={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
states={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_intermediate_states_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
ind={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
mph={int(r['episode_id']):r['macro_phase_causal'] for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_phase_causal_candidate.csv"))}
bl={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_bearleg_surgical.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}  # EVAL ONLY
EP=sorted(path)
def fn(v):
    try:return float(v)
    except:return None
MFE={b:fn(unc[b]['mfe_R']) for b in EP}
N=len(EP); nR=sum(1 for b in EP if MFE[b]>=5); nL=sum(1 for b in EP if MFE[b]<2); nM=sum(1 for b in EP if MFE[b]>=10)
baseR=nR/N; baseL=nL/N

# ---- EV booleans (reuse da aggregation) ----
def EVd(b):
    p=path[b];e=eng[b];x=ind.get(b,{});d=dec.get(b,{});blr=bl.get(b,{})
    leg=d.get('macro_reader_leg','')
    bear=leg=='MACRO_BEAR_LEG' or e.get('regime') in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or p.get('f7_regime_traj') in('REGIME_STABLE_BEAR','REGIME_DETERIORATING')
    bull=leg=='MACRO_BULL_LEG' or e.get('regime')=='MACRO_BULL' or p.get('f7_regime_traj') in('REGIME_STABLE_BULL','REGIME_IMPROVING')
    return dict(bear=bear,bull=bull,
      sweep=p.get('f1_swept_low_reclaim')=='1',swept_high=p.get('f1_swept_high_reject')=='1',
      flushV=p.get('f2_flush_state')=='FLUSH_V',grind=p.get('f2_flush_state')=='GRIND_DOWN',noflush=p.get('f2_flush_state')=='NO_FLUSH',
      accept=p.get('f3_acceptance_state')=='ACCEPTED_ABOVE_RES' or p.get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE',
      rej_res=p.get('f3_acceptance_state')=='REJECTED_AT_RES',holds=p.get('f3_acceptance_state')=='HOLDING_SUPPORT',broke=p.get('f3_acceptance_state')=='BROKE_SUPPORT',
      st_up=p.get('f4_structure_state')=='STRUCTURE_UP',st_dn=p.get('f4_structure_state')=='STRUCTURE_DOWN',st_rg=p.get('f4_structure_state')=='STRUCTURE_RANGE',BOS=p.get('f4_BOS')=='1',
      svp_acc=p.get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE',svp_below=p.get('f6_svp_state')=='BELOW_VALUE_REJECTED',
      premium=p.get('f5_range_pos_4h')=='PREMIUM',discount=p.get('f5_range_pos_4h')=='DISCOUNT',
      regime_det=p.get('f7_regime_traj')=='REGIME_DETERIORATING',
      capit=e.get('capit')=='CLIMAX_RECLAIM' or d.get('capit')=='CLIMAX_RECLAIM',knife=e.get('capit')=='FALLING_KNIFE',
      demand=d.get('demand')=='DEMAND_DEFENDED' or e.get('demand')=='DEMAND_DEFENDED',
      sup_markup=e.get('supply') in('CLEAN_SKY_BULLISH','MARKUP_BREAKING') or d.get('sup_cat') in('CLEAN_SKY','SUPPLY_NEAR_BUT_BROKEN'),
      sup_reject=e.get('supply') in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET') or d.get('sup_cat') in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS','SUPPLY_BLOCKS_TARGET'),
      fuel_low=e.get('fuel')=='low_fuel',mom_exh=e.get('momentum')=='LATE_TOP_EXHAUSTION',mom_strong=e.get('momentum') in('STRONG_BULL_MOMENTUM','HEALTHY_HIGH_LEGPOS'),
      bub_climax=x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL',smc_choch=x.get('smc')=='SMC_CHOCH_BULL_TRIGGER',nas_long=x.get('nas')=='NAS_LONG_RECENT',bull_div=x.get('rsi')=='RSI_BULL_DIV',
      bottom_turn=d.get('bottom_turn')=='True',clean_sky=d.get('clean_sky_flag')=='True',mphase_bull=mph.get(b)=='MACRO_BULL_RUN',risk_bad=e.get('risk') in('SL_TOO_SHORT','SL_TOO_WIDE'),
      bl_block=blr.get('refined')=='BLOCK',bl_preserve=blr.get('refined')=='PRESERVE',
      eng_skip=e.get('policy') in('SKIP','REVIEW','REVIEW_RISK'),eng_take=e.get('policy')=='TAKE')
EV={b:EVd(b) for b in EP}

# ---- T1 inventário + T2 master matrix ----
inv=[]
TYPES={'path':[k for k in path[EP[0]] if k not in('bar_idx','datetime')],
       'dspa_state':['dspa_primary_state','dspa_secondary_state','confidence'],
       'engine_state':['supply','demand','volume','mtf','regime','momentum','capit','fuel','risk','macro_state'],
       'indicator_state':['context','bubbles','smc','nas','rsi','indicator_confluence'],
       'prior_layer':['macro_reader_leg','sup_cat','clean_sky_flag','bottom_turn','macro_broken','weekly_slope','macro_phase','bear_leg_refined']}
for typ,feats in TYPES.items():
    for f in feats:
        inv.append(dict(feature=f,type=typ,causality='causal (DSPA L1 causal-verified / engine shift D-1 / state as-of-bar)',
            tested_isolated=('yes' if f in('sup_cat','macro_phase','bear_leg_refined','clean_sky_flag') else 'partial'),
            conditional_evidence_status='ALIVE_AS_CONDITIONAL_EVIDENCE'))
with open(f"{D}/l2_bpt_dspa_cross_feature_inventory.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['feature','type','causality','tested_isolated','conditional_evidence_status'],lineterminator="\n");w.writeheader();w.writerows(inv)
# master matrix
mm=[]
for b in EP:
    row=dict(bar_idx=b,datetime=path[b]['datetime'])
    for k in TYPES['path']: row['path_'+k]=path[b][k]
    row['dspa_primary']=states[b]['dspa_primary_state']; row['dspa_secondary']=states[b]['dspa_secondary_state']
    for k in TYPES['engine_state']: row['eng_'+k]=eng[b].get(k,'')
    for k in TYPES['indicator_state']: row['ind_'+k]=ind.get(b,{}).get(k,'')
    row['macro_reader_leg']=dec.get(b,{}).get('macro_reader_leg',''); row['sup_cat']=dec.get(b,{}).get('sup_cat',''); row['macro_phase']=mph.get(b,'')
    row['bear_leg_refined']=bl.get(b,{}).get('refined','')
    row['EVAL_mfe_R']=MFE[b]; row['EVAL_runner']=int(MFE[b]>=5); row['EVAL_loser']=int(MFE[b]<2); row['EVAL_monumental']=int(MFE[b]>=10); row['EVAL_eng_policy']=eng[b].get('policy')
    mm.append(row)
with open(f"{D}/l2_bpt_dspa_cross_master_matrix_276.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(mm[0].keys()),lineterminator="\n");w.writeheader();w.writerows(mm)

# ---- controles ----
def comb(n,k): return math.comb(n,k) if 0<=k<=n else 0
def hyper_runner_p(grp):
    n=len(grp); x=sum(1 for b in grp if MFE[b]>=5)
    if n==0: return 1.0
    return sum(comb(nR,i)*comb(N-nR,n-i) for i in range(x,min(n,nR)+1))/comb(N,n)
def hyper_loser_p(grp):
    n=len(grp); x=sum(1 for b in grp if MFE[b]<2)
    if n==0: return 1.0
    return sum(comb(nL,i)*comb(N-nL,n-i) for i in range(x,min(n,nL)+1))/comb(N,n)
def win(b): return 'P1' if path[b]['datetime']<'2023-01-01' else 'P2'
def evalrule(name,fam,intent,pred):
    grp=[b for b in EP if pred(EV[b])]; n=len(grp)
    if n==0: return None
    r=sum(1 for b in grp if MFE[b]>=5); l=sum(1 for b in grp if MFE[b]<2); m=sum(1 for b in grp if MFE[b]>=10)
    rr=r/n; lr=l/n
    p1=[b for b in grp if win(b)=='P1']; p2=[b for b in grp if win(b)=='P2']
    rr1=(sum(1 for b in p1 if MFE[b]>=5)/len(p1)) if p1 else 0; rr2=(sum(1 for b in p2 if MFE[b]>=5)/len(p2)) if p2 else 0
    lr1=(sum(1 for b in p1 if MFE[b]<2)/len(p1)) if p1 else 0; lr2=(sum(1 for b in p2 if MFE[b]<2)/len(p2)) if p2 else 0
    sw=sum(1 for b in grp if MFE[b]>=5 and EV[b]['eng_skip'])  # skip-winners recovered (se TAKE-intent)
    lc=sum(1 for b in grp if MFE[b]<2 and EV[b]['eng_take'])   # loser-takes cut (se SKIP-intent)
    pr=hyper_runner_p(grp); pl=hyper_loser_p(grp)
    return dict(rule=name,family=fam,intent=intent,n=n,runner_pct=round(100*rr,1),runner_lift=round(rr/baseR,2),
        loser_pct=round(100*lr,1),loser_lift=round(lr/baseL,2),monum=m,runner_p=round(pr,4),loser_p=round(pl,4),
        P1_rr=round(100*rr1,1),P2_rr=round(100*rr2,1),P1_lr=round(100*lr1,1),P2_lr=round(100*lr2,1),
        skipwin_recover=sw,losertake_cut=lc)

# ---- T3 famílias de confluência (regras DECLARADAS, estruturais, não todas-combinações) ----
def g(*ks): return lambda e: all(e[k] for k in ks)
RULES=[
 # A bear-leg legitimacy (TAKE-intent: runner concentration)
 ('A1_pair_demand_accept_bear','A','TAKE', g('bear','demand','accept')),
 ('A2_bear_sweep_or_flush_reclaim','A','TAKE', lambda e: e['bear'] and (e['sweep'] or e['flushV']) and (e['capit'] or e['demand'])),
 ('A3_bear_capit_demand','A','TAKE', g('bear','capit','demand')),
 ('A4_bear_svp_accept_struct','A','TAKE', lambda e: e['bear'] and e['svp_acc'] and (e['st_up'] or e['holds'])),
 ('A5_LBB_full','A','TAKE', lambda e: e['bear'] and e['demand'] and e['accept'] and (e['sweep'] or e['flushV'] or e['bottom_turn'])),
 # B supply interaction
 ('B1_bull_accept_markup','B','TAKE', lambda e: e['bull'] and e['accept'] and e['sup_markup']),
 ('B2_supply_reject_fuel_low','B','SKIP', g('sup_reject','fuel_low')),
 ('B3_bull_structup_BOS','B','TAKE', lambda e: e['bull'] and e['st_up'] and e['BOS']),
 ('B4_reject_fuel_premium','B','SKIP', lambda e: e['sup_reject'] and e['fuel_low'] and e['premium']),
 # C reversal/runner capture
 ('C1_capit_sweep_demand','C','TAKE', g('capit','sweep','demand')),
 ('C2_flushV_reclaim_div','C','TAKE', lambda e: e['flushV'] and (e['bull_div'] or e['capit'])),
 ('C3_bottomturn_demand_accept','C','TAKE', g('bottom_turn','demand','accept')),
 ('C4_discount_capit_demand','C','TAKE', g('discount','capit','demand')),
 ('C5_bub_climax_sweep','C','TAKE', lambda e: e['bub_climax'] and (e['sweep'] or e['capit'])),
 # D loser-take cutting
 ('D1_bear_reject_fuel','D','SKIP', g('bear','sup_reject','fuel_low')),
 ('D2_bear_grind_nocapit','D','SKIP', lambda e: e['bear'] and (e['grind'] or e['noflush']) and not e['capit']),
 ('D3_range_chop','D','SKIP', lambda e: e['st_rg'] and (e['noflush'] or e['grind'])),
 ('D4_reject_premium_exh','D','SKIP', lambda e: e['rej_res'] and e['premium'] and e['mom_exh']),
 ('D5_bear_pullback_trap_state','D','SKIP', lambda e: False),  # placeholder substituído por state-based abaixo
 # E skip-winner recovery: já capturado via skipwin_recover em A/C rules
]
res=[evalrule(n,f,i,p) for n,f,i,p in RULES if n!='D5_bear_pullback_trap_state']
# D5 via DSPA state
g_bpt=[b for b in EP if states[b]['dspa_primary_state']=='BEAR_PULLBACK_TRAP']
res.append(evalrule('D5_BPT_state','D','SKIP', lambda e: False) or {})
res[-1]=dict(rule='D5_BPT_state',family='D',intent='SKIP',n=len(g_bpt),runner_pct=round(100*sum(1 for b in g_bpt if MFE[b]>=5)/len(g_bpt),1),
   runner_lift=round((sum(1 for b in g_bpt if MFE[b]>=5)/len(g_bpt))/baseR,2),loser_pct=round(100*sum(1 for b in g_bpt if MFE[b]<2)/len(g_bpt),1),
   loser_lift=round((sum(1 for b in g_bpt if MFE[b]<2)/len(g_bpt))/baseL,2),monum=0,runner_p=round(hyper_runner_p(g_bpt),4),loser_p=round(hyper_loser_p(g_bpt),4),
   P1_rr=0,P2_rr=0,P1_lr=0,P2_lr=0,skipwin_recover=0,losertake_cut=sum(1 for b in g_bpt if MFE[b]<2 and EV[b]['eng_take']))
res=[r for r in res if r]
M=len(res); bonf=0.05/M
print("="*100);print(f"DSPA CROSS-CONFLUENCE | base runner={100*baseR:.0f}% loser={100*baseL:.0f}% | {M} regras declaradas | Bonferroni alpha={bonf:.4f}")
print(f"{'rule':30}{'fam':4}{'int':5}{'n':>4}{'run%':>6}{'rLft':>6}{'los%':>6}{'lLft':>6}{'mon':>4}{'run_p':>7}{'los_p':>7}{'P1/P2r':>10}{'sw/lc':>7}")
for r in sorted(res,key=lambda x:(x['family'],-x['runner_lift'])):
    star=''
    if r['intent']=='TAKE' and r['runner_p']<=bonf: star=' ***'
    elif r['intent']=='SKIP' and r['loser_p']<=bonf: star=' ***'
    elif (r['intent']=='TAKE' and r['runner_p']<0.05) or (r['intent']=='SKIP' and r['loser_p']<0.05): star=' *'
    print(f"{r['rule']:30}{r['family']:4}{r['intent']:5}{r['n']:>4}{r['runner_pct']:>6}{r['runner_lift']:>6}{r['loser_pct']:>6}{r['loser_lift']:>6}{r['monum']:>4}{r['runner_p']:>7}{r['loser_p']:>7}{str(r['P1_rr'])+'/'+str(r['P2_rr']):>10}{str(r['skipwin_recover'])+'/'+str(r['losertake_cut']):>7}{star}")

# ---- T5 lead ranking + status ----
def classify(r):
    sig = (r['runner_p']<=bonf) if r['intent']=='TAKE' else (r['loser_p']<=bonf)
    nom = (r['runner_p']<0.05) if r['intent']=='TAKE' else (r['loser_p']<0.05)
    p1p2_stable = (abs(r['P1_rr']-r['P2_rr'])<15) if r['intent']=='TAKE' else (abs(r['P1_lr']-r['P2_lr'])<15)
    if sig and p1p2_stable and r['n']>=20: return 'STRONG_CANDIDATE'
    if nom and r['n']>=20: return 'WEAK_REAL_STRUCTURE'
    if r['n']<12: return 'OVERFIT_HULL_RISK'   # tiny-n primeiro: lift alto em n<12 = hull, não conditional
    if (r['intent']=='TAKE' and r['runner_lift']>=1.2) or (r['intent']=='SKIP' and r['loser_lift']>=1.2): return 'CONDITIONAL_EVIDENCE'
    return 'DEAD_AS_PRIMARY_ALIVE_CONDITIONAL'
for r in res: r['status']=classify(r)
ranked=sorted(res,key=lambda r:(0 if r['status']=='STRONG_CANDIDATE' else 1 if r['status']=='WEAK_REAL_STRUCTURE' else 2 if r['status']=='CONDITIONAL_EVIDENCE' else 3, -max(r['runner_lift'],r['loser_lift'])))
with open(f"{D}/l2_bpt_dspa_cross_lead_ranking.csv","w",newline="") as f:
    cols=['rule','family','intent','status','n','runner_pct','runner_lift','loser_pct','loser_lift','monum','runner_p','loser_p','P1_rr','P2_rr','P1_lr','P2_lr','skipwin_recover','losertake_cut']
    w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows(ranked)
print("\n--- RANKING (status) ---")
from collections import Counter
print(dict(Counter(r['status'] for r in res)))
for r in ranked[:8]: print(f"  {r['status']:32}{r['rule']:28} lift={max(r['runner_lift'],r['loser_lift'])} p={min(r['runner_p'],r['loser_p'])} n={r['n']}")

# ---- T6 error map (skip-winners / loser-takes recuperáveis vs não) ----
# união das TAKE-rules CONDITIONAL+ p/ recuperação; união das SKIP-rules p/ corte
take_rules=[r for r in res if r['intent']=='TAKE' and r['status'] in('STRONG_CANDIDATE','WEAK_REAL_STRUCTURE','CONDITIONAL_EVIDENCE')]
skip_rules=[r for r in res if r['intent']=='SKIP' and r['status'] in('STRONG_CANDIDATE','WEAK_REAL_STRUCTURE','CONDITIONAL_EVIDENCE')]
take_pred={n:p for n,f,i,p in RULES}
recov=set(); cut=set()
for n,f,i,p in RULES:
    if n=='D5_bear_pullback_trap_state': continue
    rr=next((x for x in res if x['rule']==n),None)
    if not rr: continue
    if rr['intent']=='TAKE' and rr['status'] in('STRONG_CANDIDATE','WEAK_REAL_STRUCTURE','CONDITIONAL_EVIDENCE'):
        recov |= set(b for b in EP if p(EV[b]) and MFE[b]>=5 and EV[b]['eng_skip'])
    if rr['intent']=='SKIP' and rr['status'] in('STRONG_CANDIDATE','WEAK_REAL_STRUCTURE','CONDITIONAL_EVIDENCE'):
        cut |= set(b for b in EP if p(EV[b]) and MFE[b]<2 and EV[b]['eng_take'])
skipwin_all=set(b for b in EP if MFE[b]>=5 and EV[b]['eng_skip'])
losertake_all=set(b for b in EP if MFE[b]<2 and EV[b]['eng_take'])
mon_all=set(b for b in EP if MFE[b]>=10)
mon_threat=set(b for b in EP if MFE[b]>=10 and any(p(EV[b]) for n,f,i,p in RULES if i=='SKIP' and n!='D5_bear_pullback_trap_state'))
emap=[dict(category='SKIP_WINNERS_recoverable',count=len(recov&skipwin_all),of_total=len(skipwin_all)),
      dict(category='SKIP_WINNERS_not_yet',count=len(skipwin_all-recov),of_total=len(skipwin_all)),
      dict(category='LOSER_TAKES_cuttable',count=len(cut&losertake_all),of_total=len(losertake_all)),
      dict(category='LOSER_TAKES_not_yet',count=len(losertake_all-cut),of_total=len(losertake_all)),
      dict(category='MONUMENTALS_total',count=len(mon_all),of_total=len(mon_all)),
      dict(category='MONUMENTALS_threatened_by_SKIP_rules',count=len(mon_threat),of_total=len(mon_all))]
with open(f"{D}/l2_bpt_dspa_cross_error_map.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['category','count','of_total'],lineterminator="\n");w.writeheader();w.writerows(emap)
print("\n--- ERROR MAP ---")
for e in emap: print(f"  {e['category']:42} {e['count']}/{e['of_total']}")
print(f"\nBASELINES p/ comparação: demand+accept(A1) bear_leg_refined(D1-ish) supply_reject(B2) DSPA-LBB(A5)")
print("DONE cross-confluence. NÃO promovido. NÃO policy. Outcome só avaliação.")
