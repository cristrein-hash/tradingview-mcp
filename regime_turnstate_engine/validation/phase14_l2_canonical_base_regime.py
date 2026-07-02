#!/usr/bin/env python3
"""RTSE — regime detector phase10 sobre a BASE CANÓNICA L2/BPT (Cris travou 2026-06-30):
universo 276 + SL_CONTEXT + LET-RUN. Artefacto: l2_bpt_regua_structural.csv (n=245), coluna letrun_struct (PRÉ-CUSTO).
Custo oficial = 0.35R/trade. SEM skip (base de trabalho re-derivável). Regime causal = reg[bar_idx] do phase10.
Objetivo: diretrizes de avaliação estratégica por regime (factual). Caveats: BETA não-controlado (achado-padrão),
n por célula pequeno, thresholds calibrados. NÃO é promoção; é lente de avaliação."""
import csv,io,contextlib,sys,datetime as dt
from pathlib import Path
COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T
R=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv")
rows=[]
for r in csv.DictReader(open(R)):
    bi=int(r["bar_idx"]);unc=float(r["letrun_struct"])-COST     # let-run pós-custo (oficial)
    rows.append({"bi":bi,"R":unc,"mfe":float(r["mfe_struct"]),
                 "regime":(reg[bi] if 0<=bi<len(reg) else None),
                 "yr":(dt.datetime.utcfromtimestamp(T[bi]).year if 0<=bi<len(T) else None)})
from collections import Counter
def panel(rs,name):
    if not rs: print(f"  {name:24} N=0");return
    rs=sorted(rs,key=lambda x:x["bi"]);n=len(rs);w=sum(1 for x in rs if x["R"]>0);s=sum(x["R"] for x in rs)
    cum=peak=dd=0;cs=mxl=0
    for x in rs:
        cum+=x["R"];peak=max(peak,cum);dd=min(dd,cum-peak)
        cs=cs+1 if x["R"]<=0 else 0;mxl=max(mxl,cs)
    run5=sum(1 for x in rs if x["R"]>=5)
    print(f"  {name:24} N={n:3} WR={100*w/n:3.0f}% sumR={s:+7.1f} avgR={s/n:+5.2f} DD={dd:6.1f} ret/DD={(s/abs(dd) if dd<0 else 99):5.1f} run≥5={run5:2} loseStk={mxl}")
print("="*84);print("L2/BPT BASE CANÓNICA (universo 276 + SL_CONTEXT + let-run, n=245, PÓS-CUSTO 0.35R) × regime phase10");print("="*84)
tot=sum(x["R"] for x in rows)
print(f"regime dist: {dict(Counter(x['regime'] for x in rows))} | sumR pós-custo total = {tot:+.1f}R (≈ +53R canon)")
print("\n### POR REGIME (pós-custo) ###")
panel(rows,"TODOS")
for rg in ["BULL","RANGE","BEAR"]: panel([x for x in rows if x["regime"]==rg],f"regime={rg}")
print("\n### BETA-CHECK: ANO × regime (o gradiente é seleção ou só a maré bull 2023+?) ###")
for y in sorted(set(x["yr"] for x in rows if x["yr"])):
    g=[x for x in rows if x["yr"]==y];print(f"  {y}: N={len(g):3} sumR={sum(x['R'] for x in g):+6.1f} avgR={sum(x['R'] for x in g)/len(g):+5.2f} regimes={dict(Counter(x['regime'] for x in g))}")
print("\n### EXCURSÃO NÃO-CAPTURADA (MFE é TETO FORWARD, NÃO-capturável causalmente — NÃO é edge) por regime ###")
for rg in ["BULL","RANGE","BEAR"]:
    g=[x for x in rows if x["regime"]==rg]
    if g:
        big=sum(1 for x in g if x["mfe"]>=8)
        print(f"  {rg:6}: avgR-REALIZADO {sum(x['R'] for x in g)/len(g):+.2f} | avg-MFE(teto-forward, não-bankable) {sum(x['mfe'] for x in g)/len(g):+.2f} | trades c/ MFE≥8R: {big}")
print("""
### DIRETRIZES DE AVALIAÇÃO (corrigidas pós-DA — lente DESCRITIVA, não promoção) ###
- Régua: SÓ esta base (universo 276 + SL_CONTEXT + let-run, pós-custo). Mirage 1.5ATR-cap PROIBIDA como R.
- ⛔ #1 REGIME NÃO É SELETOR IDENTIFICÁVEL nesta data: o label de regime é PROXY QUASE-PERFEITO de CALENDÁRIO.
  BEAR é NÃO-IDENTIFICADO fora de 2021/2026 (36 BEAR: 21 em 2026 + 13 em 2023, 0 em 2024/2025). 'BEAR seleciona mal' =
  '2021/2026 foram fracos'. Não é só confoundável com beta — para BEAR não é identificado. NÃO gatear entry/skip por regime
  esperando alpha de seleção = seria fitar calendário.
- ⛔ #2 EXCURSÃO: realizado (+0.50 BULL) << MFE (+5.83) mostra que há excursão NÃO-capturada — MAS MFE é teto forward,
  NÃO-bankable. Se um exit CAUSAL monetiza isso é questão SEPARADA e NÃO-TESTADA (não é diretriz de regime).
- ⛔ #3 (n): células pequenas, thresholds calibrados. Tudo aqui = hipótese descritiva, NUNCA promoção.
- ⚠️ join regime→trade causal por construção (reg[bi] lê só bars≤i; FSM forward, pivôs confirmados com atraso); teste formal
  de truncação não rodado.""")
