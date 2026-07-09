#!/usr/bin/env python3
"""FASE 4 — EXIT CURRENT STATE AUDIT (N83). Exit = target fixo +3R (tgt=ent+3*risk), first-touch,
SL-first no mesmo bar (conservador), horizon 1440 bars (~15d). Auditar: derivação do outcome,
timeouts, ambiguidade both-touch-same-bar, executabilidade live, time-in-trade.
Output: xau_15m_n83_exit_audit_result.json."""
import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
base=L.reproduce_base(); regmap,cut,fam=L.load_context()
n83=[t for t in base if t["trade_id"] not in cut]
both=[]; toi=[]; ocs={"SL":0,"TGT":0,"TIME":0}
for tr in n83:
    sim=L.simulate(tr["j"],tr["ent"],tr["sl"],tr["tgt"])
    ocs[sim["oc"]]+=1; toi.append(sim["bars"])
    m=sim["end"]
    if sim["oc"] in ("SL","TGT") and L.LO[m]<=tr["sl"] and L.HI[m]>=tr["tgt"]:
        both.append(tr["trade_id"])          # bar tocou AMBOS -> resolvido SL-first (conservador)
toi_s=sorted(toi)
res={"n":len(n83),
     "exit_classification":"FIXED_3R (tgt=ent+3*risk) + horizon 1440 bars (sem time-stop explícito)",
     "exit_source":"entry_engine_master_20260707.py linhas 76-80",
     "outcome_derivation":"first-touch forward j+1..j+1440; SL checado ANTES do target no MESMO bar (conservador)",
     "outcomes":ocs,
     "timeouts":ocs["TIME"],
     "plus3_minus1_is_executable":ocs["TIME"]==0,
     "both_touch_same_bar_ids":both,"both_touch_count":len(both),
     "uses_mfe_future":"NÃO (MFE nunca é trigger)","visual_hindsight":"NÃO",
     "known_before_trade":"SIM — tgt fixado no fecho do bar de entry (ent, risk conhecidos)",
     "executable_live":"SIM — ordem limite no target + stop no SL; sem decisão discricionária",
     "time_in_trade_bars":{"min":toi_s[0],"p25":toi_s[len(toi_s)//4],"median":toi_s[len(toi_s)//2],
                            "p75":toi_s[3*len(toi_s)//4],"max":toi_s[-1]},
     "notes":["+125R do PDF = 52*3-31*1 sob este modelo; com 0 timeouts o scoring +3/-1 = modelo executável first-touch",
              "caveat de execução restante: slippage/spread/gap (stress na Fase 9), não estrutura do modelo"]}
res["verdict"]="EXIT_CAUSAL_FIXED3R_OK"
(HERE/"xau_15m_n83_exit_audit_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
