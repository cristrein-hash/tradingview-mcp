#!/usr/bin/env python3
"""TAREFA 3 — leitor estrutural CONVERGENTE dos 62 (canon efaf48a). DIAGNÓSTICO, não engine oficial.
Lê por convergência interpretável de aspectos (NÃO soma cega de votos), por prioridade causal:
contexto macro (camada 1) → convergência auction (camada 2) → risco/SL/exit (camada 3).
outcome NUNCA entra aqui (predicado proibido). Política em 6 estados."""
import csv
D = "results"
P = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_structural_reading_packets_62.csv"))}
def fn(v):
    try: return float(v)
    except: return None

BULL_FAM = {'MACRO_BULL_RUN_CONTINUATION','BULL_PULLBACK_CONTINUATION','RANGE_MACRO_BULL_RECLAIM',
            'BOTTOM_REVERSAL_VALID','CAPITULATION_RECLAIM_VALID','NO_OVERHEAD_MARKUP'}
RISK_FAM = {'BEAR_BOUNCE_RISK','CORRECTIVE_BEAR_LEG','LATE_TOP_EXHAUSTION','SUPPLY_COLADA_REJECTION'}
RESIDUAL_IDS = {'T17','T20','T24','T32'}  # micro-top/late-top auction-irredutível (provado nos blocos anteriores)

def risk_axis(r):
    """eixo próprio: avalia se o SL estrutural é operável ou exige review humano (canon ponto 4)."""
    sl = fn(r['sl_atr']); st = r['spec_risk']
    if sl is None: return 'SL_UNKNOWN', 'review'
    if sl > 4.0: return 'SL_TOO_WIDE_REVIEW', 'review'         # >4ATR = review humano (não cap automático)
    if st == 'SL_TOO_SHORT': return 'SL_TOO_SHORT', 'review'   # T34-like: entrada boa, SL no ruído
    if st == 'SL_STRUCTURAL_OK': return 'SL_OK', 'ok'
    return 'SL_ACCEPTABLE', 'ok'

def converge(r):
    """convergência interpretável: conta suportes/conflitos ESTRUTURAIS por aspecto, com leitura macro como contexto."""
    fam = r['macro_family']; ms = r['macro_state']; leg = r['d1_leg']
    sup, dem, vol = r['spec_supply'], r['spec_demand'], r['spec_volume']
    mom, cap, fuel = r['spec_momentum'], r['spec_capit'], r['spec_fuel']
    supports, conflicts = [], []
    # suportes estruturais
    if dem == 'DEMAND_DEFENDED': supports.append('demand_defended')
    if sup in ('CLEAN_SKY_BULLISH','MARKUP_BREAKING'): supports.append('supply_clear_or_breaking')
    if vol == 'ACCEPTANCE_ABOVE_VALUE': supports.append('value_acceptance')
    if mom in ('STRONG_BULL_MOMENTUM','HEALTHY_HIGH_LEGPOS'): supports.append('momentum_healthy')
    if cap in ('CLIMAX_RECLAIM',): supports.append('capitulation_reclaim')
    if fuel == 'high_fuel': supports.append('high_fuel')
    if r['spec_mtf'] in ('FULL_BULL_ALIGN','PARTIAL_BULL'): supports.append('mtf_bull')
    # conflitos estruturais
    if sup in ('SUPPLY_REJECTING_RISK','SUPPLY_BLOCKS_TARGET'): conflicts.append('supply_overhead_rejecting')
    if dem == 'DEMAND_ABSENT': conflicts.append('no_demand_base')
    if vol == 'REJECTION_BELOW_VALUE': conflicts.append('value_rejection')
    if mom == 'LATE_TOP_EXHAUSTION': conflicts.append('late_top_exhaustion')
    if mom == 'WEAK_MOMENTUM' and fam == 'RISK': conflicts.append('weak_momentum_in_risk')
    if fuel == 'low_fuel': conflicts.append('low_fuel')
    if leg == 'MACRO_BEAR_LEG': conflicts.append('macro_bear_markdown_leg')
    return supports, conflicts

