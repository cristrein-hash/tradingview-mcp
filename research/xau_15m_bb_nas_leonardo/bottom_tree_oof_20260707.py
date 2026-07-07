#!/usr/bin/env python3
"""ÁRVORE DE DECISÃO out-of-fold por regime (2026-07-07, Cris: a diferença existe, N<=100).
A separação fundo-vs-não é multi-modal (BULL raso/profundo, BEAR) — corte linear falha. Árvore CART
(numpy, depth 3) capta sub-modos + interações. VALIDAÇÃO out-of-fold (5-fold): prob de fundo prevista
só por folds que não viram o pivô -> ranking honesto -> top-N recall. Features estruturais do cache.
SANITY_PROBE: features estruturais/trajetória; árvore multi-fatorial (interações); prob OUT-OF-FOLD
(não in-sample); ranking top-N; não snapshot; não métrica-FN."""
import json, bisect
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
piv=json.load(open(HERE/"results"/"bottom_pivots_cache_20260707.json"))
cat=json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
FT=sorted([int(n["t"]) for n in cat["notes"]["FUNDO"] if n["t"]])
FMS=json.load(open(HERE/"results"/"macro_regime_multiscale_20260707.json")); mid_by_date={x["date"][:10]:x["mid"] for x in FMS}
import datetime as dt
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
FEATS=["drop","reclaim","scale","sweep","perna_bars","upleg","retr","vclimax"]
for p in piv:
    if p.get("reclaim") is None: p["reclaim"]=99
X=np.array([[float(p[k]) for k in FEATS] for p in piv])
y=np.array([p["fund"] for p in piv]); reg=np.array([p["reg"] for p in piv]); pt=np.array([p["pt"] for p in piv])
def gini(yv):
    if len(yv)==0: return 0
    p1=yv.mean(); return 1-p1*p1-(1-p1)*(1-p1)
def best_split(Xs,ys):
    n,m=Xs.shape; best=(None,None,1e9)
    for j in range(m):
        vals=np.unique(Xs[:,j])
        if len(vals)<2: continue
        for t in vals[:-1]:
            L=Xs[:,j]<=t; R=~L
            if L.sum()<8 or R.sum()<8: continue
            g=(L.sum()*gini(ys[L])+R.sum()*gini(ys[R]))/n
            if g<best[2]: best=(j,t,g)
    return best
class Node: pass
def build(Xs,ys,depth):
    nd=Node(); nd.leaf=True; nd.prob=ys.mean() if len(ys) else 0
    if depth==0 or len(ys)<16 or ys.sum()==0 or ys.sum()==len(ys): return nd
    j,t,g=best_split(Xs,ys)
    if j is None: return nd
    L=Xs[:,j]<=t
    nd.leaf=False; nd.j=j; nd.t=t; nd.L=build(Xs[L],ys[L],depth-1); nd.R=build(Xs[~L],ys[~L],depth-1)
    return nd
def pred(nd,x):
    while not nd.leaf: nd=nd.L if x[nd.j]<=nd.t else nd.R
    return nd.prob
# OOF por regime (5-fold dentro de cada regime)
prob=np.zeros(len(piv)); rng=np.random.default_rng(7)
for r in ("BULL","RANGE","BEAR"):
    idx=np.where(reg==r)[0]
    if len(idx)<20 or y[idx].sum()<4:
        # regime pequeno: prob = taxa base
        prob[idx]=y[idx].mean() if len(idx) else 0; continue
    perm=rng.permutation(idx); folds=np.array_split(perm,5)
    for fi in range(5):
        te=folds[fi]; tr=np.concatenate([folds[k] for k in range(5) if k!=fi])
        nd=build(X[tr],y[tr],3)
        for i in te: prob[i]=pred(nd,X[i])
order=np.argsort(-prob)
def recall_topN(K):
    sel=order[:K]; T=sorted(pt[i] for i in sel); g=0
    for ft in FT:
        j=bisect.bisect_left(T,ft-14*3600)
        if j<len(T) and T[j]<=ft+14*3600: g+=1
    return g, sel
print("=== ÁRVORE OOF por regime — recall top-N ===")
for K in (60,80,100,120,150):
    g,_=recall_topN(K); print(f"  top-{K}: recall {g}/42 · fundos-pivô {int(y[order[:K]].sum())}")
g,sel=recall_topN(100)
T=sorted(pt[i] for i in sel)
missed=[ft for ft in FT if not (bisect.bisect_left(T,ft-14*3600)<len(T) and T[bisect.bisect_left(T,ft-14*3600)]<=ft+14*3600)]
print(f"\nTOP-100 recall {g}/42 · MISSED: "+", ".join(f"{ds(m)}[{mid_by_date.get(ds(m),'?')}]" for m in missed))
json.dump({"top100_recall":g},open(HERE/"results"/"bottom_tree_oof_20260707.json","w"))
print("OK")
