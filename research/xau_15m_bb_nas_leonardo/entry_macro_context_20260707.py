#!/usr/bin/env python3
"""STEP 0 — classificador de CONTEXTO MACRO estrutural para os 96 entries (2026-07-07, ordem Cris).
Corrige o proxy errado anterior (EMA diária lenta colapsava macro->micro). Usa SWINGS DIÁRIOS (semanas)
e ESTRUTURA (HH-HL / LH-LL) para classificar cada entry: BULL / RANGE / BEAR macro. Deriva também:
  - choch_up: em bear, preço fechou ACIMA do último lower-high (mudança de caráter = bear quebrada).
  - leg_ext: extensão da perna de alta corrente desde a origem (último swing-low diário), em ATR-dia.
  - room_up: distância ao swing-high diário acima (pequeno = perto do topo macro = exaustão).
  - range_pos: se RANGE, posição na banda (0=demanda/fundo, 1=topo).
Verifica contra o visual: winners devem cair em BULL-markup jovem; losers em topo/range/bear.
SANITY_PROBE: contexto MACRO estrutural (swings diários, semanas); HH-HL/LH-LL; CHoCH-up; maturidade de
perna; trajetória; NÃO snapshot, NÃO EMA-lenta; master markup/correção preservado."""
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
# --- daily bars ---
from collections import OrderedDict
days=OrderedDict()
for b in S:
    d=dt.datetime.utcfromtimestamp(b["t"]).strftime("%Y-%m-%d")
    if d not in days: days[d]={"t":b["t"],"h":b["h"],"l":b["l"],"c":b["c"]}
    dd=days[d]; dd["h"]=max(dd["h"],b["h"]); dd["l"]=min(dd["l"],b["l"]); dd["c"]=b["c"]
D=list(days.values()); ND=len(D); DT=[x["t"] for x in D]; DH=[x["h"] for x in D]; DL=[x["l"] for x in D]; DC=[x["c"] for x in D]
DATR=[]; tr=[]
for i in range(ND):
    t=DH[i]-DL[i] if i==0 else max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1]))
    tr.append(t); DATR.append(sum(tr[-14:])/min(len(tr),14))
# daily zigzag -> macro swings (ordenados)
def dzz(r=1.2):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,ND):
        a=DATR[i] or 10
        if DH[i]>DH[ehi]: ehi=i
        if DL[i]<DL[elo]: elo=i
        if d<=0 and DH[i]-DL[elo]>=r*a and elo<i: piv.append(("L",elo,DL[elo])); d=1; ehi=max(range(elo,i+1),key=lambda k:DH[k])
        elif d>=0 and DH[ehi]-DL[i]>=r*a and ehi<i: piv.append(("H",ehi,DH[ehi])); d=-1; elo=min(range(ehi,i+1),key=lambda k:DL[k])
    return piv
PIV=dzz(1.2)
def di(t): return bisect.bisect_right(DT,t)-1
def macro_ctx(t0):
    dd=di(t0)
    ph=[(i,pr) for tp,i,pr in PIV if tp=="H" and i<=dd]
    pl=[(i,pr) for tp,i,pr in PIV if tp=="L" and i<=dd]
    if len(ph)<2 or len(pl)<2: return {"ctx":"NA","choch_up":0,"leg_ext":0,"room_up":99,"range_pos":0.5}
    H2=ph[-2:]; L2=pl[-2:]
    hh=H2[-1][1]>H2[-2][1]; hl=L2[-1][1]>L2[-2][1]
    lh=H2[-1][1]<H2[-2][1]; ll=L2[-1][1]<L2[-2][1]
    if hh and hl: ctx="BULL"
    elif lh and ll: ctx="BEAR"
    else: ctx="RANGE"
    a=DATR[dd] or 10; px=DC[dd]
    # choch_up: em bear/range, preço fechou acima do último lower-high (quebra da bear)
    last_LH=H2[-1][1]
    choch_up=1 if (ctx!="BULL" and px>last_LH+0.1*a) else 0
    # leg_ext: origem = último swing-low; extensão até px
    origin=pl[-1][1]; leg_ext=(px-origin)/a
    # room_up: swing-high diário acima de px
    above=[pr for i,pr in ph if pr>px]
    room_up=min((pr-px)/a for pr in above) if above else 99
    # range_pos: banda dos últimos 12 dias
    lo=min(DL[max(0,dd-12):dd+1]); hi=max(DH[max(0,dd-12):dd+1])
    range_pos=(px-lo)/((hi-lo) or 1)
    return {"ctx":ctx,"choch_up":choch_up,"leg_ext":round(leg_ext,2),"room_up":round(room_up,2),"range_pos":round(range_pos,2)}
