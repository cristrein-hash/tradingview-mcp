#!/usr/bin/env python3
"""TESTE CONDICIONADO (Cris): bubbles SOZINHAS conflam capitulação×faca-caindo. Agrega 2 camadas p/ ISOLAR capitulação:
  (1) SVP DERIVADO do volume RAW (value-by-price janela ~session) → low ABAIXO da value area (VAL)?
  (2) POSIÇÃO NA MACROLEG: queda macro estendida (drop do topo de ~2d em ATR) = fim-de-perna, não meio.
Pergunta: DENTRO do subconjunto capitulação (abaixo-VA + macro-down estendido), o large-SELL prediz BOUNCE (positivo)?
Compara corr large-SELL→bounce: geral vs condicionado. RAW-causal. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
def selL(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    return sum(1 for x in bb[a:b] if x["side"]=="SELL" and x["size"]=="L"), sum(2 if x["size"]=="L" else 0 for x in bb[a:b] if x["side"]=="SELL")
def value_area(s,p,win=96,nb=40):
    """SVP derivado do volume RAW: histograma volume-por-preço em [p-win,p] → POC e VAL (borda inferior da área 70%)."""
    lo=max(0,p-win); seg=s[lo:p+1]
    pmin=min(b["l"] for b in seg); pmax=max(b["h"] for b in seg)
    if pmax<=pmin: return None,None
    step=(pmax-pmin)/nb; vol=[0.0]*nb
    for b in seg:
        mid=(b["h"]+b["l"])/2; k=min(nb-1,int((mid-pmin)/step)); vol[k]+=b.get("v",0) or 0
    tot=sum(vol)
    if tot<=0: return None,None
    poc=max(range(nb),key=lambda k:vol[k]); inc={poc}; acc=vol[poc]
    while acc<0.7*tot:
        l=min(inc)-1; r=max(inc)+1
        vl=vol[l] if l>=0 else -1; vr=vol[r] if r<nb else -1
        if vl>=vr and l>=0: inc.add(l); acc+=vl
        elif r<nb: inc.add(r); acc+=vr
        else: break
    val=pmin+min(inc)*step; poc_p=pmin+poc*step
    return poc_p,val
def fwd96(s,p):
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; end=min(p+96,len(s)-1)
    return (max(s[i]["h"] for i in range(p+1,end+1))-Lp)/a if end>p else 0
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(96,len(s)-4) if L[p]==min(L[p-4:p+5])]
def rank(xs):
    o=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0]*len(xs)
    for pos,i in enumerate(o): r[i]=pos
    return r
def pear(a,b):
    n=len(a);ma=sum(a)/n;mb=sum(b)/n;cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    va=sum((x-ma)**2 for x in a)**.5;vb=sum((x-mb)**2 for x in b)**.5;return cov/(va*vb) if va*vb else 0
def spear(a,b): return pear(rank(a),rank(b)) if len(a)>10 else 0
data=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        a=s[p]["atr"] or 1.0
        sL,sLw=selL(k,s[p]["t"])
        poc,val=value_area(s,p)
        below_va=(val is not None and s[p]["l"]<val)
        # macroleg: drop do topo de ~2 dias (192 barras 15M) em ATR
        lo=max(0,p-192); macro_drop=(max(b["h"] for b in s[lo:p+1])-s[p]["l"])/a
        data.append({"sL":sL,"fwd":fwd96(s,p),"below_va":below_va,"macro_drop":macro_drop})
n=len(data); print(f"candidatos: {n}")
def corr_sub(sub,label):
    if len(sub)<30: print(f"  {label}: n={len(sub)} (poucos)"); return
    c=spear([x["sL"] for x in sub],[x["fwd"] for x in sub])
    hi=[x for x in sub if x["sL"]>=2]; lo=[x for x in sub if x["sL"]==0]
    fb=st.mean([x["fwd"] for x in hi]) if hi else 0; fl=st.mean([x["fwd"] for x in lo]) if lo else 0
    print(f"  {label}: n={len(sub)} | corr(large-SELL,bounce)={c:+.3f} | bounce: L-SELL>=2 ={fb:.1f} vs L-SELL=0 ={fl:.1f}ATR (Δ={fb-fl:+.1f})")
print("GERAL (sem condição):"); corr_sub(data,"todos")
print("CONDICIONADO (capitulação = abaixo-VA + macro_drop alto):")
corr_sub([x for x in data if x["below_va"]],"abaixo-VA")
corr_sub([x for x in data if x["macro_drop"]>=10],"macro_drop>=10ATR")
corr_sub([x for x in data if x["below_va"] and x["macro_drop"]>=10],"abaixo-VA & macro_drop>=10  <== CAPITULAÇÃO")
corr_sub([x for x in data if x["below_va"] and x["macro_drop"]>=15],"abaixo-VA & macro_drop>=15  (extremo)")
