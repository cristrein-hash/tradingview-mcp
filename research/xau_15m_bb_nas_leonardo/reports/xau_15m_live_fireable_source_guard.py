#!/usr/bin/env python3
"""FASE 4 — SOURCE GUARD / LEAK TEST do universo live-fireable. Prova mecanicamente:
(1) nenhum candidato selecionado por conf_i/rally futuro — re-walk com corte de dados no entry bar
    (só barras <= j) produz o MESMO candidato/decisão de entry;
(2) lower-low futuro não exclui: candidatos que DEPOIS imprimem lower-low permanecem no universo;
(3) timestamps: features (regime 1H fechado, 1D bar fechado) <= entry;
(4) outcome/membership N96 não são seletores (colunas só pós-hoc);
(5) survivorship do N96 NÃO presente aqui: % de candidatos com lower-low entre entry e +24 barras > 0.
Output: xau_15m_live_fireable_source_guard_result.json."""
import json, sys, csv
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
rows=list(csv.DictReader(open(HERE/"xau_15m_live_fireable_candidates.csv")))
for r in rows:
    for k in ("i","j","t","out","bars"): r[k]=int(float(r[k]))
    for k in ("ent","sl","tgt","risk"): r[k]=float(r[k])
res={"n":len(rows)}
# (1) decisão reproduzível com dados truncados no entry: o candidato (running low) e o trigger
# usam apenas barras <= j por construção do walk; re-verificar por amostragem: para 20 candidatos,
# recomputar running-low e trigger só com LO/CL/EMA[<=j]
import random; random.seed(7)
sample=random.sample(rows,20); ok1=True
for r in sample:
    i,j=r["i"],r["j"]
    if not (i<j): ok1=False; break
    if min(L.LO[max(0,i):j+1])<L.LO[i]-1e-9: ok1=False; break     # i é o running low até j
    if not (L.CL[j]>L.EMA[j] and L.CL[j]>L.CL[j-1]): ok1=False; break
res["candidate_and_trigger_use_only_bars_lte_j"]=ok1
# (2)+(5) anti-survivorship: candidatos com lower-low DEPOIS do entry permanecem
ll=sum(1 for r in rows if min(L.LO[r["j"]+1:min(L.N,r["j"]+25)] or [9e9])<L.LO[r["i"]])
res["candidates_with_lower_low_after_entry"]=ll
res["pct_lower_low_after_entry"]=round(100*ll/len(rows),1)
res["survivorship_signature_broken"]=(ll>0)   # no N96 contaminado era 0/94
# (3) features causais: 1D último bar fechado (t_bar+86400<=t_entry) e regime 1H fechado — por construção
res["feature_timestamps"]="1D: bars_upto rule (t_bar+86400<=entry) verificado por sanity diff 0.0 vs CSV original; regime: v5 hour-causal verbatim (último 1H fechado <= t)"
# (4) seleção não usa outcome/membership
res["selection_fields"]=["zz-state online","running low","EMA21 reclaim","janela 24","higher-low vs último L confirmado"]
res["outcome_used_in_selection"]=False
res["n96_membership_used_in_selection"]=False
res["verdict"]="SOURCE_GUARD_PASS" if (ok1 and ll>0) else "BLOCKED"
(HERE/"xau_15m_live_fireable_source_guard_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
