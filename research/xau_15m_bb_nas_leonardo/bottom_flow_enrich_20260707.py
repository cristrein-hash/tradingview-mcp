#!/usr/bin/env python3
"""ENRIQUECER pivôs com FLUXO/ABSORÇÃO e re-testar árvore OOF (2026-07-07, Cris: a diferença existe).
Estrutura sozinha não separou os fundos BULL rasos. Adicionar as features que o Cris usa: fluxo de
bubbles (sell-climax, buy-accum, absorção), RSI-profundo, NAS. Todas causais (bubbles known_at<=pt).
Re-rodar árvore CART OOF por regime com feature set EXPANDIDO. Meta N<=100 recall alto.
SANITY_PROBE: features estruturais+fluxo (trajetória), causais known_at; árvore OOF multi-fatorial;
não snapshot; não métrica-FN."""
import json, bisect, glob
import numpy as np
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
piv=json.load(open(HERE/"results"/"bottom_pivots_cache_20260707.json"))
series={}; NAS=[]
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
    NAS+=[e for e in d["nas_events"] if e.get("t") and e.get("dir")]
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]; OP=[b.get("o",b["c"]) for b in S]; VOL=[float(b.get("v") or 0) for b in S]; RSI=[b.get("rsi") for b in S]; ATR=[b.get("atr") or 5.0 for b in S]
NAS.sort(key=lambda e:e["t"]); NAST=[e["t"] for e in NAS]
BUB=[]
for p in glob.glob(str(HERE/"bubbles"/"*.bubbles.jsonl")):
    for l in open(p):
        if l.strip(): BUB.append(json.loads(l))
BUB.sort(key=lambda x:(x.get("known_at") or x["t"])); BUBK=[(x.get("known_at") or x["t"]) for x in BUB]
W={"S":1,"M":2,"L":3}
def bubs(cj,wlo,whi):
    hi=bisect.bisect_right(BUBK,cj); return [BUB[i] for i in range(hi) if cj-whi*900<=BUB[i]["t"]<=cj-wlo*900]
