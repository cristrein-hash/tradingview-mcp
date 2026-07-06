#!/usr/bin/env python3
"""LAYER FUNDOS SUAVES + UNIÃO (2026-07-06). A veia cascata pega os fundos FORTES (capitulação, ~6/60).
Layer p/ os fundos SUAVES (sem cascade>=3): entry = reclaim & oversold & demanda, no pool família.
UNIÃO capitulação(E6) + suave = mais recall mantendo WR. Tudo causal. Curva de thresholds do suave."""
import json, bisect, hashlib, random
import numpy as np
exec(open("event_cascade_filter_curve_20260706.py").read().split('X=np.array')[0])
X=np.array([ev[0]["_vec"] for ev in EV]); isf=np.array([ev[0]["_isf"] for ev in EV]); efam=np.array([ev[0]["_efam"] for ev in EV]); cmax=np.array([ev[0]["_cmax"] for ev in EV]); NF=int(isf.sum())
def fam_env(fm):
    m=np.zeros(len(EV),bool)
    for fam in ("RASO","BANDA","FUNDO","SEM"):
        idx=np.where(efam==fam)[0]; fidx=np.where((efam==fam)&fm)[0]
        if len(fidx)<3: m[idx]=True; continue
        lo=X[fidx].min(0); hi=X[fidx].max(0)
        for i in idx:
            if np.all((X[i]>=lo)&(X[i]<=hi)): m[i]=True
    return m
FAM=fam_env(isf); WK=len({u["g_week"] for u in U})
def panel(rows,tag):
    if not rows: print(f"  {tag}: 0"); return
    nets=[R3[r["cj_t"]]["net3"] for r in sorted(rows,key=lambda x:x["cj_t"])]
    h=sum(1 for r in rows if R3[r["cj_t"]]["R3"]>=3); w=sum(1 for x in nets if x>0); eq=pk=dd=0.0; mL=cl=0
    for x in nets:
        eq+=x;pk=max(pk,eq);dd=min(dd,eq-pk)
        if x<=0: cl+=1;mL=max(mL,cl)
        else: cl=0
    yr={}
    for r in rows: yr[r["yr"]]=round(yr.get(r["yr"],0)+R3[r["cj_t"]]["net3"],1)
    cc=set()
    for r in rows: cc|=r["_circ"]
    # streak distribucional
    random.seed(7); q=[]
    for _ in range(2000):
        sq=random.choices(nets,k=len(nets)); c2=m2=0
        for x in sq:
            c2=c2+1 if x<=0 else 0; m2=max(m2,c2)
        q.append(m2)
    q.sort()
    print(f"  {tag:<20} N{len(rows)} WR {100*w/len(rows):.1f}% hit3R {100*h/len(rows):.1f}% NET {sum(nets):+.1f} DD {dd:.1f} stk-{mL}(q95 {q[int(.95*2000)]}) {len(rows)/WK:.2f}/sem círc {len(cc)}/60 | {yr}")
def get_F(u,k): return u["_F"].get(k)
# layer capitulação: eventos família com cascade>=3, entry E6
def lay_cap():
    out=[]
    for k,ev in zip(FAM,EV):
        if not k or ev[0]["_cmax"]<3: continue
        for u in ev:
            if u["_casc"]>=3 and u["_hl"]==1 and u["_reclaim"]==1: out.append(u); break
    return out
# layer suave: eventos família sem cascade>=3, entry = 1º reclaim & oversold & below_poc
def lay_soft(rsi_thr, dem):
    out=[]
    for k,ev in zip(FAM,EV):
        if not k or ev[0]["_cmax"]>=3: continue
        min_flo=1e18
        for pos,u in enumerate(ev,1):
            prevmin=min_flo; min_flo=min(min_flo,u["_flo"])
            if pos>1 and u["_hl"]==1 and u["_reclaim"]==1 and get_F(u,"rsi_min8")<=rsi_thr:
                if (dem=="any") or (dem=="poc" and get_F(u,"below_poc")==1) or (dem=="ob" and get_F(u,"ob_demand_mitig")==1):
                    out.append(u); break
    return out
print(f"eventos {len(EV)} · fundo {NF}")
cap=lay_cap(); panel(cap,"CAPITULAÇÃO(E6)")
for rsi_thr in (35,38,42):
    for dem in ("poc","ob","any"):
        s=lay_soft(rsi_thr,dem)
        panel(s,f"SUAVE rsi<={rsi_thr} {dem}")
    print()
# UNIÃO melhor
best_soft=lay_soft(38,"poc")
uni={id(u):u for u in cap+best_soft}.values()
print("UNIÃO capitulação + suave(rsi<=38,poc):")
panel(list(uni),"UNIÃO")
print("OK")
