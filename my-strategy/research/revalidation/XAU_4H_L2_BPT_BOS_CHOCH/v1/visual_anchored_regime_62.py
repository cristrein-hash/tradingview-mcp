#!/usr/bin/env python3
"""BLOCO — VISUAL-ANCHORED REGIME MEASUREMENT (canon efaf48a). DIAGNÓSTICO nos 62 (ensino).
Ancora a CAMADA 1 (regime/contexto macro) na leitura VISUAL do Cris (prints + verdicts + estrutura XAU
2020-2026), substituindo o escalar regimeB QUEBRADO (over-fira em bull, cego ao bear-junk). regimeB vira
EVIDÊNCIA, não autoridade. supply lens CONDICIONADA ao regime. risk_sl eixo próprio. outcome só na calibração.
Visual-anchored regime = INPUT HUMANO discricionário (não auto-feature promovível) — calibração, não validação."""
import csv
D = "results"
pkt = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_structural_reading_packets_62.csv"))}
cal = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_structural_trade_calibration_62.csv"))}
corr = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_full62_corrected_reading.csv"))}
crisv = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0_cris_verdicts.csv"))}
def fn(v):
    try: return float(v)
    except: return None

# ---- TIMELINE MACRO-VISUAL (ancorada em prints + verdicts + estrutura XAU; date ranges YYYY-MM-DD) ----
# context_class: BULL (take-context) / RANGE (review) / BEAR (skip-context) / BOTTOM (take-convexity)
PHASES = [
 ("2020-01-01","2020-03-15","PRE_COVID_TOP_RANGE","RANGE"),
 ("2020-03-15","2020-08-07","BULL_RUN_TO_ATH2075","BULL"),
 ("2020-08-07","2021-03-31","BEAR_MARKDOWN_FROM_2075","BEAR"),
 ("2021-04-01","2021-06-10","BOTTOM_RECOVERY_BULL","BOTTOM"),
 ("2021-06-11","2021-11-10","RANGE_CHOP_2021","RANGE"),
 ("2021-11-11","2022-01-09","LOCAL_TOP_DECLINE","BEAR"),
 ("2022-01-10","2022-03-08","RALLY_TO_WAR_TOP","BULL"),
 ("2022-03-09","2022-10-25","BEAR_MARKDOWN_FROM_2070","BEAR"),
 ("2022-10-26","2022-12-31","BOTTOM_TURN_NOV2022","BOTTOM"),
 ("2023-01-01","2023-12-31","BULL_RECOVERY_RANGE_2023","BULL"),
 ("2024-01-01","2025-09-30","BULL_RUN_2024_2025","BULL"),
 ("2025-10-01","2025-11-30","CORRECTIVE_TOP_EARLY_BEAR","BEAR"),
 ("2025-12-01","2026-02-28","BULL_CONTINUATION_2026","BULL"),
 ("2026-03-01","2026-12-31","DISTRIBUTION_TOP_BEAR_2026","BEAR"),
]
def phase_of(dt):
    d=dt[:10]
    for s,e,name,ctx in PHASES:
        if s<=d<=e: return name,ctx
    return "UNKNOWN_PHASE","RANGE"

# ---- VISUAL OVERRIDE do Cris (cris_reason -> regime visual; AUTORIDADE máxima onde existe) ----
# mapeia verdicts a um regime-visual + policy de referência (ground-truth de calibração, não predicado de outcome)
def cris_override(p):
    cv=crisv.get(p,{}).get('cris_verdict',''); rs=crisv.get(p,{}).get('cris_reason','').lower()
    if not cv: return None,None,None
    if cv.startswith('PROTECT'):
        # regime visual pela razão
        if 'bullrun' in rs or 'bull run' in rs: vr='VISUAL_BULL_RUN_CONTINUATION'
        elif 'range macro bull' in rs or 'acumulacao bull' in rs or 'acumulação bull' in rs: vr='VISUAL_RANGE_BULL_ACCUMULATION'
        elif 'demand_reclaim' in rs or 'demand reclaim' in rs: vr='VISUAL_BOTTOM_TURN_RECLAIM'
        else: vr='VISUAL_BULL_RUN_CONTINUATION'
        # T34: entrada boa, falha SL -> risk axis
        pol='REVIEW_RISK_SL' if 'risk_sl' in rs or 'sl curto' in rs else 'TAKE_CANDIDATE'
        return vr,pol,cv
    if cv.startswith('BLOCK'):
        vr='VISUAL_BEAR_PULLBACK_TRAP' if 'bear' in rs else 'VISUAL_RANGE_CHOP_RISK'
        return vr,'SKIP_STRUCTURAL',cv
    if cv.startswith('REVIEW'):
        return 'VISUAL_LATE_TOP_RESIDUAL','REVIEW',cv
    return None,None,cv

RESIDUAL={'T17','T20','T24','T32'}  # micro-top/late-top auction-irredutível (provado)
def supply_in_regime(p, ctx):
    """supply lens CONDICIONADA ao regime: bull -> near/broken supply = markup (bom); bear -> supply = risco."""
    sup=pkt[p]['spec_supply']
    if ctx in('BULL','BOTTOM'):
        return 'markup_or_clear'  # supply perto em bull = rompimento, NÃO veta
    if sup in('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'): return 'supply_risk'
    return 'neutral'

