#!/usr/bin/env python3
"""TAREFA 2 — pacote estrutural causal dos 62 (canon efaf48a). Reúne camadas por prioridade causal +
camadas anteriores como evidência condicional. outcome/exitype/realR em COLUNAS DE EVAL SEPARADAS, NUNCA
predicado. Sem 276/OOS, sem produção. Reusa artefatos causais já computados (9 especialistas, d1 backbone)."""
import csv, json
D = "results"
conf = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_macro_specialist_confluence_62.csv"))}
packs = {json.loads(l)['plot_id']: json.loads(l) for l in open(f"{D}/l2_bpt_leg_state_d1_evidence_packs.jsonl")}
v3 = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_bear_leg_block_gate_v3_62.csv"))}
micro = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_microstructure_feature_values_62.csv"))}
master = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_deep_master_matrix_62.csv"))}
vm = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
outc = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
DEEP7 = {'T2','T3','T4','T16','T17','T23','T24'}

def fn(v):
    try: return round(float(v), 3)
    except: return None

rows = []
for p in sorted(packs, key=lambda x: (x[0], int(x[1:]))):
    pk = packs[p]; d1 = pk['d1_evidence']; C = conf[p]; mz = micro[p]; M = master[p]
    bidx = int(vm[p]['episode_id']); o = outc.get(bidx, {})
    eq = pk.get('entry_quality', {}); cap = pk.get('capit', {}); mom = pk.get('momentum', {}); rk = pk.get('risk_sl', {}); svp = pk.get('svp', {})
    row = dict(
        plot_id=p, set=v3[p]['set'], datetime=pk['datetime'],
        # ---- CAMADA 1: macro contexto (D1/weekly backbone) ----
        d1_leg=pk['d1_macro_leg'], regimeB_state=d1.get('regimeB_state'), regimeB_combined=d1.get('regimeB_combined'),
        macro_broken=d1.get('macro_broken'), weekly_slope=fn(d1.get('weekly_slope')), weekly_rsi=fn(d1.get('weekly_rsi')),
        spec_regime=C['regime'], spec_mtf=C['mtf'],
        # ---- CAMADA 2: convergência auction (9 especialistas determinísticos + categóricas) ----
        sup_cat=pk.get('sup_cat'), pol_cat=pk.get('pol_cat'), demand_cat=pk.get('demand_cat'),
        has_overhead=pk.get('has_overhead'), dist_supply=fn(pk.get('dist_4h_supply')), dist_demand=fn(eq.get('dist_4h_demand')),
        supply_broken=pk.get('supply_broken'), demand_touched=eq.get('demand_touched'),
        spec_supply=C['supply'], spec_demand=C['demand'], spec_volume=C['volume'],
        below_VAL=svp.get('below_VAL'), dist_POC=fn(svp.get('dist_POC_atr')), dist_VAL=fn(svp.get('dist_VAL_atr')),
        va_width=fn(svp.get('va_width_atr')), rel_volume=fn(svp.get('rel_volume')),
        trend_30=fn(mom.get('trend_30_atr')), trend_90=fn(M.get('trend_90_atr')), rsi=fn(mom.get('rsi')),
        rsi_1d=fn(mom.get('rsi_1d')), legpos90=fn(mom.get('legpos90')), legpos30=fn(M.get('legpos30')),
        rise20=fn(M.get('rise20_atr')), drop20=fn(cap.get('drop20_atr')), bear_div=fn(mom.get('bear_div')),
        spec_momentum=C['momentum'], spec_capit=C['capit'], rsi_min8=fn(cap.get('rsi_min8')),
        sweet_spot=cap.get('sweet_spot'), reclaim_body=fn(eq.get('reclaim_body')), spec_fuel=C['fuel'],
        # convergência já computada
        macro_state=C['macro_state'], macro_family=C['family'], macro_confidence=C['confidence'],
        # ---- CAMADA 3: risco/SL/exit estrutural (eixo próprio) ----
        sl_atr=fn(rk.get('sl_atr')), sl_type=rk.get('sl_type'), spec_risk=C['risk'],
        # ---- camadas anteriores como evidência condicional (flags, não regra) ----
        bear_leg_v3=v3[p]['gate_v3'], clean_sky_flag=mz.get('clean_sky_flag'),
        micro_residual=('YES' if p in ('T17','T20','T24','T32') else 'NO'),
        deep7_member=('YES' if p in DEEP7 else 'NO'),
        # ---- EVAL ONLY (NUNCA predicado — só calibração Tarefa 5) ----
        EVAL_exitype=o.get('exitype'), EVAL_realR=fn(o.get('realR')), EVAL_sl_atr=fn(o.get('sl_atr')),
    )
    rows.append(row)
with open(f"{D}/l2_bpt_structural_reading_packets_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
print(f"pacote estrutural: {len(rows)} trades x {len(rows[0])} colunas")
print(f"  EVAL cols (separadas, não-predicado): {[c for c in rows[0] if c.startswith('EVAL_')]}")
from collections import Counter
print(f"  d1_leg:", dict(Counter(r['d1_leg'] for r in rows)))
print(f"  macro_family:", dict(Counter(r['macro_family'] for r in rows)))
print(f"  exitype (eval):", dict(Counter(r['EVAL_exitype'] for r in rows)))
