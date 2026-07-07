#!/usr/bin/env python3
"""KIT MTF FRACTAL partilhado (2026-07-07) — HTF resampleado do RAW 15M + acesso CAUSAL + avaliador
OOF+mining-null. Os agentes IMPORTAM daqui para consistencia e para nao poderem trapacear com in-sample.

USO:
  import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
  from mtf_kit import HTF, htf_closed_upto, htf_swings, ENTRIES, PHASE, oof_mining_null, score
  # HTF={'4H':[...],'1D':[...],'1W':[...]} bars {start,end,o,h,l,c}. htf_closed_upto(tf,t)=barras END<=t (FECHADAS, anti-lookahead).
  # PHASE={n:'A'/'B'/'C'/'D'} labels do Cris. oof_mining_null(X,y_out) -> {oof_hit,poison,y2025,y2026,mining_null_p,verdict}.
ANTI-LOOKAHEAD: htf_closed_upto EXCLUI a barra HTF corrente (nao fechada). NUNCA uses a barra que contem t.
"""
import bisect, sys
import datetime as dt
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S, TS, ENTRIES, score
def _resample(bucket_s):
    bk={}
    for b in S:
        k=(b["t"]//bucket_s)*bucket_s; d=bk.get(k)
        if d is None: bk[k]={"start":k,"end":k+bucket_s,"o":b["c"],"h":b["h"],"l":b["l"],"c":b["c"]}
        else: d["h"]=max(d["h"],b["h"]); d["l"]=min(d["l"],b["l"]); d["c"]=b["c"]
    return [bk[k] for k in sorted(bk)]
HTF={"4H":_resample(4*3600),"1D":_resample(24*3600),"1W":_resample(7*24*3600)}
_ENDS={tf:[x["end"] for x in HTF[tf]] for tf in HTF}
def htf_closed_upto(tf,t):
    """barras HTF cujo END<=t (FECHADAS antes do entry). Barra corrente EXCLUIDA. CAUSAL."""
    return HTF[tf][:bisect.bisect_right(_ENDS[tf],t)]
def htf_swings(bars,r=2.0):
    """zigzag causal sobre barras HTF; devolve (piv,H,L,C,ATR). piv=[(tp,idx,price)]."""
    n=len(bars)
    if n<5: return [],[],[],[],[]
    H=[b["h"] for b in bars];L=[b["l"] for b in bars];C=[b["c"] for b in bars];tr=[];A=[]
    for i in range(n):
        t=H[i]-L[i] if i==0 else max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1]));tr.append(t);A.append(sum(tr[-14:])/min(len(tr),14))
    piv=[];d=0;ehi=elo=0
    for i in range(1,n):
        a=A[i] or 1
        if H[i]>H[ehi]:ehi=i
        if L[i]<L[elo]:elo=i
        if d<=0 and H[i]-L[elo]>=r*a and elo<i:piv.append(("L",elo,L[elo]));d=1;ehi=max(range(elo,i+1),key=lambda k:H[k])
        elif d>=0 and H[ehi]-L[i]>=r*a and ehi<i:piv.append(("H",ehi,H[ehi]));d=-1;elo=min(range(ehi,i+1),key=lambda k:L[k])
    return piv,H,L,C,A
PHASE={}
for n in [1,11,12,13,14,28,29,30,44,45,71,72,73,74,75,95,96]: PHASE[n]="A"
for n in [82,61,62,63,26]: PHASE[n]="B"
for n in [21,23,25,31,55,56,57,59,60,65,67,79,83,84,85]: PHASE[n]="C"
for n in [66,68,69,86,87,89,92,93,94,49,50]: PHASE[n]="D"
_Y=np.array([dt.datetime.utcfromtimestamp(int(e["t"])).year for e in ENTRIES])
_NS=np.array([e["n"] for e in ENTRIES])
def _fit(X,y,l2=1.0,steps=300,lr=0.3):
    w=np.zeros(X.shape[1]);b=0.0;m=len(y)
    for _ in range(steps):
        p=1/(1+np.exp(-(X@w+b)));g=p-y;w-=lr*(X.T@g/m+l2*w/m);b-=lr*g.mean()
    return w,b
def _loo(Xs,y):
    P=np.zeros(len(y))
    for t in range(len(y)):
        idx=np.arange(len(y))!=t;w,b=_fit(Xs[idx],y[idx]);P[t]=1/(1+np.exp(-(Xs[t]@w+b)))
    return P
def oof_mining_null(X, y_out=None, nperm=200, seed=7):
    """X: matriz (96 x k) de features causais (ordem = ENTRIES). Avalia classificador OOF (LOO logistic,
    keep=prob>0.5) + mining-null (re-corre LOO sobre outcomes permutados). Devolve metricas honestas."""
    X=np.asarray(X,dtype=float)
    y=np.array([e["out"] for e in ENTRIES],dtype=float) if y_out is None else np.asarray(y_out,dtype=float)
    if X.shape[0]!=len(ENTRIES): return {"error":f"X tem {X.shape[0]} linhas, esperado {len(ENTRIES)}"}
    mu=X.mean(0);sd=X.std(0)+1e-9;Xs=(X-mu)/sd
    P=_loo(Xs,y);keep=P>0.5
    if keep.sum()==0: return {"oof_hit":0,"N_keep":0,"note":"keep vazio"}
    sc=score([int(n) for n,k in zip(_NS,keep) if k]); obs=sc["hit3r_kept"]
    rng=np.random.default_rng(seed);vals=[]
    for _ in range(nperm):
        yp=rng.permutation(y);Pp=_loo(Xs,yp);kp=Pp>0.5
        if kp.sum(): vals.append(yp[kp].mean())
    vals=np.array(vals);pv=float((vals>=obs).mean())
    return {"oof_hit":round(obs,3),"N_keep":sc["N_kept"],"poison_ratio":sc["poison_ratio"],
            "y2025":sc["y2025"],"y2026":sc["y2026"],"base":sc["base"],
            "mining_null_p":round(pv,3),"null_median":round(float(np.median(vals)),3),
            "verdict":"SINAL (P<0.1 & hit>base)" if (pv<0.1 and obs>0.542) else "ARTEFATO/sem-edge"}
if __name__=="__main__":
    print("HTF bars:",{tf:len(HTF[tf]) for tf in HTF},"· ENTRIES",len(ENTRIES),"· labeled",len(PHASE))
