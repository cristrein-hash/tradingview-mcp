#!/usr/bin/env python3
"""DETECTOR DE FUNDO v4 — do PADRÃO catalogado (2026-07-07, Cris: cada fundo=evento, reusar elementos).
Padrão comum dos 42 (catálogo estrutural): PERNA de queda significativa (drop grande) + REVERSÃO
estrutural (CHoCH+ após o low OU reclaim EMA21). Elementos reusados: zigzag (pivô-low), SMC CHoCH+,
EMA21. Contexto macro como GUIA (não corte rígido).
DETECTOR (cada pivô-low = evento): emite se PERNA drop>=D e REVERSÃO (CHoCH+ desde o low até known_at
OU reclaim EMA21 em <=R barras). Sem retr arbitrário. Curva de D para recall×densidade. Contexto
secular anexado (BULL/BEAR) mas não filtra. Ordem: estrutura(perna)+reversão(trajetória), não snapshot.
SANITY_PROBE: multi-fatorial (perna+CHoCH++reclaim); trajetória sequencial; pivô/CHoCH+ causais
known_at; recall por regime; catalogação/detecção não métrica-FN."""
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
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DT=[days[k]["t"] for k in DK]
def ema(v,n):
    k=2/(n+1); e=v[0]; o=[e]
    for x in v[1:]: e=x*k+e*(1-k); o.append(e)
    return o
E50=ema(DC,50); E100=ema(DC,100)
def reg_sec(t):
    di=bisect.bisect_right(DT,t-86400)-1
    return "BULL" if (di>=100 and E50[di]>E100[di]) else ("BEAR" if di>=100 else "WARM")
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
            assert i>elo; lows.append({"pi":elo,"ki":i,"pt":TS[elo],"kt":TS[i]}); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
    return lows
PIV=zz(3.0)
def choch_up_since(kt, lo_i):
    t_low=TS[lo_i]; hi=bisect.bisect_right(ET,kt)
    for m in range(hi-1,-1,-1):
        if events[m]["t"]<=t_low: break
        if events[m]["tok"]=="CHoCH+": return round((events[m]["t"]-t_low)/900)
    return None
for p in PIV:
    li=p["pi"]; a=ATR[li] or 5.0
    hp=max(HI[max(0,li-192):li+1]); p["drop"]=(hp-LO[li])/a
    p["choch"]=choch_up_since(p["kt"], li)
    rl=None
    for k in range(li,min(N,li+48)):
        if CL[k]>ema15(k,21): rl=k-li; break
    p["reclaim"]=rl; p["sec"]=reg_sec(p["kt"])
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
fundos=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json"))
mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
def recall(rows, WH=14):
    T=sorted(r["pt"] for r in rows); got=set()
    for ft in fundos:
        j=bisect.bisect_left(T,ft-WH*3600)
        if j<len(T) and T[j]<=ft+WH*3600: got.add(ft)
    return len(got), got
def dens(rows, got): return (len(rows)-len(got))/max(1,len(got))
print(f"pivôs r=3: {len(PIV)} · fundos {len(fundos)}")
print("\ncurva: PERNA drop>=D & REVERSÃO(CHoCH+ OU reclaim<=6b):")
for D in (3,4,5,6,8):
    sel=[p for p in PIV if p["drop"]>=D and (p["choch"] is not None or (p["reclaim"] is not None and p["reclaim"]<=6))]
    rc,got=recall(sel); print(f"  D>={D}: n{len(sel):>4} recall {rc}/42 densidade {dens(sel,got):.0f}:1")
# escolher D=4 (equilíbrio) e detalhar por regime + missed
D=4
SEL=[p for p in PIV if p["drop"]>=D and (p["choch"] is not None or (p["reclaim"] is not None and p["reclaim"]<=6))]
rc,got=recall(SEL)
from collections import Counter
print(f"\nD>={D}: n{len(SEL)} recall {rc}/42 densidade {dens(SEL,got):.0f}:1")
byreg={"BULL":[0,0],"RANGE":[0,0],"BEAR":[0,0]}
gs=got
for ft in fundos:
    mid=mid_by_date.get(ds(ft),"?")
    if mid in byreg: byreg[mid][1]+=1; byreg[mid][0]+= (1 if ft in gs else 0)
for k,v in byreg.items():
    if v[1]: print(f"  recall {k}: {v[0]}/{v[1]}")
missed=[ft for ft in fundos if ft not in gs]
print(f"MISSED ({len(missed)}): "+", ".join(f"{ds(ft)}[{mid_by_date.get(ds(ft),'?')}]" for ft in missed))
# detecções NOVAS (não marcadas) = detecta MAIS fundos
FT=sorted(fundos)
def near_marked(t):
    j=bisect.bisect_left(FT,t-14*3600); return j<len(FT) and FT[j]<=t+14*3600
novos=[p for p in SEL if not near_marked(p["pt"])]
print(f"\nDETECÇÕES NOVAS (candidatas a fundo não marcado): {len(novos)} · sec BULL {sum(1 for p in novos if p['sec']=='BULL')} BEAR {sum(1 for p in novos if p['sec']=='BEAR')}")
json.dump({"n_piv":len(PIV),"D":D,"n_sel":len(SEL),"recall":rc,"byreg":byreg,
           "missed":[ds(ft) for ft in missed],"n_novos":len(novos)},
          open(HERE/"results"/"bottom_detector_v4_pattern_20260707.json","w"),indent=1,default=str)
print("OK -> results/bottom_detector_v4_pattern_20260707.json")