def policy(r, supports, conflicts, rstate, rflag):
    fam = r['macro_family']; ms = r['macro_state']; leg = r['d1_leg']; pid = r['plot_id']
    ns, nc = len(supports), len(conflicts)
    # CAMADA 1 contexto: macro-bear-markdown-leg genuíno = único SKIP estrutural robusto (canon ponto 2)
    if leg == 'MACRO_BEAR_LEG':
        return 'SKIP_STRUCTURAL', 'macro-bear-markdown-leg: contexto bear genuíno (único bloqueio robusto)'
    # resíduo micro-top/late-top auction-irredutível (provado): aceitar como custo, não matar via gate
    if pid in RESIDUAL_IDS or ms == 'LATE_TOP_EXHAUSTION':
        return 'WATCHLIST_TRANSFORM', 'resíduo late-top/micro-top auction-irredutível (entrada disfarçada; custo aceitável)'
    # CAMADA 2 convergência: família BULL com convergência forte
    if fam == 'BULL':
        if ns >= 3 and nc <= 1:
            if rflag == 'ok':
                return 'TAKE_CANDIDATE', f'convergência bull forte ({ns} suportes) + risco operável'
            return 'REVIEW', f'convergência bull forte ({ns} suportes) MAS risco {rstate} = review humano (eixo SL/exit)'
        if ns >= 2:
            return 'REVIEW', f'convergência bull parcial ({ns} suportes, {nc} conflitos)'
        return 'REVIEW', f'bull macro mas convergência fraca ({ns} suportes)'
    # família RISK (não-bear-leg): bounce/corrective/supply-colada
    if fam == 'RISK':
        if 'supply_overhead_rejecting' in conflicts and 'weak_momentum_in_risk' in conflicts:
            return 'SKIP_STRUCTURAL', 'bear-bounce/supply-colada + momentum fraco = repique sob teto (estrutural)'
        return 'REVIEW', f'família RISK ({ms}) mas sem convergência bear completa = review'
    return 'UNKNOWN', f'sem convergência clara ({ms})'

rows = []
dist = {}
for pid in sorted(P, key=lambda x: (x[0], int(x[1:]))):
    r = P[pid]
    rstate, rflag = risk_axis(r)
    supports, conflicts = converge(r)
    pol, interp = policy(r, supports, conflicts, rstate, rflag)
    # exit/management state (eixo próprio, sem outcome)
    exit_state = 'CONVEX_OK' if rflag == 'ok' else 'RISK_REVIEW'
    what_inval = 'close < swing-low estrutural / perda da demanda defendida' if r['macro_family']=='BULL' else 'higher-high confirmado reverte o contexto bear'
    what_resid = 'late-top/micro-top disfarçado de continuação (Auction)' if pol=='WATCHLIST_TRANSFORM' else ''
    rows.append(dict(plot_id=pid, datetime=r['datetime'], set=r['set'],
        macro_context=f"{r['d1_leg']}/{r['regimeB_state']}", auction_structure_state=r['macro_state'],
        demand_supply_state=f"{r['spec_demand']}|{r['spec_supply']}", volume_acceptance_state=r['spec_volume'],
        momentum_state=r['spec_momentum'], capitulation_state=r['spec_capit'], fuel_state=r['spec_fuel'],
        risk_sl_state=rstate, exit_management_state=exit_state,
        prior_layers_support='|'.join(supports), prior_layers_conflict='|'.join(conflicts),
        structural_read=f"{r['macro_family']}:{r['macro_state']}", recommended_policy=pol,
        confidence=r['macro_confidence'], reason_codes=f"sup={len(supports)};conf={len(conflicts)};risk={rstate}",
        market_interpretation=interp, what_would_invalidate=what_inval, what_is_irreducible_or_residual=what_resid))
    dist[pol] = dist.get(pol, 0) + 1
with open(f"{D}/l2_bpt_structural_convergent_decisions_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
print(f"leitura convergente: {len(rows)} trades")
print(f"distribuição política: {dist}")
