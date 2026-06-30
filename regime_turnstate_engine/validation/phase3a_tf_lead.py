#!/usr/bin/env python3
"""RTSE FASE 3a — sonda EIXO VELOCIDADE: TF baixo antecipa o alto?
Estado de regime causal (sinal da inclinação de EMA, mesmo lookback de CALENDÁRIO ~200h em cada TF) em 15M/30M/1H/4H.
Mede latência de detecção da virada vs bordas MACRO do Cris + FP/ano por TF. Espera-se: TF baixo = menor latência,
maior FP -> o 'lead' em horas é o ganho de velocidade disponível. Determinístico, causal, só leitura."""
import json,csv,statistics as st,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation"; GT=ROOT/"regime_turnstate_engine/ground_truth"
PR=ROOT/"research/xau_15m_bb_nas_leonardo/primitives"
def load15m():
    bars={}
    for f in sorted(PR.glob("*.primitives.json")):
        for b in json.loads(f.read_text())["series"]:
            bars[b["t"]]={"t":b["t"],"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"]}
    return [bars[t] for t in sorted(bars)]
def loadj(p):
    b=[json.loads(l) for l in p.read_text().splitlines()]; b.sort(key=lambda x:x["t"]); return b
SER={"15M":load15m(),"30M":loadj(GT/"raw_30m_ohlc.jsonl"),"1H":loadj(REV/"raw_1h_ohlc.jsonl"),"4H":loadj(REV/"raw_4h_ohlc.jsonl")}
TFH={"15M":0.25,"30M":0.5,"1H":1.0,"4H":4.0}
def ema(c,n):
    a=2/(n+1);o=[c[0]]
    for x in c[1:]:o.append(a*x+(1-a)*o[-1])
    return o
def flips(ser,tfh,Nb=20):
    # swing-break NATIVO: rompe máx/mín das últimas Nb barras DO PRÓPRIO TF (fino no TF baixo). causal.
    C=[b["c"] for b in ser]
    H=[b.get("h",b["c"]) for b in ser];L=[b.get("l",b["c"]) for b in ser];T=[b["t"] for b in ser]
    ev=[];prev=None;cur=None
    for i in range(len(C)):
        if i>=Nb:
            if C[i]>max(H[i-Nb:i]):cur="UP"
            elif C[i]<min(L[i-Nb:i]):cur="DOWN"
        if cur and cur!=prev: ev.append((T[i],cur));prev=cur
        elif cur: prev=cur
    return ev
# bordas MACRO Cris (UP/DOWN), restritas ao período com 15M (2024-05+)
W0=SER["15M"][0]["t"]
edges=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"] in("BULL","BEAR"):
        ts=int(r["start"])
        if ts>=W0-10*86400: edges.append((ts,"UP" if r["family"]=="BULL" else "DOWN"))
edges.sort()
YRS=(SER["15M"][-1]["t"]-W0)/(365.25*86400)
def score(fr,W=45*86400,TOL=5*86400):
    lat=[];me=0;byd={"UP":[t for t,d in edges if d=="UP"],"DOWN":[t for t,d in edges if d=="DOWN"]}
    for et,ed in edges:
        c=[ft for ft,fd in fr if fd==ed and et-TOL<=ft<=et+W]
        if c:me+=1;lat.append(max(0,(min(c)-et)/3600))  # latência em HORAS
    tp=sum(1 for ft,fd in fr if any(ft-W<=et<=ft+TOL for et in byd[fd]))
    return me/len(edges),(st.median(lat) if lat else None),len(fr),(len(fr)-tp)/YRS
print(f"FASE 3a — eixo VELOCIDADE | bordas MACRO (2024+): {len(edges)} | janela {YRS:.1f} anos")
print(f"{'TF':5} | recall | lat_med(h) | flips | FP/ano")
res={}
for tf,ser in SER.items():
    fr=flips(ser,TFH[tf]);rc,lm,nf,fpy=score(fr);res[tf]=(rc,lm,nf,fpy)
    print(f"{tf:5} | {rc:.2f}   | {('%.0f'%lm) if lm is not None else '—':>6}   | {nf:>4}  | {fpy:.0f}")
if res["15M"][1] is not None and res["4H"][1] is not None:
    print(f"\nLEAD 15M vs 4H: {res['4H'][1]-res['15M'][1]:.0f}h ({(res['4H'][1]-res['15M'][1])/24:.1f}d) mais cedo no 15M")
print("LEITURA: TF baixo deve dar menor latência + maior FP/ano -> confirma que dá p/ antecipar (custo=FP, cortado depois por aceitação/dip-vs-flip).")
