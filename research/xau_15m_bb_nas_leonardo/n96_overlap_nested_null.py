#!/usr/bin/env python3
"""N96 · NESTED mining-null (2026-07-08) — fecha o buraco do winner's-curse do overlap_context.
O teste anterior selecionou top6 features na amostra e so depois LOO+null com top6 FIXO (a busca de
selecao nao foi paga). Aqui: em CADA permutacao, re-seleciona top-k features por AUC sobre y_permutado,
depois LOO — a busca de features entra no null. Se oof_obs sobrevive, o sinal intra-contexto e real."""
import csv, sys
import numpy as np, statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE
from agent_ctx_kit import score
rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
BYN={int(r["n"]):r for r in rows}
def g(r,k):
    try: return float(r.get(k))
    except: return None
FEATS=[c for c in rows[0] if c not in ("n","out","fam")]
def D_subs(r): return sum([ (g(r,"4H_ema_trend") or 0)<0,(g(r,"4H_px_vs_ema") or 9)<0,(g(r,"1D_px_vs_ema") or 9)<0,(g(r,"mtf_bull_align") or 9)<=1,(g(r,"4H_dem_below") or 9)<1.5 ])
def C_subs(r): return sum([ (g(r,"4H_rsi") or 0)>58,(g(r,"4H_px_vs_ema") or -9)>2,(g(r,"4H_dem_below") or 0)>3,(g(r,"1D_ema_trend") or 0)>3,(g(r,"1H_rsi_slope") or 9)<-5 ])
COND=[int(r["n"]) for r in rows if D_subs(r)>=3 or C_subs(r)>=3]
NS=COND; y0=np.array([1 if BYN[n]["out"]=="1" else 0 for n in NS],dtype=float)
# matriz completa de features usaveis (>=8 nao-nulos em ambas as classes no subset)
USE=[]
for k in FEATS:
    v=[g(BYN[n],k) for n in NS if g(BYN[n],k) is not None]
    if len(v)>=len(NS)-5: USE.append(k)
M=np.array([[ (g(BYN[n],k) if g(BYN[n],k) is not None else np.nan) for k in USE] for n in NS],dtype=float)
col_med=np.nanmedian(M,0); inds=np.where(np.isnan(M)); M[inds]=np.take(col_med,inds[1])
KTOP=6
def auc_col(col,y):
    a=col[y==1]; b=col[y==0]
    if len(a)==0 or len(b)==0: return 0.5
    # rank-AUC
    order=np.argsort(col); ranks=np.empty(len(col)); ranks[order]=np.arange(1,len(col)+1)
    return (ranks[y==1].sum()-len(a)*(len(a)+1)/2)/(len(a)*len(b))
def fit(Xt,yt,l2=1.0,s=250,lr=0.3):
    w=np.zeros(Xt.shape[1]); b=0.0; m=len(yt)
    for _ in range(s):
        p=1/(1+np.exp(-(Xt@w+b))); gg=p-yt; w-=lr*(Xt.T@gg/m+l2*w/m); b-=lr*gg.mean()
    return w,b
def pipeline_oof(y):
    """re-seleciona top-K por |AUC-0.5| sobre y, standardiza, LOO logistic, devolve hit-3R do keep."""
    seps=np.array([abs(auc_col(M[:,j],y)-0.5) for j in range(M.shape[1])])
    top=np.argsort(seps)[::-1][:KTOP]
    Xs=(M[:,top]-M[:,top].mean(0))/(M[:,top].std(0)+1e-9)
    P=np.zeros(len(y))
    for t in range(len(y)):
        idx=np.arange(len(y))!=t; w,b=fit(Xs[idx],y[idx]); P[t]=1/(1+np.exp(-(Xs[t]@w+b)))
    keep=P>0.5
    kept=[int(NS[i]) for i in range(len(NS)) if keep[i]]
    if not kept: return None,0,[]
    return score(kept)["hit3r_kept"], keep.sum(), kept
obs,nk,kept=pipeline_oof(y0)
base=y0.mean()
rng=np.random.default_rng(13); vals=[]
for _ in range(300):
    yp=rng.permutation(y0); o,k,_=pipeline_oof(yp)
    if o is not None: vals.append(o)
vals=np.array(vals); pv=float((vals>=obs).mean())
print(f"NESTED mining-null (selecao de features DENTRO do null, K={KTOP}, subset n={len(NS)}):")
print(f"  base_condicionada={base:.3f}  oof_hit_obs={obs:.3f}  N_keep={nk}")
print(f"  null: mediana={np.median(vals):.3f}  q95={np.quantile(vals,0.95):.3f}  P(null>=obs)={pv:.3f}")
verdict="SOBREVIVE_NESTED (sinal intra-contexto real)" if (pv<0.1 and obs>base) else "NAO_SOBREVIVE (winner's-curse — selecao explicava o ganho)"
print(f"  --> {verdict}")
print(f"  kept(n={nk}): {sorted(kept)}")
