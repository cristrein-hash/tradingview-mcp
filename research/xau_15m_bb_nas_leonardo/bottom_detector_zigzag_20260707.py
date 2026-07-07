#!/usr/bin/env python3
"""DETECTOR DE FUNDO v2 — PIVÔS ZIGZAG MULTI-ESCALA (2026-07-07). Os fundos do Cris são swing-lows
de ESCALAS diferentes: pullback raso BULL = pivô de r pequeno; capitulação BEAR = pivô de r grande.
Zigzag causal (pivô LOW confirmado quando preço sobe r·ATR do low; known_at = barra de confirmação,
NUNCA a barra do pivô). Multi-escala r em {1.5, 3, 6}. Cada pivô-low = 1 candidato de fundo (limpo,
sem varredura de barras nem dedup destrutivo). Classificar por regime multi-escala. Recall vs 42.
Ordem: estrutura (pivô+regime) -> reversão (o pivô confirma = reverteu) -> emissão no known_at.
SANITY_PROBE: pivô causal (known_at>pivot, assert); multi-escala; recall por regime; não métrica-FN."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
# regime multi-escala dia
days={}
for b in S:
    k=b["t"]//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"],"t":k*86400})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]; DT=[days[k]["t"] for k in DK]
def ema(v,n):
    k=2/(n+1); e=v[0]; o=[e]
    for x in v[1:]: e=x*k+e*(1-k); o.append(e)
    return o
E20=ema(DC,20); E40=ema(DC,40)
TRd=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
ATRd=[sum(TRd[max(1,i-13):i+1])/max(1,len(TRd[max(1,i-13):i+1])) for i in range(len(DK))]
def regime_at(t):
    di=bisect.bisect_right(DT,t-86400)-1
    if di<40: return "WARMUP"
    slope=(E20[di]-E20[di-20])/max(0.01,ATRd[di])
    if E20[di]>E40[di] and slope>0.3: return "BULL"
    if E20[di]<E40[di] and slope<-0.3: return "BEAR"
    return "RANGE"
def zigzag_lows(r):
    lows=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i:
            d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
        elif d<=0 and HI[i]-LO[elo]>=r*a and elo<i:
            assert i>elo
            lows.append({"pivot_i":elo,"known_i":i,"r":r,"low":LO[elo],
                         "known_t":TS[i],"pivot_t":TS[elo]})
            d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
    return lows
# uniao multi-escala, dedup por pivot_i proximo (mesma vela low em escalas diferentes -> mantem menor r)
allp=[]
for r in (1.5,3.0,6.0): allp+=zigzag_lows(r)
allp.sort(key=lambda x:(x["pivot_i"], x["r"]))
piv=[]; seen={}
for p in allp:
    key=p["pivot_i"]//4  # ~1h de tolerancia no pivo
    if key in seen: continue
    seen[key]=1; piv.append(p)
piv.sort(key=lambda x:x["known_t"])
# regime + profundidade por pivo
for p in piv:
    p["regime"]=regime_at(p["known_t"])
    li=p["pivot_i"]; a=ATR[li] or 5.0
    hp=max(HI[max(0,li-192):li+1]); p["drop_atr"]=round((hp-LO[li])/a,1)
print(f"pivôs-low multi-escala (candidatos de fundo): {len(piv)}")
from collections import Counter
print("por regime:", dict(Counter(p["regime"] for p in piv)))
print("por escala r:", dict(Counter(p["r"] for p in piv)))
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
fundos=sorted([n for n in cat["notes"]["FUNDO"] if n["t"]],key=lambda x:int(x["t"]))
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json"))
mid_by_date={r["date"]:r["mid"] for r in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
# recall: fundo marcado detectado se algum PIVÔ-low tem pivot_t em ±12h do timestamp da nota
PT=[p["pivot_t"] for p in piv]
def near(ft, WH=14):
    j=bisect.bisect_left(PT,ft-WH*3600)
    while j<len(piv) and piv[j]["pivot_t"]<=ft+WH*3600:
        return piv[j]
    return None
hit=0; bym={"BULL":[0,0],"BEAR":[0,0],"RANGE":[0,0]}; miss=[]
for f in fundos:
    ft=int(f["t"]); mid=mid_by_date.get(ds(ft),"?")
    if mid in bym: bym[mid][1]+=1
    d=near(ft)
    if d: hit+=1; bym.get(mid,[0,0])[0]+=1 if mid in bym else 0
    else: miss.append((ds(ft),f["price"],mid))
print(f"\nRECALL (pivô-low em ±14h): {hit}/{len(fundos)}")
for k,v in bym.items():
    if v[1]: print(f"  {k}: {v[0]}/{v[1]}")
print(f"\nMISSED ({len(miss)}):")
for d,p,m in miss: print(f"  {d} {p:.0f} [{m}]")
json.dump({"n_piv":len(piv),"recall":hit,"total":len(fundos),"by_mid":bym,
           "missed":[{"date":d,"price":p,"mid":m} for d,p,m in miss]},
          open(HERE/"results"/"bottom_detector_zigzag_20260707.json","w"),indent=1,default=str)
print("OK -> results/bottom_detector_zigzag_20260707.json")
