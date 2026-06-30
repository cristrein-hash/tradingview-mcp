#!/usr/bin/env python3
"""RTSE Fase 3 — reancorado na EXTREMA REAL, sets separados. Sem M8.
SET A = fundos MACRO (bordas →BULL dos retângulos, NÃO filtrados) na mínima real ±5d.
SET B = fundos da estratégia 15M (swept-runner) na mínima real (argmin em [cj-6,cj], não entry+3).
NEG = ar limpo (longe de qualquer extrema). Features de FUNDO avaliadas na barra da mínima (causal).
Mede fire-rate A vs NEG e B vs NEG + null. Determinístico."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo";REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
S={}
for f in sorted((RX/"primitives").glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: S[b["t"]]=b
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)};n=len(S)
C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S];RS=[b.get("rsi") for b in S];EMA=[b.get("ema21") for b in S]
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
B30=load(GT/"raw_30m_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
def ema(c,k):
    a=2/(k+1);o=[c[0]]
    for x in c[1:]:o.append(a*x+(1-a)*o[-1])
    return o
e15f=ema(C,9);e15s=ema(C,30)
def stTF(bars,ts):
    c=[b["c"] for b in bars];ef=ema(c,9);es=ema(c,30);j=bisect.bisect_right([b["t"] for b in bars],ts)-1
    return (1 if ef[j]>es[j] else -1) if j>=0 else 0
ret=[0.0]+[math.log(C[i]/C[i-1]) for i in range(1,n)];adn=set();sn=0.0
for i in range(1,n):
    w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1;z=(ret[i]-mu)/sg;sn=max(0,sn+(-z-0.5))
    if sn>5: adn.add(i);sn=0.0
def atr(i,k=14): return sum(max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-k+1,i+1))/k
def feats(e):  # na MÍNIMA real (fundo)
    d={};r=RS[e] or 50;a=atr(e)
    d["new_low"]=1.0 if Lo[e]<=min(Lo[e-10:e]) else 0.0
    d["oversold"]=1.0 if r<35 else 0.0
    # divergência: novo low mas RSI acima do RSI no low anterior
    pl=min(range(e-15,e-2),key=lambda k:Lo[k]); d["rsidiv"]=1.0 if (Lo[e]<Lo[pl] and (RS[e] or 50)>(RS[pl] or 50)) else 0.0
    d["stretch"]=1.0 if (EMA[e] and (EMA[e]-C[e])/a>1.0) else 0.0
    v1=C[e]-C[e-3];v2=C[e-3]-C[e-6];d["decel"]=1.0 if (v1>v2 and v1<0) else 0.0
    d["flush_cusum"]=1.0 if any((e-w) in adn for w in range(0,6)) else 0.0
    d["climax"]=1.0 if (H[e]-Lo[e])>=2.0*st.mean([atr(x) for x in range(e-20,e)]) else 0.0
    d["mtf_down"]=1.0 if sum(1 for s in [(1 if e15f[e]<e15s[e] else -1),(-1 if stTF(B30,T[e])==-1 else 1),(-1 if stTF(B4,T[e])==-1 else 1)] if s==-1)>=2 else 0.0
    return d
def extreme_lo(i,lo=6,hi=1):
    return min(range(max(20,i-lo),min(n-1,i+hi)),key=lambda k:Lo[k])
# SET A: bordas BULL dos retângulos -> mínima real ±5d
A=set()
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"]=="BULL":
        j=bisect.bisect_right(T,int(r["start"]))-1
        if 25<=j<n-1:
            lo=max(25,j-20);hiw=min(n-1,j+20);A.add(min(range(lo,hiw),key=lambda k:Lo[k]))
A=sorted(A)
# SET B: entradas estratégia -> mínima real
B=set()
for r in [json.loads(l) for l in (RX/"substrate4_flow.jsonl").read_text().splitlines()]:
    i=idx.get(r["cj_t"])
    if i is not None and 25<=i<n-1: B.add(extreme_lo(i))
B=sorted(B)
# NEG: ar limpo
ban=set()
for i in list(A)+list(B):
    for w in range(-30,31): ban.add(i+w)
cand=[i for i in range(40,n-1) if i not in ban]
random.seed(1);NEG=sorted(random.sample(cand,min(600,len(cand))))
FK=["new_low","oversold","rsidiv","stretch","decel","flush_cusum","climax","mtf_down"]
def rowsof(ids): return [feats(e) for e in ids]
RA=rowsof(A);RB=rowsof(B);RN=rowsof(NEG)
def test(name,RP):
    print(f"\n== {name}: n{len(RP)} vs ar-limpo n{len(RN)} ==")
    print(f"{'feature':11}{'set%':>6}{'limpo%':>8}{'lift':>7}{'null_p':>8}")
    pool=RP+RN;labs=[1]*len(RP)+[0]*len(RN);N=len(pool);random.seed(4)
    for k in FK:
        pv=st.mean([x[k] for x in RP]);ng=st.mean([x[k] for x in RN]);real=pv-ng
        allv=[x[k] for x in pool];lb=labs[:];dd=[]
        for _ in range(400):
            random.shuffle(lb);dd.append(st.mean([allv[i] for i in range(N) if lb[i]])-st.mean([allv[i] for i in range(N) if not lb[i]]))
        p=sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
        print(f"  {k:11}{100*pv:>5.0f}{100*ng:>8.0f}{100*real:>+7.0f}{p:>8.3f}{' *' if p<0.05 else ''}")
test("SET A — fundos MACRO (retângulos, não-filtrados)",RA)
test("SET B — fundos ESTRATÉGIA 15M (mínima real)",RB)
