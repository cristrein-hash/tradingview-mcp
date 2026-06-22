#!/usr/bin/env python3
"""DSPA CAMADA 4 — AGGREGATION / INTERMEDIATE STATE READING. Base 276. DIAGNÓSTICO/calibração.
Consome DSPA path features (7 famílias) + Macro engine states + Indicator v2 + prior layers (evidência condicional)
→ 9 estados intermediários de TRAJETÓRIA por convergência MULTI-FATORIAL (nunca eixo único; ≥2 fatores de ≥2 fontes).
NÃO promove TAKE/SKIP final. Outcome/MFE/realR SÓ na avaliação (Tarefa 5), NUNCA como input. Causal. Script salvo."""
import csv, json, random
D="results"
dspa={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
ind={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
mph={int(r['episode_id']):r['macro_phase_causal'] for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_phase_causal_candidate.csv"))}
bl={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_bearleg_surgical.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}  # EVAL ONLY
EP=sorted(dspa)
def fn(v):
    try:return float(v)
    except:return None

# ---- evidência por episódio: (bool, source). Multi-fatorial, multi-fonte. ----
def evidence(b):
    p=dspa[b]; e=eng[b]; x=ind.get(b,{}); d=dec.get(b,{}); blr=bl.get(b,{})
    leg=d.get('macro_reader_leg','')
    bear_ctx = leg=='MACRO_BEAR_LEG' or e.get('regime') in('MACRO_BROKEN_DISTRIBUTION','CASCADE_DECLINE') or p.get('f7_regime_traj') in('REGIME_STABLE_BEAR','REGIME_DETERIORATING')
    bull_ctx = leg=='MACRO_BULL_LEG' or e.get('regime')=='MACRO_BULL' or p.get('f7_regime_traj') in('REGIME_STABLE_BULL','REGIME_IMPROVING')
    EV={}  # name -> (bool, source)
    EV['bear_context']=(bear_ctx,'regime')
    EV['bull_context']=(bull_ctx,'regime')
    EV['sweep_low_reclaim']=(p.get('f1_swept_low_reclaim')=='1','dspa_F1')
    EV['swept_high_reject']=(p.get('f1_swept_high_reject')=='1','dspa_F1')
    EV['flush_V']=(p.get('f2_flush_state')=='FLUSH_V','dspa_F2')
    EV['grind_down']=(p.get('f2_flush_state')=='GRIND_DOWN','dspa_F2')
    EV['no_flush']=(p.get('f2_flush_state')=='NO_FLUSH','dspa_F2')
    EV['acceptance_above']=(p.get('f3_acceptance_state')=='ACCEPTED_ABOVE_RES' or p.get('f6_svp_state')=='ACCEPTING_ABOVE_VALUE','dspa_F3F6')
    EV['rejected_at_res']=(p.get('f3_acceptance_state')=='REJECTED_AT_RES','dspa_F3')
    EV['holding_support']=(p.get('f3_acceptance_state')=='HOLDING_SUPPORT','dspa_F3')
    EV['broke_support']=(p.get('f3_acceptance_state')=='BROKE_SUPPORT','dspa_F3')
    EV['structure_up']=(p.get('f4_structure_state')=='STRUCTURE_UP','dspa_F4')
    EV['structure_down']=(p.get('f4_structure_state')=='STRUCTURE_DOWN','dspa_F4')
    EV['structure_range']=(p.get('f4_structure_state')=='STRUCTURE_RANGE','dspa_F4')
    EV['BOS']=(p.get('f4_BOS')=='1','dspa_F4')
    EV['svp_below']=(p.get('f6_svp_state')=='BELOW_VALUE_REJECTED','dspa_F6')
    EV['premium']=(p.get('f5_range_pos_4h')=='PREMIUM','dspa_F5ctx')  # F5 = context, não trajetória principal
    EV['discount']=(p.get('f5_range_pos_4h')=='DISCOUNT','dspa_F5ctx')
    EV['regime_deteriorating']=(p.get('f7_regime_traj')=='REGIME_DETERIORATING','dspa_F7')
    EV['capit_climax']=(e.get('capit')=='CLIMAX_RECLAIM' or d.get('capit')=='CLIMAX_RECLAIM','macro_capit')
    EV['falling_knife']=(e.get('capit')=='FALLING_KNIFE','macro_capit')
    EV['demand_defended']=(d.get('demand')=='DEMAND_DEFENDED' or e.get('demand')=='DEMAND_DEFENDED','macro_demand')
    EV['supply_markup']=(e.get('supply') in('CLEAN_SKY_BULLISH','MARKUP_BREAKING') or d.get('sup_cat') in('CLEAN_SKY','SUPPLY_NEAR_BUT_BROKEN'),'macro_supply')
    EV['supply_reject']=(e.get('supply') in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET') or d.get('sup_cat') in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS','SUPPLY_BLOCKS_TARGET'),'macro_supply')
    EV['fuel_low']=(e.get('fuel')=='low_fuel','macro_fuel')
    EV['momentum_exhaustion']=(e.get('momentum')=='LATE_TOP_EXHAUSTION','macro_momentum')
    EV['momentum_strong']=(e.get('momentum') in('STRONG_BULL_MOMENTUM','HEALTHY_HIGH_LEGPOS'),'macro_momentum')
    EV['bub_climax_bull']=(x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL','ind_bubbles')  # context-aware: sell-climax em fundo = bull
    EV['smc_choch_bull']=(x.get('smc')=='SMC_CHOCH_BULL_TRIGGER','ind_smc')
    EV['nas_long']=(x.get('nas')=='NAS_LONG_RECENT','ind_nas')
    EV['bull_div']=(x.get('rsi')=='RSI_BULL_DIV','ind_rsi')
    EV['bottom_turn']=(d.get('bottom_turn')=='True','prior_bottom_turn')
    EV['clean_sky']=(d.get('clean_sky_flag')=='True','prior_clean_sky')
    EV['macro_phase_bullrun']=(mph.get(b)=='MACRO_BULL_RUN','prior_macro_phase')
    EV['risk_bad']=(e.get('risk') in('SL_TOO_SHORT','SL_TOO_WIDE'),'macro_risk')
    EV['bl_refined_block']=(blr.get('refined')=='BLOCK','prior_bearleg_refined')   # evidência condicional, NÃO veto cego
    EV['bl_refined_preserve']=(blr.get('refined')=='PRESERVE','prior_bearleg_refined')
    return EV

# ---- 9 estados: (gate, supports, conflicts). Convergência: ≥2 supports de ≥2 fontes. ----
STATES={
 'LEGITIMATE_BEAR_BUY': dict(gate='bear_context',
   sup=['sweep_low_reclaim','flush_V','capit_climax','demand_defended','acceptance_above','bottom_turn','bub_climax_bull','smc_choch_bull','bull_div','bl_refined_preserve'],
   con=['supply_reject','grind_down','momentum_strong']),
 'BEAR_PULLBACK_TRAP': dict(gate='bear_context',
   sup=['grind_down','no_flush','supply_reject','fuel_low','rejected_at_res','momentum_exhaustion','bl_refined_block','swept_high_reject'],
   con=['sweep_low_reclaim','capit_climax','flush_V','bottom_turn']),
 'MARKUP_THROUGH_SUPPLY': dict(gate='bull_context',
   sup=['acceptance_above','supply_markup','structure_up','BOS','momentum_strong','clean_sky','macro_phase_bullrun'],
   con=['rejected_at_res','momentum_exhaustion']),
 'SUPPLY_REJECTION_TRAP': dict(gate=None,
   sup=['rejected_at_res','supply_reject','fuel_low','premium','momentum_exhaustion','swept_high_reject'],
   con=['acceptance_above','supply_markup','capit_climax']),
 'REVERSAL_RUNNER': dict(gate=None,
   sup=['capit_climax','sweep_low_reclaim','demand_defended','discount','bottom_turn','bull_div','flush_V'],
   con=['momentum_strong','supply_reject']),
 'BULL_PULLBACK_CONTINUATION': dict(gate='bull_context',
   sup=['demand_defended','holding_support','acceptance_above','structure_up','momentum_strong','macro_phase_bullrun'],
   con=['supply_reject','structure_down','momentum_exhaustion']),
 'RANGE_CHOP_NO_EDGE': dict(gate=None,
   sup=['structure_range','no_flush','grind_down'],   # range + sem flush claro
   con=['capit_climax','sweep_low_reclaim','BOS','acceptance_above']),
}
def score_state(EV, st):
    g=st['gate']
    if g and not EV[g][0]: return None
    fired=[f for f in st['sup'] if EV[f][0]]; src=set(EV[f][1] for f in fired)
    confl=[f for f in st['con'] if EV[f][0]]
    if len(fired)<2 or len(src)<2: return None   # convergência: ≥2 fatores de ≥2 fontes (anti eixo-único)
    sc=len(fired)-0.6*len(confl)
    return dict(score=round(sc,1),supports=fired,conflicts=confl,n_src=len(src))

def aggregate(b):
    EV=evidence(b); cand={}
    for name,st in STATES.items():
        r=score_state(EV,st)
        if r: cand[name]=r
    # bull & bear fortes simultâneos = UNKNOWN_CONFLICT
    bull_strong=any(n in cand for n in('MARKUP_THROUGH_SUPPLY','BULL_PULLBACK_CONTINUATION')) and cand.get('MARKUP_THROUGH_SUPPLY',cand.get('BULL_PULLBACK_CONTINUATION',{})).get('score',0)>=2.5
    bear_strong=any(n in cand for n in('BEAR_PULLBACK_TRAP','SUPPLY_REJECTION_TRAP')) and max([cand[n]['score'] for n in('BEAR_PULLBACK_TRAP','SUPPLY_REJECTION_TRAP') if n in cand]+[0])>=2.5
    if not cand:
        prim='UNKNOWN_CONFLICT'; sec=''; conf='low'; sup=[]; con=[]; nsrc=0
    else:
        ordered=sorted(cand.items(),key=lambda kv:-kv[1]['score'])
        prim=ordered[0][0]; sup=cand[prim]['supports']; con=cand[prim]['conflicts']; nsrc=cand[prim]['n_src']
        sec=ordered[1][0] if len(ordered)>1 else ''
        sc=cand[prim]['score']
        conf='high' if sc>=3.5 and nsrc>=3 else ('med' if sc>=2.4 else 'low')
        if bull_strong and bear_strong: prim='UNKNOWN_CONFLICT'; sec=ordered[0][0]; conf='low'
    # risk overlay (eixo próprio): entrada take-leaning + risk_bad -> STRUCTURAL_RISK_SL_PROBLEM (não misturar c/ entrada ruim)
    risk_bad=EV['risk_bad'][0]
    take_leaning=prim in('LEGITIMATE_BEAR_BUY','MARKUP_THROUGH_SUPPLY','REVERSAL_RUNNER','BULL_PULLBACK_CONTINUATION')
    if risk_bad and take_leaning:
        sec=prim; prim='STRUCTURAL_RISK_SL_PROBLEM'; con=con+['risk_bad']
    unavail=[k for k in ('f5_range_pos_1d','f6_svp_state','f7_regime_traj') if dspa[b].get(k)=='UNAVAILABLE']
    return dict(primary=prim,secondary=sec,confidence=conf,supports=sup,conflicts=con,n_src=nsrc,unavail=unavail,EV=EV)

# ---- RODAR (Tarefa 4 outputs) ----
rows=[]; evrows=[]
for b in EP:
    a=aggregate(b)
    src_layers=sorted(set(a['EV'][f][1] for f in a['supports'])) if a['supports'] else []
    rows.append(dict(bar_idx=b,timestamp=dspa[b]['datetime'],macro_reader_leg=dec.get(b,{}).get('macro_reader_leg',''),
        dspa_primary_state=a['primary'],dspa_secondary_state=a['secondary'],confidence=a['confidence'],
        evidence_supports='|'.join(a['supports']),evidence_conflicts='|'.join(a['conflicts']),
        source_layers_used='|'.join(src_layers),unavailable_flags='|'.join(a['unavail']),
        reason_code=f"{a['primary']}<={'+'.join(a['supports'][:4])}"))
    evrows.append(dict(bar_idx=b,primary=a['primary'],secondary=a['secondary'],confidence=a['confidence'],
        supports=a['supports'],conflicts=a['conflicts'],source_layers=src_layers,unavailable=a['unavail']))
cols=list(rows[0].keys())
with open(f"{D}/l2_bpt_dspa_intermediate_states_276.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,lineterminator="\n");w.writeheader();w.writerows(rows)
with open(f"{D}/l2_bpt_dspa_intermediate_evidence_276.jsonl","w") as f:
    for r in evrows: f.write(json.dumps(r)+"\n")

from collections import Counter
print("="*80);print("DSPA CAMADA 4 — INTERMEDIATE STATES (base 276)")
dist=Counter(r['dspa_primary_state'] for r in rows)
print("distribuição primary state:",dict(dist))
print("confidence:",dict(Counter(r['confidence'] for r in rows)))

# ---- TAREFA 5: AVALIAÇÃO DIAGNÓSTICA (outcome SÓ aqui) ----
MFE={b:fn(unc[b]['mfe_R']) for b in EP}
nR=sum(1 for b in EP if MFE[b]>=5); nL=sum(1 for b in EP if MFE[b]<2); nM=sum(1 for b in EP if MFE[b]>=10)
baseR=nR/len(EP); baseL=nL/len(EP)
st_by_b={r['bar_idx']:r['dspa_primary_state'] for r in rows}
print(f"\n--- AVALIAÇÃO DIAGNÓSTICA (base runner_rate={100*baseR:.0f}% loser_rate={100*baseL:.0f}% | runners={nR} losers={nL} monumentais={nM}) ---")
print(f"{'state':28}{'n':>4}{'run%':>6}{'rLift':>6}{'los%':>6}{'lLift':>6}{'mon':>4}")
ev_rows=[]
for s in [k for k in list(STATES)+['STRUCTURAL_RISK_SL_PROBLEM','UNKNOWN_CONFLICT']]:
    bs=[b for b in EP if st_by_b[b]==s]; n=len(bs)
    if not n: continue
    run=sum(1 for b in bs if MFE[b]>=5); los=sum(1 for b in bs if MFE[b]<2); mon=sum(1 for b in bs if MFE[b]>=10)
    rr=run/n; lr=los/n
    ev_rows.append(dict(state=s,n=n,runner_pct=round(100*rr,1),runner_lift=round(rr/baseR,2),loser_pct=round(100*lr,1),loser_lift=round(lr/baseL,2),monumentals=mon))
    print(f"{s:28}{n:>4}{100*rr:>6.0f}{rr/baseR:>6.2f}{100*lr:>6.0f}{lr/baseL:>6.2f}{mon:>4}")
with open(f"{D}/l2_bpt_dspa_aggregation_da.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['state','n','runner_pct','runner_lift','loser_pct','loser_lift','monumentals'],lineterminator="\n");w.writeheader();w.writerows(ev_rows)

# distinguibilidade dos pares-chave + skip-winner/loser-take potential + null
def grp(s): return [b for b in EP if st_by_b[b]==s]
def rr(bs): return (sum(1 for b in bs if MFE[b]>=5)/len(bs)) if bs else 0
def lr(bs): return (sum(1 for b in bs if MFE[b]<2)/len(bs)) if bs else 0
print(f"\n--- DISTINGUIBILIDADE (pares-chave) ---")
print(f"  LEGITIMATE_BEAR_BUY runner%={100*rr(grp('LEGITIMATE_BEAR_BUY')):.0f} (n={len(grp('LEGITIMATE_BEAR_BUY'))}) vs BEAR_PULLBACK_TRAP runner%={100*rr(grp('BEAR_PULLBACK_TRAP')):.0f} loser%={100*lr(grp('BEAR_PULLBACK_TRAP')):.0f} (n={len(grp('BEAR_PULLBACK_TRAP'))})")
print(f"  MARKUP_THROUGH_SUPPLY runner%={100*rr(grp('MARKUP_THROUGH_SUPPLY')):.0f} (n={len(grp('MARKUP_THROUGH_SUPPLY'))}) vs SUPPLY_REJECTION_TRAP loser%={100*lr(grp('SUPPLY_REJECTION_TRAP')):.0f} (n={len(grp('SUPPLY_REJECTION_TRAP'))})")
# skip-winner recovery / loser-take cut potential vs engine policy
TAKE_LEAN={'LEGITIMATE_BEAR_BUY','MARKUP_THROUGH_SUPPLY','REVERSAL_RUNNER','BULL_PULLBACK_CONTINUATION'}
SKIP_LEAN={'BEAR_PULLBACK_TRAP','SUPPLY_REJECTION_TRAP','RANGE_CHOP_NO_EDGE'}
sw=sum(1 for b in EP if MFE[b]>=5 and eng[b]['policy'] in('SKIP','REVIEW','REVIEW_RISK') and st_by_b[b] in TAKE_LEAN)
lc=sum(1 for b in EP if MFE[b]<2 and eng[b]['policy']=='TAKE' and st_by_b[b] in SKIP_LEAN)
print(f"\n  skip-winner recovery POTENTIAL (runner em SKIP-engine, DSPA take-leaning): {sw}")
print(f"  loser-take cut POTENTIAL (loser em TAKE-engine, DSPA skip-leaning): {lc}")
# null por estado (take-leaning agregado): runner concentration vs random
rng=random.Random(13); tl=[b for b in EP if st_by_b[b] in TAKE_LEAN]; k=len(tl); obs=rr(tl); ge=0; mv=[MFE[b] for b in EP]
for _ in range(3000):
    idx=list(range(len(EP)));rng.shuffle(idx);s=idx[:k]
    if sum(1 for j in s if mv[j]>=5)/k>=obs: ge+=1
print(f"\n  TAKE-leaning agregado: n={k} runner%={100*obs:.0f} (lift {obs/baseR:.2f}) null_p={ge/3000:.3f}")
# P1/P2
def win(b): return 'P1' if dspa[b]['datetime']<'2023-01-01' else 'P2'
for w_ in('P1','P2'):
    bs=[b for b in tl if win(b)==w_]; print(f"  TAKE-leaning {w_}: n={len(bs)} runner%={100*rr(bs):.0f}")
print("\nNÃO promovido a TAKE/SKIP. NÃO automation-ready. NÃO feature dead. Diagnóstico apenas.")
print("DONE DSPA aggregation.")
