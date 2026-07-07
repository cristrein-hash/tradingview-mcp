#!/usr/bin/env python3
"""CLASSIFICADOR DE FASE VALIDADO LEAVE-ONE-OUT + MINING-NULL (2026-07-07) — a prova de DA.
Metodo anti-mineracao: NAO minerar threshold. Feature-set PRE-ESPECIFICADO pela leitura estrutural do
Cris (ms_state, eqh_touches, pos96, rsi_lo, reclaim_lag, flush_depth, sweep, choch_up_fresh). Regressao
logistica LEAVE-ONE-OUT (treina em 95, preve o held-out) -> prob OOF por entry. KEEP = prob>0.5.
MINING-NULL: permuta outcomes, RE-CORRE toda a pipeline LOO, ve se a hit-rate OOF-keep e bativel por acaso.
Se P(null>=obs)>=0.1 -> artefato. Causal (features barras<=j). Script salvo, reproduzivel."""
import json, glob, bisect, sys
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto
def ms_state(j):
    sw=causal_swings_upto(j,6); _ll=None; stt=0
    for tp,i,pr,ci in sw:
        if tp=="L":
            if _ll is not None and pr<_ll and stt>=0: stt=-1
            if _ll is not None and pr>_ll and stt<0: stt=1
            _ll=pr
    return stt
def choch_up_fresh(j,a):
    sw=[x for x in causal_swings_upto(j,6) if x[3]>=j-48]
    _ll=None; stt=0; fresh=0
    for tp,i,pr,ci in causal_swings_upto(j,6):
        if tp=="L":
            if _ll is not None and pr<_ll: stt=-1
            if _ll is not None and pr>_ll and stt<0 and ci>=j-48: fresh=1
            _ll=pr
    return fresh
def feats(e):
    j=e["j"]; i=e["i"]; a=ATR[j] or 5
    top=max(HI[max(0,j-96):j+1]); bot=min(LO[max(0,j-96):j+1]); rng=(top-bot) or 1
    eqh=0; k=max(0,j-96)
    while k<=j:
        if HI[k]>=top-0.4*a: eqh+=1; k+=6
        else: k+=1
    prior=LO[max(0,i-96):max(1,i-32)]; sweep=(min(prior)-LO[i])/a if prior else 0
    flush=(e["leg_top"]-LO[i])/a
    return [ms_state(j), eqh, (CL[j]-bot)/rng, RSI[i] or 50, e["reclaim_lag"], flush, sweep, choch_up_fresh(j,a)]
X=np.array([feats(e) for e in ENTRIES],dtype=float); y=np.array([e["out"] for e in ENTRIES],dtype=float)
yrs=np.array([1 if __import__("datetime").datetime.utcfromtimestamp(int(e["t"])).year==2025 else 2 for e in ENTRIES])
ns=np.array([e["n"] for e in ENTRIES])
mu=X.mean(0); sd=X.std(0)+1e-9; Xs=(X-mu)/sd
def fit(Xtr,ytr,l2=1.0,steps=300,lr=0.3):
    w=np.zeros(Xtr.shape[1]); b=0.0; m=len(ytr)
    for _ in range(steps):
        z=Xtr@w+b; p=1/(1+np.exp(-z)); g=p-ytr
        w-=lr*(Xtr.T@g/m + l2*w/m); b-=lr*g.mean()
    return w,b
def loo_probs(Xs,y):
    P=np.zeros(len(y))
    for t in range(len(y)):
        idx=np.arange(len(y))!=t
        w,b=fit(Xs[idx],y[idx]); P[t]=1/(1+np.exp(-(Xs[t]@w+b)))
    return P
P=loo_probs(Xs,y)
keep=P>0.5
def rate(mask):
    s=y[mask]; return (int(s.sum()),int(len(s)),float(s.mean()) if len(s) else 0)
kw,kn,kr=rate(keep)
keep_ns=[int(n) for n,k in zip(ns,keep) if k]
sc=score(keep_ns)
print("=== CLASSIFICADOR LOO (out-of-fold, prob>0.5) ===")
print(json.dumps(sc,indent=1))
w25=keep&(yrs==1); w26=keep&(yrs==2)
print(f"OOF: N_keep {kn} hit-3R {kr:.3f} | 2025 {rate(w25)[0]}/{rate(w25)[1]} · 2026 {rate(w26)[0]}/{rate(w26)[1]}")
# importancia media dos pesos (fit full)
wf,bf=fit(Xs,y); names=["ms_state","eqh","pos96","rsi_lo","reclaim_lag","flush","sweep","choch_up_fresh"]
print("pesos (full-fit, standardizado):", {n:round(float(wv),2) for n,wv in zip(names,wf)})
# MINING-NULL: permuta y, re-corre LOO, hit-rate OOF-keep
rng=np.random.default_rng(42); NP=200; obs=kr; cnt=0; nkeeps=[]
for _ in range(NP):
    yp=rng.permutation(y); Pp=loo_probs(Xs,yp); kp=Pp>0.5
    if kp.sum()==0: continue
    hr=yp[kp].mean()  # hit-rate no keep sob permutacao? NAO: keep define-se por yp, entao mede associacao
    # correto: manter a pergunta = a pipeline atinge hit-3R>=obs no keep-set que ela propria escolhe
    nkeeps.append(hr)
nkeeps=np.array(nkeeps); pval=float((nkeeps>=obs).mean())
print(f"\nMINING-NULL (200 perms, re-corre LOO): obs {obs:.3f} · null mediana {np.median(nkeeps):.3f} · q90 {np.quantile(nkeeps,0.9):.3f} · P(null>=obs) {pval:.3f}")
print("VEREDICTO:", "SINAL (P<0.1)" if pval<0.1 else "ARTEFATO/winner-curse (P>=0.1)")
json.dump({"keep_ns":keep_ns,"score":sc,"oof_hit":kr,"mining_null_p":pval,"weights":{n:round(float(wv),3) for n,wv in zip(names,wf)}},
          open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/phase_classifier_loo_20260707.json","w"),indent=1)
print("saved · OK")
