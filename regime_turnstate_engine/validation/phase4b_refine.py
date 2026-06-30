#!/usr/bin/env python3
"""RTSE Fase 4b — refina a hipótese do Cris condicionando ao separador VALIDADO (divergência/overbought no topo
ANTES das 5 velas). Testa se isso converte o detector que disparava demais (dip-vs-flip) em causal+seletivo.
Variantes: A=expansão-bear pura (baseline) · B=A + topo DIVERGENTE (HH preço, LH RSI) · C=A + topo OVERBOUGHT/climax.
Mede recall/latência/FP-ano/null-base-rate em 30M e 4H (n=15). n pequeno => CALIBRAÇÃO (não validação). Causal."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
def rsi_series(c,k=14):
    g=[0.0]*len(c);l=[0.0]*len(c)
    for i in range(1,len(c)):
        d=c[i]-c[i-1];g[i]=max(d,0);l[i]=max(-d,0)
    ag=st.mean(g[1:k+1]) if len(c)>k else 0;al=st.mean(l[1:k+1]) if len(c)>k else 0;out=[50.0]*len(c)
    for i in range(k+1,len(c)):
        ag=(ag*(k-1)+g[i])/k;al=(al*(k-1)+l[i])/k;out[i]=100-100/(1+ag/al) if al else 100.0
    return out
TOPS=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"]=="BEAR": TOPS.append(int(r["start"]))
    if r["role"]=="MACRO" and r["family"]=="BULL": TOPS.append(int(r["end"]))
    if r["role"]=="PULLBACK" and r["family"]=="BEAR" and r["parent_fam"]=="BULL": TOPS.append(int(r["start"]))
TOPS=sorted(set(TOPS))
def rng(b): return b["h"]-b["l"]
def make_signal(B,variant):
    C=[b["c"] for b in B];H=[b["h"] for b in B];RSI=rsi_series(C)
    def S(i):
        if i<25 or i>=len(B): return False
        if C[i-5]<=C[i-14]: return False
        legvol=st.mean([rng(b) for b in B[i-14:i-4]]) or 1e-9
        w=B[i-4:i+1];nbear=sum(1 for b in w if b["c"]<b["o"]);wide=sum(1 for b in w if rng(b)>1.5*legvol)
        if not(nbear>=4 and wide>=2 and C[i]<C[i-5]): return False
        if variant=="A": return True
        hi=max(range(i-8,i-3),key=lambda k:H[k])          # topo imediatamente antes das bears
        phi=max(range(i-22,i-9),key=lambda k:H[k])        # topo anterior
        if variant=="B": return H[hi]>H[phi] and RSI[hi]<RSI[phi]       # HH preço + LH RSI (divergência)
        if variant=="C": return RSI[hi]>65 or any(rng(B[k])>2.0*legvol and B[k]["c"]>B[k]["o"] for k in range(i-8,i-3))  # overbought/climax-up
        return False
    return S
def extreme_hi(B,j,W): return max(range(max(20,j-W),min(len(B)-1,j+W)),key=lambda k:B[k]["h"])
def run(name,B,K,W):
    T=[b["t"] for b in B];n=len(B);cov0,cov1=T[0],T[-1];yrs=(cov1-cov0)/(365.25*86400)
    tops=sorted(set(extreme_hi(B,bisect.bisect_right(T,t)-1,W) for t in TOPS if cov0<=t<=cov1 and 25<bisect.bisect_right(T,t)-1<n-1))
    print(f"\n== {name} (topos {len(tops)}, K={K}b, {dt.datetime.utcfromtimestamp(cov0).date()}..{dt.datetime.utcfromtimestamp(cov1).date()}) ==")
    print(f"  {'var':4}{'fires':>7}{'%bar':>6}{'recall':>8}{'lat':>5}{'FP/ano':>8}{'null_p':>8}")
    for v in ["A","B","C"]:
        S=make_signal(B,v);fires=[i for i in range(25,n) if S(i)];fs=set(fires)
        lats=[];hit=0
        for e in tops:
            f=[i for i in range(e,min(n,e+K+1)) if i in fs]
            if f: hit+=1;lats.append(f[0]-e)
        recall=hit/len(tops) if tops else 0
        topwin=set(e+k for e in tops for k in range(0,K+1));fp=sum(1 for i in fires if i not in topwin);fpy=fp/yrs
        random.seed(7);M=len(fires);pool=list(range(25,n));dd=[]
        for _ in range(1000):
            rf=set(random.sample(pool,M)) if M<=len(pool) else set(pool)
            dd.append(sum(1 for e in tops if any((e+k) in rf for k in range(0,K+1)))/len(tops) if tops else 0)
        p=sum(1 for x in dd if x>=recall)/len(dd)
        lat=f"{st.median(lats):.0f}" if lats else "-"
        print(f"  {v:4}{len(fires):>7}{100*len(fires)/n:>5.1f}{recall:>8.2f}{lat:>5}{fpy:>8.0f}{p:>8.3f}{' *' if p<0.05 else ''}")
B30=load(GT/"raw_30m_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
run("30M",B30,8,12)
run("4H (n maior = mais confiável)",B4,4,8)
