#!/usr/bin/env python3
"""CAMINHADA DE PERNAS — reproduzir os PLT/DM do Cris a partir da estrutura, SEM ele marcar (2026-07-07).
Objetivo: provar que a leitura contextual sai do que JÁ existe. Percorro o markup na escala das PERNAS
(zigzag 15M em vários r intermédios) e comparo os swing-highs (candidatos a PLT) e swing-lows (candidatos
a DM) da caminhada contra as 10 PLT + 11 DM que o Cris marcou na janela ago-out/2025.
Se a caminhada reproduz as marcações -> a estrutura já contém os PLT/DM; não precisa marcação manual.
SANITY_PROBE: caminhada sequencial de pernas (processo, escala intermédia); reproduzir marcações do Cris
a partir da estrutura existente; contexto de semanas; causal; NÃO filtro de pool, NÃO snapshot."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
def zz(r):
    """zigzag 15M com limiar r*ATR; devolve pivôs (tipo,idx,preço,conf_idx) em ordem."""
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
rows=json.load(open(HERE/"results"/"manual_shapes_pltdm_20260707.json"))
def gp(r):
    pts=r.get("points") or []; return (int(pts[0]["time"]),pts[0]["price"]) if pts and pts[0].get("time") else None
PLT=sorted([gp(r) for r in rows if r["name"]=="text_note" and r["text"].strip().upper()=="PLT" and gp(r)])
DM=sorted([gp(r) for r in rows if r["name"]=="text_note" and r["text"].strip().upper()=="DM" and gp(r)])
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
WIN=(min(t for t,_ in PLT)-2*86400, max(t for t,_ in DM)+2*86400)  # janela ago-out do Cris
def match(marks, piv, typ):
    """cada marca do Cris casa com um pivô do tipo (±tempo e ±preço)?"""
    ph=[(TS[i],pr,ci) for tp,i,pr,ci in piv if tp==typ]
    hits=0; used=set()
    for mt,mp in marks:
        a=ATR[bisect.bisect_right(TS,mt)-1] or 5
        cand=[(abs(pt-mt),k) for k,(pt,pr,ci) in enumerate(ph) if abs(pr-mp)<=0.7*a and abs(pt-mt)<=2*86400 and k not in used]
        if cand:
            cand.sort(); used.add(cand[0][1]); hits+=1
    return hits
print("=== reproduzir PLT/DM do Cris pela CAMINHADA (vários r intermédios) ===")
print(f"janela: {ds(WIN[0])[:10]} .. {ds(WIN[1])[:10]} · marcas Cris: {len(PLT)} PLT · {len(DM)} DM")
for r in (3,4,5,6,8,10,12):
    piv=zz(r)
    pivw=[(tp,i,pr,ci) for tp,i,pr,ci in piv if WIN[0]<=TS[i]<=WIN[1]]
    nH=sum(1 for x in pivw if x[0]=="H"); nL=sum(1 for x in pivw if x[0]=="L")
    mp=match(PLT,pivw,"H"); md=match(DM,pivw,"L")
    print(f"  r={r:>2}: pernas na janela {len(pivw):>2} (H{nH}/L{nL}) · PLT reproduzidos {mp}/10 · DM reproduzidos {md}/11")
# escolher o melhor r e imprimir a caminhada lado-a-lado
best_r=6
piv=zz(best_r); pivw=[(tp,i,pr,ci) for tp,i,pr,ci in piv if WIN[0]<=TS[i]<=WIN[1]]
print(f"\n=== CAMINHADA r={best_r} na janela do Cris (sequência de pernas) ===")
for tp,i,pr,ci in pivw:
    tag="PLT?" if tp=="H" else "DM? "
    near=""
    marks=PLT if tp=="H" else DM
    a=ATR[i] or 5
    m=[mp for mt,mp in marks if abs(mp-pr)<=0.7*a and abs(mt-TS[i])<=2*86400]
    if m: near=f"  <-- CASA Cris @{m[0]:.0f}"
    print(f"  {ds(TS[i])}  {tp} @{pr:7.1f}  {tag}{near}")
print("OK")
