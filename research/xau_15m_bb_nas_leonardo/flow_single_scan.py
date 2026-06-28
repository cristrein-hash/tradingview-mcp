#!/usr/bin/env python3
"""Teto do fluxo: para cada feature NAS/Bubbles/OB/SMC sobre o substrato #4 (substrate4_flow.jsonl),
W/L std-diff + melhor corte single (q0.25 hi/lo) com losL/runL/avgR/null-p. Mostra o ceiling honesto."""
import json,statistics as st,random
from pathlib import Path
HERE=Path(__file__).parent
R=[json.loads(l) for l in (HERE/"substrate4_flow.jsonl").read_text().splitlines()]
for r in R: r["_F"]=r["flow"]
FE=sorted(R[0]["flow"].keys())
W=[r for r in R if r["R"]>0]; L=[r for r in R if r["R"]<=0]
def m(g,k): v=[r["_F"][k] for r in g if r["_F"].get(k) is not None]; return (st.mean(v),st.pstdev(v) if len(v)>1 else 0) if v else (0,0)
def panel(rows):
    Rs=[x["R"] for x in sorted(rows,key=lambda z:z["cj_t"])]; n=len(Rs)
    if not n: return None
    sm=sum(Rs); w=sum(1 for x in Rs if x>0); eq=pk=dd=0
    for x in Rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return n,round(sm/n,3),round(dd,1),sum(1 for x in Rs if x<=0),sum(1 for x in Rs if x>=3),{y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}
def quant(vals,q): vs=sorted(vals); return vs[min(len(vs)-1,max(0,int(q*len(vs))))]
base=panel(R); print(f"SUBSTRATO#4: N{base[0]} avgR{base[1]} DD{base[2]} losers{base[3]} runners{base[4]} yr{base[5]}\n")
print("== std-diff WIN vs LOSER + melhor corte single (q0.25) ==")
print(f"{'feat':<22}{'stddiff':>8}{'dir':>5}{'N':>5}{'avgR':>7}{'DD':>7}{'losL':>6}{'runL':>6}{'nullp':>7}{'anos+':>7}")
rows=[]
for k in FE:
    mw,sw=m(W,k); ml,sl_=m(L,k); sp=((sw**2+sl_**2)/2)**0.5 or 1; d=(mw-ml)/sp
    vals=[r["_F"][k] for r in R if r["_F"].get(k) is not None]
    if len(set(vals))<=2:  # binário: eq1 favorável se win-mean>loser-mean
        keep=[r for r in R if r["_F"].get(k)==(1 if d>0 else 0)]; dr="eq1" if d>0 else "eq0"
    else:
        if d>0: thr=quant(vals,0.25); keep=[r for r in R if r["_F"].get(k) is None or r["_F"][k]>=thr]; dr="hi"
        else: thr=quant(vals,0.75); keep=[r for r in R if r["_F"].get(k) is None or r["_F"][k]<=thr]; dr="lo"
    pk=panel(keep)
    if not pk or pk[0]==base[0]: rows.append((abs(d),k,round(d,2),dr,base[0],base[1],base[2],0,0,1.0,True)); continue
    n,av,dd,nl,nr,yr=pk; ncut=base[0]-n
    rng=random.Random(1); avs=[]
    for _ in range(300):
        idx=set(rng.sample(range(len(R)),ncut)) if 0<ncut<len(R) else set()
        kk=[R[i] for i in range(len(R)) if i not in idx]; pp=panel(kk); avs.append(pp[1])
    p=round(sum(1 for x in avs if x>=av)/len(avs),3)
    rows.append((abs(d),k,round(d,2),dr,n,av,dd,base[3]-nl,base[4]-nr,p,all(v>=0 for v in yr.values())))
for ad,k,d,dr,n,av,dd,dl,dr_,p,ap in sorted(rows,reverse=True):
    print(f"{k:<22}{d:>+8}{dr:>5}{n:>5}{av:>7}{dd:>7}{dl:>6}{dr_:>6}{p:>7}{('sim' if ap else 'NAO'):>7}")
print("\n(losL=losers cortados, runL=runners cortados, nullp<0.02 seria robusto; anos+=todos anos positivos)")