def flow(li):
    t=TS[li]; a=ATR[li] or 5.0
    r8=bubs(t,0,8); r4=bubs(t,0,4)
    sell_climax=sum(1 for x in r4 if x["side"]=="SELL" and x["size"] in ("M","L"))
    buy_recent=sum(W[x["size"]] for x in r4 if x["side"]=="BUY")
    # absorção causal: SELL M/L nas 8 barras cujas 4 barras seguintes (todas <=li) não fizeram novo low
    absb=0
    for x in r8:
        if x["side"]=="SELL" and x["size"] in ("M","L"):
            bt=bisect.bisect_right(TS,x["t"])-1
            if bt+4<=li and min(LO[bt+1:bt+5])>=x["l"]-0.2*a: absb+=W[x["size"]]
    rsi_min8=min([RSI[k] for k in range(max(0,li-8),li+1) if RSI[k] is not None] or [50])
    v48=VOL[max(0,li-48):li]; vdry=(sum(VOL[max(0,li-8):li])/8)/max(1e-9,(sum(v48)/max(1,len(v48)))) if v48 else 1
    j=bisect.bisect_right(NAST,t)-1; nas_long=int(j>=0 and NAS[j]["dir"]=="LONG" and (t-NAS[j]["t"])//900<=8)
    return {"sell_climax":sell_climax,"buy_recent":buy_recent,"absorb":absb,"rsi_min8":rsi_min8,"vdry":round(vdry,2),"nas_long":nas_long}
for p in piv:
    p.update(flow(p["li"]))
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
FT=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json")); mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
FEATS=["drop","reclaim","scale","sweep","perna_bars","upleg","retr","vclimax","sell_climax","buy_recent","absorb","rsi_min8","vdry","nas_long"]
for p in piv:
    if p.get("reclaim") is None: p["reclaim"]=99
X=np.array([[float(p[k]) for k in FEATS] for p in piv]); y=np.array([p["fund"] for p in piv]); reg=np.array([p["reg"] for p in piv]); pt=np.array([p["pt"] for p in piv])
# MWU das novas features fundo-vs-não
import math
def mwu(a,b):
    na,nb=len(a),len(b)
    if na<5 or nb<5: return 1.0
    allv=sorted([(v,0) for v in a]+[(v,1) for v in b]); rk=[0]*len(allv); i=0
    while i<len(allv):
        j=i
        while j+1<len(allv) and allv[j+1][0]==allv[i][0]: j+=1
        for k in range(i,j+1): rk[k]=(i+j)/2+1
        i=j+1
    Ra=sum(rk[k] for k in range(len(allv)) if allv[k][1]==0); Ua=Ra-na*(na+1)/2; U=min(Ua,na*nb-Ua)
    mu=na*nb/2; sd=math.sqrt(na*nb*(na+nb+1)/12)
    return math.erfc(abs((U-mu)/sd)/math.sqrt(2)) if sd else 1.0
Fp=[p for p in piv if p["fund"]]; NFp=[p for p in piv if not p["fund"]]
import statistics as st
print("=== FLUXO fundo-vs-não (MWU) ===")
for k in ("sell_climax","buy_recent","absorb","rsi_min8","vdry","nas_long"):
    print(f"  {k:<12} fund {st.median([p[k] for p in Fp]):>6.2f} · não {st.median([p[k] for p in NFp]):>6.2f} · p={mwu([p[k] for p in Fp],[p[k] for p in NFp]):.4f}")
# árvore OOF
def gini(yv):
    if len(yv)==0: return 0
    p1=yv.mean(); return 1-p1*p1-(1-p1)*(1-p1)
def best_split(Xs,ys):
    n,m=Xs.shape; best=(None,None,1e9)
    for j in range(m):
        vals=np.unique(Xs[:,j])
        for t in vals[:-1]:
            L=Xs[:,j]<=t
            if L.sum()<8 or (~L).sum()<8: continue
            g=(L.sum()*gini(ys[L])+(~L).sum()*gini(ys[~L]))/n
            if g<best[2]: best=(j,t,g)
    return best
class Nd: pass
def build(Xs,ys,d):
    nd=Nd(); nd.leaf=True; nd.prob=ys.mean() if len(ys) else 0
    if d==0 or len(ys)<16 or ys.sum() in (0,len(ys)): return nd
    j,t,g=best_split(Xs,ys)
    if j is None: return nd
    L=Xs[:,j]<=t; nd.leaf=False; nd.j=j; nd.t=t; nd.L=build(Xs[L],ys[L],d-1); nd.R=build(Xs[~L],ys[~L],d-1); return nd
def pred(nd,x):
    while not nd.leaf: nd=nd.L if x[nd.j]<=nd.t else nd.R
    return nd.prob
prob=np.zeros(len(piv)); rng=np.random.default_rng(7)
for r in ("BULL","RANGE","BEAR"):
    idx=np.where(reg==r)[0]
    if len(idx)<20 or y[idx].sum()<4: prob[idx]=y[idx].mean() if len(idx) else 0; continue
    perm=rng.permutation(idx); folds=np.array_split(perm,5)
    for fi in range(5):
        te=folds[fi]; tr=np.concatenate([folds[k] for k in range(5) if k!=fi])
        nd=build(X[tr],y[tr],4)
        for i in te: prob[i]=pred(nd,X[i])
order=np.argsort(-prob)
def rc(K):
    sel=order[:K]; T=sorted(pt[i] for i in sel); g=0
    for ft in FT:
        j=bisect.bisect_left(T,ft-14*3600)
        if j<len(T) and T[j]<=ft+14*3600: g+=1
    return g
print("\n=== ÁRVORE OOF (estrutura+FLUXO) — recall top-N ===")
for K in (60,80,100,120,150): print(f"  top-{K}: recall {rc(K)}/42 · fundos-pivô {int(y[order[:K]].sum())}")
g=rc(100); sel=order[:100]; T=sorted(pt[i] for i in sel)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nTOP-100 recall {g}/42 · MISSED: "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
json.dump([{k:p[k] for k in ["li","pt","fund","reg"]+FEATS} for p in piv], open(HERE/"results"/"bottom_pivots_flow_cache_20260707.json","w"))
print("OK")
