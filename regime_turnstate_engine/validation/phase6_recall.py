#!/usr/bin/env python3
"""RTSE Fase 6 — subir RECALL sem inflar FP. Caminho: (A) DIAGNOSTICAR quais viradas se perdem + por quê;
(B) adicionar detectores ORTOGONAIS dirigidos ao subtipo perdido (cada um raro => união soma recall, não FP).
Testa complementos FP-eficientes: fundo=CUSUM-up multi-escala (30M ∪ 1H); topo=4H(exp+div∪CUSUM-down) ∪ overbought-rejection.
Mede recall/FP-ano/null antes vs depois. n pequeno=calibração; null por densidade=honesto. Causal."""
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
def anchor(B,ts,bot,W):
    T=[b["t"] for b in B];n=len(B);out=set()
    for t in ts:
        if not(T[0]<=t<=T[-1]): continue
        j=bisect.bisect_right(T,t)-1
        if not(25<j<n-6): continue
        rk=range(max(25,j-W),min(n-6,j+W));out.add(min(rk,key=lambda k:B[k]["l"]) if bot else max(rk,key=lambda k:B[k]["h"]))
    return sorted(out)
B30=load(GT/"raw_30m_ohlc.jsonl");B1=load(REV/"raw_1h_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
RS={id(B):rsi_series([b["c"] for b in B]) for B in [B30,B1,B4]}
def bear_exp(B):
    C=[b["c"] for b in B];out=[]
    for i in range(25,len(B)):
        if C[i-5]<=C[i-14]: continue
        legvol=st.mean([rng(b) for b in B[i-14:i-4]]) or 1e-9;w=B[i-4:i+1]
        if sum(1 for b in w if b["c"]<b["o"])>=4 and sum(1 for b in w if rng(b)>1.5*legvol)>=2 and C[i]<C[i-5]: out.append(i)
    return out
H4=[b["h"] for b in B4];R4=RS[id(B4)];T4=[b["t"] for b in B4]
cd4=cusum([b["c"] for b in B4],-1)
expdiv4=[]
for i in bear_exp(B4):
    hi=max(range(i-8,i-3),key=lambda k:H4[k]);ph=max(range(i-22,i-9),key=lambda k:H4[k])
    if H4[hi]>H4[ph] and R4[hi]<R4[ph]: expdiv4.append(i)
# overbought-rejection 4H (topo de range: máxima feita + RSI>62 + fecha de volta abaixo)
ob_rej4=[]
for i in range(25,len(B4)):
    if H4[i]>=max(H4[i-10:i]) and R4[i-1]>62 and B4[i]["c"]<B4[i]["o"] and B4[i]["c"]<(H4[i]-0.5*(H4[i]-B4[i]["l"])): ob_rej4.append(i)
def mapfires(srcB,src_idx,dstB):  # mapeia índices de srcB p/ barra dstB pelo tempo
    Td=[b["t"] for b in dstB];out=set()
    for j in src_idx:
        k=bisect.bisect_right(Td,srcB[j]["t"])-1
        if 0<=k<len(dstB): out.add(k)
    return out
def evalarm(B,fires,targets,K):
    n=len(B);T=[b["t"] for b in B];yrs=(T[-1]-T[0])/(365.25*86400);fs=set(fires);lats=[];hit=0;miss=[]
    for e in targets:
        f=[i for i in range(e,min(n,e+K+1)) if i in fs]
        if f: hit+=1;lats.append(f[0]-e)
        else: miss.append(e)
    recall=hit/len(targets) if targets else 0
    win=set(e+k for e in targets for k in range(0,K+1));fp=sum(1 for i in fires if i not in win)
    random.seed(7);M=len(fires);pool=list(range(25,n));dd=[]
    for _ in range(800):
        rf=set(random.sample(pool,M)) if 0<M<=len(pool) else set(pool)
        dd.append(sum(1 for e in targets if any((e+k) in rf for k in range(0,K+1)))/len(targets) if targets else 0)
    p=sum(1 for x in dd if x>=recall)/len(dd)
    return dict(fires=len(fires),recall=recall,lat=(st.median(lats) if lats else None),fpy=fp/yrs if yrs else 0,p=p,hit=hit,miss=miss)
# ---------- (A) DIAGNÓSTICO das perdas ----------
print("#### (A) DIAGNÓSTICO — quais viradas se perdem e por quê")
botsB=anchor(B30,BOTS,True,12);up30=sorted(cusum([b["c"] for b in B30],1));ufs=set(up30)
print(f"\n FUNDOS (30M, alvo {len(botsB)}) — braço CUSUM-up:")
for e in botsB:
    near=[(i-e) for i in up30 if abs(i-e)<=40];lat=min([d for d in near if d>=0],default=None)
    caught="OK" if (lat is not None and lat<=8) else "PERDE"
    dd=dt.datetime.utcfromtimestamp(B30[e]["t"]).date();a=atr(B30,e);drop=(max(b["c"] for b in B30[e-20:e])-B30[e]["l"])/a
    print(f"  {dd} {caught:5} lat={lat} RSI={RS[id(B30)][e]:.0f} drop={drop:.1f}ATR climax={(rng(B30[e])>2*st.mean([atr(B30,x) for x in range(e-20,e)]))}")
tops4=anchor(B4,TOPS,False,8);topf=sorted(set(expdiv4)|set(cd4));tfs=set(topf)
print(f"\n TOPOS (4H, alvo {len(tops4)}) — braço exp+div ∪ CUSUM-down:")
for e in tops4:
    near=[(i-e) for i in topf if abs(i-e)<=20];lat=min([d for d in near if d>=0],default=None)
    caught="OK" if (lat is not None and lat<=4) else "PERDE"
    dd=dt.datetime.utcfromtimestamp(B4[e]["t"]).date();a=atr(B4,e);rise=(B4[e]["h"]-min(b["c"] for b in B4[e-20:e]))/a
    print(f"  {dd} {caught:5} lat={lat} RSI={R4[e]:.0f} rise={rise:.1f}ATR climax={(rng(B4[e])>2*st.mean([atr(B4,x) for x in range(e-20,e)]))}")
# ---------- (B) COMPLEMENTOS ortogonais ----------
print("\n\n#### (B) COMPLEMENTOS — recall ANTES vs DEPOIS (FP controlado)")
# FUNDO: 30M ∪ 1H CUSUM-up
up1_on30=mapfires(B1,sorted(cusum([b["c"] for b in B1],1)),B30)
botbase=evalarm(B30,up30,botsB,8);botML=evalarm(B30,sorted(set(up30)|up1_on30),botsB,8)
print(f"\n FUNDO (30M, alvo {len(botsB)}):")
print(f"  {'arm':28}{'fires':>6}{'recall':>7}{'FP/ano':>8}{'null_p':>8}")
print(f"  {'base CUSUM-up 30M':28}{botbase['fires']:>6}{botbase['recall']:>7.2f}{botbase['fpy']:>8.0f}{botbase['p']:>8.3f}")
print(f"  {'+ CUSUM-up 1H (multiescala)':28}{botML['fires']:>6}{botML['recall']:>7.2f}{botML['fpy']:>8.0f}{botML['p']:>8.3f}")
# TOPO: base ∪ overbought-rejection
topbase=evalarm(B4,topf,tops4,4);topC=evalarm(B4,sorted(set(topf)|set(ob_rej4)),tops4,4)
print(f"\n TOPO (4H, alvo {len(tops4)}):")
print(f"  {'arm':28}{'fires':>6}{'recall':>7}{'FP/ano':>8}{'null_p':>8}")
print(f"  {'base exp+div∪CUSUM-down':28}{topbase['fires']:>6}{topbase['recall']:>7.2f}{topbase['fpy']:>8.0f}{topbase['p']:>8.3f}")
print(f"  {'+ overbought-rejection':28}{topC['fires']:>6}{topC['recall']:>7.2f}{topC['fpy']:>8.0f}{topC['p']:>8.3f}")
print(f"\n COMBINADO base: recall {(botbase['hit']+topbase['hit'])/(len(botsB)+len(tops4)):.2f} ({botbase['hit']+topbase['hit']}/{len(botsB)+len(tops4)}) FP/ano {botbase['fpy']+topbase['fpy']:.0f}")
print(f" COMBINADO +complementos: recall {(botML['hit']+topC['hit'])/(len(botsB)+len(tops4)):.2f} ({botML['hit']+topC['hit']}/{len(botsB)+len(tops4)}) FP/ano {botML['fpy']+topC['fpy']:.0f}")
