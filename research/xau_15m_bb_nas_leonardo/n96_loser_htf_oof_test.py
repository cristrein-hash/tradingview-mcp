#!/usr/bin/env python3
"""OOF + mining-null das features HTF RAW-native (2026-07-07) — teste honesto do filtro (a prova de DA).
Lê results/n96_loser_raw_mtf_feature_audit.csv (RAW-native 15M+30M+1H+4H+1D). Classificador logístico
LEAVE-ONE-OUT (out-of-fold) sobre features HTF (4H/1D/1H RSI+trend, dem/sup HTF) + mining-null.
Determinista, read-only. Resultado: hit-3R OOF vs base 0.542 + P(null>=obs). NAO chama validacao."""
import json, csv, sys
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score
HERE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
rows=list(csv.DictReader(open(HERE+"/results/n96_loser_raw_mtf_feature_audit.csv")))
byn={int(r["n"]):r for r in rows}
FEATS=["4H_rsi","1D_rsi","4H_trend","1D_trend","1H_rsi","1H_trend","30M_trend","4H_dem_below","1D_dem_below","4H_sup_above","1D_sup_above"]
ns=[e["n"] for e in ENTRIES]; y=np.array([e["out"] for e in ENTRIES],dtype=float)
def val(n,k):
    try: return float(byn[n].get(k))
    except Exception: return 99.0
X=np.array([[val(n,k) for k in FEATS] for n in ns],dtype=float)
mu=X.mean(0); sd=X.std(0)+1e-9; Xs=(X-mu)/sd
def fit(Xt,yt,l2=1.0,st=300,lr=0.3):
    w=np.zeros(Xt.shape[1]); b=0.0; m=len(yt)
    for _ in range(st):
        p=1/(1+np.exp(-(Xt@w+b))); g=p-yt; w-=lr*(Xt.T@g/m+l2*w/m); b-=lr*g.mean()
    return w,b
def loo(Xs,y):
    P=np.zeros(len(y))
    for t in range(len(y)):
        idx=np.arange(len(y))!=t; w,b=fit(Xs[idx],y[idx]); P[t]=1/(1+np.exp(-(Xs[t]@w+b)))
    return P
P=loo(Xs,y); keep=P>0.5
sc=score([int(n) for n,k in zip(ns,keep) if k]); obs=sc["hit3r_kept"]
rng=np.random.default_rng(7); vals=[]
for _ in range(200):
    yp=rng.permutation(y); Pp=loo(Xs,yp); kp=Pp>0.5
    if kp.sum(): vals.append(yp[kp].mean())
vals=np.array(vals); pv=float((vals>=obs).mean())
res={"oof_hit":round(obs,3),"base":0.542,"score":sc,"mining_null_p":round(pv,3),"null_median":round(float(np.median(vals)),3),
     "verdict":"SINAL" if (pv<0.1 and obs>0.542) else "NO_EDGE_OOF"}
print(json.dumps(res,indent=1))
json.dump(res, open(HERE+"/results/n96_loser_htf_oof_test.json","w"), indent=1)
