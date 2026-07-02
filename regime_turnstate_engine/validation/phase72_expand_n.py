#!/usr/bin/env python3
"""Objetivo (Cris): ADICIONAR trades referenciados na V2 p/ subir N+WR+R:R SEM subir streak. Multi-critério + trajetória.
Diagnóstico: 245 sinais L2 (R let-run), marca os 17 V2, e testa uma família candidata CAUSAL e referenciada na V2:
CONTINUAÇÃO = sinal L2 que ocorre DEPOIS de um trade V2-capitulação já ter CONFIRMADO (atingido +2R = reversão real),
dentro da mesma perna de alta (regime≠BEAR, ≤80 barras após a confirmação), e que não é V2. Perfil desses + painel
V2 vs V2+continuação (WR, avgR, DD, STREAK, por-ano). custo 0.35."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
COST=0.35;HZ=120
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for config import (robust, no daemon/global sys.path)
from config import paths as CP
VAL=CP.repo("regime_turnstate_engine","validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open(CP.causal_segments())),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def seg_idx(t):
    for i in range(len(segs)):
        if segs[i]['start']<=t<=segs[i]['end']: return i
    return None
def regime_at(bi):
    idx=seg_idx(T[bi]);return segs[idx]['regime'] if idx is not None else '?'
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
def letrun(bi,entry,sl):
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
def conf_bar(bi,entry,sl):
    """barra em que o trade atinge +2R (confirmação); None se stopa antes."""
    risk=entry-sl;tp=entry+2*risk;end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return None
        if H[j]>=tp: return j
    return None
Dr=CP.ruler("XAU_4H_L2_BPT_BOS_CHOCH","v1","results")
allsig=[];v2=[];capit_conf=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);entry=float(r["entry"]);sl=float(r["sl"])
    if entry-sl<=0: continue
    R=round(letrun(bi,entry,sl)-COST,2);allsig.append({"bi":bi,"entry":entry,"sl":sl,"R":R})
    t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0: continue
    s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo'];ztop=(prev['hi']-amp/3,prev['hi']);zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    keep=(s['regime']=='BULL' and ztop[0]<=entry<=ztop[1]) or (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.34)
    if keep:
        v2.append(bi)
        capit=(s['regime']=='BEAR') or (s['regime']=='RANGE' and pos<0.25)
        if capit:
            cb=conf_bar(bi,entry,sl)
            if cb is not None: capit_conf.append(cb)   # barra de confirmação (+2R)
v2set=set(v2)
# CONTINUAÇÃO: sinal L2 não-V2, após uma confirmação de capitulação, ≤80 barras, regime≠BEAR
cont=[]
for x in allsig:
    if x['bi'] in v2set: continue
    for cb in capit_conf:
        if cb < x['bi'] <= cb+80 and regime_at(x['bi'])!='BEAR':
            cont.append(x);break
def pan(bis_or_rows,tag):
    rows=bis_or_rows if isinstance(bis_or_rows[0],dict) else [next(a for a in allsig if a['bi']==b) for b in bis_or_rows]
    rows=sorted(rows,key=lambda z:z['bi']);n=len(rows);w=sum(1 for z in rows if z['R']>0);s=sum(z['R'] for z in rows)
    cum=peak=dd=0;st=mx=0
    for z in rows:
        cum+=z['R'];peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if z['R']<=0 else 0;mx=max(mx,st)
    print(f"{tag:26} N={n:3} WR={100*w/n:3.0f}% sumR={s:+7.1f} avgR={s/n:+5.2f} DD={dd:6.1f} STREAK={mx} big={sum(1 for z in rows if z['R']>=3)}")
    return rows
print(f"Universo L2 total: {len(allsig)} sinais\n")
pan(allsig,"TODOS os 245 L2")
v2rows=pan(v2,"V2 (17)")
if cont:
    pan(cont,"CONTINUAÇÃO só (nova)")
    pan(v2rows+cont,"V2 + CONTINUAÇÃO")
else:
    print("CONTINUAÇÃO: 0 candidatos")
print(f"\nconfirmações de capitulação (+2R): {len(capit_conf)} | candidatos continuação: {len(cont)}")
