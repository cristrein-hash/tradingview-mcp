#!/usr/bin/env python3
"""Reconciliar B3/B6 (Cris: big winners) com os dados. Para cada bull-reteste: MFE SEM stop (potencial puro até fim do
regime bull), pullback máximo nas 1as 15 barras (o SL necessário p/ não stopar), e resultado com SL=abaixo-do-pullback
(estrutural largo) + let-run até fim do impulso bull. Mostra se o 'big winner' aparece com o SL certo. custo 0.35."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
v2bars=set()
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];entry=float(r["entry"]);sl=float(r["sl"]);amp=prev['hi']-prev['lo']
    ztop=(prev['hi']-amp/3,prev['hi']);zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    keep=(s['regime']=='BULL' and ztop[0]<=entry<=ztop[1]) or (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.34)
    if keep and entry-sl>0: v2bars.add(bi)
print(f"{'#':4}{'date':11}{'entry':8}{'i1_end':11}{'pull15%':8}{'MFEnostop':10}{'SLpull':8}{'R(SLpull+letrunRegime)':22}")
i=0
for idx in range(1,len(segs)):
    s=segs[idx]
    if s['regime']!='BULL': continue
    prev=segs[idx-1];amp=prev['hi']-prev['lo'];niv=prev['hi'];zlo=niv-amp/3
    i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
    if i1-i0<3: continue
    k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
    if k is None: continue
    rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
    if rj is None: continue
    if any(abs(rj-b)<=1 for b in v2bars): continue
    i+=1;entry=C[rj]
    # pullback máximo nas 1as 15 barras (o SL precisa ficar abaixo disto p/ sobreviver)
    w=min(rj+15,i1);pull_lo=min(L[rj:w+1]);pull_pct=100*(entry-pull_lo)/entry
    sl_pull=pull_lo-0.1*atr(rj)   # SL estrutural = abaixo do fundo do pullback
    risk=entry-sl_pull
    # MFE sem stop até fim do regime bull
    endreg=i1;mfe=max((H[j]-entry) for j in range(rj+1,endreg+1))/risk
    # resultado: SL abaixo do pullback + let-run até fim do regime (stop-first)
    R=None
    for j in range(rj+1,endreg+1):
        if L[j]<=sl_pull: R=-1.0;break
    if R is None: R=(C[endreg]-entry)/risk
    d=dt.datetime.utcfromtimestamp(T[rj]).strftime("%Y-%m-%d");ed=dt.datetime.utcfromtimestamp(T[endreg]).strftime("%Y-%m-%d")
    print(f"B{i:<3}{d:11}{entry:8.1f}{ed:11}{pull_pct:7.1f}%{mfe:+10.2f}{sl_pull:8.1f}{R-COST:+8.2f}  (risk {risk:.0f}pts={100*risk/entry:.1f}%)")
