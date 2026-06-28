#!/usr/bin/env python3
"""Painéis comparativos: base anterior (swept-sempre) -> +h1_pos>=0.44 -> +substrato (leitura estrutural micro).
N/WR/sumR/avgR/DD/streak/winners/losers/runners/por-ano. Lê sweptsempre_micro.jsonl. Determinístico."""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
R=[json.loads(l) for l in (HERE/"sweptsempre_micro.jsonl").read_text().splitlines()]
for r in R: r["_F"]={**r["micro"], **{k:v for k,v in r["feat"].items() if isinstance(v,(int,float))}, "h1_pos":r.get("h1_pos",0.5)}
def quant(rows,ft,q):
    vs=sorted(x["_F"][ft] for x in rows if x["_F"].get(ft) is not None);
    return vs[min(len(vs)-1,max(0,int(q*len(vs))))] if vs else 0
def panel(rows,tag):
    rows=sorted(rows,key=lambda z:z["cj_t"]); Rs=[x["R"] for x in rows]; n=len(Rs)
    if not n: print(f"{tag:<34} vazio"); return
    sm=sum(Rs); w=sum(1 for x in Rs if x>0); ls=n-w; run=sum(1 for x in Rs if x>=3)
    eq=pk=dd=0
    for x in Rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in Rs:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    py={y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}
    print(f"{tag:<34} N{n:>4} WR{100*w/n:>5.1f}% W{w:>4}/L{ls:>4} run{run:>3} | sumR{sm:>7.1f} avgR{sm/n:>6.3f} DD{dd:>6.1f} streak-{mL}/+{mW} | yr {py[2024]}/{py[2025]}/{py[2026]}")
A=R                                   # swept-sempre (base aprovada original)
B=[r for r in A if r["_F"]["h1_pos"]>=0.44]   # + filtro #1
# substrato 1: leitura estrutural "impulso + acima EMA21 + momentum" (sinais, interpretável)
C=[r for r in B if r["_F"].get("dist_ema21",0)>=0 and r["_F"].get("body_cj",0)>=0 and r["_F"].get("rsi_slope3",0)>=0]
# substrato 2: combo quantil mais forte do scan (pos_recent20 + rsi_cj)
q_pos=quant(B,"pos_recent20",0.25); q_rsi=quant(B,"rsi_cj",0.2)
D=[r for r in B if r["_F"].get("pos_recent20",0)>=q_pos and r["_F"].get("rsi_cj",0)>=q_rsi]
# substrato 3: leitura estrutural completa (impulso forte + posição alta + acima EMA21)
q_body=quant(B,"body_cj",0.33); q_cpos=quant(B,"close_pos_cj",0.33)
E=[r for r in B if r["_F"].get("dist_ema21",0)>=0 and r["_F"].get("body_cj",0)>=q_body and r["_F"].get("close_pos_cj",0)>=q_cpos and r["_F"].get("pos_recent20",0)>=quant(B,"pos_recent20",0.33)]
print("COMPARATIVO DE BASES (XAU 15M LONG BOTTOM):\n")
panel(A,"1) swept-sempre (base orig)")
panel(B,"2) +h1_pos>=0.44 (base atual)")
panel(C,"3) +substrato sinais (EMA21+body+rsiSlope)")
panel(D,"4) +substrato scan (pos20+rsi_cj)")
panel(E,"5) +substrato estrutural completo")