def risk_axis(p):
    sl=fn(pkt[p]['sl_atr']); st=pkt[p]['spec_risk']
    if sl is not None and sl>4.0: return 'SL_TOO_WIDE_REVIEW'
    if st=='SL_TOO_SHORT': return 'SL_TOO_SHORT_REVIEW'
    return 'SL_OK'

rows=[]
for p in sorted(pkt,key=lambda x:(x[0],int(x[1:]))):
    dt=pkt[p]['datetime']; phase,ctx=phase_of(dt)
    dem=pkt[p]['spec_demand']; mom=pkt[p]['spec_momentum']; rsk=risk_axis(p)
    vr_c,pol_c,cv=cris_override(p)
    supctx=supply_in_regime(p,ctx)
    # ---- VISUAL-ANCHORED STATE + POLICY (prioridade causal: visual Cris > timeline macro > auction > regimeB-evidência) ----
    if p in RESIDUAL:
        va='VA_LATE_TOP_RESIDUAL'; pol='WATCHLIST_TRANSFORM'; why='resíduo micro-top/late-top auction-irredutível'
    elif vr_c:  # autoridade visual do Cris
        if pol_c=='TAKE_CANDIDATE': va='VA_BULL_MARKUP_TAKE' if 'BULL_RUN' in vr_c else 'VA_RANGE_BULL_REVIEW' if 'RANGE' in vr_c else 'VA_BOTTOM_TURN_TAKE'; pol='TAKE_CANDIDATE'
        elif pol_c=='REVIEW_RISK_SL': va='VA_RISK_SL_REVIEW'; pol='REVIEW'
        elif pol_c=='SKIP_STRUCTURAL': va='VA_BEAR_PULLBACK_SKIP'; pol='SKIP_STRUCTURAL'
        else: va='VA_LATE_TOP_RESIDUAL'; pol='REVIEW'
        why=f'âncora visual Cris [{cv}]: {vr_c}'
    elif ctx=='BEAR':
        va='VA_BEAR_PULLBACK_SKIP'; pol='SKIP_STRUCTURAL'; why=f'timeline macro-visual BEAR ({phase}): bull-pullback/markdown intra-bear'
    elif ctx=='BOTTOM':
        va='VA_BOTTOM_TURN_TAKE'; pol='TAKE_CANDIDATE'; why=f'timeline macro-visual BOTTOM ({phase}): reversão de fundo (convexidade)'
    elif ctx=='BULL':
        # bull macro: supply perto = markup, não veta. demanda defendida ou markup -> TAKE
        if rsk!='SL_OK':
            va='VA_RISK_SL_REVIEW'; pol='REVIEW'; why=f'bull macro ({phase}) MAS eixo risco {rsk} (camada 3)'
        else:
            va='VA_BULL_MARKUP_TAKE'; pol='TAKE_CANDIDATE'; why=f'bull macro ({phase}); supply-perto=markup não-veta; risco operável'
    else:  # RANGE
        va='VA_RANGE_BULL_REVIEW'; pol='REVIEW'; why=f'range ({phase}): precisa microestrutura/reclaim, senão review'
    # concordância feature-regime (d1_leg/regimeB) vs visual
    feat_bull = pkt[p]['macro_family']=='BULL'
    visual_bull = ctx in('BULL','BOTTOM') or (vr_c and 'BULL' in (vr_c or '') )
    agree_feat = 'YES' if (feat_bull==bool(visual_bull)) else 'NO'
    rows.append(dict(plot_id=p,datetime=dt[:10],
        cris_verdict=cv or '-', visual_phase=phase, visual_context=ctx,
        d1_leg=pkt[p]['d1_leg'], regimeB=pkt[p]['regimeB_state'], regimeB_combined=pkt[p]['regimeB_combined'],
        macro_broken=pkt[p]['macro_broken'], sup_cat=pkt[p]['sup_cat'], supply_in_regime=supctx,
        spec_demand=dem, spec_momentum=mom, legpos90=pkt[p]['legpos90'], risk_sl=rsk,
        visual_anchored_state=va, recommended_policy=pol, confidence=('high' if vr_c else 'med'),
        reason=why, feature_regime_agrees_visual=agree_feat,
        old_policy=cal[p]['FINAL_policy'], corrected_5ac3f9e=corr[p]['corrected_policy'],
        EVAL_exitype=cal[p]['EVAL_exitype'], EVAL_realR=cal[p]['EVAL_realR']))
with open(f"{D}/l2_bpt_visual_anchored_regime_reading_62.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)
from collections import Counter
print("=== VISUAL-ANCHORED policy ===",dict(Counter(r['recommended_policy'] for r in rows)))
print("=== visual_context distribution ===",dict(Counter(r['visual_context'] for r in rows)))
print("=== feature-regime concorda com visual? ===",dict(Counter(r['feature_regime_agrees_visual'] for r in rows)))
print("  -> NÃO-concordância = onde o escalar regimeB/d1 diverge do visual (o gargalo)")
print(f"divergências feature-vs-visual: {sum(1 for r in rows if r['feature_regime_agrees_visual']=='NO')}/62")
