#!/usr/bin/env python3
"""N96 · LEITURA CONTEXTUAL DO OVERLAP (2026-07-08). Confluencia HTF isola centroide mas nao poupa winner
(winners partilham contexto HTF dos losers). Logo o discriminador residual mora DENTRO da mesma confluencia.
Este script condiciona ao conjunto que dispara a confluencia loser (SKIP bear-top) e compara WIN vs LOSER
AI DENTRO, feature a feature — diferencas aqui sao INTRA-CONTEXTO (nao regime/ano). Depois honest-test
(LOO logistic restrito ao subset) + mining-null. SEM veredito — DA arbitra."""
import csv, sys
import numpy as np, statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, famof
from agent_ctx_kit import ENTRIES, score
rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
BYN={int(r["n"]):r for r in rows}
def g(r,k):
    try: return float(r.get(k))
    except: return None
FEATS=[c for c in rows[0] if c not in ("n","out","fam")]

def D_subs(r): return sum([ (g(r,"4H_ema_trend") or 0)<0,(g(r,"4H_px_vs_ema") or 9)<0,(g(r,"1D_px_vs_ema") or 9)<0,(g(r,"mtf_bull_align") or 9)<=1,(g(r,"4H_dem_below") or 9)<1.5 ])
def C_subs(r): return sum([ (g(r,"4H_rsi") or 0)>58,(g(r,"4H_px_vs_ema") or -9)>2,(g(r,"4H_dem_below") or 0)>3,(g(r,"1D_ema_trend") or 0)>3,(g(r,"1H_rsi_slope") or 9)<-5 ])

# ---- conjunto condicionado: dispara confluencia loser (D>=3 OR C>=3) ----
COND=[int(r["n"]) for r in rows if D_subs(r)>=3 or C_subs(r)>=3]
Win=[n for n in COND if BYN[n]["out"]=="1"]; Los=[n for n in COND if BYN[n]["out"]=="0"]
print(f"CONTEXTO CONDICIONADO (D>=3 or C>=3): n={len(COND)}  winners={len(Win)}  losers={len(Los)}")
print(f"  -> pergunta: DENTRO deste contexto HTF-loser, o que separa o WINNER do LOSER?\n")

def auc(a,b):
    if not a or not b: return 0.5
    c=t=0
    for x in a:
        for y in b:
            t+=1; c+=1 if x>y else (0.5 if x==y else 0)
    return c/t
print(f"{'feature':<22}{'WIN_med':>9}{'LOS_med':>9}{'AUC':>7}  sep")
ranked=[]
for k in FEATS:
    wv=[g(BYN[n],k) for n in Win if g(BYN[n],k) is not None]
    lv=[g(BYN[n],k) for n in Los if g(BYN[n],k) is not None]
    if len(wv)<8 or len(lv)<8: continue
    a=auc(wv,lv); sep=abs(a-0.5)
    ranked.append((sep,k,round(st.median(wv),3),round(st.median(lv),3),round(a,3)))
ranked.sort(reverse=True)
for sep,k,wm,lm,a in ranked[:22]:
    print(f"{k:<22}{wm:>9}{lm:>9}{a:>7}  {sep:.2f}")

# ---- honest-test: LOO logistic restrito ao subset condicionado + mining-null ----
top=[k for _,k,_,_,_ in ranked[:6]]
NS=COND; y=np.array([1 if BYN[n]["out"]=="1" else 0 for n in NS],dtype=float)
X=np.array([[ (g(BYN[n],k) if g(BYN[n],k) is not None else 99.0) for k in top] for n in NS],dtype=float)
mu=X.mean(0); sd=X.std(0)+1e-9; Xs=(X-mu)/sd
def fit(Xt,yt,l2=1.0,s=300,lr=0.3):
    w=np.zeros(Xt.shape[1]); b=0.0; m=len(yt)
    for _ in range(s):
        p=1/(1+np.exp(-(Xt@w+b))); gg=p-yt; w-=lr*(Xt.T@gg/m+l2*w/m); b-=lr*gg.mean()
    return w,b
def loo(Xs,y):
    P=np.zeros(len(y))
    for t in range(len(y)):
        idx=np.arange(len(y))!=t; w,b=fit(Xs[idx],y[idx]); P[t]=1/(1+np.exp(-(Xs[t]@w+b)))
    return P
P=loo(Xs,y); keep=P>0.5
kept=[int(NS[i]) for i in range(len(NS)) if keep[i]]
sc=score(kept); obs=sc["hit3r_kept"]
base_cond=len(Win)/len(COND)
rng=np.random.default_rng(11); vals=[]
for _ in range(300):
    yp=rng.permutation(y); Pp=loo(Xs,yp); kp=Pp>0.5
    if kp.sum(): vals.append(yp[kp].mean())
vals=np.array(vals); pv=float((vals>=obs).mean())
print(f"\nHONEST-TEST intra-contexto (LOO+mining-null, top6={top}):")
print(f"  base_condicionada={base_cond:.3f}  oof_hit={obs:.3f}  N_keep={sc['N_kept']}  poison={sc['poison_ratio']}")
print(f"  y2025={sc['y2025']} y2026={sc['y2026']}  mining_null_p={pv:.3f}")
print(f"  (in-sample NAO conta; separa DENTRO do contexto = nao-regime SE p<0.1 e oof>base)")
print("\nSEM veredito. Leitura contextual entregue como DADO. DA decide adotabilidade + forward.")
