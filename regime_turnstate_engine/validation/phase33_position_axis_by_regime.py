#!/usr/bin/env python3
"""Cris (2026-07-01, aprovado): EIXO POSIÇÃO-POR-REGIME causal. Validar PRIMEIRO no CHASING (bull+range):
a entrada tardia/alta (topo do bloco de regime) perde; a de fundo/demanda ganha? Medir POR REGIME separadamente.
pos = (entry − running_min) / (running_max − running_min) desde o INÍCIO do bloco de regime corrente até à barra i (100% CAUSAL,
nunca box-inteira). age = idade no bloco. amp = amplitude do bloco em ATR. Comparar eixo contínuo vs cap-ordinal (1ª vs resto).
BEAR reportado à parte (capitulação = passo posterior). let-run canónico, custo 0.35. Só análise."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
from collections import defaultdict
COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    rg=reg[bi];i0=bi
    while i0>0 and reg[i0-1]==rg: i0-=1          # início CAUSAL do bloco de regime corrente
    rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);a=atr(bi);entry=float(r["entry"])
    pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else 0.5
    rows.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"reg":rg,
                 "pos":pos,"age":bi-i0,"amp_atr":(rmax-rmin)/a,"R":round(float(r["letrun_struct"])-COST,2),
                 "is_first":(bi==i0 or all(int(x["bi"])!=j for x in [] for j in []))})
rows.sort(key=lambda x:x["bi"])
# marca 1ª entrada por bloco (mesma boxkey de regime): agrupar por (reg,i0)
byblk=defaultdict(list)
for x in rows:
    bi=x["bi"];rg=x["reg"];i0=bi
    while i0>0 and reg[i0-1]==rg: i0-=1
    x["blk"]=(rg,i0);byblk[x["blk"]].append(x)
for k,g in byblk.items():
    g.sort(key=lambda z:z["bi"])
    for i,z in enumerate(g): z["ord"]=i;z["is_first"]=(i==0)
def agg(g,lab):
    if not g: print(f"    {lab:26} N=0");return
    n=len(g);w=sum(1 for x in g if x["R"]>0);s=sum(x["R"] for x in g)
    print(f"    {lab:26} N={n:3} WR={100*w/n:3.0f}% avgR={s/n:+5.2f} sumR={s:+6.1f}")
print("EIXO POSIÇÃO-POR-REGIME (causal) — validação no CHASING")
print("dist regime:",{r:sum(1 for x in rows if x['reg']==r) for r in ('BULL','RANGE','BEAR')})
for RG in ("BULL","RANGE"):
    g=[x for x in rows if x["reg"]==RG]
    print(f"\n### {RG} (N={len(g)}) — pos-no-bloco (0=fundo/demanda, 1=topo) ###")
    agg([x for x in g if x["pos"]<0.34],"pos FUNDO  (<0.34)")
    agg([x for x in g if 0.34<=x["pos"]<0.67],"pos MEIO   (0.34-0.67)")
    agg([x for x in g if x["pos"]>=0.67],"pos TOPO   (>=0.67)")
    print("   -- por AGE (idade no bloco) --")
    med=sorted(x["age"] for x in g)[len(g)//2]
    agg([x for x in g if x["age"]<=med],f"age BAIXA (<= {med})")
    agg([x for x in g if x["age"]>med],f"age ALTA  (> {med})")
    print("   -- cap-ordinal (comparar com eixo contínuo) --")
    agg([x for x in g if x["is_first"]],"1ª do bloco")
    agg([x for x in g if not x["is_first"]],"tardias (resto)")
    # correlação pos vs R (sinal do gradiente)
    import statistics as st
    hi=[x["R"] for x in g if x["pos"]>=0.67];lo=[x["R"] for x in g if x["pos"]<0.34]
    if len(hi)>=3 and len(lo)>=3:
        print(f"   >> Δ avgR (FUNDO − TOPO) = {st.mean(lo)-st.mean(hi):+.2f}  ({'fundo>topo=chasing confirmado' if st.mean(lo)>st.mean(hi) else 'NAO separa/invertido'})")
print(f"\n### BEAR (N={sum(1 for x in rows if x['reg']=='BEAR')}) — só referência (capitulação=passo posterior) ###")
gb=[x for x in rows if x["reg"]=="BEAR"]
agg([x for x in gb if x["pos"]<0.34],"pos FUNDO (<0.34)")
agg([x for x in gb if x["pos"]>=0.67],"pos TOPO  (>=0.67)")
