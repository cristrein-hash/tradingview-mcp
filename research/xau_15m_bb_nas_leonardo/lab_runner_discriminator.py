#!/usr/bin/env python3
"""Procura discriminador CAUSAL na ENTRADA que separe os 25 runners do Cris (cris_Rpot>3) do resto.
Cris 2026-06-27: o "deixa correr" e' decisao de QUAIS trades segurar, nao de trailing.
Usa features causais ja existentes em filter_dataset.jsonl. Testa um conjunto PRE-ESPECIFICADO,
teoria-fundado (sem varredura de dezenas): room_above_atr (clean-sky), macro_bull, h4_pos, disp4_atr,
leg_ext_atr, path_eff, dist_supply_atr, regime_age_h, atr_regime. Reporta mediana runner vs resto + lift.
CAVEAT: n=25 (calibracao, nao validacao). So MEDE."""
import json, csv, statistics as st
from pathlib import Path
HERE=Path(__file__).parent
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
def fnum(x): return float(x) if x not in (None,"","None") else None

trades=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); gt=GT.get(num)
    if not fd or not gt: continue
    rp=fnum(gt["cris_Rpot"])
    trades.append({"num":num,"rp":rp,"runner":rp is not None and rp>3,"fd":fd})
runners=[x for x in trades if x["runner"]]; rest=[x for x in trades if not x["runner"]]
print(f"runners (Rpot>3): {len(runners)} | resto: {len(rest)}\n")
FEATS=["room_above_atr","macro_bull","h4_pos","disp4_atr","leg_ext_atr","path_eff",
       "dist_supply_atr","regime_age_h","atr_regime","h1_pos","h1_eff","vol_climax","dist_demand_atr"]
def med(g,f):
    v=[x["fd"].get(f) for x in g if x["fd"].get(f) is not None]
    return round(st.median(v),3) if v else None
print(f"{'feature':<18}{'med_runner':>11}{'med_resto':>10}{'separacao':>11}")
seps=[]
for f in FEATS:
    mr=med(runners,f); mo=med(rest,f)
    if mr is None or mo is None: continue
    # separacao simples: |mr-mo| normalizado pelo desvio do conjunto
    allv=[x["fd"].get(f) for x in trades if x["fd"].get(f) is not None]
    sd=st.pstdev(allv) or 1e-9
    sep=round((mr-mo)/sd,2)
    seps.append((f,mr,mo,sep))
    print(f"{f:<18}{mr:>11}{mo:>10}{sep:>11}")
print("\nordenado por |separacao| (cohen-d aprox.):")
for f,mr,mo,sep in sorted(seps,key=lambda z:-abs(z[3])):
    print(f"  {f:<18} d={sep:+.2f}  runner {mr} vs resto {mo}")

# checagem rapida: thresholds naturais nos 2-3 melhores -> lift de runner
print("\n=== lift de runner sob threshold (top features) ===")
def lift(f,op,thr):
    sel=[x for x in trades if x["fd"].get(f) is not None and (x["fd"][f]>=thr if op==">=" else x["fd"][f]<=thr)]
    if not sel: return None
    rr=sum(1 for x in sel if x["runner"])/len(sel)
    return len(sel),round(100*rr,1)
base=round(100*len(runners)/len(trades),1)
print(f"  base runner-rate: {base}% ({len(runners)}/{len(trades)})")
for f,mr,mo,sep in sorted(seps,key=lambda z:-abs(z[3]))[:4]:
    op=">=" if sep>0 else "<="; thr=mr
    r=lift(f,op,thr)
    if r: print(f"  {f} {op} {thr}: n={r[0]}, runner-rate {r[1]}% (lift {r[1]/base:.2f}x)")
