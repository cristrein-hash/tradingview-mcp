#!/usr/bin/env python3
"""RTSE — REFAZ a avaliação de regime na L2/BPT no SET APROVADO + R UNCAPPED (corrige o erro do set capado).
Set aprovado = régua oficial SL_CONTEXT+let-run: `l2_bpt_regua_structural.csv` (n=245, bar_idx + letrun_struct UNCAPPED).
Regime causal phase10 = reg[bar_idx]. Compara CAPADO vs UNCAPPED por regime (reordena? onde vivem os monumentais?).
DIAGNÓSTICO p/ reflexão — n por célula pequeno, thresholds calibrados, BETA não-controlado (caveat permanente)."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T
R=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv")
rows=[]
for r in csv.DictReader(open(R)):
    bi=int(r["bar_idx"])
    rows.append({"bi":bi,"cap":float(r["capped_struct"]),"unc":float(r["letrun_struct"]),"mfe":float(r["mfe_struct"]),
                 "regime":(reg[bi] if 0<=bi<len(reg) else None),
                 "yr":(dt.datetime.utcfromtimestamp(T[bi]).year if 0<=bi<len(T) else None)})
def panel(rs,name,key):
    if not rs: print(f"  {name:26} N=0");return
    rs=sorted(rs,key=lambda x:x["bi"]);n=len(rs);w=sum(1 for x in rs if x[key]>0);s=sum(x[key] for x in rs)
    cum=peak=dd=0;cs=mxl=0
    for x in rs:
        cum+=x[key];peak=max(peak,cum);dd=min(dd,cum-peak)
        cs=cs+1 if x[key]<=0 else 0;mxl=max(mxl,cs)
    run5=sum(1 for x in rs if x[key]>=5);mon=sum(1 for x in rs if x[key]>=15)
    print(f"  {name:26} N={n:3} WR={100*w/n:3.0f}% sumR={s:+7.1f} avgR={s/n:+5.2f} DD={dd:6.1f} run≥5={run5:2} mon≥15={mon} loseStreak={mxl}")
print("="*86);print("L2/BPT SET APROVADO (régua oficial SL_CONTEXT+let-run, n=245) × phase10 regime");print("="*86)
from collections import Counter
print(f"regime dist (245): {dict(Counter(x['regime'] for x in rows))}")
tot_unc=sum(x['unc'] for x in rows);tot_cap=sum(x['cap'] for x in rows)
print(f"sumR UNCAPPED total={tot_unc:+.1f} | sumR CAPPED total={tot_cap:+.1f}  (a régua oficial é a UNCAPPED)")
print("\n### CAPADO (o que eu reportei antes, ERRADO como régua) — por regime ###")
for rg in ["BULL","RANGE","BEAR",None]: panel([x for x in rows if x["regime"]==rg],f"capado · {rg}","cap")
print("\n### ⭐ UNCAPPED (régua oficial aprovada) — por regime ###")
panel(rows,"UNCAPPED · TODOS","unc")
for rg in ["BULL","RANGE","BEAR",None]: panel([x for x in rows if x["regime"]==rg],f"UNCAPPED · {rg}","unc")
print("\n### REORDENA? avgR por regime: capado -> uncapped ###")
for rg in ["BULL","RANGE","BEAR"]:
    g=[x for x in rows if x["regime"]==rg]
    if g: print(f"  {rg:6}: capado {sum(x['cap'] for x in g)/len(g):+.2f}  ->  UNCAPPED {sum(x['unc'] for x in g)/len(g):+.2f}   (n{len(g)})")
print("\n### onde vivem os MONUMENTAIS (uncapped ≥15R) e RUNNERS (≥5R)? ###")
mons=[x for x in rows if x["unc"]>=15];runs=[x for x in rows if x["unc"]>=5]
print(f"  monumentais≥15R: n={len(mons)} regimes={dict(Counter(x['regime'] for x in mons))} | datas={[dt.datetime.utcfromtimestamp(T[x['bi']]).strftime('%Y-%m-%d') for x in mons]}")
print(f"  runners≥5R: n={len(runs)} regimes={dict(Counter(x['regime'] for x in runs))} sumR={sum(x['unc'] for x in runs):+.0f}")
print("\n### por ANO × regime (uncapped) ###")
for y in sorted(set(x["yr"] for x in rows if x["yr"])):
    g=[x for x in rows if x["yr"]==y];print(f"  {y}: N={len(g):3} sumR={sum(x['unc'] for x in g):+6.1f} regimes={dict(Counter(x['regime'] for x in g))}")
