#!/usr/bin/env python3
"""FUNDO = EVENTO DE RETORNO A ZONA MACRO (2026-07-07) — escala DIÁRIA, não 15M-local.
Correção de miopia (Cris): pivôs 15M zigzag r=3 = LOCAL (poucas barras); PLT/DM abrangem SEMANAS.
Reconstruo na escala macro: resample -> barras DIÁRIAS -> swing diário (semanas) -> zonas PLT/DM macro
(poucas ao longo de 2 anos) -> EVENTO = preço RETORNA a uma zona macro. N pequeno por CONSTRUÇÃO.
  MACRO PLT = swing-high diário depois EXCEDIDO (close diário acima) -> polaridade -> suporte.
  MACRO DM  = swing-low diário que ORIGINA perna que rompe o swing-high diário anterior (BOS macro).
  EVENTO = 1º toque 15M numa zona macro ativa após >=N barras fora (episódio de retorno, dedup).
SANITY_PROBE: escala DIÁRIA (semanas de contexto, NÃO snapshot 15M-local); evento contextual de
retorno a zona macro; estrutura anterior por meses; causal known_at; não busca-por-barra."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
# --- resample DIÁRIO ---
from collections import OrderedDict
days=OrderedDict()
for b in S:
    d=dt.datetime.utcfromtimestamp(b["t"]).strftime("%Y-%m-%d")
    if d not in days: days[d]={"t":b["t"],"o":b["o"] if "o" in b else b["c"],"h":b["h"],"l":b["l"],"c":b["c"],"i0":None}
    dd=days[d]; dd["h"]=max(dd["h"],b["h"]); dd["l"]=min(dd["l"],b["l"]); dd["c"]=b["c"]
D=list(days.values()); ND=len(D)
DH=[d["h"] for d in D]; DL=[d["l"] for d in D]; DC=[d["c"] for d in D]
# ATR diário 14
DATR=[]; tr=[]
for i in range(ND):
    if i==0: t=DH[i]-DL[i]
    else: t=max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1]))
    tr.append(t); DATR.append(sum(tr[-14:])/min(len(tr),14))
# --- swing diário (zigzag r*ATR-diário) ---
def dzz(r):
    hs=[]; ls=[]; d=0; ehi=elo=0
    for i in range(1,ND):
        a=DATR[i] or 10
        if DH[i]>DH[ehi]: ehi=i
        if DL[i]<DL[elo]: elo=i
        if d<=0 and DH[i]-DL[elo]>=r*a and elo<i: ls.append({"i":elo,"L":DL[elo],"conf":i}); d=1; ehi=max(range(elo,i+1),key=lambda k:DH[k])
        elif d>=0 and DH[ehi]-DL[i]>=r*a and ehi<i: hs.append({"i":ehi,"H":DH[ehi],"conf":i}); d=-1; elo=min(range(ehi,i+1),key=lambda k:DL[k])
    return hs,ls
# validar contra PLT do Cris: qual r diário reproduz os 10 PLT?
rows=json.load(open(HERE/"results"/"manual_shapes_pltdm_20260707.json"))
PLT=[(int(r["points"][0]["time"]),r["points"][0]["price"]) for r in rows if r["name"]=="text_note" and r["text"].strip().upper()=="PLT" and r.get("points")]
DMc=[(int(r["points"][0]["time"]),r["points"][0]["price"]) for r in rows if r["name"]=="text_note" and r["text"].strip().upper()=="DM" and r.get("points")]
def di(t): return bisect.bisect_right([d["t"] for d in D],t)-1
print("=== qual escala diária reproduz PLT(topo)/DM(fundo) do Cris? ===")
for r in (0.8,1.0,1.3,1.6,2.0):
    hs,ls=dzz(r)
    pm=sum(1 for t,pp in PLT if any(abs(h["H"]-pp)<=0.6*(DATR[h["i"]] or 10) and abs(h["i"]-di(t))<=4 for h in hs))
    dm=sum(1 for t,pp in DMc if any(abs(l["L"]-pp)<=0.6*(DATR[l["i"]] or 10) and abs(l["i"]-di(t))<=4 for l in ls))
    print(f"  r={r}: {len(hs)} swing-high · {len(ls)} swing-low diários · PLT {pm}/10 · DM {dm}/11")
# escolher r que melhor cobre e construir zonas macro
R=1.3
HS,LS=dzz(R)
# MACRO PLT: swing-high diário depois excedido (polaridade)
PLTz=[]
for h in HS:
    H=h["H"]; bi=None
    for m in range(h["conf"],ND):
        if DC[m]>H+0.1*(DATR[m] or 10): bi=m; break
    if bi is not None: PLTz.append({"lvl":H,"active_day":bi,"i":h["i"]})
# MACRO DM: swing-low diário que origina perna rompendo o swing-high diário anterior
DMz=[]
for L in LS:
    prior=[h["H"] for h in HS if h["conf"]<=L["conf"]]
    if not prior: continue
    ref=prior[-1]; bi=None
    for m in range(L["conf"],min(ND,L["conf"]+30)):
        if DC[m]>ref+0.1*(DATR[m] or 10): bi=m; break
    if bi is not None: DMz.append({"lvl":L["L"],"active_day":bi,"i":L["i"]})
print(f"\nzonas macro (r={R}): PLT {len(PLTz)} · DM {len(DMz)}")
# --- EVENTO = 1º toque 15M numa zona macro ativa após >=COOL barras fora ---
day_t=[d["t"] for d in D]
def zones_active_at(ti):
    didx=bisect.bisect_right(day_t,TS[ti])-1
    z=[]
    for Z in PLTz:
        if Z["active_day"]<didx: z.append(Z["lvl"])
    for Z in DMz:
        if Z["active_day"]<didx: z.append(Z["lvl"])
    return z
COOL=192  # 2 dias fora antes de novo evento na mesma zona
def build_events(tolatr=0.8):
    # tol em ATR diário do dia corrente
    ev=[]; last_touch={}
    for ti in range(ND, N):  # começa após 1º dia
        didx=bisect.bisect_right(day_t,TS[ti])-1
        a=DATR[didx] if didx<len(DATR) else 10
        lo=LO[ti]
        for Z in PLTz+DMz:
            if Z["active_day"]>=didx: continue
            lvl=Z["lvl"]
            if lvl-tolatr*a<=lo<=lvl+tolatr*a:
                key=id(Z)
                if key in last_touch and ti-last_touch[key]<COOL: last_touch[key]=ti; break
                last_touch[key]=ti; ev.append({"ti":ti,"t":TS[ti],"lvl":lvl,"kind":"PLT" if Z in PLTz else "DM"}); break
    return ev
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
FT=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
def recall(ev,WH=18):
    T=sorted(e["t"] for e in ev); g=0; hit=[]
    for ft in FT:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: g+=1; hit.append(ft)
    return g,hit
print("\n=== EVENTOS de retorno a zona macro (por tolerância) ===")
for tol in (0.5,0.8,1.2):
    ev=build_events(tol); g,hit=recall(ev)
    print(f"  tol={tol}ATR-dia: N-eventos {len(ev)} · recall {g}/42 · densidade {len(ev)/max(1,g):.1f}:1")
ev=build_events(0.8); g,hit=recall(ev)
missed=[ft for ft in FT if ft not in hit]
print(f"\ntol=0.8 · N{len(ev)} recall {g}/42")
print("MISSED: "+", ".join(ds(m) for m in missed))
json.dump({"R":R,"nPLT":len(PLTz),"nDM":len(DMz),"N":len(ev),"recall":g,"events":[{"t":e["t"],"d":ds(e["t"]),"kind":e["kind"],"lvl":round(e["lvl"],1)} for e in ev]},open(HERE/"results"/"macro_event_20260707.json","w"),indent=1)
print("OK")
