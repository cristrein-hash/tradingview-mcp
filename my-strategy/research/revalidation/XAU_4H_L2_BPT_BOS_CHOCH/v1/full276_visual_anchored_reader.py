#!/usr/bin/env python3
"""FULL 276 — leitura estrutural com predicados CAUSAIS congelados da leitura visual-ancorada (canon efaf48a).
DIAGNÓSTICO. NÃO usa: plot_id, labels Cris, outcome, realR, hindsight, fase-visual-com-futuro.
Onde a leitura exige julgamento VISUAL não-reproduzível causalmente → HUMAN_VISUAL_REQUIRED (não inventa).
Reusa decisions causais já computadas (macro_leg/broken/combined/weekly D-1, sup_cat, capit, demand, drop20,
bottom_turn) + 84-stream (sl_atr/sl_type/legpos/supply). outcome só em colunas EVAL (Tarefa 5)."""
import csv, bisect
D = "results"
dec = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
tqm = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_matrix.csv"))}
outc = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
def fn(v):
    try: return float(v)
    except: return None

# ---- TAREFA 3: manifesto de predicados causais congelados ----
MANIFEST = [
 ("d1_macro_leg","D1/weekly backbone (causal shift D-1)","contexto camada-1, não gate isolado","CAUSAL"),
 ("genuine_bear=MACRO_BEAR_LEG","único bloqueio robusto causal","SKIP_STRUCTURAL","CAUSAL"),
 ("corrective_shallow=CORRECTIVE & drop20<1.0 & not bottom_turn","corrective raso sem flush (bear-leg v3)","SKIP_STRUCTURAL","CAUSAL"),
 ("bear_confluence=RANGE/TRANS & macro_broken & combined<0 & weekly_slope<=0","bear-context causal (regime quebrado+combined neg+weekly não-sobe)","SKIP_STRUCTURAL","CAUSAL"),
 ("ambiguous_bear=RANGE/TRANS & macro_broken & combined<0 & weekly_slope>0","regime quebrado MAS weekly subindo (caso T9): visual necessário","HUMAN_VISUAL_REQUIRED","HUMAN"),
 ("supply_in_bull=BULL_LEG: supply-perto/rompida=markup","NÃO vetar por under-supply em bull (inversão corrigida)","não-veta","CAUSAL"),
 ("supply_in_bear: rejection/near=risco","supply colada em bear = risco","conflito","CAUSAL"),
 ("regimeB_not_authority: broken&combined<0 NÃO sobrepõe BULL_LEG confirmado","over-fire guard (T19/T34)","mantém bull-context","CAUSAL"),
 ("risk_sl_axis: sl_atr>4 OR SL_TOO_SHORT","entrada pode ser boa + SL ruim (T34-like)","REVIEW(risk), não corte de entrada","CAUSAL"),
 ("bottom_turn=climax OR (rsi_min8<=32 & reclaim>=0.4 & demand_defended)","reversão de fundo (convexidade)","TAKE","CAUSAL"),
 ("micro_top_residual=range-bull high-legpos","T17/T20-like: feature-missing, NÃO filtro auto","HUMAN_VISUAL_REQUIRED/REVIEW","HUMAN"),
 ("clean_sky_vacuo","flag contextual de supply, nunca regra","flag","CAUSAL"),
]
with open(f"{D}/l2_bpt_full276_visual_anchored_predicate_manifest.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(["predicado","aprendizado","papel","reprodutibilidade"]);[w.writerow(r) for r in MANIFEST]

def risk_axis(b):
    sl=fn(tqm[b].get('sl_atr')); st=tqm[b].get('sl_type','')
    if sl is not None and sl>4.0: return 'SL_TOO_WIDE'
    if st in('LATE_WIDE',) or (sl is not None and sl>5): return 'SL_LATE_WIDE'
    # SL_TOO_SHORT: heurística — sl<0.7 ATR
    if sl is not None and sl<0.7: return 'SL_TOO_SHORT'
    return 'SL_OK'

def reader(b):
    d=dec[b]; t=tqm[b]; leg=d['macro_reader_leg']; mb=d['macro_broken'] in('True',True)
    cs=fn(d['d1_combined']); wsl=fn(d['weekly_slope']); drop=fn(d['drop20_atr']); bt=d['bottom_turn']=='True'
    supc=d['sup_cat']; legpos=fn(t.get('legpos90')); rsk=risk_axis(b); rc=[]
    # bottom-turn (convexidade) tem precedência fora de bull-leg
    if bt and leg!='MACRO_BULL_LEG':
        return 'TAKE_CANDIDATE','VA_BOTTOM_TURN','bottom_turn (reversão de fundo, convexidade)',rsk,'NO'
    # CAMADA 1: bear genuíno causal
    if leg=='MACRO_BEAR_LEG':
        return 'SKIP_STRUCTURAL','VA_BEAR_MARKDOWN','MACRO_BEAR_LEG (bloqueio robusto causal)',rsk,'NO'
    if leg=='MACRO_CORRECTIVE_PULLBACK' and not bt and drop is not None and drop<1.0:
        return 'SKIP_STRUCTURAL','VA_CORRECTIVE_SHALLOW','corrective raso sem flush (drop<1.0)',rsk,'NO'
    if leg in('MACRO_RANGE','MACRO_TRANSITION') and mb and cs is not None and cs<0:
        if wsl is not None and wsl<=0:
            return 'SKIP_STRUCTURAL','VA_BEAR_PULLBACK','bear-context causal (broken+combined<0+weekly<=0)',rsk,'NO'
        return 'HUMAN_VISUAL_REQUIRED','VA_AMBIGUOUS_BEAR','regime quebrado MAS weekly subindo (T9-like): visual necessário',rsk,'YES'
    # CAMADA 1 bull-leg: bull-context, supply-perto=markup (não veta)
    if leg=='MACRO_BULL_LEG':
        if rsk!='SL_OK':
            return 'REVIEW','VA_RISK_SL','bull-leg MAS eixo risco/SL (camada 3)',rsk,'NO'
        return 'TAKE_CANDIDATE','VA_BULL_MARKUP','bull-leg; supply-perto=markup não-veta; risco operável',rsk,'NO'
    # RANGE/TRANSITION sem bear-confluence
    if leg in('MACRO_RANGE','MACRO_TRANSITION'):
        # range-bull com legpos alto = possível micro-top residual = visual necessário
        if legpos is not None and legpos>=85:
            return 'HUMAN_VISUAL_REQUIRED','VA_RANGE_HIGH_LEGPOS','range/transition + legpos alto = micro-top/residual: visual necessário',rsk,'YES'
        if rsk!='SL_OK':
            return 'REVIEW','VA_RISK_SL','range/transition + eixo risco',rsk,'NO'
        return 'REVIEW','VA_RANGE_REVIEW','range/transition: precisa microestrutura/reclaim',rsk,'NO'
    return 'UNKNOWN','VA_UNKNOWN','sem leitura clara',rsk,'NO'

order = sorted(dec.keys(), key=lambda b: dec[b]['datetime'])
rows=[]
for b in order:
    d=dec[b]; t=tqm[b]; o=outc.get(b,{})
    pol,va,why,rsk,hvr = reader(b)
    rows.append(dict(episode_id=b, datetime=d['datetime'], macro_context=d['macro_reader_leg'],
        visual_anchored_regime_proxy=va, auction_structure_state=d['sup_cat'],
        demand_supply_state=f"{d['demand']}|{d['sup_cat']}", volume_acceptance_state=('below_VAL' if t.get('below_VAL') in('True','1') else 'in/above_value'),
        momentum_state=('weak' if fn(t.get('trend_30_atr')) is not None and fn(t['trend_30_atr'])<0 else 'bull'),
        capitulation_state=d['capit'], fuel_state=('clean_sky' if d['clean_sky_flag'] in('True',True) else 'overhead'),
        risk_sl_state=rsk, microstructure_flag=('RESIDUAL_HIGH_LEGPOS' if 'HIGH_LEGPOS' in va else 'none'),
        human_visual_required=hvr, final_policy=pol, confidence=('high' if pol in('SKIP_STRUCTURAL','TAKE_CANDIDATE') else 'med'),
        reason_codes=why, regimeB=d['d1_regimeB'], combined=d['d1_combined'], macro_broken=d['macro_broken'], weekly_slope=d['weekly_slope'],
        # EVAL ONLY
        EVAL_exitype=o.get('exitype'), EVAL_realR=fn(o.get('realR'))))
with open(f"{D}/l2_bpt_full276_visual_anchored_reading.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)
from collections import Counter
print(f"276 lidos. final_policy:",dict(Counter(r['final_policy'] for r in rows)))
print("human_visual_required:",sum(1 for r in rows if r['human_visual_required']=='YES'),"/276")
print("por macro_context (TAKE):",dict(Counter(r['macro_context'] for r in rows if r['final_policy']=='TAKE_CANDIDATE')))
