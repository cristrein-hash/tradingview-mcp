#!/usr/bin/env python3
"""RTSE Fase 8 — MÁQUINA DE ESTADO causal sobre o detector único. Vira BEAR no 1º topo (estando BULL),
BULL no 1º fundo (estando BEAR), SEGURA entre viradas (o hold filtra o ruído dos 73 fundos soltos).
VALIDA: concordância barra-a-barra vs gabarito do Cris (BULL/BEAR; RANGE reportado à parte) + nº de segmentos (whipsaw).
Testa raw vs histerese (min-hold). Emite segmentos p/ plotagem. Causal (eventos já têm latência embutida)."""
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
T30=[b["t"] for b in B30];C30=[b["c"] for b in B30];H30=[b["h"] for b in B30];L30=[b["l"] for b in B30]
# eventos
up30=sorted(cusum(C30,1))
R4=rsi([b["c"] for b in B4]);H4=[b["h"] for b in B4]
cd4=cusum([b["c"] for b in B4],-1)
expdiv4=[i for i in bear_exp(B4) if H4[max(range(i-8,i-3),key=lambda k:H4[k])]>H4[max(range(i-22,i-9),key=lambda k:H4[k])] and R4[max(range(i-8,i-3),key=lambda k:H4[k])]<R4[max(range(i-22,i-9),key=lambda k:H4[k])]]
topf=sorted(set(expdiv4)|set(cd4))
# stream de eventos no relógio 30M (mapeia topos 4H -> índice 30M)
def to30(ts): 
    j=bisect.bisect_right(T30,ts)-1;return j if j>=0 else None
ev=[]
for i in up30: ev.append((T30[i],"BOT"))
for i in topf:
    j=to30(B4[i]["t"])
    if j is not None: ev.append((T30[j],"TOP"))
ev=sorted(ev)
# gabarito por barra
boxes=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO": boxes.append((int(r["start"]),int(r["end"]),r["family"]))
def gt_at(ts):
    for s,e,f in boxes:
        if s<=ts<=e: return f
    return None
def run_fsm(hold_days):
    H=hold_days*86400
    # init: estado antes do 1º evento = oposto do 1º evento
    first=next((k for _,k in ev),"TOP");state="BULL" if first=="TOP" else "BEAR"
    segs=[];seg_start=T30[0];last_flip=-10**18
    for ts,k in ev:
        if k=="TOP" and state=="BULL" and ts-last_flip>=H:
            segs.append([seg_start,ts,"BULL"]);seg_start=ts;state="BEAR";last_flip=ts
        elif k=="BOT" and state=="BEAR" and ts-last_flip>=H:
            segs.append([seg_start,ts,"BEAR"]);seg_start=ts;state="BULL";last_flip=ts
    segs.append([seg_start,T30[-1],state])
    # concordância barra-a-barra
    agree=tot=rng_bull=rng_bear=rng_tot=0
    si=0
    for ts in T30:
        while si<len(segs)-1 and ts>=segs[si][1]: si+=1
        cs=segs[si][2];g=gt_at(ts)
        if g in("BULL","BEAR"):
            tot+=1; agree+= (cs==g)
        elif g=="RANGE":
            rng_tot+=1; rng_bull+=(cs=="BULL"); rng_bear+=(cs=="BEAR")
    return segs,(agree/tot if tot else 0),tot,(rng_bull,rng_bear,rng_tot)
print(f"eventos: {sum(1 for _,k in ev if k=='BOT')} fundos + {sum(1 for _,k in ev if k=='TOP')} topos (relógio 30M de {dt.datetime.utcfromtimestamp(T30[0]).date()})")
best=None
for hd in [0,3,5,8,12]:
    segs,acc,tot,(rb,rr,rt)=run_fsm(hd)
    nseg=len(segs);flips=nseg-1
    print(f"\nhold={hd}d: segmentos={nseg} (flips={flips}) | concordância BULL/BEAR={acc*100:.0f}% (n={tot} barras) | em RANGE: {100*rb/rt:.0f}% BULL/{100*rr/rt:.0f}% BEAR")
    if hd==5: best=segs
# dump segmentos do hold escolhido (5d) p/ plotagem, com hi/lo do trecho
out=[]
for s,e,f in best:
    i0=bisect.bisect_left(T30,s);i1=bisect.bisect_right(T30,e)
    if i1<=i0: continue
    hi=max(H30[i0:i1]);lo=min(L30[i0:i1])
    out.append({"start":s,"end":e,"regime":f,"hi":round(hi,2),"lo":round(lo,2),
                "d0":dt.datetime.utcfromtimestamp(s).strftime("%Y-%m-%d"),"d1":dt.datetime.utcfromtimestamp(e).strftime("%Y-%m-%d")})
json.dump(out,open("/tmp/causal_segments.json","w"))
print(f"\n--- SEGMENTOS CAUSAIS (hold=5d) p/ plotagem: {len(out)} ---")
for s in out: print(f"  {s['regime']:4} {s['d0']} -> {s['d1']}  ({s['lo']}-{s['hi']})")
