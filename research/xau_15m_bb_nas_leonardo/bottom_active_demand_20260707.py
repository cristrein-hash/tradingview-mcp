#!/usr/bin/env python3
"""FUNDO = RETORNO À DEMANDA ATIVA CORRENTE (2026-07-07) — máquina de estado macro, UMA zona por vez.
Correção de PARADIGMA (Cris): num markup de 2 anos quase todo topo é rompido -> 145 zonas históricas ->
densidade inevitável. ERRADO. Em cada momento há UMA demanda ATIVA = base da perna macro corrente
(o último higher-low que lançou a perna vigente). O fundo é o preço RECUAR a ESSA zona. ~1 evento/perna
POR CONSTRUÇÃO estrutural, não por filtro sobre pool.
Máquina de estado sobre swings DIÁRIOS (contexto de semanas):
  - up-context: preço faz higher-highs; demanda ativa = último higher-low confirmado.
  - evento = 1º toque 15M na demanda ativa após estar acima (retorno/pullback à base da perna).
  - quando novo higher-low se confirma acima, a demanda ativa SOBE (escada); se preço fecha abaixo da
    demanda ativa = perna quebrada -> muda de estado (procura nova base / fim-de-queda).
SANITY_PROBE: estado macro de UMA zona ativa (não pool de 145); leitura por evento em escala diária
(semanas); estrutura anterior por meses; causal known_at; NÃO busca-por-barra míope."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
from collections import OrderedDict
days=OrderedDict()
for b in S:
    d=dt.datetime.utcfromtimestamp(b["t"]).strftime("%Y-%m-%d")
    if d not in days: days[d]={"t":b["t"],"h":b["h"],"l":b["l"],"c":b["c"]}
    dd=days[d]; dd["h"]=max(dd["h"],b["h"]); dd["l"]=min(dd["l"],b["l"]); dd["c"]=b["c"]
D=list(days.values()); ND=len(D); day_t=[d["t"] for d in D]
DH=[d["h"] for d in D]; DL=[d["l"] for d in D]; DC=[d["c"] for d in D]
DATR=[]; tr=[]
for i in range(ND):
    t=DH[i]-DL[i] if i==0 else max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1]))
    tr.append(t); DATR.append(sum(tr[-14:])/min(len(tr),14))
def dzz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,ND):
        a=DATR[i] or 10
        if DH[i]>DH[ehi]: ehi=i
        if DL[i]<DL[elo]: elo=i
        if d<=0 and DH[i]-DL[elo]>=r*a and elo<i: piv.append(("L",elo,DL[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:DH[k])
        elif d>=0 and DH[ehi]-DL[i]>=r*a and ehi<i: piv.append(("H",ehi,DH[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:DL[k])
    return piv  # (tipo, idx_dia, preço, dia_confirmação)
def run(R, tolatr, halo):
    piv=dzz(R)
    # sequência de swings confirmados -> demanda ativa (último higher-low) e polaridade (último higher-high rompido)
    events=[]; active=None; active_conf=None; prev_low=None; prev_high=None; armed=False
    ppi=0
    last_touch=-10**9
    for ti in range(N):
        # atualizar swings confirmados até este instante
        while ppi<len(piv) and day_t[piv[ppi][3]]<=TS[ti]:
            typ,idx,price,conf=piv[ppi]
            if typ=="L":
                # higher-low? -> nova demanda ativa da perna (sobe a escada)
                if prev_low is None or price>prev_low:
                    active=price; active_conf=conf; armed=True
                else:
                    # lower-low = perna quebrada; demanda ativa passa a ser esta base (fim-de-queda)
                    active=price; active_conf=conf; armed=True
                prev_low=price
            else:
                prev_high=price
            ppi+=1
        if active is None: continue
        didx=bisect.bisect_right(day_t,TS[ti])-1
        a=DATR[didx] if didx<len(DATR) else 10
        # evento = preço recua e TOCA a demanda ativa após estar >halo acima (retorno à base)
        if armed and LO[ti]<=active+tolatr*a and LO[ti]>=active-tolatr*a:
            if ti-last_touch>=96:
                events.append({"ti":ti,"t":TS[ti],"lvl":active}); last_touch=ti
            armed=False  # desarma até subir de novo
        elif active is not None and CL[ti]>active+halo*a:
            armed=True  # subiu acima do halo -> re-arma para próximo retorno
    return events
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
FT=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
def recall(ev,WH=18):
    T=sorted(e["t"] for e in ev); g=0; hit=set()
    for ft in FT:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: g+=1; hit.add(ft)
    return g,hit
print("=== retorno à DEMANDA ATIVA (uma zona por vez) — grid escala/tol ===")
best=None
for R in (0.8,1.0,1.3):
    for tol in (0.5,0.8,1.2):
        for halo in (1.5,2.5):
            ev=run(R,tol,halo); g,hit=recall(ev)
            dens=len(ev)/max(1,g)
            if len(ev)>0 and (best is None or (g>=best[3] and len(ev)<best[2]) or (g>best[3])):
                pass
            print(f"  R={R} tol={tol} halo={halo}: N {len(ev):>3} · recall {g}/42 · dens {dens:.1f}:1")
# escolher config de referência e detalhar
ev=run(1.0,0.8,2.5); g,hit=recall(ev)
missed=[ft for ft in FT if ft not in hit]
print(f"\nREF R=1.0 tol=0.8 halo=2.5 · N{len(ev)} recall {g}/42")
print("MISSED: "+", ".join(ds(m) for m in missed))
json.dump({"N":len(ev),"recall":g,"events":[{"t":e["t"],"d":ds(e["t"]),"lvl":round(e["lvl"],1)} for e in ev]},open(HERE/"results"/"active_demand_20260707.json","w"),indent=1)
print("OK")
