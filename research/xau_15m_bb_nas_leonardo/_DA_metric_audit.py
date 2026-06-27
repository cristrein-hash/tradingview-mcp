#!/usr/bin/env python3
"""AUDITORIA do metro: meu fwd_rev (para na 1ª perfuração de BUF*ATR) pode ZERAR o bounce nos fundos climáticos
(flush final perfura antes do V). Compara nos 17 fundos do Cris: large-SELL no janela vs fwd_rev(meu) vs fwd96
(maior alta nas próximas 96 barras SEM corte de perfuração) vs fwd_to_swing. Se big-sell tem fwd_rev baixo MAS fwd96
alto → metro quebrado (Cris certo). RAW-causal. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900; BUF=0.25
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
def selL(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]; a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    sL=sum(1 for x in bb[a:b] if x["side"]=="SELL" and x["size"]=="L")
    sAll=sum(1 for x in bb[a:b] if x["side"]=="SELL")
    return sL,sAll
def fwd_rev(s,p):  # MEU metro (para na perfuração)
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; ext=Lp; end=min(p+192,len(s)-1)
    for i in range(p+1,end+1):
        if s[i]["l"]<Lp-BUF*a: break
        ext=max(ext,s[i]["h"])
    return (ext-Lp)/a
def fwd96(s,p):  # robusto: maior alta nas próximas 96 barras, SEM corte
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; end=min(p+96,len(s)-1)
    return (max(s[i]["h"] for i in range(p+1,end+1))-Lp)/a if end>p else 0
def blk_for(t):
    for k,pr in PRIM.items():
        s=pr["series"]
        if s[0]["t"]<=t<=s[-1]["t"]: return k
    return None
def nidx(s,t): return min(range(len(s)),key=lambda i:abs(s[i]["t"]-t))
his=[3326.83,3375.62,3516.03,3623.49,3631.35,3725.33,3802.45,3830.9,3946.28,3950,4204.32,3888.33,4015.8,4277.91,4324.59,4427.94,4671.74]
ht=[1755867600,1756271700,1756955700,1757466900,1757897100,1758744900,1759224600,1759421700,1759827600,1760038200,1760722200,1761638400,1763445600,1765877400,1767371400,1770005700,1770338700]
print("teus 17 fundos: large-SELL(janela) | sell_total | fwd_rev(meu) | fwd96(robusto) | ratio")
import datetime as dt
for price,t in sorted(zip(his,ht),key=lambda x:x[1]):
    k=blk_for(t); s=PRIM[k]["series"]; i0=nidx(s,t)
    i=min(range(max(0,i0-6),min(len(s),i0+7)),key=lambda j:s[j]["l"])  # flush low local
    sL,sAll=selL(k,s[i]["t"]); fr=fwd_rev(s,i); f96=fwd96(s,i)
    print(f"  {dt.datetime.utcfromtimestamp(s[i]['t']):%Y-%m-%d %H:%M} L-SELL={sL:>2} sell={sAll:>2} | fwd_rev={fr:>5.1f} | fwd96={f96:>5.1f} | f96/fr={f96/fr if fr>0.1 else 99:>4.1f}")
# correlação global: large-sell vs fwd96 (robusto) controlando down_leg, vs vs fwd_rev
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(20,len(s)-4) if L[p]==min(L[p-4:p+5])]
def rank(xs):
    o=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0]*len(xs)
    for pos,i in enumerate(o): r[i]=pos
    return r
def pear(a,b):
    n=len(a);ma=sum(a)/n;mb=sum(b)/n;cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    va=sum((x-ma)**2 for x in a)**.5;vb=sum((x-mb)**2 for x in b)**.5;return cov/(va*vb) if va*vb else 0
def spear(a,b): return pear(rank(a),rank(b))
sLv=[];frv=[];f96v=[];dlv=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        sL,_=selL(k,s[p]["t"]); a=s[p]["atr"] or 1.0
        sLv.append(sL); frv.append(fwd_rev(s,p)); f96v.append(fwd96(s,p)); dlv.append((s[p-PRE//900]["c"]-s[p]["l"])/a)
print(f"\nGLOBAL n={len(sLv)} | corr(large-SELL, fwd_rev MEU)={spear(sLv,frv):+.3f} | corr(large-SELL, fwd96 ROBUSTO)={spear(sLv,f96v):+.3f}")
# controlado por down_leg (quartis)
qs=sorted(dlv); q=[qs[len(qs)//4],qs[len(qs)//2],qs[3*len(qs)//4]]
def bk(x): return 0 if x<q[0] else 1 if x<q[1] else 2 if x<q[2] else 3
import collections
for tgt,nm in [(frv,"fwd_rev MEU"),(f96v,"fwd96 ROBUSTO")]:
    cs=[]
    for bb in range(4):
        idx=[i for i in range(len(dlv)) if bk(dlv[i])==bb]
        if len(idx)>30: cs.append(spear([sLv[i] for i in idx],[tgt[i] for i in idx]))
    print(f"  corr CONTROLADA (down_leg) large-SELL→{nm}: {sum(cs)/len(cs):+.3f}  por bucket {[round(c,2) for c in cs]}")
