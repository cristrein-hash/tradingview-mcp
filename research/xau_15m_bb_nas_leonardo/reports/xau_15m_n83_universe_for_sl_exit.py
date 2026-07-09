#!/usr/bin/env python3
"""FASE 2 — FREEZE do universo N83 p/ SL/exit review. Reproduz o pipeline (byte-match asserts na lib),
aplica o cut list (13) -> N83=83, e congela contexto (regime causal, families loser-only, timeouts).
Fail-loud. Output: xau_15m_n83_universe_for_sl_exit_result.json."""
import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
base=L.reproduce_base()                       # asserts 96 + byte-match
regmap,cut,fam=L.load_context()
assert len(cut)==13, "cut != 13"
n83=[tr for tr in base if tr["trade_id"] not in cut]
assert len(n83)==83, f"N83 != 83 ({len(n83)})"
# verificação: os 13 cortados são losers na base
assert all(tr["out"]==0 for tr in base if tr["trade_id"] in cut), "cut inclui winner!"
# timeouts (out==0 sem tocar SL): recomputar oc real
tm=[]
for tr in base:
    r=L.simulate(tr["j"],tr["ent"],tr["sl"],tr["tgt"])
    tr["oc"]=r["oc"]; tr["bars_held"]=r["bars"]; tr["R_exec"]=round(r["R"],3) if r["R"] is not None else None
    if r["oc"]=="TIME": tm.append(tr["trade_id"])
res={"N96":len(base),"N83":len(n83),"cut_ids":sorted(cut),"cut_all_losers":True,
     "predicate":"SKIP se macro_regime==BEAR (v5 causal) e 1D_px_vs_ema>=0",
     "unit":"markup-demand episode -> entry causal reclaim EMA21 (congelada)",
     "regimes_n96":{r:sum(1 for t in base if regmap.get(t["trade_id"])==r) for r in ("BULL","BEAR","RANGE")},
     "regimes_n83":{r:sum(1 for t in n83 if regmap.get(t["trade_id"])==r) for r in ("BULL","BEAR","RANGE")},
     "timeout_ids_n96":tm,
     "timeouts_in_n83":[i for i in tm if i not in cut],
     "families_mapped_losers":len(fam),
     "byte_match":"PASS (asserts na lib: t/ent/sl/tgt/out 96/96)"}
res["verdict"]="UNIVERSE_FROZEN"
(HERE/"xau_15m_n83_universe_for_sl_exit_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
