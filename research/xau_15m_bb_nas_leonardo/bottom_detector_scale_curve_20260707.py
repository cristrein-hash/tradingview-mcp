#!/usr/bin/env python3
"""CURVA ESCALA×PROFUNDIDADE do detector de fundo (2026-07-07). Cada escala de zigzag isolada +
filtro por drop, medindo recall vs n_pivôs (densidade). Achar o detector de recall alto e densidade
gerenciável (não 100:1). Ordem: estrutura (pivô+regime+drop). Meta: detectar MAIS fundos sem LA."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
series={}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
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
def zz(r):
    lows=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
        elif d<=0 and HI[i]-LO[elo]>=r*a and elo<i:
            hp=max(HI[max(0,elo-192):elo+1]); lows.append({"pi":elo,"ki":i,"pt":TS[elo],"kt":TS[i],
                "drop":(hp-LO[elo])/(ATR[elo] or 5.0),"reg":regime_at(TS[i])}); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
    return lows
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
fundos=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
def recall(piv, WH=14):
    PT=sorted(p["pt"] for p in piv); h=0
    for ft in fundos:
        j=bisect.bisect_left(PT,ft-WH*3600)
        if j<len(PT) and PT[j]<=ft+WH*3600: h+=1
    return h
print(f"{'escala r':>8} {'n_piv':>6} {'recall':>7} {'dens':>6}   filtros drop:")
for r in (1.5, 3.0, 4.5, 6.0):
    piv=zz(r); rc=recall(piv)
    print(f"{r:>8} {len(piv):>6} {rc:>5}/42 {(len(piv)-42)/42:>5.0f}:1")
    for dmin in (2,3,5):
        pf=[p for p in piv if p["drop"]>=dmin]; rcf=recall(pf)
        print(f"           drop>={dmin}: n{len(pf):>5} recall {rcf}/42 dens {(len(pf)-rcf)/max(1,rcf):.0f}:1")
# escala natural por fundo: menor r em que o fundo aparece como pivô
print("\n=== ESCALA NATURAL de cada fundo (menor r que o captura) + regime ===")
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json"))
mid_by_date={x["date"]:x["mid"] for x in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
zzs={r:zz(r) for r in (1.5,3.0,4.5,6.0)}
from collections import Counter
esc=Counter()
for ft in fundos:
    natural=None
    for r in (6.0,4.5,3.0,1.5):
        PT=sorted(p["pt"] for p in zzs[r])
        j=bisect.bisect_left(PT,ft-14*3600)
        if j<len(PT) and PT[j]<=ft+14*3600: natural=r
    esc[(natural, mid_by_date.get(ds(ft),"?"))]+=1
for (r,mid),n in sorted(esc.items(), key=lambda x:str(x[0])):
    print(f"  escala r>={r} · regime {mid}: {n} fundos")
print("OK")
