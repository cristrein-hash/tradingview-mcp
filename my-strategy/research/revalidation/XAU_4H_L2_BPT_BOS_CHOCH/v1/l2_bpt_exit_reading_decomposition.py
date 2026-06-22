#!/usr/bin/env python3
"""L2/BPT — Tarefas 3-5: separar valor de EXIT vs valor de LEITURA + mapa do gargalo macro/auction.
T3: decomposição A/B/C/D/E (trade ruim salvo por exit / bom prejudicado por exit / bom preservado / ruim mantido / residual).
T4: error map — winners SKIPADOS (runner mas reading cortou) + losers MANTIDOS (loser mas reading tomou) com CONTEXTO.
T5: bottleneck classification por episódio.
Junta: uncapped outcomes (verdade runner) + engine policy + regime/context + indicator context.
DIAGNÓSTICO. Outcome só avaliação, nunca predicado. Full 276. Sem produção/promoção/OOS."""
import csv
D="results"
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
exitcal={}  # realized por política (recompute leve do uncapped: capped, letrun, vstair)
for b,r in unc.items():
    exitcal[b]=dict(capped=float(r['capped_realR']),letrun=float(r['realized_letrun_120']),vstair=float(r['realized_vstair_120']))
def fn(v):
    try:return float(v)
    except:return None
EP=sorted(unc)

def ctx(b):
    """estado estrutural causal do episódio (da decisions + indicator)."""
    d=dec.get(b,{}); e=eng.get(b,{}); x=xv2.get(b,{})
    leg=d.get('macro_reader_leg',''); mb=d.get('macro_broken')=='True'; wsl=fn(d.get('weekly_slope'))
    sup=d.get('sup_cat',''); cap=d.get('capit',''); dem=d.get('demand',''); bt=d.get('bottom_turn')=='True'
    cs=d.get('clean_sky_flag')=='True'; drop=fn(d.get('drop20_atr'))
    icx=x.get('context','')  # TOP/BOTTOM/PULLBACK
    # rótulos estruturais
    bear_leg = leg=='MACRO_BEAR_LEG'
    bull_pullback_in_bear = (leg in('MACRO_RANGE','MACRO_TRANSITION','MACRO_CORRECTIVE_PULLBACK') and mb and (wsl is not None and wsl<=0))
    range_top = (leg in('MACRO_RANGE','MACRO_TRANSITION') and icx=='TOP')
    supply_reject = sup in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS','SUPPLY_BLOCKS_TARGET')
    return dict(leg=leg,bear_leg=bear_leg,bull_pullback_in_bear=bull_pullback_in_bear,range_top=range_top,
        supply_reject=supply_reject,bottom_turn=bt,clean_sky=cs,capit=cap,demand=dem,icx=icx,mb=mb,sup=sup,
        policy=e.get('policy',''),family=e.get('family',''),momentum=e.get('momentum',''))

# ---- T3: decomposição A/B/C/D/E ----
dec_rows=[]
for b in EP:
    mfe=fn(unc[b]['mfe_R']); cap=exitcal[b]['capped']; lr=exitcal[b]['letrun']
    stop2=unc[b]['stop_before_2R']=='1'; c=ctx(b)
    runner=mfe>=5; loser=mfe<2
    if runner and c['policy']=='TAKE' and lr>=mfe*0.5: cls='C_bom_preservado'
    elif runner and cap<mfe-3: cls='B_bom_prejudicado_exit'          # exit clipou um runner
    elif runner: cls='B_bom_prejudicado_exit'
    elif loser and c['policy']=='TAKE': cls='D_ruim_mantido'
    elif loser and lr>cap+0.5: cls='A_ruim_salvo_exit'
    elif loser: cls='E_residual'
    else: cls='C_bom_preservado' if lr>0 else 'E_residual'
    dec_rows.append(dict(bar_idx=b,datetime=unc[b]['datetime'],mfe_R=mfe,capped=cap,letrun=lr,
        policy=c['policy'],class_ABCDE=cls,leg=c['leg'],context=c['icx']))
