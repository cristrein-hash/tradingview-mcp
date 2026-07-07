#!/usr/bin/env python3
"""SIGNIFICÂNCIA DE LARGO-CONTEXTO DOS PLT DO CRIS (2026-07-07) — entendimento por evento, não filtro.
Hipótese: a tua DM/PLT não é "topo rompido" (há centenas num markup) — é um topo que foi RESISTÊNCIA
SIGNIFICATIVA por SEMANAS (múltiplas reações/toques) antes de romper. Ao romper, polaridade -> suporte.
Meço, para cada um dos 10 PLT do Cris, a história ANTES do rompimento (largo contexto, em DIAS):
  - span_dias: quantos dias entre 1º toque no nível e o rompimento (idade como teto).
  - n_reacoes: quantos swings-high DIÁRIOS distintos reagiram desse nível (+-0.6 ATR-dia) antes de romper.
  - dias_como_teto: nº de dias em que o preço bateu no nível e recuou (rejeição por cima->baixo).
Contraste: os mesmos números para topos diários rompidos GENÉRICOS (a população de fundo).
Se os PLT do Cris têm span/reações MUITO acima dos genéricos -> esse é o critério de largo-contexto
que eu colapsava. Não é density-filter: é caracterização dos eventos DELE.
SANITY_PROBE: caracterização de largo-contexto (semanas) dos eventos marcados pelo Cris; história de
resistência multi-semana; causal (só antes do rompimento); entendimento por evento, não pool-filter."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
import statistics as st
HERE = Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); N=len(S)
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
def dswings(r=1.0):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,ND):
        a=DATR[i] or 10
        if DH[i]>DH[ehi]: ehi=i
        if DL[i]<DL[elo]: elo=i
        if d<=0 and DH[i]-DL[elo]>=r*a and elo<i: piv.append(("L",elo,DL[elo])); d=1; ehi=max(range(elo,i+1),key=lambda k:DH[k])
        elif d>=0 and DH[ehi]-DL[i]>=r*a and ehi<i: piv.append(("H",ehi,DH[ehi])); d=-1; elo=min(range(ehi,i+1),key=lambda k:DL[k])
    return piv
SW=dswings(1.0); SWH=[(i,p) for t,i,p in SW if t=="H"]
def di(t): return bisect.bisect_right(day_t,t)-1
def significance(level, break_day, lookback=180):
    """história do nível ANTES do rompimento: reações e span (em dias)."""
    a=DATR[break_day] if break_day<len(DATR) else 10
    lo=break_day-lookback
    # reações = swings-high diários perto do nível antes do rompimento
    reac=[i for i,p in SWH if lo<=i<break_day and abs(p-level)<=0.6*a]
    # dias-como-teto: dias cujo high bate no nível (+-0.4A) e fecha abaixo (rejeição)
    teto=[i for i in range(max(0,lo),break_day) if DH[i]>=level-0.4*a and DC[i]<level-0.1*a]
    span=(break_day-min(reac)) if reac else 0
    return {"n_reacoes":len(reac),"dias_como_teto":len(teto),"span_dias":span,"atr":round(a,1)}
rows=json.load(open(HERE/"results"/"manual_shapes_pltdm_20260707.json"))
PLT=[(int(r["points"][0]["time"]),r["points"][0]["price"]) for r in rows if r["name"]=="text_note" and r["text"].strip().upper()=="PLT" and r.get("points")]
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
print("=== SIGNIFICÂNCIA DE LARGO-CONTEXTO — 10 PLT do Cris ===")
plt_stats=[]
for t,p in sorted(PLT):
    d0=di(t)
    # dia de rompimento = 1º dia após t com close>level
    bd=None
    for m in range(d0,ND):
        if DC[m]>p+0.1*(DATR[m] or 10): bd=m; break
    if bd is None: bd=d0
    sg=significance(p,bd); plt_stats.append(sg)
    print(f"  PLT {ds(t)} @{p:.0f}: reações={sg['n_reacoes']} dias-como-teto={sg['dias_como_teto']} span={sg['span_dias']}d")
def summ(stats,label):
    for k in ("n_reacoes","dias_como_teto","span_dias"):
        v=[s[k] for s in stats]
        print(f"    {label} {k}: med {st.median(v):.1f} · min {min(v)} · max {max(v)}")
print("  -- resumo PLT-Cris --"); summ(plt_stats,"PLT")
# CONTRASTE: topos diários rompidos GENÉRICOS
gen=[]
for i,p in SWH:
    bd=None
    for m in range(i+1,ND):
        if DC[m]>p+0.1*(DATR[m] or 10): bd=m; break
    if bd is None: continue
    gen.append(significance(p,bd))
print(f"\n=== CONTRASTE: {len(gen)} topos diários rompidos genéricos ===")
summ(gen,"GEN")
# separação: fração de genéricos que atingem o piso dos PLT-Cris
import numpy as np
thr_r=min(s["n_reacoes"] for s in plt_stats); thr_s=min(s["span_dias"] for s in plt_stats)
med_r=st.median([s["n_reacoes"] for s in plt_stats]); med_s=st.median([s["span_dias"] for s in plt_stats])
above=[g for g in gen if g["n_reacoes"]>=med_r and g["span_dias"]>=med_s]
print(f"\nPLT-Cris medianas: reações {med_r} · span {med_s}d")
print(f"genéricos que atingem AMBAS medianas PLT: {len(above)}/{len(gen)} ({len(above)/len(gen):.0%}) -> nº de topos 'significativos' no período")
print("OK")
