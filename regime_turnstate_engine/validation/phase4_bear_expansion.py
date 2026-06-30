#!/usr/bin/env python3
"""RTSE Fase 4 — hipótese do Cris (BULL->BEAR no 30M): no fim de perna bull, 5 velas com >=4 bear e 2-3 delas
ESTOURANDO a volatilidade da perna bull anterior => sinaliza virada RÁPIDO. Testa DETECTÁVEL + CAUSAL no RAW.
Sinal S(i) causal (só barras <=i). Mede: RECALL nos topos reais (fire em [topo .. topo+K]), LATÊNCIA (barras pós-topo),
FP/ano (fires longe de topo) e NULL base-rate (Monte Carlo: fires aleatórios de mesma densidade pegam tanto recall?).
Topos = bordas macro-BEAR-start + macro-BULL-end + pullback bear-em-bull-start. Ancora na máxima real ±W. Determinístico."""
import json,csv,math,statistics as st,random,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth";RX=ROOT/"research/xau_15m_bb_nas_leonardo"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
def load15():
    S={}
    for f in sorted((RX/"primitives").glob("*.primitives.json")):
        for b in json.loads(f.read_text())["series"]: S[b["t"]]={"t":b["t"],"o":b["o"] if "o" in b else b["c"],"h":b["h"],"l":b["l"],"c":b["c"]}
    return [S[t] for t in sorted(S)]
# topos (BULL->BEAR): macro BEAR start, macro BULL end, pullback bear-em-bull start
TOPS=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO" and r["family"]=="BEAR": TOPS.append(int(r["start"]))
    if r["role"]=="MACRO" and r["family"]=="BULL": TOPS.append(int(r["end"]))
    if r["role"]=="PULLBACK" and r["family"]=="BEAR" and r["parent_fam"]=="BULL": TOPS.append(int(r["start"]))
TOPS=sorted(set(TOPS))
def rng(b): return b["h"]-b["l"]
def signal(B,i):
    """S(i) causal: fim de perna bull + 5 velas >=4 bear + >=2 estourando vol da perna bull + caiu líquido."""
    if i<20 or i>=len(B): return False
    C=[b["c"] for b in B]
    leg=B[i-14:i-4]                      # perna anterior às 5
    if C[i-5]<=C[i-14]: return False     # exige perna BULL antes (subiu)
    legvol=st.mean([rng(b) for b in leg]) or 1e-9
    w=B[i-4:i+1]                          # 5 velas
    nbear=sum(1 for b in w if b["c"]<b["o"])
    wide=sum(1 for b in w if rng(b)>1.5*legvol)
    return (nbear>=4 and wide>=2 and C[i]<C[i-5])
def extreme_hi(B,j,W):
    return max(range(max(20,j-W),min(len(B)-1,j+W)),key=lambda k:B[k]["h"])
def run(name,B,K,W):
    T=[b["t"] for b in B];n=len(B)
    cov0,cov1=T[0],T[-1]
    tops=[extreme_hi(B,bisect.bisect_right(T,t)-1,W) for t in TOPS if cov0<=t<=cov1 and 20<bisect.bisect_right(T,t)-1<n-1]
    tops=sorted(set(tops))
    fires=[i for i in range(20,n) if signal(B,i)]
    fireset=set(fires)
    # recall + latência
    lats=[];hit=0
    for e in tops:
        f=[i for i in range(e,min(n,e+K+1)) if i in fireset]
        if f: hit+=1;lats.append(f[0]-e)
    recall=hit/len(tops) if tops else 0
    # FP: fires que NÃO estão em [topo..topo+K] de nenhum topo
    topwin=set()
    for e in tops:
        for k in range(0,K+1): topwin.add(e+k)
    fp=sum(1 for i in fires if i not in topwin)
    yrs=(cov1-cov0)/(365.25*86400);fpy=fp/yrs if yrs else 0
    # NULL base-rate: fires aleatórios de mesma quantidade -> recall esperado
    random.seed(7);M=len(fires);pool=list(range(20,n));dd=[]
    for _ in range(1000):
        rf=set(random.sample(pool,M));h=sum(1 for e in tops if any((e+k) in rf for k in range(0,K+1)))
        dd.append(h/len(tops) if tops else 0)
    p=sum(1 for x in dd if x>=recall)/len(dd)
    print(f"\n== {name} (n_bars {n}, {dt.datetime.utcfromtimestamp(cov0).date()}..{dt.datetime.utcfromtimestamp(cov1).date()}, K={K}b) ==")
    print(f"  topos na janela: {len(tops)} | fires totais: {len(fires)} ({100*len(fires)/n:.1f}% das barras) | FP/ano: {fpy:.0f}")
    print(f"  RECALL (fire em [topo..+{K}b]): {recall:.2f} ({hit}/{len(tops)}) | latência mediana: {st.median(lats) if lats else float('nan')}b | null base-rate recall p={p:.3f}{' *' if p<0.05 else ''}")
    print(f"  null recall médio (aleatório mesma densidade): {st.mean(dd):.2f}")
B30=load(GT/"raw_30m_ohlc.jsonl");B1=load(REV/"raw_1h_ohlc.jsonl");B4=load(REV/"raw_4h_ohlc.jsonl");B15=load15()
run("30M (hipótese do Cris)",B30,8,12)
run("15M",B15,16,24)
run("1H",B1,4,6)
run("4H (cross-check maior-n)",B4,4,8)
