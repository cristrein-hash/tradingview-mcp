#!/usr/bin/env python3
"""ESTUDO DE CASO DOS LOSERS — filtragem CONTEXTUAL primeiro (2026-07-07, ordem do Cris).
Master = markup/correção (leg-walk). Sobre os 96 entries MARKUP, caracterizo os 44 losers em dimensões
CONTEXTUAIS de estrutura/perna (NÃO snapshot, NÃO features isoladas):
  1. EXAUSTÃO / entrada ALTA na perna: entry_pos_in_leg = (entry−demanda)/(topo_perna−demanda);
     extension_atr = (entry−demanda)/ATR — reclaim que correu muito = entrada alta/chased.
  2. MACRO-BEARLEG: regime macro (EMA diária 20/40 + inclinação) no entry — compra no meio de queda macro.
  3. NEAR-MISS: MFE em R (máx excursão favorável antes do SL) — loser que quase foi winner (>=2.5R).
Filtros aplicados NA ORDEM do Cris (exaustão -> macro-bearleg -> near-miss), cumulativos, mantendo
markup MASTER, exigindo N e ambos-anos. Indicadores ficam para DEPOIS de exaurir isto.
SANITY_PROBE: contexto de perna/macro (trajetória multi-barra, não snapshot); MFE trajetória; master
markup; dois objetivos (cortar loser + manter winner); filtros contextuais estruturais; não features isoladas."""
import json, glob, bisect
import datetime as dt
from pathlib import Path
import statistics as st
HERE=Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]; EMA=[b.get("ema21") for b in S]
# daily EMA20/40 p/ macro regime
from collections import OrderedDict
days=OrderedDict()
for b in S:
    d=dt.datetime.utcfromtimestamp(b["t"]).strftime("%Y-%m-%d")
    if d not in days: days[d]={"t":b["t"],"c":b["c"]}
    days[d]["c"]=b["c"]
D=list(days.values()); DT=[x["t"] for x in D]; DC=[x["c"] for x in D]
def ema(arr,n):
    out=[None]*len(arr); k=2/(n+1); e=None
    for i,v in enumerate(arr):
        e=v if e is None else v*k+e*(1-k); out[i]=e
    return out
DE20=ema(DC,20); DE40=ema(DC,40)
def macro_reg(t0):
    di=bisect.bisect_right(DT,t0)-1
    if di<41: return "NA"
    up=DE20[di]>DE40[di]; slope=DE20[di]-DE20[di-5]
    if up and slope>0: return "BULL"
    if (not up) and slope<0: return "BEAR"
    return "RANGE"
# reconstruir eventos markup (mesma caminhada r=6) + entry + MFE
def zz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
piv=zz(6); EV=[]; prevH=prevL=None; lastH=None
for tp,i,pr,ci in piv:
    if tp=="H": prevH=pr; lastH=pr
    else:
        if prevH is not None and lastH is not None and (prevL is None or pr>prevL):  # MARKUP
            EV.append({"i":i,"lo":pr,"leg_top":lastH})
        prevL=pr
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
rows=[]
for e in EV:
    i=e["i"]
    if not (W0<=TS[i]<=W1): continue
    lo=e["lo"]; a=ATR[i] or 5
    j=None
    for k in range(i+1,min(N,i+25)):
        if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]: j=k; break
    if j is None: continue
    ent=CL[j]; sl=lo-0.1*a; risk=ent-sl
    if risk<=0.05*a: continue
    tgt=ent+3*risk; out=0; mfe=0; endm=min(N,j+1440)
    for m in range(j+1,endm):
        mfe=max(mfe,(HI[m]-ent)/risk)
        if LO[m]<=sl: out=0; break
        if HI[m]>=tgt: out=1; break
    lp=(ent-lo)/((e["leg_top"]-lo) or 1)         # posição da entry na perna (0=demanda,1=topo)
    ext=(ent-lo)/a                                # extensão do reclaim em ATR (entrada alta/chased)
    rl=j-i
    rows.append({"d":ds(TS[j]),"out":out,"mfe":round(mfe,2),"leg_pos":round(lp,2),"ext_atr":round(ext,2),
                 "reclaim_lag":rl,"macro":macro_reg(TS[j]),"sig2":1 if rl<=4 else 0})
def yr(d): return d[:4]
def panel(sel,tag):
    if not sel: print(f"  {tag:<34} N0"); return
    h=sum(r["out"] for r in sel); ybk=" ".join(f"{y}:{sum(r['out'] for r in sel if yr(r['d'])==y)}/{sum(1 for r in sel if yr(r['d'])==y)}" for y in ("2025","2026"))
    print(f"  {tag:<34} N{len(sel):<4} hit-3R {h/len(sel):.1%} · {ybk}")
W=[r for r in rows if r["out"]==1]; L=[r for r in rows if r["out"]==0]
print(f"MARKUP entries {len(rows)} · winners {len(W)} losers {len(L)}")
print("\n=== CONTEXTO: winners vs losers (medianas) ===")
for k in ("leg_pos","ext_atr","mfe","reclaim_lag"):
    print(f"  {k:<12} WIN {st.median([r[k] for r in W]):.2f}  LOSE {st.median([r[k] for r in L]):.2f}")
print("  macro (winner%):")
for mr in ("BULL","RANGE","BEAR","NA"):
    ww=[r for r in rows if r["macro"]==mr]
    if ww: print(f"    {mr:<6} N{len(ww):<3} hit-3R {sum(r['out'] for r in ww)/len(ww):.1%}")
print("\n=== NEAR-MISS: losers que quase foram winners ===")
for thr in (2.0,2.5,2.8):
    nm=[r for r in L if r["mfe"]>=thr]; print(f"  losers MFE>={thr}R: {len(nm)}/{len(L)}")
print("\n=== FILTROS CONTEXTUAIS na ORDEM do Cris (cumulativos, markup MASTER) ===")
panel(rows,"0. base markup")
f1=[r for r in rows if r["leg_pos"]<=0.6]; panel(f1,"1. + não-alta na perna (leg_pos<=0.6)")
f1b=[r for r in rows if r["leg_pos"]<=0.5]; panel(f1b,"1b. leg_pos<=0.5 (mais estrito)")
f2=[r for r in f1 if r["macro"]!="BEAR"]; panel(f2,"2. + fora de macro-BEARleg")
f2b=[r for r in f1 if r["macro"]=="BULL"]; panel(f2b,"2b. só macro-BULL")
# sinal2 sob os filtros
s2=[r for r in f2 if r["sig2"]==1]; panel(s2,"3. + reclaim rápido (R) [sinal2]")
json.dump(rows,open(HERE/"results"/"loser_case_study_20260707.json","w"),indent=1)
print("\nsaved · OK")