# --- reconstruir os 96 entries markup (mesma caminhada r=6) ---
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
        if prevH is not None and lastH is not None and (prevL is None or pr>prevL): EV.append({"i":i,"lo":pr,"leg_top":lastH})
        prevL=pr
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
rows=[]; n=0
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
    tgt=ent+3*risk; out=0
    for m in range(j+1,min(N,j+1440)):
        if LO[m]<=sl: out=0; break
        if HI[m]>=tgt: out=1; break
    n+=1; mc=macro_ctx(TS[j])
    rows.append({"n":n,"d":ds(TS[j]),"t":TS[j],"out":out,"reclaim_lag":j-i,"sig2":1 if j-i<=4 else 0,**mc})
json.dump(rows,open(HERE/"results"/"entry_macro_context_20260707.json","w"),indent=1)
def yr(d): return d[:4]
def rate(sel): return sum(x["out"] for x in sel)/len(sel) if sel else 0
print(f"96 entries reclassificados por contexto MACRO estrutural (daily swings r=1.2)")
print("\n=== macro_ctx x outcome (verificar vs visual) ===")
for c in ("BULL","RANGE","BEAR","NA"):
    sel=[r for r in rows if r["ctx"]==c]
    if sel: print(f"  {c:<6} N{len(sel):<3} hit-3R {rate(sel):.1%} · winners {sum(x['out'] for x in sel)}")
# STEP1 preview: dentro de BEAR, choch_up separa?
print("\n=== STEP1 preview — dentro de BEAR: choch_up (bear quebrada) separa? ===")
BE=[r for r in rows if r["ctx"]=="BEAR"]
for cu in (1,0):
    sel=[r for r in BE if r["choch_up"]==cu]
    if sel: print(f"  choch_up={cu}: N{len(sel):<3} hit-3R {rate(sel):.1%} · winners {sum(x['out'] for x in sel)}  ex: {[r['n'] for r in sel][:8]}")
# STEP2 preview: dentro de RANGE, range_pos (demanda=baixo) separa?
print("\n=== STEP2 preview — dentro de RANGE: range_pos (demanda=fundo) separa? ===")
RG=[r for r in rows if r["ctx"]=="RANGE"]
for lo,hi in [(0,0.33),(0.33,0.66),(0.66,1.01)]:
    sel=[r for r in RG if lo<=r["range_pos"]<hi]
    if sel: print(f"  range_pos {lo}-{hi}: N{len(sel):<3} hit-3R {rate(sel):.1%} · winners {sum(x['out'] for x in sel)}")
# STEP3 preview: exaustão (room_up pequeno / leg_ext grande) nos losers?
print("\n=== STEP3 preview — exaustão: room_up e leg_ext (winner vs loser, todos) ===")
W=[r for r in rows if r["out"]==1]; L=[r for r in rows if r["out"]==0]
for k in ("leg_ext","room_up"):
    print(f"  {k:<10} WIN med {st.median([r[k] for r in W]):.2f}  LOSE med {st.median([r[k] for r in L]):.2f}")
print("\nsaved results/entry_macro_context_20260707.json · OK")
