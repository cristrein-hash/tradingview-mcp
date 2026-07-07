#!/usr/bin/env python3
"""LEITOR FRACTAL MULTI-TIMEFRAME das 4 fases (2026-07-07, diretriz Cris: mercado e fractal, escala e
essencia). Resample do RAW 15M -> 4H/1D/1W. Para cada entry, features HTF CAUSAIS (so barras HTF FECHADAS
antes do entry — a barra corrente NAO fechada e EXCLUIDA = anti-lookahead MTF rigoroso). A fase 15M le-se
pela POSICAO/MATURIDADE da perna HTF (relativa a perna, nao ao calendario -> mata o confound de regime).
Valida OOF (leave-one-out) + mining-null.
SANITY_PROBE: leitura fractal multi-escala (4H/1D/1W), maturidade-de-perna HTF relativa (nao calendario);
causal estrito (barra HTF corrente excluida); OOF+mining-null; multi-fatorial; nao snapshot single-scale."""
import json, glob, bisect, sys
import datetime as dt
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score
# ---- resample 15M -> HTF (bucket por periodo; end_time = fim do bucket) ----
def resample(bucket_s):
    buckets={}
    for b in S:
        k=(b["t"]//bucket_s)*bucket_s
        d=buckets.get(k)
        if d is None: buckets[k]={"start":k,"end":k+bucket_s,"o":b["c"],"h":b["h"],"l":b["l"],"c":b["c"]}
        else:
            d["h"]=max(d["h"],b["h"]); d["l"]=min(d["l"],b["l"]); d["c"]=b["c"]
    arr=[buckets[k] for k in sorted(buckets)]
    return arr
HTF={"4H":resample(4*3600),"1D":resample(24*3600),"1W":resample(7*24*3600)}
def htf_closed_upto(tf, t):
    """barras HTF cujo END <= t (FECHADAS antes do entry). Exclui a barra corrente = anti-lookahead."""
    arr=HTF[tf]; ends=[x["end"] for x in arr]
    hi=bisect.bisect_right(ends, t)   # ends[hi-1] <= t
    return arr[:hi]
def swings(bars, r=2.0):
    """zigzag causal sobre barras HTF (ATR simples da propria serie)."""
    n=len(bars)
    if n<5: return []
    H=[b["h"] for b in bars]; L=[b["l"] for b in bars]; C=[b["c"] for b in bars]
    tr=[]; A=[]
    for i in range(n):
        t=H[i]-L[i] if i==0 else max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])); tr.append(t); A.append(sum(tr[-14:])/min(len(tr),14))
    piv=[]; d=0; ehi=elo=0
    for i in range(1,n):
        a=A[i] or 1
        if H[i]>H[ehi]: ehi=i
        if L[i]<L[elo]: elo=i
        if d<=0 and H[i]-L[elo]>=r*a and elo<i: piv.append(("L",elo,L[elo])); d=1; ehi=max(range(elo,i+1),key=lambda k:H[k])
        elif d>=0 and H[ehi]-L[i]>=r*a and ehi<i: piv.append(("H",ehi,H[ehi])); d=-1; elo=min(range(ehi,i+1),key=lambda k:L[k])
    return piv,H,L,C,A
def htf_feats(tf, t, px):
    bars=htf_closed_upto(tf,t)
    if len(bars)<8: return {"dir":0,"maturity":0,"pos":0.5,"pullback":0,"pushes":0}
    res=swings(bars);
    if not res: return {"dir":0,"maturity":0,"pos":0.5,"pullback":0,"pushes":0}
    piv,H,L,C,A=res
    highs=[pr for tp,i,pr in piv if tp=="H"]; lows=[pr for tp,i,pr in piv if tp=="L"]
    hh=len(highs)>=2 and highs[-1]>highs[-2]; hl=len(lows)>=2 and lows[-1]>lows[-2]
    lh=len(highs)>=2 and highs[-1]<highs[-2]; ll=len(lows)>=2 and lows[-1]<lows[-2]
    dir=1 if (hh and hl) else (-1 if (lh and ll) else 0)
    a=A[-1] or 1
    origin=lows[-1] if lows else L[-1]; maturity=(px-origin)/a   # extensao da perna corrente HTF em ATR-HTF (relativa a perna!)
    win=[b for b in bars[-20:]]; hi=max(b["h"] for b in win); loo=min(b["l"] for b in win); pos=(px-loo)/((hi-loo) or 1)
    # pushes = higher-highs consecutivos
    pushes=0
    for m in range(len(highs)-1,0,-1):
        if highs[m]>highs[m-1]: pushes+=1
        else: break
    pullback=1 if dir==1 and pos<0.7 else 0
    return {"dir":dir,"maturity":round(maturity,2),"pos":round(pos,2),"pullback":pullback,"pushes":pushes}
