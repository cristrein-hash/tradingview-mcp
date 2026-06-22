#!/usr/bin/env python3
"""L2/BPT — Tarefa 6: reavaliar PRIOR LAYERS sob o NOVO target (convexidade uncapped). DIAGNÓSTICO.
Cada layer = predicado de BLOCK (runners_cut ruim vs losers_cut bom) ou TAKE (preserva runners). Mede
trade-off sob runners(MFE>=5)/losers(MFE<2). Prior layers vivas como evidência condicional. Sem produção/OOS.
NOTA reprodutibilidade: este script materializa a tabela que antes foi gerada inline (correção DA aad41aa)."""
import csv
D="results"
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
mph={int(r['episode_id']):r['macro_phase_causal'] for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_phase_causal_candidate.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
def fn(v):
    try:return float(v)
    except:return None
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
RUN=[b for b in EP if MFE[b]>=5]; LOS=[b for b in EP if MFE[b]<2]; nR=len(RUN); nL=len(LOS)
def lay_block(name,pred):
    rc=sum(1 for b in RUN if pred(b)); lc=sum(1 for b in LOS if pred(b))
    lift=round((lc/nL)/((rc/nR) if rc else 1e-9),2)
    return dict(layer=name,runners_cut=rc,runners_cut_pct=round(100*rc/nR,1),losers_cut=lc,losers_cut_pct=round(100*lc/nL,1),
        lift_loser_over_runner=lift,net_score=lc-rc,
        status=('USEFUL' if lc-rc>=10 and rc<=3 else 'KILLS_RUNNERS' if rc>5 else 'WEAK' if lc-rc<5 else 'CONDITIONAL'))
def lay_take(name,pred):
    rk=sum(1 for b in RUN if pred(b)); lk=sum(1 for b in LOS if pred(b))
    return dict(layer=name+'(TAKE)',runners_cut=-rk,runners_cut_pct=round(100*rk/nR,1),losers_cut=-lk,losers_cut_pct=round(100*lk/nL,1),
        lift_loser_over_runner=round((lk/nL)/((rk/nR) if rk else 1e-9),2),net_score=rk-lk,
        status=('USEFUL_TAKE' if rk-lk>=8 else 'WEAK_TAKE' if rk-lk<3 else 'CONDITIONAL_TAKE'))
LAYERS=[
 ('bear_leg_block',lambda b: dec[b].get('macro_reader_leg')=='MACRO_BEAR_LEG'),
 ('supply_reject_block',lambda b: dec[b].get('sup_cat') in('SUPPLY_NEAR_AND_REJECTING','SUPPLY_FRESH_DANGEROUS','SUPPLY_BLOCKS_TARGET')),
 ('indicator_TOP_skip',lambda b: xv2.get(b,{}).get('context')=='TOP'),
 ('macro_phase_not_BULLRUN',lambda b: mph.get(b)!='MACRO_BULL_RUN'),
 ('regimeB_broken',lambda b: dec[b].get('macro_broken')=='True'),
 ('range_transition',lambda b: dec[b].get('macro_reader_leg') in('MACRO_RANGE','MACRO_TRANSITION')),
 ('engine_SKIP',lambda b: eng[b].get('policy') in('SKIP','REVIEW','REVIEW_RISK')),
]
TAKES=[
 ('bottom_turn',lambda b: dec[b].get('bottom_turn')=='True'),
 ('capit_climax',lambda b: dec[b].get('capit')=='CLIMAX_RECLAIM'),
 ('clean_sky',lambda b: dec[b].get('clean_sky_flag')=='True'),
 ('macro_phase_BULLRUN',lambda b: mph.get(b)=='MACRO_BULL_RUN'),
]
rows=[lay_block(n,p) for n,p in LAYERS]+[lay_take(n,p) for n,p in TAKES]
print(f"PRIOR LAYERS sob convexidade (runners={nR} losers={nL})")
for r in rows: print(f"{r['layer']:26}{r['runners_cut']:>6}{r['losers_cut']:>6} lift={r['lift_loser_over_runner']:>5} {r['status']}")
with open(f"{D}/l2_bpt_prior_layers_under_exit_target_276.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['layer','runners_cut','runners_cut_pct','losers_cut','losers_cut_pct','lift_loser_over_runner','net_score','status'],lineterminator="\n")
    w.writeheader();w.writerows(rows)
print("DONE (script materializado).")
