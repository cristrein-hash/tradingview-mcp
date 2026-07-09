#!/usr/bin/env python3
"""FASE 7 — EXIT REVIEW (N83): alternativas PRÉ-REGISTRADAS com SL atual (V1). B=+2R · C=+3R (atual) ·
D=+4R · F=time-stop 288 bars (fecho a mercado, sem target) · H=+3R com cap 288 bars.
E (partial+runner) e G (BB/NAS/estrutura) = SEM base causal pré-registrada -> NOT_TESTED (declarado).
Sem MFE-trigger, sem hindsight, sem mudar entry/filtro. Output: xau_15m_n83_exit_review_result.json."""
import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
base=L.reproduce_base(); regmap,cut,fam=L.load_context()
n83=[t for t in base if t["trade_id"] not in cut]
def run(mult=None, time_cap=None):
    Rs=[]; yr={}; bars=[]
    for tr in n83:
        risk=tr["ent"]-tr["sl"]
        tgt=(tr["ent"]+mult*risk) if mult else None
        sim=L.simulate(tr["j"],tr["ent"],tr["sl"],tgt,time_cap=time_cap)
        R=sim["R"]; Rs.append(R); bars.append(sim["bars"])
        yr.setdefault(L.dstr(tr["t"])[:4],[]).append(R)
    p=L.panel(Rs)
    p["avg_bars"]=round(sum(bars)/len(bars),1)
    p["per_year"]={k:{"n":v2["n"],"WR":v2["WR"],"sumR":v2["sumR"]} for k,v2 in ((k,L.panel(v)) for k,v in sorted(yr.items()))}
    return p
res={"design":"pré-registrado; SL atual V1 fixo; muda SÓ exit","alts":{
    "B_fixed_2R":run(mult=2),
    "C_fixed_3R_current":run(mult=3),
    "D_fixed_4R":run(mult=4),
    "F_timestop_288b":run(mult=None,time_cap=288),
    "H_3R_cap288":run(mult=3,time_cap=288)},
 "not_tested":{"E_partial_runner":"sem base causal pré-registrada (regra de parcial não definida) — NOT_TESTED",
               "G_structure_bb_nas_exit":"fonte causal de exit estrutural não definida no prereg — NOT_TESTED"}}
(HERE/"xau_15m_n83_exit_review_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
for name,p in res["alts"].items():
    print(f"{name:<22} n={p['n']:<3} WR={p['WR']:<5} sumR={p['sumR']:<7} PF={p['PF']} DD={p['maxDD_R']} stk={p['streak']} bars={p['avg_bars']:<6} | " +
          " ".join(f"{y}:{v['sumR']}" for y,v in p["per_year"].items()))