from collections import Counter
print("T3 — DECOMPOSIÇÃO EXIT vs LEITURA:",dict(Counter(r['class_ABCDE'] for r in dec_rows)))
with open(f"{D}/l2_bpt_exit_vs_reading_decomposition_276.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(dec_rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(dec_rows)

# ---- T4: ERROR MAP — winners skipados + losers mantidos ----
SKIP_POL={'SKIP','REVIEW','REVIEW_RISK'}
win_skip=[]; los_kept=[]
for b in EP:
    mfe=fn(unc[b]['mfe_R']); c=ctx(b); stop2=unc[b]['stop_before_2R']=='1'
    if mfe>=5 and c['policy'] in SKIP_POL:   # runner que a leitura cortou
        win_skip.append(dict(bar_idx=b,datetime=unc[b]['datetime'],mfe_R=mfe,policy=c['policy'],leg=c['leg'],
            context=c['icx'],bottom_turn=c['bottom_turn'],clean_sky=c['clean_sky'],capit=c['capit'],
            supply=c['sup'],why_cut=('bottom_turn' if c['bottom_turn'] else 'bull_markup' if c['family']=='BULL' else 'bear_ctx_cut' if c['bear_leg'] else 'risk_or_range')))
    if mfe<2 and stop2 and c['policy']=='TAKE':  # loser que a leitura tomou
        los_kept.append(dict(bar_idx=b,datetime=unc[b]['datetime'],mfe_R=mfe,policy=c['policy'],leg=c['leg'],
            context=c['icx'],bear_leg=c['bear_leg'],bull_pullback_in_bear=c['bull_pullback_in_bear'],
            range_top=c['range_top'],supply_reject=c['supply_reject'],
            why_kept=('bear_pullback_long' if c['bull_pullback_in_bear'] else 'range_top_trap' if c['range_top'] else 'supply_misread' if c['supply_reject'] else 'bull_no_run')))
print(f"\nT4 — WINNERS SKIPADOS: {len(win_skip)} | por motivo:",dict(Counter(r['why_cut'] for r in win_skip)))
print(f"     LOSERS MANTIDOS:  {len(los_kept)} | por motivo:",dict(Counter(r['why_kept'] for r in los_kept)))
print(f"     winners skipados por contexto:",dict(Counter(r['context'] for r in win_skip)))
print(f"     losers mantidos por leg:",dict(Counter(r['leg'] for r in los_kept)))
with open(f"{D}/l2_bpt_macro_reading_error_map_276.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['type','bar_idx','datetime','mfe_R','policy','leg','context','signature'])
    for r in win_skip: w.writerow(['WINNER_SKIPPED',r['bar_idx'],r['datetime'],r['mfe_R'],r['policy'],r['leg'],r['context'],r['why_cut']])
    for r in los_kept: w.writerow(['LOSER_KEPT',r['bar_idx'],r['datetime'],r['mfe_R'],r['policy'],r['leg'],r['context'],r['why_kept']])

# ---- T5: bottleneck classification por episódio ----
bn_rows=[]
for b in EP:
    mfe=fn(unc[b]['mfe_R']); cap=exitcal[b]['capped']; lr=exitcal[b]['letrun']; c=ctx(b)
    stop2=unc[b]['stop_before_2R']=='1'; runner=mfe>=5; loser=mfe<2
    if runner and c['policy']=='TAKE' and cap<mfe-3: bn='EXIT_ONLY'           # leu certo, exit clipou
    elif runner and c['policy'] in SKIP_POL and c['bottom_turn']: bn='BOTTOM_TURN'
    elif runner and c['policy'] in SKIP_POL: bn='READING_ONLY'                # runner cortado pela leitura
    elif loser and c['policy']=='TAKE' and c['bull_pullback_in_bear']: bn='BEAR_PULLBACK_LONG'
    elif loser and c['policy']=='TAKE' and c['range_top']: bn='RANGE_TOP_TRAP'
    elif loser and c['policy']=='TAKE' and c['supply_reject']: bn='SUPPLY_CONTEXT'
    elif loser and c['policy']=='TAKE' and c['bear_leg']: bn='REGIME_CONTEXT'
    elif loser and c['policy']=='TAKE': bn='READING_ONLY'
    elif stop2 and mfe>=3: bn='RISK_SL'                                       # stopou cedo mas tinha corrida
    elif loser: bn='RESIDUAL'
    else: bn='EXIT_ONLY' if cap<mfe-2 else 'RESIDUAL'
    bn_rows.append(dict(bar_idx=b,datetime=unc[b]['datetime'],mfe_R=mfe,policy=c['policy'],leg=c['leg'],bottleneck=bn))
print("\nT5 — BOTTLENECK por episódio:",dict(Counter(r['bottleneck'] for r in bn_rows)))
with open(f"{D}/l2_bpt_bottleneck_classification_276.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(bn_rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(bn_rows)
print("\nDONE T3-T5.")
