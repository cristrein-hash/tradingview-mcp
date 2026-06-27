#!/usr/bin/env python3
"""Última checagem de artefato: normalizar bounce por ATR pode esconder o sinal (cluster SELL grande = flush de ATR
alto → bounce/ATR suprimido mesmo com bounce$ grande). Compara corr(large-SELL, bounce) em ATR vs DÓLAR vs %.
Também corr(large-SELL, ATR) p/ ver se large-SELL puxa ATR alto. RAW-causal. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
def selL(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    return sum(1 for x in bb[a:b] if x["side"]=="SELL" and x["size"]=="L")
def fwd_dollar(s,p):
    Lp=s[p]["l"]; end=min(p+96,len(s)-1); return max(s[i]["h"] for i in range(p+1,end+1))-Lp if end>p else 0
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(96,len(s)-4) if L[p]==min(L[p-4:p+5])]
def rank(xs):
    o=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0]*len(xs)
    for pos,i in enumerate(o): r[i]=pos
    return r
def pear(a,b):
    n=len(a);ma=sum(a)/n;mb=sum(b)/n;cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    va=sum((x-ma)**2 for x in a)**.5;vb=sum((x-mb)**2 for x in b)**.5;return cov/(va*vb) if va*vb else 0
def spear(a,b): return pear(rank(a),rank(b))
sL=[];b_atr=[];b_usd=[];b_pct=[];atrs=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        a=s[p]["atr"] or 1.0; d=fwd_dollar(s,p)
        sL.append(selL(k,s[p]["t"])); b_usd.append(d); b_atr.append(d/a); b_pct.append(d/s[p]["l"]); atrs.append(a)
n=len(sL)
print(f"n={n}")
print(f"corr(large-SELL, bounce ATR)   = {spear(sL,b_atr):+.3f}")
print(f"corr(large-SELL, bounce DÓLAR) = {spear(sL,b_usd):+.3f}")
print(f"corr(large-SELL, bounce %)     = {spear(sL,b_pct):+.3f}")
print(f"corr(large-SELL, ATR no fundo) = {spear(sL,atrs):+.3f}  (se alto: large-SELL puxa ATR alto)")
# médias por bucket large-SELL
for lab,f in [("ATR",b_atr),("DÓLAR",b_usd)]:
    hi=[f[i] for i in range(n) if sL[i]>=2]; lo=[f[i] for i in range(n) if sL[i]==0]
    print(f"  bounce {lab}: L-SELL>=2 ={st.mean(hi):.1f} vs L-SELL=0 ={st.mean(lo):.1f}")
