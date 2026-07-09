#!/usr/bin/env python3
"""FASE 6 — SL REVIEW (N83): alternativas PRÉ-REGISTRADAS, sem otimização solta. Mesmos entries/filtro;
muda SÓ o SL (o target segue 3R do NOVO risco = modelo R coerente). Alternativas:
A=atual demand-0.1ATR (V1) · C=swing12-0.1ATR · D=ATR1.5 do entry · E=hybrid min(demand,swing12)-0.1ATR ·
F=wider demand-0.5ATR. Métricas em R (do próprio risco). Per-year p/ robustez. Sem low futuro.
Output: xau_15m_n83_sl_review_result.json."""
import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import xau_15m_n83_sl_exit_lib as L
base=L.reproduce_base(); regmap,cut,fam=L.load_context()
n83=[t for t in base if t["trade_id"] not in cut]
ALTS={"A_current_demand_0.1ATR":L.sl_current,
      "C_swing12_0.1ATR":L.sl_swing,
      "D_atr1.5_entry":L.sl_atr,
      "E_hybrid_min_demand_swing":L.sl_hybrid,
      "F_wider_demand_0.5ATR":L.sl_wider}
res={"design":"pré-registrado; target=ent+3*(ent-sl_alt); first-touch SL-first; horizon 1440","alts":{}}
for name,fn in ALTS.items():
    Rs=[]; yr={}; skipped=0
    for tr in n83:
        sl=fn(tr); risk=tr["ent"]-sl
        if risk<=0.05*(L.ATR[tr["j"]] or 5): skipped+=1; continue
        tgt=tr["ent"]+3*risk
        sim=L.simulate(tr["j"],tr["ent"],sl,tgt)
        R=sim["R"]; Rs.append(R)
        yr.setdefault(L.dstr(tr["t"])[:4],[]).append(R)
    p=L.panel(Rs); p["skipped_degenerate"]=skipped
    p["per_year"]={k:{"n":v2["n"],"WR":v2["WR"],"sumR":v2["sumR"]} for k,v2 in ((k,L.panel(v)) for k,v in sorted(yr.items()))}
    res["alts"][name]=p
res["notes"]=["R normalizado ao risco de CADA alternativa (comparável em unidades de risco)",
              "nenhum SL usa low futuro; swing12 = lows ATÉ o entry j (inclusive)",
              "TIME nas alternativas largas = fecho no cutoff (executável)"]
(HERE/"xau_15m_n83_sl_review_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
for name,p in res["alts"].items():
    print(f"{name:<30} n={p['n']:<3} WR={p['WR']:<5} sumR={p['sumR']:<7} PF={p['PF']} DD={p['maxDD_R']} stk={p['streak']} | " +
          " ".join(f"{y}:{v['sumR']}" for y,v in p["per_year"].items()))
