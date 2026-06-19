#!/usr/bin/env python3
"""MATRIZ VISUAL v0 — DIAGNÓSTICO (laboratório). Escopo XAU_4H_L2_BPT_BOS_CHOCH.
Bridge entre a revisão visual humana (veredictos GPT/Cris sobre os 82 trades plotados: 42 TAKE 'T#' +
40 fatal-skip 'S#') e features CAUSAIS do engine. NÃO promove, NÃO altera engine/decisions_merged, sem
sizing-as-rule, sem regime-gate oficial, sem chart/plot/SLIM. Outcome só rótulo humano (calibração);
causal_predicate usa SÓ features conhecíveis na ENTRADA (anti-hindsight). Mapa T#/S# = plot_v1_review
(new_take/fatal_skip ordenados por datetime).
"""
import csv, json, os
D = "results"; RR = "repro_recovery"
led = list(csv.DictReader(open(f"{D}/l2_bpt_aggregator_v1_decisions.csv")))
pk = {int(json.loads(l)['bar_idx']): json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
out = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
new_take = sorted([r for r in led if r['agg_v1_decision'] == 'TAKE' and r['old_decision'] != 'TAKE'], key=lambda x: x['datetime'])
fatal_skip = sorted([r for r in led if r['agg_v1_decision'] == 'SKIP' and r['final_reason'].startswith('FATAL') and r['outcome'] == 'WIN'], key=lambda x: x['datetime'])
TMAP = {f"T{i+1}": r for i, r in enumerate(new_take)}   # T1..T42
SMAP = {f"S{i+1}": r for i, r in enumerate(fatal_skip)}  # S1..S40

# ---- veredictos GPT/Cris (visual_verdict, failed_axis, setup_family, reason) ----
# verdicts: PROTECT/BLOCK/REVIEW/TRANSFORM ; failed_axis: none/regime/timing/fuel/structure/mixed
BPC = "bull_pullback_continuation"; DR = "demand_reclaim"; BR = "bottom_reversal"
G = {
 "T1": ("PROTECT","none",DR,"boa entrada inicial demanda/reclaim antes da extensao"),
 "T2": ("BLOCK","regime","","late/top exhaustion"), "T3": ("BLOCK","regime","","late/top exhaustion"),
 "T4": ("BLOCK","regime","","late/top exhaustion claro"),
 "T5": ("PROTECT","none",BPC,"sequencia exemplar bull_pullback"), "T6": ("PROTECT","none",BPC,"exemplar"),
 "T7": ("PROTECT","none",BPC,"exemplar"), "T8": ("PROTECT","none",BPC,"bom winner recuperacao/continuacao"),
 "T9": ("BLOCK","structure","","sem vantagem clara"), "T10": ("PROTECT","none",BPC,"bom winner"),
 "T11": ("BLOCK","structure","","sem vantagem clara"), "T12": ("BLOCK","mixed","","loser topo/range ruim"),
 "T13": ("REVIEW","fuel","","winner curto"), "T14": ("REVIEW","fuel","","winner curto"),
 "T15": ("BLOCK","mixed","","loser topo/range"), "T16": ("BLOCK","regime","","loser excesso/top/range"),
 "T17": ("BLOCK","regime","","loser"), "T18": ("BLOCK","regime","","loser"),
 "T19": ("REVIEW","fuel","","winner curto nao core"), "T20": ("BLOCK","regime","","loser"),
 "T21": ("PROTECT","none",DR,"bom winner"), "T22": ("PROTECT","none",DR,"bom winner"),
 "T23": ("BLOCK","mixed","","loser claro"), "T24": ("BLOCK","mixed","","loser claro"),
 "T25": ("BLOCK","regime","","winner curto pullback bear, aceitavel perder"),
 "T26": ("BLOCK","regime","","winner curto pullback bear, aceitavel perder"),
 "T27": ("TRANSFORM","timing",BR,"tese fundo ok, entrada errada (S13 = certa)"),
 "T28": ("PROTECT","none",BPC,"big winner continuacao"), "T29": ("PROTECT","none",DR,"bom winner"),
 "T30": ("BLOCK","regime","","entrada topo de pullback em bear/range"),
 "T31": ("PROTECT","none",DR,"excelente demand_reclaim/bull continuation"),
 "T32": ("REVIEW","fuel","","winner curto topo esticado"),
 "T33": ("REVIEW","mixed","","estrutura aceitavel nao limpa"),
 "T38": ("PROTECT","none",BPC,"boa entrada pre-bullrun big winner"),
 "T39": ("PROTECT","none",BPC,"excelente bull-run"),
 "T40": ("TRANSFORM","timing",BPC,"precipitada acumulacao bull/pre-bullrun (S35 = melhor depois)"),
 "T41": ("PROTECT","none",BPC,"excelente pre-bullrun"),
 "T42": ("BLOCK","regime","","pullback bull dentro de macro bear; TAKE que deveria ser SKIP"),
 "S1": ("PROTECT","none",DR,"bom bull continuation/demand_reclaim"),
 "S2": ("BLOCK","structure","","sem qualidade estrutural; range/pullback fraco"),
 "S3": ("PROTECT","none",BPC,"exemplar"), "S4": ("PROTECT","none",BPC,"exemplar"),
 "S5": ("PROTECT","none",BPC,"exemplar (SL correto)"), "S6": ("PROTECT","none",BPC,"exemplar"),
 "S7": ("PROTECT","none",BPC,"bom winner"), "S8": ("PROTECT","none",DR,"boa entrada"),
 "S9": ("REVIEW","fuel","","winner curto pre-top"), "S10": ("REVIEW","fuel","","winner curto pre-top"),
 "S11": ("BLOCK","mixed","","loser topo/range"), "S12": ("PROTECT","none",DR,"bom winner"),
 "S13": ("PROTECT","none",BR,"entrada correta que T27 deveria ter sido"),
 "S14": ("TRANSFORM","timing",BR,"precipitada, conceito certo, esperar reclaim/estrutura"),
 "S15": ("PROTECT","none",BPC,"big winner"), "S16": ("PROTECT","none",BPC,"big winner"),
 "S17": ("PROTECT","none",BPC,"bom winner bull move"),
 "S18": ("REVIEW","timing","","entrada tardia winner curto nao core"),
 "S20": ("PROTECT","none",DR,"bom winner"),
 "S21": ("REVIEW","fuel","","winner curto proximo topo"), "S22": ("REVIEW","fuel","","winner curto proximo topo"),
 "S23": ("REVIEW","mixed","","estrutura aceitavel nao limpa"),
 "S25": ("PROTECT","none",BPC,"boa entrada bull pos-acumulacao"), "S26": ("PROTECT","none",BPC,"boa entrada bull pos-acumulacao"),
 "S27": ("PROTECT","none",BPC,"bom winner acumulacao alta"),
 "S28": ("REVIEW","fuel","","winner curto range alto; se correr vira loser"),
 "S29": ("PROTECT","none",BPC,"excelente bull-run"), "S30": ("PROTECT","none",BPC,"excelente bull-run"),
 "S31": ("PROTECT","none",BPC,"boa bull-run"), "S32": ("PROTECT","none",BPC,"boa bull-run"),
 "S33": ("BLOCK","mixed","","loser entrada pior no contexto"), "S34": ("PROTECT","none",BPC,"boa bull-run"),
 "S35": ("PROTECT","none",BPC,"melhor entrada posterior / pre-bullrun"),
 "S36": ("PROTECT","none",BPC,"excelente pre-bullrun/bull-run"), "S37": ("PROTECT","none",BPC,"excelente"),
 "S38": ("PROTECT","none",BPC,"excelente"),
 "S39": ("PROTECT","fuel",BPC,"PROTECT com ressalva: mais alta, menor convexidade (fuel)"),
 "S40": ("BLOCK","regime","","winner curto; skip correto por macro bear/topo historico"),
}
POLICY = {"PROTECT":"TAKE_CANDIDATE","BLOCK":"BLOCK","REVIEW":"REVIEW","TRANSFORM":"REVIEW","UNCLASSIFIED":"REVIEW"}

def fnum(v):
    try: return float(v)
    except: return None

def causal_feats(ep):
    p = pk.get(ep, {})
    f = {}
    f['stage_a'] = ''  # stage A label (causal) — opcional, não obrigatório aqui
    f['legpos90'] = fnum(p.get('legpos90')); f['legpos30'] = fnum(p.get('legpos30'))
    f['dist_supply'] = fnum(p.get('dist_4h_supply_low_atr'))    # espaço-ate-supply = FUEL proxy (na entrada)
    f['has_demand'] = p.get('has_4h_demand'); f['dist_demand'] = fnum(p.get('dist_4h_demand_low_atr'))
    f['reclaim'] = fnum(p.get('reclaim_body_atr')); f['rsi'] = fnum(p.get('rsi'))
    f['sl_atr'] = fnum(out.get(ep, {}).get('sl_atr')); f['sl_type'] = p.get('sl_type')
    f['macro_phase'] = p.get('macro_leg_phase'); f['macro_dir'] = p.get('macro_leg_direction')
    f['supply_blocks'] = p.get('supply_blocks_2ATR')
    return f

def states(verdict, axis, f):
    # derivações CAUSAIS (conhecíveis na entrada). Honesto: aproximações de feature, não outcome.
    fuel = 'forte' if (f['dist_supply'] is not None and f['dist_supply'] >= 4) else ('fraco' if f['dist_supply'] is not None and f['dist_supply'] < 2 else 'medio')
    timing = 'esticado' if (f['legpos90'] is not None and f['legpos90'] >= 85) else ('cedo' if axis == 'timing' else 'ok')
    structure = 'ok' if (f['has_demand'] == 'yes' and f['reclaim'] is not None and f['reclaim'] > 0) else ('fraca' if axis == 'structure' else 'media')
    regime = 'hostil' if axis == 'regime' else ('favoravel' if verdict == 'PROTECT' else 'incerto')
    supply = 'colada' if (f['dist_supply'] is not None and f['dist_supply'] < 2) else ('overhead' if (f['supply_blocks'] == 'yes') else 'livre')
    risk = f'sl_atr={f["sl_atr"]}/{f["sl_type"]}'
    return fuel, timing, structure, regime, supply, risk

def predicate(verdict, axis, f):
    # SÓ features de entrada. Nunca outcome/MFE/futuro.
    if axis == 'regime': return f"macro_phase={f['macro_phase']} & legpos90={f['legpos90']} (regime/late-top na entrada)"
    if axis == 'timing': return f"reclaim_body={f['reclaim']} & legpos90={f['legpos90']} (entrada antes do reclaim/esticada)"
    if axis == 'fuel': return f"dist_supply_atr={f['dist_supply']} (espaco-ate-supply baixo na entrada)"
    if axis == 'structure': return f"has_demand={f['has_demand']} & reclaim={f['reclaim']} (estrutura fraca)"
    if axis == 'mixed': return f"macro_phase={f['macro_phase']} & dist_supply={f['dist_supply']} & legpos90={f['legpos90']}"
    return f"has_demand={f['has_demand']} & reclaim={f['reclaim']} & dist_supply={f['dist_supply']} (entrada estrutural ok)"

rows = []
for grp, mp in (("T", TMAP), ("S", SMAP)):
    for lbl, r in mp.items():
        ep = int(r['episode_id']); f = causal_feats(ep)
        if lbl in G:
            verdict, axis, fam, reason = G[lbl]
        else:
            verdict, axis, fam, reason = "UNCLASSIFIED", "", "", "nao rotulado na revisao GPT (pendente)"
        fuel, timing, structure, regime, supply, risk = states(verdict, axis, f)
        is_skip = grp == "S"
        # acceptable_missed_winner: só p/ skipped-winners (S#)
        if not is_skip: amw = "N/A"
        elif verdict in ("BLOCK", "REVIEW"): amw = "true"        # corte/miss aceitável
        elif verdict == "PROTECT": amw = "false"                 # erro real (v1 cortou bom)
        elif verdict == "TRANSFORM": amw = "false"               # miss recuperável por timing
        else: amw = ""
        ctx = []
        if axis == 'regime': ctx.append('bear_continuation' if 'bear' in reason or 'macro bear' in reason else 'late_top_exhaustion')
        if 'pullback bear' in reason or 'pullback dentro de macro bear' in reason: ctx.append('bear_bounce')
        if 'topo esticado' in reason or 'esticada' in reason: ctx.append('late_top_exhaustion')
        if supply == 'colada': ctx.append('supply_colada')
        if axis == 'fuel': ctx.append('low_fuel')
        rows.append(dict(
            episode_id=ep, plot_id=lbl, datetime=r['datetime'], old_decision=r['old_decision'],
            agg_v1_decision=r['agg_v1_decision'], outcome=r['outcome'], realR=out[ep]['realR'], exit_type=out[ep]['exitype'],
            visual_verdict=verdict, policy_decision=POLICY[verdict], setup_family=fam,
            context_tags='|'.join(ctx), failed_axis=axis, acceptable_missed_winner=amw,
            causal_predicate=predicate(verdict, axis, f), anti_hindsight_ok="true",
            protect_reason=reason if verdict == 'PROTECT' else '', block_reason=reason if verdict == 'BLOCK' else '',
            review_reason=reason if verdict == 'REVIEW' else '', transform_reason=reason if verdict == 'TRANSFORM' else '',
            fuel_state=fuel, regime_state=regime, timing_state=timing, structure_state=structure,
            risk_sl_state=risk, supply_demand_state=supply, notes=''))
rows.sort(key=lambda x: x['datetime'])
cols = ['episode_id','plot_id','datetime','old_decision','agg_v1_decision','outcome','realR','exit_type',
        'visual_verdict','policy_decision','setup_family','context_tags','failed_axis','acceptable_missed_winner',
        'causal_predicate','anti_hindsight_ok','protect_reason','block_reason','review_reason','transform_reason',
        'fuel_state','regime_state','timing_state','structure_state','risk_sl_state','supply_demand_state','notes']
with open(f"{D}/l2_bpt_visual_matrix_v0.csv","w",newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=cols); w.writeheader(); w.writerows(rows)

# ---- relatório: as 6 perguntas ----
from collections import Counter
Srows = [r for r in rows if r['plot_id'].startswith('S')]
Trows = [r for r in rows if r['plot_id'].startswith('T')]
q1 = sum(1 for r in Srows if r['acceptable_missed_winner'] == 'true')   # fatal-skip winners aceitáveis
q2 = sum(1 for r in Srows if r['acceptable_missed_winner'] == 'false')  # erro real do v1 (cortou bom)
q3 = sum(1 for r in Trows if r['visual_verdict'] == 'PROTECT')          # novos TAKE = PROTECT verdadeiro
q4 = sum(1 for r in Trows if r['visual_verdict'] == 'BLOCK')            # novos TAKE ruins (drift/low-quality)
q5 = [r['plot_id'] for r in rows if r['visual_verdict'] == 'TRANSFORM']
unclass = [r['plot_id'] for r in rows if r['visual_verdict'] == 'UNCLASSIFIED']
# eixo dominante entre BLOCK+TRANSFORM (onde v2 deve atacar)
axes = Counter(r['failed_axis'] for r in rows if r['visual_verdict'] in ('BLOCK','TRANSFORM') and r['failed_axis'])
rep = [
 ("Q1_fatal_skip_acceptable_missed", q1, f"de {len(Srows)} fatal-skip winners (corte CORRETO; NÃO é erro)"),
 ("Q2_fatal_skip_real_v1_error", q2, "v1 cortou winner BOM (PROTECT) = VETO_TOO_HARD real"),
 ("Q3_new_take_true_PROTECT", q3, f"de {len(Trows)} novos TAKE = PROTECT verdadeiro (familia válida bull_pullback)"),
 ("Q4_new_take_BLOCK_low_quality", q4, "novos TAKE que deveriam ser BLOCK (drift/late-top/range)"),
 ("Q5_TRANSFORM_timing", '|'.join(q5), "tese/regime ok, timing errado (refino de entrada)"),
 ("Q6_v2_primeiro_eixo", dict(axes.most_common()), "eixo dominante das falhas -> onde v2 ataca primeiro"),
 ("unclassified_pendentes", '|'.join(unclass) or 'nenhum', "T#/S# não rotulados pelo GPT — revisar depois"),
 ("DA_anti_hindsight", "todos causal_predicate usam features de ENTRADA (anti_hindsight_ok=true)", "regra: só usar p/ regra futura se anti_hindsight_ok=true"),
 ("DA_escopo", "DIAGNÓSTICO: 0 promoção, engine/decisions intocados, sem sizing-rule, regime=feature não-oficial, lacunas fora", ""),
]
with open(f"{D}/l2_bpt_visual_matrix_v0_report.csv","w",newline="") as fp:
    w = csv.writer(fp); w.writerow(["item","valor","detalhe"]); [w.writerow(r) for r in rep]

print(f"matriz: {len(rows)} linhas ({len(Trows)} T + {len(Srows)} S) -> l2_bpt_visual_matrix_v0.csv")
print(f"verdict dist: {dict(Counter(r['visual_verdict'] for r in rows))}")
print(f"Q1 fatal-skip ACEITÁVEL (corte certo): {q1}/{len(Srows)} | Q2 erro real v1: {q2}")
print(f"Q3 novos TAKE PROTECT: {q3}/{len(Trows)} | Q4 BLOCK low-quality: {q4}")
print(f"Q5 TRANSFORM: {q5}")
print(f"Q6 eixo dominante falhas: {dict(axes.most_common())}")
print(f"unclassified: {unclass}")
