#!/usr/bin/env python3
"""REGIME MACRO MULTI-ESCALA por vela de fundo (2026-07-07, correção Cris: há fundos válidos em
BEAR macro também). A medição EMA50>EMA100 (secular) mascarava correções BEAR de médio prazo.
Três escalas causais (agregação diária, só <= t_fundo):
  SECULAR (6-9m): EMA50 vs EMA100 (tendência de fundo — quase sempre BULL neste ouro)
  MÉDIO (1-2m):   EMA20 vs EMA40 + slope 20d/ATR (a escala que distingue correção BEAR de pullback)
  CURTO (2-3sem): direção últimas 12 barras-dia
Classificar cada fundo por regime MÉDIO (o relevante): BULL-pullback / BEAR-reversal / RANGE.
Caracterizar diferenças: retração da perna, profundidade da queda de médio prazo, se o fundo é
o FIM de uma perna BEAR de médio prazo (reversal) ou um pullback dentro de alta.
Aplicar aos 42 fundos + 3 inválidos (perna BEAR clara) + 1 pequena-acumulação.
SANITY_PROBE: catalogação/caracterização (não teste métrica); regime multi-escala causal dia."""
import json, bisect, glob
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
series = {}
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
days={}
for b in S:
    k=b["t"]//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"],"t":k*86400})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]; DT=[days[k]["t"] for k in DK]
def ema(vals,n):
    k=2/(n+1); e=vals[0]; out=[e]
    for v in vals[1:]: e=v*k+e*(1-k); out.append(e)
    return out
E20=ema(DC,20); E40=ema(DC,40); E50=ema(DC,50); E100=ema(DC,100)
TRd=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
ATRd=[sum(TRd[max(1,i-13):i+1])/max(1,len(TRd[max(1,i-13):i+1])) for i in range(len(DK))]
def regime_medio(di):
    if di<40: return None
    slope=(E20[di]-E20[di-20])/max(0.01,ATRd[di])
    if E20[di]>E40[di] and slope>0.3: return "BULL"
    if E20[di]<E40[di] and slope<-0.3: return "BEAR"
    return "RANGE"
def mid_downleg(di):
    # maior queda pico->vale nas ultimas ~40 barras-dia (medio prazo) terminando <=8 dias do fundo
    seg=range(max(0,di-40),di+1); pk=max(seg,key=lambda i:DH[i])
    aft=range(pk,di+1); vl=min(aft,key=lambda i:DL[i])
    return (DH[pk]-DL[vl])/max(0.01,ATRd[di]), di-vl
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
fundos=sorted([n for n in cat["notes"]["FUNDO"] if n["t"]],key=lambda x:int(x["t"]))
inval=sorted([n for n in cat["notes"].get("INVALIDO",[]) if n["t"]],key=lambda x:int(x["t"]))
def classify(t):
    di=bisect.bisect_right(DT,t)-1
    if di<40: return None
    rm=regime_medio(di); rs="BULL" if E50[di]>E100[di] else "BEAR"
    drop,dsv=mid_downleg(di)
    ci=bisect.bisect_right(TS,t)-1; flo=LO[ci]
    seg6=range(max(0,di-126),di+1); lo_i=min(seg6,key=lambda i:DL[i]); hi_a=max(range(lo_i,di+1),key=lambda i:DH[i]) if lo_i<di else di
    upleg=DH[hi_a]-DL[lo_i]; retr=(DH[hi_a]-flo)/max(0.01,upleg) if upleg>0 else None
    return {"sec":rs,"mid":rm,"drop_mid_atr":round(drop,1),"d_since_vale":dsv,"retr_up":round(retr,2) if retr else None}
from collections import Counter
print("=== 42 VELAS DE FUNDO por REGIME MULTI-ESCALA ===")
print(f"{'data':<12} {'sec':<5} {'mid':<6} {'drop_mid':>8} {'d_vale':>7} {'retr_up':>8}")
dist=Counter(); recs=[]
for f in fundos:
    c=classify(int(f["t"]));
    if not c: continue
    dist[c["mid"]]+=1; recs.append({"date":ds(f["t"]),**c})
    print(f"{ds(f['t']):<12} {c['sec']:<5} {c['mid']:<6} {c['drop_mid_atr']:>8} {c['d_since_vale']:>7} {str(c['retr_up']):>8}")
print(f"\nDISTRIBUIÇÃO regime-MÉDIO dos 42 fundos: {dict(dist)}")
# caracterizar diferenças por regime medio
import statistics as st
for rm in ("BULL","RANGE","BEAR"):
    g=[r for r in recs if r["mid"]==rm]
    if not g: continue
    print(f"  {rm}: n={len(g)} · retr_up med {st.median([r['retr_up'] for r in g if r['retr_up'] is not None]):.2f} · drop_mid med {st.median([r['drop_mid_atr'] for r in g]):.1f} · d_vale med {st.median([r['d_since_vale'] for r in g])}")
print("\n=== INVÁLIDOS (regra Cris) — regime + estrutura ===")
for iv in inval:
    c=classify(int(iv["t"])); tag=iv["text"].strip().replace(chr(10)," ")
    if c: print(f"{ds(iv['t'])}  sec {c['sec']} mid {c['mid']} drop_mid {c['drop_mid_atr']} d_vale {c['d_since_vale']} retr {c['retr_up']} :: {tag}")
json.dump(recs,open(HERE/"results"/"macro_regime_multiscale_20260707.json","w"),indent=1)
print("\nOK -> results/macro_regime_multiscale_20260707.json")
