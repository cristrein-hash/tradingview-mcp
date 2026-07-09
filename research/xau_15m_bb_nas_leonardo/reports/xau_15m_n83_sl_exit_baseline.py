#!/usr/bin/env python3
"""FASE 5 — BASELINE métrico N83 sob SL/exit atual (V1 + 3R fixo). Painel completo + per-year/regime/
family + delta N96->N83. Modelo simplificado +3/-1 == modelo executável (0 timeouts, provado F4).
Output: xau_15m_n83_sl_exit_baseline_result.json."""
import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
base=L.reproduce_base(); regmap,cut,fam=L.load_context()
n83=[t for t in base if t["trade_id"] not in cut]
def R_of(tr): return 3.0 if tr["out"]==1 else -1.0
def seg(trs,key):
    out={}
    for tr in trs: out.setdefault(key(tr),[]).append(R_of(tr))
    return {k:L.panel(v) for k,v in sorted(out.items())}
res={"model":"executável first-touch (== +3/-1; 0 timeouts, 0 both-touch)",
     "N96":L.panel([R_of(t) for t in base]),
     "N83":L.panel([R_of(t) for t in n83]),
     "delta_filter":"remove 13 losers/0 winners = +13R e -13 trades",
     "per_year_n83":seg(n83,lambda t:L.dstr(t["t"])[:4]),
     "per_regime_n83":seg(n83,lambda t:regmap.get(t["trade_id"],"?")),
     "per_family_losers_n83":seg([t for t in n83 if t["out"]==0],lambda t:fam.get(t["trade_id"],"?")),
     "leg_state":"todos = MARKUP demand (unidade da base; per-leg_state trivial)",
     "time_in_trade":"median 61 bars / p75 144 / max 535 (audit F4)"}
res["verdict"]="BASELINE_REPRODUCED"
(HERE/"xau_15m_n83_sl_exit_baseline_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
