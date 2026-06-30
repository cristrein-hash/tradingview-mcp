#!/usr/bin/env python3
"""RTSE Fase 6b — 3 caminhos FP-eficientes p/ subir recall (do diagnóstico 6a):
P1 orçamento de LATÊNCIA topos (K 4->7): recupera topos pegos tarde, ZERO fire novo.
P2 detector FUNDO-GRIND ortogonal (reclaim EMA21 + higher-low, NÃO return-spike) p/ fundo quieto; união c/ CUSUM-up.
P3 limpar 2 âncoras-artefato de topo (rise<1.5ATR = sem máxima real).
Mede recall/FP-ano/null antes vs depois. Causal. n pequeno=calibração."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
def rsi_series(c,k=14):
    g=[0.0]*len(c);l=[0.0]*len(c)
    for i in range(1,len(c)):
        d=c[i]-c[i-1];g[i]=max(d,0);l[i]=max(-d,0)
    if len(c)<=k: return [50.0]*len(c)
    ag=st.mean(g[1:k+1]);al=st.mean(l[1:k+1]);out=[50.0]*len(c)
    for i in range(k+1,len(c)):
        ag=(ag*(k-1)+g[i])/k;al=(al*(k-1)+l[i])/k;out[i]=100-100/(1+ag/al) if al else 100.0
    return out
def ema(c,k):
    a=2/(k+1);o=[c[0]]
    for x in c[1:]: o.append(a*x+(1-a)*o[-1])
    return o
def cusum(c,direction):
    ret=[0.0]+[math.log(c[i]/c[i-1]) for i in range(1,len(c))];al=set();s=0.0
    for i in range(1,len(c)):
        w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1
        z=(ret[i]-mu)/sg;s=max(0,s+(direction*z-0.5))
        if s>5: al.add(i);s=0.0
    return al
def rng(b): return b["h"]-b["l"]
def atr(B,i,k=14): return sum(max(B[j]["h"]-B[j]["l"],abs(B[j]["h"]-B[j-1]["c"]),abs(B[j]["l"]-B[j-1]["c"])) for j in range(i-k+1,i+1))/k
TOPS=[];BOTS=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"]=="BEAR": TOPS.append(int(r["start"]));BOTS.append(int(r["end"]))
    if r["role"]=="MACRO" and r["family"]=="BULL": TOPS.append(int(r["end"]));BOTS.append(int(r["start"]))
    if r["role"]=="PULLBACK" and r["family"]=="BEAR" and r["parent_fam"]=="BULL": TOPS.append(int(r["start"]))
    if r["role"]=="PULLBACK" and r["family"]=="BULL" and r["parent_fam"]=="BEAR": BOTS.append(int(r["start"]))
TOPS=sorted(set(TOPS));BOTS=sorted(set(BOTS))
def anchor(B,ts,bot,W,min_excursion=0.0):
    T=[b["t"] for b in B];n=len(B);out=[]
    for t in ts:
        if not(T[0]<=t<=T[-1]): continue
        j=bisect.bisect_right(T,t)-1
        if not(25<j<n-6): continue
        rk=range(max(25,j-W),min(n-6,j+W));e=min(rk,key=lambda k:B[k]["l"]) if bot else max(rk,key=lambda k:B[k]["h"])
        if min_excursion>0:
            a=atr(B,e);exc=(B[e]["h"]-min(b["c"] for b in B[e-20:e]))/a if not bot else (max(b["c"] for b in B[e-20:e])-B[e]["l"])/a
            if exc<min_excursion: continue   # P3: descarta âncora sem excursão real
        out.append(e)
    return sorted(set(out))
B30=load(GT/"raw_30m_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
RS={id(B):rsi_series([b["c"] for b in B]) for B in [B30,B4]}
def bear_exp(B):
    C=[b["c"] for b in B];out=[]
    for i in range(25,len(B)):
        if C[i-5]<=C[i-14]: continue
        legvol=st.mean([rng(b) for b in B[i-14:i-4]]) or 1e-9;w=B[i-4:i+1]
        if sum(1 for b in w if b["c"]<b["o"])>=4 and sum(1 for b in w if rng(b)>1.5*legvol)>=2 and C[i]<C[i-5]: out.append(i)
    return out
H4=[b["h"] for b in B4];R4=RS[id(B4)]
cd4=cusum([b["c"] for b in B4],-1)
expdiv4=[i for i in bear_exp(B4) if H4[max(range(i-8,i-3),key=lambda k:H4[k])]>H4[max(range(i-22,i-9),key=lambda k:H4[k])] and R4[max(range(i-8,i-3),key=lambda k:H4[k])]<R4[max(range(i-22,i-9),key=lambda k:H4[k])]]
topf=sorted(set(expdiv4)|set(cd4))
up30=sorted(cusum([b["c"] for b in B30],1))
# P2 fundo-grind: reclaim EMA21 vindo de baixo após down-leg + higher-low
def grind_bottom(B):
    C=[b["c"] for b in B];L=[b["l"] for b in B];e21=ema(C,21);out=[]
    for i in range(30,len(B)):
        cross=C[i]>e21[i] and C[i-1]<=e21[i-1]
        downleg=e21[i-2]<e21[i-12]                      # EMA estava caindo
        hl=min(L[i-8:i+1])>min(L[i-20:i-8])             # higher-low
        if cross and downleg and hl: out.append(i)
    return out
gb30=grind_bottom(B30)
def evalarm(B,fires,targets,K):
    n=len(B);T=[b["t"] for b in B];yrs=(T[-1]-T[0])/(365.25*86400);fs=set(fires);lats=[];hit=0
    for e in targets:
        f=[i for i in range(e,min(n,e+K+1)) if i in fs]
        if f: hit+=1;lats.append(f[0]-e)
    recall=hit/len(targets) if targets else 0
    win=set(e+k for e in targets for k in range(0,K+1));fp=sum(1 for i in fires if i not in win)
    random.seed(7);M=len(fires);pool=list(range(25,n));dd=[]
    for _ in range(800):
        rf=set(random.sample(pool,M)) if 0<M<=len(pool) else set(pool)
        dd.append(sum(1 for e in targets if any((e+k) in rf for k in range(0,K+1)))/len(targets) if targets else 0)
    p=sum(1 for x in dd if x>=recall)/len(dd)
    return dict(fires=len(fires),recall=recall,lat=(st.median(lats) if lats else None),fpy=fp/yrs if yrs else 0,p=p,hit=hit)
def line(tag,d,tg): print(f"  {tag:34}{d['fires']:>6}{d['recall']:>7.2f}{str(d['lat']):>5}{d['fpy']:>8.0f}{d['p']:>8.3f}   ({d['hit']}/{tg})")
botsB=anchor(B30,BOTS,True,12)
print("#### P1 — orçamento de LATÊNCIA topos (mesmos fires, K varia)")
tops4=anchor(B4,TOPS,False,8)
print(f"  {'topo arm @K':34}{'fires':>6}{'recall':>7}{'lat':>5}{'FP/ano':>8}{'null_p':>8}")
for K in [4,5,6,7,8]: line(f"exp+div∪CUSUM K={K}",evalarm(B4,topf,tops4,K),len(tops4))
print("\n#### P2 — FUNDO-GRIND ortogonal + união c/ CUSUM-up (30M)")
print(f"  {'fundo arm':34}{'fires':>6}{'recall':>7}{'lat':>5}{'FP/ano':>8}{'null_p':>8}")
line("CUSUM-up (base)",evalarm(B30,up30,botsB,8),len(botsB))
line("grind-bottom (só)",evalarm(B30,sorted(gb30),botsB,8),len(botsB))
line("CUSUM-up ∪ grind",evalarm(B30,sorted(set(up30)|set(gb30)),botsB,8),len(botsB))
print("\n#### P3 — limpar âncoras-artefato (excursão >=1.5ATR) + COMBINADO FINAL recomendado")
tops4c=anchor(B4,TOPS,False,8,min_excursion=1.5)
botT=evalarm(B30,up30,botsB,8)                  # grind DESCARTADO (falhou); fundo = CUSUM-up sozinho
topT=evalarm(B4,topf,tops4c,7)                  # P1 latência K=7 + P3 âncora limpa
print(f"  topos reais (excursão>=1.5ATR): {len(tops4c)} (de {len(tops4)})")
line("FUNDO CUSUM-up K=8 (grind descartado)",botT,len(botsB))
line("TOPO exp+div∪CUSUM K=7 (clean)",topT,len(tops4c))
print(f"\n  COMBINADO RECOMENDADO (P1+P3, grind fora): recall {(botT['hit']+topT['hit'])/(len(botsB)+len(tops4c)):.2f} "
      f"({botT['hit']+topT['hit']}/{len(botsB)+len(tops4c)}) | FP/ano {botT['fpy']+topT['fpy']:.0f}")
print(f"  (base anterior era recall 0.58 / FP-ano 50)")
