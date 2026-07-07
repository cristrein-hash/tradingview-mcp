#!/usr/bin/env python3
"""DETECTOR v5 — APROFUNDAR contexto estrutural p/ baixar N de 926 (2026-07-07, Cris).
Sobre os pivôs-low r=3 (recall 39/42 com perna+reversão), adicionar CONTEXTO ESTRUTURAL (trajetória,
não snapshot) e achar convergência que baixe N mantendo recall:
  A perna>=D ATR (magnitude da queda)
  B CHoCH+ desde o low (reversão estrutural CONFIRMADA — não só reclaim)
  C reclaim EMA21 rápido (<=Rb)
  D ZONA de demanda revisitada: flo perto (<=1.5ATR) de swing-low anterior (192-1920b) = memória
  E PERNA DE ALTA MACRO antes da correção: nos ~40 dias antes, houve subida >= U·ATRdia (o fundo é
    retração de uma alta, não queda-livre BEAR contínua)
  F retração da perna de alta macro em faixa (0,1-1,0) — nem topo nem abaixo da origem
Curva de convergências. Meta: N ~100-200 com recall >=34/42. Cada pivô = evento.
SANITY_PROBE: features ESTRUTURAIS/trajetória (perna/zona/reversão macro), multi-fatorial,
causais known_at; não snapshot; recall por regime; não métrica-FN."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src=(HERE/"macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
N=len(S); ATR=[b.get("atr") or 5.0 for b in S]; HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
days={}
for b in S:
    k=b["t"]//86400; g=days.setdefault(k,{"c":b["c"],"h":b["h"],"l":b["l"],"t":k*86400})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]; DT=[days[k]["t"] for k in DK]
TRd=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
ATRd=[sum(TRd[max(1,i-13):i+1])/max(1,len(TRd[max(1,i-13):i+1])) for i in range(len(DK))]
def ema(v,n):
    k=2/(n+1); e=v[0]; o=[e]
    for x in v[1:]: e=x*k+e*(1-k); o.append(e)
    return o
E50=ema(DC,50); E100=ema(DC,100)
def ema15(i,n):
    a=CL[max(0,i-3*n):i+1]; k=2/(n+1); e=a[0]
    for v in a[1:]: e=v*k+e*(1-k)
    return e
def zz(r):
    lows=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
        elif d<=0 and HI[i]-LO[elo]>=r*a and elo<i:
            lows.append({"pi":elo,"ki":i,"pt":TS[elo],"kt":TS[i]}); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
    return lows
PIV=zz(3.0)
# swing-lows 15M para zona de demanda (fractais w=8)
SWL=[k for k in range(8,N-8) if LO[k]==min(LO[k-8:k+9]) and LO[k-8:k].count(LO[k])==0]
SWLp=[LO[k] for k in SWL]; SWLt=[TS[k] for k in SWL]
def choch_up_since(kt, li):
    tl=TS[li]; hi=bisect.bisect_right(ET,kt)
    for m in range(hi-1,-1,-1):
        if events[m]["t"]<=tl: break
        if events[m]["tok"]=="CHoCH+": return round((events[m]["t"]-tl)/900)
    return None
for p in PIV:
    li=p["pi"]; a=ATR[li] or 5.0; flo=LO[li]
    hp=max(HI[max(0,li-192):li+1]); p["drop"]=(hp-flo)/a
    p["choch"]=choch_up_since(p["kt"],li)
    rl=None
    for k in range(li,min(N,li+48)):
        if CL[k]>ema15(k,21): rl=k-li; break
    p["reclaim"]=rl
    # D zona demanda: swing-low anterior (>=96b antes, <=1920b) perto do flo
    j=bisect.bisect_left(SWLt, TS[li]-1920*900); revisit=0
    while j<len(SWL) and SWLt[j] <= TS[li]-96*900:
        if abs(SWLp[j]-flo)<=1.5*a: revisit=1; break
        j+=1
    p["revisit"]=revisit
    # E/F perna de alta macro + retração
    di=bisect.bisect_right(DT,TS[li]-86400)-1
    if di>=50:
        seg6=range(max(0,di-126),di+1); loi=min(seg6,key=lambda i:DL[i]); hia=max(range(loi,di+1),key=lambda i:DH[i]) if loi<di else di
        upleg=(DH[hia]-DL[loi])/max(0.01,ATRd[di]); upleg_atr=upleg
        retr=(DH[hia]-flo)/max(0.01,(DH[hia]-DL[loi])) if DH[hia]>DL[loi] else None
        p["upleg_atr"]=round(upleg_atr,1); p["retr_up"]=round(retr,2) if retr else None
        p["sec"]="BULL" if E50[di]>E100[di] else "BEAR"
    else:
        p["upleg_atr"]=0; p["retr_up"]=None; p["sec"]="WARM"
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
fundos=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json"))
mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
def recall(rows,WH=14):
    T=sorted(r["pt"] for r in rows); got=set()
    for ft in fundos:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: got.add(ft)
    return got
base=[p for p in PIV if p["drop"]>=4 and (p["choch"] is not None or (p["reclaim"] is not None and p["reclaim"]<=6))]
print(f"base (perna>=4 & reversão): n{len(base)} recall {len(recall(base))}/42")
print("\ncurva de convergência (contexto estrutural):")
def show(sel,tag):
    got=recall(sel); print(f"  {tag:<48} n{len(sel):>4} recall {len(got)}/42 dens {(len(sel)-len(got))/max(1,len(got)):.0f}:1")
    return got
show([p for p in base if p["choch"] is not None], "+ CHoCH+ obrigatório")
show([p for p in base if p["revisit"]==1], "+ zona-demanda revisitada")
show([p for p in base if p["upleg_atr"]>=8], "+ perna-alta-macro >=8 ATRdia")
show([p for p in base if p["choch"] is not None and p["revisit"]==1], "+ CHoCH+ & zona-demanda")
show([p for p in base if p["choch"] is not None and p["upleg_atr"]>=8], "+ CHoCH+ & perna-alta>=8")
show([p for p in base if p["revisit"]==1 and p["upleg_atr"]>=8], "+ zona & perna-alta>=8")
g=show([p for p in base if p["choch"] is not None and p["revisit"]==1 and p["upleg_atr"]>=8], "+ CHoCH+ & zona & perna-alta>=8")
show([p for p in base if p["drop"]>=6 and p["choch"] is not None and p["revisit"]==1], "+ drop>=6 & CHoCH+ & zona")
# detalhe do melhor equilibrio: CHoCH+ & zona & perna-alta>=8
SEL=[p for p in base if p["choch"] is not None and p["revisit"]==1 and p["upleg_atr"]>=8]
got=recall(SEL); gs=got
byreg={"BULL":[0,0],"RANGE":[0,0],"BEAR":[0,0]}
for ft in fundos:
    mid=mid_by_date.get(ds(ft),"?")
    if mid in byreg: byreg[mid][1]+=1; byreg[mid][0]+=(1 if ft in gs else 0)
print(f"\nMELHOR EQUILÍBRIO (CHoCH+ & zona & perna-alta>=8): n{len(SEL)} recall {len(got)}/42")
for k,v in byreg.items():
    if v[1]: print(f"  {k}: {v[0]}/{v[1]}")
missed=[ds(ft) for ft in fundos if ft not in gs]
print("MISSED:", ", ".join(f"{d}[{mid_by_date.get(d,'?')}]" for d in missed))
json.dump({"n_base":len(base),"sel_n":len(SEL),"recall":len(got),"byreg":byreg,"missed":missed},
          open(HERE/"results"/"bottom_detector_v5_deepen_20260707.json","w"),indent=1,default=str)
print("OK -> results/bottom_detector_v5_deepen_20260707.json")
