#!/usr/bin/env python3
"""RTSE Fase 3 — SET A (fundos/topos MACRO dos retângulos) no RAW 4H, onde os 2 anos das bordas vivem.
Ancora na EXTREMA REAL do 4H (±15 barras da borda). FUNDOS = bordas→BULL + fim-de-BEAR. TOPOS = bordas→BEAR + fim-de-BULL.
MTF macro = 4H + diário + semanal (resample do 4H). RSI(14) Wilder nativo no 4H. vs AR-LIMPO (4H longe de extrema).
Features de virada na extrema + null. Determinístico, causal."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
B=load(REV/"raw_4h_ohlc.jsonl");T=[b["t"] for b in B];C=[b["c"] for b in B];H=[b["h"] for b in B];Lo=[b["l"] for b in B];n=len(B)
def ema(c,k):
    a=2/(k+1);o=[c[0]]
    for x in c[1:]:o.append(a*x+(1-a)*o[-1])
    return o
e4f=ema(C,9);e4s=ema(C,30)
# RSI(14) Wilder no 4H
def rsi_series(c,k=14):
    g=[0.0]*len(c);l=[0.0]*len(c)
    for i in range(1,len(c)):
        d=c[i]-c[i-1];g[i]=max(d,0);l[i]=max(-d,0)
    ag=st.mean(g[1:k+1]);al=st.mean(l[1:k+1]);out=[50.0]*len(c)
    for i in range(k+1,len(c)):
        ag=(ag*(k-1)+g[i])/k;al=(al*(k-1)+l[i])/k;out[i]=100-100/(1+ag/al) if al else 100.0
    return out
RSI=rsi_series(C)
def resample(times,closes,bucket):
    d={}
    for t,c in zip(times,closes): d[t//bucket]=c  # último close do bucket
    it=sorted(d.items());return [x[0]*bucket for x in it],[x[1] for x in it]
dt_,dc=resample(T,C,86400);def_=ema(dc,9);des=ema(dc,30)
wt_,wc=resample(T,C,7*86400);wef=ema(wc,9);wes=ema(wc,30)
def stTF(times,ef,es,ts):
    j=bisect.bisect_right(times,ts)-1;return (1 if ef[j]>es[j] else -1) if j>=0 else 0
def atr(i,k=14): return sum(max(H[j]-Lo[j],abs(H[j]-C[j-1]),abs(Lo[j]-C[j-1])) for j in range(i-k+1,i+1))/k
def feats(e,bot):
    d={};r=RSI[e];a=atr(e)
    if bot:
        d["new_extreme"]=1.0 if Lo[e]<=min(Lo[e-10:e]) else 0.0
        d["os_ob"]=1.0 if r<35 else 0.0
        pl=min(range(e-15,e-2),key=lambda k:Lo[k]);d["rsidiv"]=1.0 if (Lo[e]<Lo[pl] and RSI[e]>RSI[pl]) else 0.0
        d["stretch"]=1.0 if (e4s[e]-C[e])/a>1.0 else 0.0
        v1=C[e]-C[e-3];v2=C[e-3]-C[e-6];d["decel"]=1.0 if (v1>v2 and v1<0) else 0.0
        ctx=-1
    else:
        d["new_extreme"]=1.0 if H[e]>=max(H[e-10:e]) else 0.0
        d["os_ob"]=1.0 if r>65 else 0.0
        ph=max(range(e-15,e-2),key=lambda k:H[k]);d["rsidiv"]=1.0 if (H[e]>H[ph] and RSI[e]<RSI[ph]) else 0.0
        d["stretch"]=1.0 if (C[e]-e4s[e])/a>1.0 else 0.0
        v1=C[e]-C[e-3];v2=C[e-3]-C[e-6];d["decel"]=1.0 if (v1<v2 and v1>0) else 0.0
        ctx=1
    d["climax"]=1.0 if (H[e]-Lo[e])>=2.0*st.mean([atr(x) for x in range(e-20,e)]) else 0.0
    s=[(1 if e4f[e]>e4s[e] else -1),stTF(dt_,def_,des,T[e]),stTF(wt_,wef,wes,T[e])]
    d["mtf_ctx"]=1.0 if sum(1 for x in s if x==ctx)>=2 else 0.0  # TFs ainda no sentido pré-virada
    return d
# bordas macro -> extrema real ±15 barras
W=15;bots=set();tops=set()
def near(ts):
    j=bisect.bisect_right(T,ts)-1;return j
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]!="MACRO": continue
    s=near(int(r["start"]));en=near(int(r["end"]))
    fam=r["family"]
    if 25<=s<n-6:
        if fam=="BULL": bots.add(min(range(max(25,s-W),min(n-6,s+W)),key=lambda k:Lo[k]))
        if fam=="BEAR": tops.add(max(range(max(25,s-W),min(n-6,s+W)),key=lambda k:H[k]))
    if 25<=en<n-6:
        if fam=="BEAR": bots.add(min(range(max(25,en-W),min(n-6,en+W)),key=lambda k:Lo[k]))
        if fam=="BULL": tops.add(max(range(max(25,en-W),min(n-6,en+W)),key=lambda k:H[k]))
bots=sorted(bots);tops=sorted(tops)
ban=set()
for i in list(bots)+list(tops):
    for w in range(-W*2,W*2+1): ban.add(i+w)
cand=[i for i in range(40,n-6) if i not in ban]
random.seed(1);NEG=sorted(random.sample(cand,min(700,len(cand))))
FK=["new_extreme","climax","rsidiv","os_ob","stretch","decel","mtf_ctx"]
def test(name,ids,bot):
    RP=[feats(e,bot) for e in ids];RN=[feats(e,bot) for e in NEG]
    print(f"\n== {name}: n{len(RP)} vs ar-limpo n{len(RN)} ==")
    print(f"{'feature':12}{'set%':>6}{'limpo%':>8}{'lift':>7}{'null_p':>8}")
    pool=RP+RN;labs=[1]*len(RP)+[0]*len(RN);N=len(pool);random.seed(4)
    for k in FK:
        pv=st.mean([x[k] for x in RP]);ng=st.mean([x[k] for x in RN]);real=pv-ng
        allv=[x[k] for x in pool];lb=labs[:];dd=[]
        for _ in range(800):
            random.shuffle(lb);dd.append(st.mean([allv[i] for i in range(N) if lb[i]])-st.mean([allv[i] for i in range(N) if not lb[i]]))
        p=sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
        print(f"  {k:12}{100*pv:>5.0f}{100*ng:>8.0f}{100*real:>+7.0f}{p:>8.3f}{' *' if p<0.05 else ''}")
print(f"RAW 4H n{n} ({dt.datetime.utcfromtimestamp(T[0]).date()}..{dt.datetime.utcfromtimestamp(T[-1]).date()})")
test("FUNDOS MACRO (BULL-start + BEAR-end)",bots,True)
test("TOPOS MACRO (BEAR-start + BULL-end)",tops,False)
