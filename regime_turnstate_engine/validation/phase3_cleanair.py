#!/usr/bin/env python3
"""RTSE Fase 3 — TESTE EM RAW LIMPO (sem M8). Alvo = VIRADA vs NÃO-VIRADA (ar limpo).
VIRADAS(positivo) = fundos da estratégia 15M (swept-runner substrate4_flow) ∪ bordas →BULL dos retângulos do Cris.
AR LIMPO(negativo) = barras RAW 15M longe de qualquer virada (meio de movimento). Features de detecção de fundo
(CUSUM-up, divergência MTF, aceitação, coil, RSI-div, desaceleração, MTF-align) computadas causal multi-TF.
Mede: disparam MAIS na virada que no ar limpo? + null + por-ano + confluência. Determinístico, causal."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
RX=ROOT/"research/xau_15m_bb_nas_leonardo";REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
S={}
for f in sorted((RX/"primitives").glob("*.primitives.json")):
    for b in json.loads(f.read_text())["series"]: S[b["t"]]=b
S=[S[t] for t in sorted(S)];T=[b["t"] for b in S];idx={t:i for i,t in enumerate(T)};n=len(S)
C=[b["c"] for b in S];H=[b["h"] for b in S];Lo=[b["l"] for b in S];RS=[b.get("rsi") for b in S]
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
ret=[0.0]+[math.log(C[i]/C[i-1]) for i in range(1,n)];au=set();sp=0.0
for i in range(1,n):
    w=ret[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1;z=(ret[i]-mu)/sg;sp=max(0,sp+(z-0.5))
    if sp>5: au.add(i);sp=0.0
def atr(i,k=14): return sum(max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-k+1,i+1))/k
def feats(i):  # BOT-oriented (fundo)
    d={};ts=T[i]
    d["cusum"]=1.0 if any((i-w) in au for w in range(0,13)) else 0.0
    d["div"]=1.0 if (any((1 if e15f[i-w]>e15s[i-w] else -1)==1 for w in range(0,8)) and stTF(B30,ts)!=1) else 0.0
    lev=min(Lo[i-20:i-1]);d["accept"]=1.0 if (Lo[i]<lev and C[i]>lev) else 0.0   # sweep+reclaim
    atrm=st.mean([atr(x) for x in range(i-20,i)]);d["coil"]=1.0 if (any(atr(x)<0.8*atrm for x in range(i-6,i)) and (H[i]-Lo[i])>1.4*atrm and C[i]>C[i-1]) else 0.0
    r=RS[i] or 50;rp=RS[i-6] or 50;d["rsidiv"]=1.0 if (Lo[i]<min(Lo[i-12:i-1]) and r>rp) else 0.0
    v1=C[i]-C[i-3];v2=C[i-3]-C[i-6];d["decel"]=1.0 if (v1>v2 and v1<0) else 0.0
    d["mtf"]=1.0 if sum(1 for s in [(1 if e15f[i]>e15s[i] else -1),stTF(B30,ts),stTF(B4,ts)] if s==1)>=2 else 0.0
    return d
# VIRADAS = fundos estratégia + bordas BULL dos retângulos
pos_idx=set()
for r in [json.loads(l) for l in (RX/"substrate4_flow.jsonl").read_text().splitlines()]:
    i=idx.get(r["cj_t"])
    if i is not None and 45<=i<n-1: pos_idx.add(i)
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"]=="BULL":
        j=bisect.bisect_right(T,int(r["start"]))-1
        if 45<=j<n-1: pos_idx.add(j)
pos_idx=sorted(pos_idx)
# AR LIMPO = barras longe de qualquer virada (±30 barras), amostra n_pos
W=30;banned=set()
for i in pos_idx:
    for w in range(-W,W+1): banned.add(i+w)
cand=[i for i in range(60,n-1) if i not in banned]
random.seed(1);neg_idx=random.sample(cand,min(len(pos_idx),len(cand)))
def yr(i): return dt.datetime.utcfromtimestamp(T[i]).year
POS=[{**feats(i),"pos":1,"yr":yr(i)} for i in pos_idx]
NEG=[{**feats(i),"pos":0,"yr":yr(i)} for i in neg_idx]
rows=POS+NEG;N=len(rows)
print(f"RAW LIMPO — VIRADAS(pos) {len(POS)} vs AR-LIMPO(neg) {len(NEG)}")
print(f"{'feature':9}{'vira%':>7}{'limpo%':>8}{'lift':>8}{'null_p':>8}")
random.seed(4)
for k in ["cusum","div","accept","coil","rsidiv","decel","mtf"]:
    pv=st.mean([r[k] for r in POS]);ng=st.mean([r[k] for r in NEG]);real=pv-ng
    allv=[r[k] for r in rows];labs=[r["pos"] for r in rows];dd=[]
    for _ in range(500):
        random.shuffle(labs);dd.append(st.mean([allv[i] for i in range(N) if labs[i]])-st.mean([allv[i] for i in range(N) if not labs[i]]))
    p=sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
    print(f"{k:9}{100*pv:>7.0f}{100*ng:>8.0f}{100*real:>+8.0f}{p:>8.3f}{' *' if p<0.05 else ''}")
print("\n-- CONFLUÊNCIA (contagem) — taxa de VIRADA por nível --")
for r in rows: r["conf"]=sum(r[k] for k in ["cusum","div","accept","coil","rsidiv","decel","mtf"])
for c in range(0,8):
    g=[r for r in rows if int(r["conf"])==c]
    if g: print(f"  conf={c}: vira {100*sum(r['pos'] for r in g)/len(g):.0f}% (n{len(g)})")
hi=[r for r in rows if r["conf"]>=3];lo=[r for r in rows if r["conf"]<=1]
print(f"  conf>=3 ({len(hi)}) vira {100*sum(r['pos'] for r in hi)/len(hi):.0f}% | conf<=1 ({len(lo)}) vira {100*sum(r['pos'] for r in lo)/len(lo):.0f}%")
