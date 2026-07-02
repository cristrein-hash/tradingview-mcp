#!/usr/bin/env python3
"""Variante causal (Cris): SL = max-largura(swing-low, entry−1ATR) [piso de 1 ATR p/ não ficar apertado] + TP = let-run HZ120.
Sem hindsight. Aplica aos 10 bull-reteste (=phase58/60). Compara: orig (zona-bottom+letrun) · causal-v1 (swing-low+topo) ·
VARIANTE (SLmax+letrun). Trade-a-trade + painel. custo 0.35."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
MT=0.01;COST=0.35;HZ=120
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
def exit_letrun(bi,entry,sl,end):
    for j in range(bi+1,min(end,n4-1)+1):
        if L[j]<=sl: return (-1.0,j,"SL")
    e=min(end,n4-1);return ((C[e]-entry)/(entry-sl),e,"letrun/close")
rows=[]
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
    entry=C[rj];a=atr(rj)
    sl_orig=zlo-0.5*a
    sl_swing=min(L[max(i0,rj-4):rj+1])-0.1*a
    sl_var=min(sl_swing,entry-1.0*a)                     # VARIANTE: piso de 1 ATR de largura
    R_orig,_,_=exit_letrun(rj,entry,sl_orig,rj+HZ)
    R_var,ej,how=exit_letrun(rj,entry,sl_var,rj+HZ)      # let-run 120
    open_flag=T[min(rj+HZ,n4-1)]>T[n4-1]
    rows.append({"bi":rj,"date":dt.datetime.utcfromtimestamp(T[rj]).strftime("%Y-%m-%d"),"entry":entry,
        "sl":sl_var,"riskpct":100*(entry-sl_var)/entry,"R_orig":round(R_orig-COST,2),
        "R_var":round(R_var-COST,2),"how":how,"bars":ej-rj,"open":ej>=n4-1})
rows.sort(key=lambda x:x['bi'])
print(f"{'#':4}{'date':11}{'entry':8}{'SLvar':8}{'risk%':6}{'Rorig':7}{'Rvariante':10}{'saída':13}{'barras':6}")
for i,x in enumerate(rows,1):
    op=" ABERTO" if x['open'] else ""
    print(f"B{i:<3}{x['date']:11}{x['entry']:8.1f}{x['sl']:8.1f}{x['riskpct']:5.1f}%{x['R_orig']:+7.2f}{x['R_var']:+10.2f} {x['how']:12}{x['bars']:5}{op}")
def pan(key,tag,skip_open=False):
    rr=[x for x in rows if not (skip_open and x['open'])]
    n=len(rr);w=sum(1 for x in rr if x[key]>0);s=sum(x[key] for x in rr)
    cum=peak=dd=0;st=mx=0
    for x in rr:
        cum+=x[key];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x[key]<=0 else 0;mx=max(mx,st)
    print(f"{tag:30} N={n} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:5.1f} streak={mx} big={sum(1 for x in rr if x[key]>=3)}")
print()
pan("R_orig","ORIG (zona-bottom+letrun)")
pan("R_var","VARIANTE (SLmax+letrun)")
pan("R_var","VARIANTE só FECHADOS",skip_open=True)
print("\nRef: causal-v1 (swing-low+topo)=+0.5R · ajustes manuais hindsight=+17.5R · V2-base pura=+36.2R/17tr")
