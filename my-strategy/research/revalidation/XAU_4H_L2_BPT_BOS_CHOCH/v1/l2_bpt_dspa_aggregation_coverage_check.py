#!/usr/bin/env python3
"""DSPA Camada 4 — Tarefa 1: join seguro / cobertura 276/276. Para se algum join falhar. Sem outcome como input."""
import csv, json
D="results"
def keys_csv(p,kf): return set(kf(r) for r in csv.DictReader(open(p)))
dspa=keys_csv(f"{D}/l2_bpt_dspa_path_features_276.csv", lambda r:int(r['bar_idx']))
eng=keys_csv(f"{D}/l2_bpt_full276_macro_engine_confluence.csv", lambda r:int(r['bar_idx']))
ind=keys_csv(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv", lambda r:int(r['bar_idx']))
dec=keys_csv(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv", lambda r:int(r['bar_idx']))
mph=keys_csv(f"{D}/l2_bpt_full276_macro_phase_causal_candidate.csv", lambda r:int(r['episode_id']))
unc=keys_csv(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv", lambda r:int(r['bar_idx']))
bl=keys_csv(f"{D}/l2_bpt_bearleg_surgical.csv", lambda r:int(r['bar_idx']))  # só universo bear_leg (parcial esperado)
EP=dspa
rows=[]
for name,s,expect_full in [('dspa_path',dspa,True),('macro_engine',eng,True),('indicator_v2',ind,True),('decisions/prior',dec,True),('macro_phase',mph,True),('uncapped_outcome_EVAL_ONLY',unc,True),('bearleg_refined_surgical',bl,False)]:
    miss=len(EP-s); cov=len(EP&s)
    status='OK' if (cov==len(EP) or not expect_full) else 'FAIL'
    rows.append(dict(source=name,n=len(s),covers_276=cov,missing=miss,expect_full=expect_full,status=status,note=('partial=bear_leg universe only' if not expect_full else '')))
    print(f"{name:30} n={len(s):>4} cobre 276={cov:>3} missing={miss:>3} {status}")
fails=[r for r in rows if r['status']=='FAIL']
with open(f"{D}/l2_bpt_dspa_aggregation_coverage.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['source','n','covers_276','missing','expect_full','status','note'],lineterminator="\n");w.writeheader();w.writerows(rows)
print("\nJOIN", "SEGURO (todos full exceto bear_leg refined que é parcial por design)" if not fails else f"FALHOU: {[r['source'] for r in fails]} — PARAR")
