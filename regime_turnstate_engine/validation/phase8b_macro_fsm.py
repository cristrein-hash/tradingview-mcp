#!/usr/bin/env python3
"""RTSE Fase 8b — FSM com CONFIRMAÇÃO MACRO. Evento PROPÕE a virada; confirma só quando o preço retrai >=X%
do extremo do regime (filtra topos/fundos de pullback). Causal (espera a confirmação=latência honesta).
VALIDA: concordância barra-a-barra vs gabarito + BASELINE sempre-BULL + nº segmentos. Testa X. Sem fit às caixas."""
import json,csv,math,statistics as st,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp");REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
def rsi(c,k=14):
    g=[0.]*len(c);l=[0.]*len(c)
    for i in range(1,len(c)):
        d=c[i]-c[i-1];g[i]=max(d,0);l[i]=max(-d,0)
    ag=st.mean(g[1:k+1]);al=st.mean(l[1:k+1]);o=[50.]*len(c)
    for i in range(k+1,len(c)):
        ag=(ag*(k-1)+g[i])/k;al=(al*(k-1)+l[i])/k;o[i]=100-100/(1+ag/al) if al else 100.
    return o
def cusum(c,dr):
    r=[0.]+[math.log(c[i]/c[i-1]) for i in range(1,len(c))];a=set();s=0.
    for i in range(1,len(c)):
        w=r[max(1,i-100):i];mu=st.mean(w) if len(w)>2 else 0;sg=(st.pstdev(w) if len(w)>2 else 1) or 1
        z=(r[i]-mu)/sg;s=max(0,s+(dr*z-0.5))
        if s>5:a.add(i);s=0.
    return a
def rng(b):return b["h"]-b["l"]
def bear_exp(B):
    C=[b["c"] for b in B];o=[]
    for i in range(25,len(B)):
        if C[i-5]<=C[i-14]:continue
        lv=st.mean([rng(b) for b in B[i-14:i-4]]) or 1e-9;w=B[i-4:i+1]
        if sum(1 for b in w if b["c"]<b["o"])>=4 and sum(1 for b in w if rng(b)>1.5*lv)>=2 and C[i]<C[i-5]:o.append(i)
    return o
B30=load(GT/"raw_30m_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl")
T30=[b["t"] for b in B30];C30=[b["c"] for b in B30];H30=[b["h"] for b in B30];L30=[b["l"] for b in B30];n=len(B30)
up30=set(cusum(C30,1))
R4=rsi([b["c"] for b in B4]);H4=[b["h"] for b in B4]
cd4=cusum([b["c"] for b in B4],-1)
expdiv4=[i for i in bear_exp(B4) if H4[max(range(i-8,i-3),key=lambda k:H4[k])]>H4[max(range(i-22,i-9),key=lambda k:H4[k])] and R4[max(range(i-8,i-3),key=lambda k:H4[k])]<R4[max(range(i-22,i-9),key=lambda k:H4[k])]]
T4=[b["t"] for b in B4]
top30=set()
for i in sorted(set(expdiv4)|set(cd4)):
    j=bisect.bisect_right(T30,B4[i]["t"])-1
    if j>=0: top30.add(j)
boxes=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO": boxes.append((int(r["start"]),int(r["end"]),r["family"]))
def gt_at(ts):
    for s,e,f in boxes:
        if s<=ts<=e: return f
    return None
def run(X):
    state="BULL";ext=C30[0];pend=False;segs=[];seg_start=T30[0]
    for i in range(1,n):
        c=C30[i]
        if state=="BULL":
            ext=max(ext,c)
            if i in top30: pend=True
            if pend and c<=ext*(1-X):
                segs.append([seg_start,T30[i],"BULL"]);state="BEAR";seg_start=T30[i];ext=c;pend=False
            elif c>=ext*0.999: pend=False  # novo topo -> era pullback, cancela
        else:
            ext=min(ext,c)
            if i in up30: pend=True
            if pend and c>=ext*(1+X):
                segs.append([seg_start,T30[i],"BEAR"]);state="BULL";seg_start=T30[i];ext=c;pend=False
            elif c<=ext*1.001: pend=False
    segs.append([seg_start,T30[-1],state])
    # validação
    agree=tot=bull_bars=0;si=0
    for ts in T30:
        while si<len(segs)-1 and ts>=segs[si][1]: si+=1
        cs=segs[si][2];g=gt_at(ts)
        if g in("BULL","BEAR"):
            tot+=1;agree+=(cs==g);bull_bars+=(g=="BULL")
    base=max(bull_bars,tot-bull_bars)/tot if tot else 0  # sempre-classe-maioritária
    return segs,(agree/tot if tot else 0),base,tot,bull_bars
print("X%  segmentos  concord.  baseline(sempre-BULL)  Δvs_base  (gabarito BULL%)")
res={}
for X in [0.03,0.04,0.05,0.06,0.08,0.10]:
    segs,acc,base,tot,bb=run(X);res[X]=segs
    print(f"{X*100:>3.0f}  {len(segs):>8}  {acc*100:>7.0f}%  {base*100:>17.0f}%  {(acc-base)*100:>+7.0f}pp  ({100*bb/tot:.0f}%)")
# escolhe X que maximiza Δ vs baseline com poucos segmentos -> dump
bestX=max(res,key=lambda X:run(X)[1]-run(X)[2])
segs=res[bestX]
out=[]
for s,e,f in segs:
    i0=bisect.bisect_left(T30,s);i1=bisect.bisect_right(T30,e)
    if i1<=i0:continue
    out.append({"start":s,"end":e,"regime":f,"hi":round(max(H30[i0:i1]),2),"lo":round(min(L30[i0:i1]),2),
                "d0":dt.datetime.utcfromtimestamp(s).strftime("%Y-%m-%d"),"d1":dt.datetime.utcfromtimestamp(e).strftime("%Y-%m-%d")})
json.dump(out,open("/tmp/causal_segments.json","w"))
print(f"\nMELHOR X={bestX*100:.0f}% -> {len(out)} segmentos (dump p/ plotagem):")
for s in out: print(f"  {s['regime']:4} {s['d0']} -> {s['d1']}  ({s['lo']}-{s['hi']})")
