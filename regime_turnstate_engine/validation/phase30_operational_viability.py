#!/usr/bin/env python3
"""Cris (2026-07-01): o árbitro é VIABILIDADE PSICOLÓGICA/OPERACIONAL (streak, WR, consistência mensal p/ saque em prop),
NÃO só expectancy. Medir a SEGURABILIDADE do book L2/BPT 2023+ com o SL-no-piso-da-box aplicado SÓ às intra-range
(resto do book mantém SL_CONTEXT), vs baseline tudo-SL_CONTEXT. Métricas de execução humana:
max-loss-streak, loss-runs>=3/>=5, WR, %meses positivos, pior mês, maxDD, tempo-entre-wins.
Piso causal = running-min-so-far−0.1ATR (sem hindsight). let-run HZ120, custo 0.35. Painel COMPLETO."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
from collections import defaultdict
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None
def sim_letrun(bi,entry,sl):
    risk=entry-sl
    if risk<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/risk
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=box_of(t);entry=float(r["entry"])
    R_base=round(float(r["letrun_struct"])-COST,2)
    if box:
        i0=bisect.bisect_left(T,box['start']);rmin=min(L[i0:bi+1]);a=atr(bi)
        R_mod=round((sim_letrun(bi,entry,rmin-0.1*a) or 0)-COST,2)
    else:
        R_mod=R_base   # não-range mantém SL_CONTEXT
    rows.append({"bi":bi,"t":t,"ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),"range":bool(box),
                 "R_base":R_base,"R_mod":R_mod})
rows.sort(key=lambda x:x["bi"])
def panel(key,label):
    rs=[x[key] for x in rows];n=len(rs);w=sum(1 for v in rs if v>0)
    s=sum(rs);cum=peak=dd=0;streak=mx=0;runs=[]
    for v in rs:
        cum+=v;peak=max(peak,cum);dd=min(dd,cum-peak)
        if v<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak: runs.append(streak)
            streak=0
    if streak: runs.append(streak)
    r3=sum(1 for q in runs if q>=3);r5=sum(1 for q in runs if q>=5)
    # meses
    mth=defaultdict(float)
    for x in rows: mth[x["ym"]]+=x[key]
    posm=sum(1 for v in mth.values() if v>0);negm=sum(1 for v in mth.values() if v<0)
    worst=min(mth.values());worst_m=[k for k,v in mth.items() if v==worst][0]
    # tempo entre wins (em nº de trades)
    gaps=[];g=0
    for v in rs:
        g+=1
        if v>0: gaps.append(g);g=0
    avggap=sum(gaps)/len(gaps) if gaps else 0
    print(f"\n  === {label} ===")
    print(f"    N={n} WR={100*w/n:.0f}% sumR={s:+.1f} avgR={s/n:+.2f} maxDD={dd:.1f}")
    print(f"    max-loss-streak={mx}  loss-runs>=3:{r3}  >=5:{r5}  avg-trades-entre-wins={avggap:.1f}")
    print(f"    meses: {posm}+ / {negm}-  ({100*posm/(posm+negm):.0f}% positivos)  pior mês={worst:+.1f}R ({worst_m})")
nrange=sum(1 for x in rows if x["range"])
print(f"BOOK L2/BPT 2023+ : {len(rows)} trades ({nrange} intra-range recebem SL-no-piso; {len(rows)-nrange} mantêm SL_CONTEXT)")
panel("R_base","BASELINE (tudo SL_CONTEXT)")
panel("R_mod","MOD (intra-range → SL-piso-causal −0.1ATR)")
# delta streak dentro só das range (onde está a dor 13:1)
print("\n  --- só as 70 intra-range (onde vive a dor de streak) ---")
rr=[x for x in rows if x["range"]]
for key,lab in [("R_base","range SL_CONTEXT"),("R_mod","range SL-piso")]:
    rs=[x[key] for x in rr];w=sum(1 for v in rs if v>0);streak=mx=0
    for v in rs:
        if v<=0: streak+=1;mx=max(mx,streak)
        else: streak=0
    print(f"    {lab:20} WR={100*w/len(rs):.0f}% max-loss-streak={mx} sumR={sum(rs):+.1f}")
