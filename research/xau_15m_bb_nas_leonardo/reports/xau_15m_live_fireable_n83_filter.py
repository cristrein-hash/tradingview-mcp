#!/usr/bin/env python3
"""FASE 5+6 — aplicar o INTRA-BEAR CAPITULATION FILTER ao universo live-fireable + SL V1/3R métricas.
Filtro (inalterado): SKIP se regime==BEAR e px_vs_ema_1d>=0. Painéis: base live-fireable vs filtrado,
per-year/regime; comparação com N83 contaminado (referência). Outcomes usados SÓ para avaliação.
Outputs: xau_15m_live_fireable_n83_filter_result.json (+ sl_exit result no mesmo run)."""
import json, sys, csv
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
rows=list(csv.DictReader(open(HERE/"xau_15m_live_fireable_candidates.csv")))
for r in rows:
    for k in ("i","j","t","out","bars"): r[k]=int(float(r[k]))
    for k in ("ent","sl","tgt","risk"): r[k]=float(r[k])
    r["px_vs_ema_1d"]=float(r["px_vs_ema_1d"]) if r["px_vs_ema_1d"] else None
def R_of(r): return 3.0 if r["out"]==1 else -1.0
def seg(rs,key):
    o={}
    for r in rs: o.setdefault(key(r),[]).append(R_of(r))
    return {k:L.panel(v) for k,v in sorted(o.items())}
skip=[r for r in rows if r["regime"]=="BEAR" and (r["px_vs_ema_1d"] is not None and r["px_vs_ema_1d"]>=0)]
keep=[r for r in rows if r not in skip]
res={"filter":"SKIP se regime==BEAR e px_vs_ema_1d>=0 (inalterado)",
     "n_base":len(rows),"n_skipped":len(skip),"n_kept":len(keep),
     "skip_by_outcome":{"losers_cut":sum(1 for r in skip if r["out"]==0),"winners_cut":sum(1 for r in skip if r["out"]==1)},
     "base_panel":L.panel([R_of(r) for r in rows]),
     "kept_panel":L.panel([R_of(r) for r in keep]),
     "kept_per_year":seg(keep,lambda r:r["d"][:4]),
     "kept_per_regime":seg(keep,lambda r:r["regime"]),
     "contaminated_reference":{"N83":83,"WR":62.7,"sumR":125.0,"nota":"NÃO comparável como validação — base com survivorship"},
     "matched_orig_cut_in_universe":sum(1 for r in rows if r.get("matched_n96") and int(float(r["matched_n96"] or 0)) in (24,25,55,56,57,58,59,66,67,79,83,84,85))}
# timeouts=0 já provado; leg_state todos MARKUP_CANDIDATE_LIVE; family_label = pós-hoc (declarado)
(HERE/"xau_15m_live_fireable_n83_filter_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
p=res
print(f"BASE  n={p['n_base']}  {p['base_panel']}")
print(f"SKIP  n={p['n_skipped']}  (losers {p['skip_by_outcome']['losers_cut']} / winners {p['skip_by_outcome']['winners_cut']})")
print(f"KEPT  n={p['n_kept']}  {p['kept_panel']}")
print("per_year:",{k:{'n':v['n'],'WR':v['WR'],'sumR':v['sumR']} for k,v in p['kept_per_year'].items()})
print("per_regime:",{k:{'n':v['n'],'WR':v['WR'],'sumR':v['sumR']} for k,v in p['kept_per_regime'].items()})