# ---- montar features fractais por entry ----
PHASE={}
for n in [1,11,12,13,14,28,29,30,44,45,71,72,73,74,75,95,96]: PHASE[n]="A"
for n in [82,61,62,63,26]: PHASE[n]="B"
for n in [21,23,25,31,55,56,57,59,60,65,67,79,83,84,85]: PHASE[n]="C"
for n in [66,68,69,86,87,89,92,93,94,49,50]: PHASE[n]="D"
rows=[]
for e in ENTRIES:
    t=e["t"]; px=e["ent"]
    f4=htf_feats("4H",t,px); f1d=htf_feats("1D",t,px); f1w=htf_feats("1W",t,px)
    rows.append({"n":e["n"],"out":e["out"],"t":t,"ph":PHASE.get(e["n"]),
        "d4":f4["dir"],"m4":f4["maturity"],"p4":f4["pos"],"pb4":f4["pullback"],"pu4":f4["pushes"],
        "d1d":f1d["dir"],"m1d":f1d["maturity"],"p1d":f1d["pos"],"pb1d":f1d["pullback"],"pu1d":f1d["pushes"],
        "d1w":f1w["dir"],"m1w":f1w["maturity"],"p1w":f1w["pos"]})
json.dump(rows,open("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/mtf_fractal_phase_20260707.json","w"),indent=1)
# ---- caracterizacao por fase (medianas) ----
import statistics as st
lab=[r for r in rows if r["ph"]]
def med(sub,k): return st.median([r[k] for r in sub]) if sub else 0
A=[r for r in lab if r["ph"]=="A"];B=[r for r in lab if r["ph"]=="B"];C=[r for r in lab if r["ph"]=="C"];D=[r for r in lab if r["ph"]=="D"]
FEATS=["d4","m4","p4","pu4","d1d","m1d","p1d","pu1d","d1w","m1w","p1w"]
print(f"labeled A{len(A)} B{len(B)} C{len(C)} D{len(D)}")
print(f"{'feat':<6}{'A':>7}{'B':>7}{'C':>7}{'D':>7}  effect(AB-CD)")
for k in FEATS:
    allv=[r[k] for r in lab]; sd=st.pstdev(allv) or 1; eff=(med(A+B,k)-med(C+D,k))/sd
    print(f"{k:<6}{med(A,k):>7.2f}{med(B,k):>7.2f}{med(C,k):>7.2f}{med(D,k):>7.2f}  {eff:+.2f}{'  <<<' if abs(eff)>=0.5 else ''}")
# ---- OOF logistic + mining-null (todas as 96, target=out) ----
X=np.array([[r[k] for k in FEATS] for r in rows],dtype=float); y=np.array([r["out"] for r in rows],dtype=float)
yrs=np.array([dt.datetime.utcfromtimestamp(int(r["t"])).year for r in rows]); ns=np.array([r["n"] for r in rows])
mu=X.mean(0); sd=X.std(0)+1e-9; Xs=(X-mu)/sd
def fit(Xtr,ytr,l2=1.0,steps=300,lr=0.3):
    w=np.zeros(Xtr.shape[1]); b=0.0; m=len(ytr)
    for _ in range(steps):
        p=1/(1+np.exp(-(Xtr@w+b))); g=p-ytr; w-=lr*(Xtr.T@g/m+l2*w/m); b-=lr*g.mean()
    return w,b
def loo(Xs,y):
    P=np.zeros(len(y))
    for t in range(len(y)):
        idx=np.arange(len(y))!=t; w,b=fit(Xs[idx],y[idx]); P[t]=1/(1+np.exp(-(Xs[t]@w+b)))
    return P
P=loo(Xs,y); keep=P>0.5
sc=score([int(n) for n,k in zip(ns,keep) if k])
print("\n=== OOF (LOO, prob>0.5) ==="); print(json.dumps(sc,indent=1))
obs=sc["hit3r_kept"]
rng=np.random.default_rng(7); vals=[]
for _ in range(200):
    yp=rng.permutation(y); Pp=loo(Xs,yp); kp=Pp>0.5
    if kp.sum(): vals.append(yp[kp].mean())
vals=np.array(vals); pval=float((vals>=obs).mean())
print(f"MINING-NULL: obs {obs:.3f} · null med {np.median(vals):.3f} · q90 {np.quantile(vals,0.9):.3f} · P {pval:.3f} -> {'SINAL' if pval<0.1 else 'ARTEFATO'}")
print("OK")
