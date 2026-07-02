#!/usr/bin/env python3
"""RTSE — avaliação DIAGNÓSTICA: detector phase10 (BULL/RANGE/BEAR) aplicado à L2/BPT (estratégia de FUNDOS).
Ao contrário da L1 (trend-filtrada=circular), L2 dispara fundos em QUALQUER regime → regime é informação ortogonal.
Universo: 276 episódios qualificados (TAKE 32 = estratégia aprovada / REVIEW 114 / SKIP 130), bar_idx=índice raw_4h, realR.
Regime causal = reg[bar_idx] do phase10 (usa dados ≤ bar de entrada). n pequeno + calibração ⇒ DIAGNÓSTICO p/ reflexão, não validação.
Métricas p/ reflexão: base-rate de fundo por regime (faca-caindo?), TAKE por regime, runners/losers por regime, o que SKIP/REVIEW deixou por regime."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T
def regat(bi):
    bi=int(bi);return reg[bi] if 0<=bi<len(reg) else None
def yr(bi): return dt.datetime.utcfromtimestamp(T[int(bi)]).year if 0<=int(bi)<len(T) else None
Q=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_trade_qualification_decisions_merged.csv")
rows=[]
for r in csv.DictReader(open(Q)):
    try: bi=int(r["bar_idx"]);R=float(r["realR"])
    except: continue
    rows.append({"bi":bi,"dec":r["decision"],"R":R,"win":R>0,"setup":r["setup_type"],"exit":r["exitype"],
                 "regime":regat(bi),"yr":yr(bi)})
def panel(rs,name):
    if not rs: print(f"  {name:30} N=0");return
    rs=sorted(rs,key=lambda x:x["bi"]);n=len(rs);w=sum(1 for x in rs if x["win"]);sumR=sum(x["R"] for x in rs)
    cum=peak=dd=0;cs=mxl=0
    for x in rs:
        cum+=x["R"];peak=max(peak,cum);dd=min(dd,cum-peak)
        cs=cs+1 if not x["win"] else 0;mxl=max(mxl,cs)
    rdd=sumR/abs(dd) if dd<0 else 99
    print(f"  {name:30} N={n:3} WR={100*w/n:3.0f}% sumR={sumR:+6.1f} avgR={sumR/n:+5.2f} DD={dd:6.1f} ret/DD={rdd:5.1f} loseStreak={mxl}")
TAKE=[x for x in rows if x["dec"]=="TAKE"];REV=[x for x in rows if x["dec"]=="REVIEW"];SKIP=[x for x in rows if x["dec"]=="SKIP"]
print("="*78);print("L2/BPT (FUNDOS) — phase10 regime (causal no bar de entrada)");print("="*78)
from collections import Counter
print(f"episódios: TAKE {len(TAKE)} / REVIEW {len(REV)} / SKIP {len(SKIP)} | total {len(rows)}")
print(f"regime dist TAKE: {dict(Counter(x['regime'] for x in TAKE))}")
print("\n### 1. BASE-RATE de FUNDO por regime (TODOS 276 — fundo em que regime PAGA?) ###")
for rg in ["BULL","RANGE","BEAR",None]:
    panel([x for x in rows if x["regime"]==rg],f"todos · regime={rg}")
print("\n### 2. ESTRATÉGIA APROVADA (32 TAKE) por regime ###")
panel(TAKE,"TAKE total")
for rg in ["BULL","RANGE","BEAR",None]:
    panel([x for x in TAKE if x["regime"]==rg],f"TAKE · regime={rg}")
print("\n### 3. RUNNERS (realR>=3R) e LOSERS (realR<=-1) por regime — onde vivem? ###")
run3=[x for x in rows if x["R"]>=3.0];los=[x for x in rows if x["R"]<=-1.0]
print(f"  runners≥3R (n{len(run3)}): {dict(Counter(x['regime'] for x in run3))} | sumR {sum(x['R'] for x in run3):+.0f}")
print(f"  losers≤-1R (n{len(los)}): {dict(Counter(x['regime'] for x in los))} | sumR {sum(x['R'] for x in los):+.0f}")
print(f"  TAKE runners≥3R: {dict(Counter(x['regime'] for x in run3 if x['dec']=='TAKE'))} | TAKE losers: {dict(Counter(x['regime'] for x in los if x['dec']=='TAKE'))}")
print("\n### 4. O que SKIP/REVIEW deixou por regime (fundos não-tomados que teriam pago) ###")
for dec,grp in [("REVIEW",REV),("SKIP",SKIP)]:
    for rg in ["BULL","RANGE","BEAR"]:
        g=[x for x in grp if x["regime"]==rg]
        if g: print(f"  {dec} · {rg}: N={len(g)} WR={100*sum(1 for x in g if x['win'])/len(g):3.0f}% sumR(hipotético)={sum(x['R'] for x in g):+6.1f} avgR={sum(x['R'] for x in g)/len(g):+5.2f}")
print("\n### 5. circularidade: regime vs setup_type da própria L2 (re-descreve?) ###")
for stp in sorted(set(x["setup"] for x in rows)):
    g=[x for x in rows if x["setup"]==stp];print(f"  setup={stp:18} (n{len(g):3}) regime: {dict(Counter(x['regime'] for x in g))}")
print("\n### 6. TAKE por ANO×regime (estabilidade) ###")
for y in sorted(set(x["yr"] for x in TAKE if x["yr"])):
    g=[x for x in TAKE if x["yr"]==y];print(f"  {y}: N={len(g)} sumR={sum(x['R'] for x in g):+5.1f} regimes={dict(Counter(x['regime'] for x in g))}")
