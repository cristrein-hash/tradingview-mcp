#!/usr/bin/env python3
"""Tese LONG-RUN do Cris generaliza? Todos os 10 bull-reteste com SL estrutural causal (min-low 30b − 0.5ATR) + horizonte
LONGO (até TP de múltiplo R fixo ou SL, sem cap) — exits TP=3R e TP=5R. Random-control: 200 draws de entradas ALEATÓRIAS
em regime BULL, mesmíssimo SL/exit. Se bull-reteste batem random-p95 = edge de LONG-RUN; se ~random = beta do bull secular.
custo 0.35."""
import json,io,contextlib,sys,bisect,csv,random,datetime as dt
from pathlib import Path
random.seed(20260701);COST=0.35
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
def run(bi,m):
    entry=C[bi];sl=min(L[max(0,bi-30):bi+1])-0.5*atr(bi);risk=entry-sl
    if risk<=0: return None,False
    tp=entry+m*risk
    for j in range(bi+1,n4):
        if L[j]<=sl: return -1.0,False
        if H[j]>=tp: return float(m),False
    return (C[n4-1]-entry)/risk,True   # aberto no fim dos dados
# bull-reteste entries
bulls=[]
for idx in range(1,len(segs)):
    s=segs[idx]
    if s['regime']!='BULL': continue
    prev=segs[idx-1];amp=prev['hi']-prev['lo'];niv=prev['hi']
    i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
    if i1-i0<3: continue
    k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
    if k is None: continue
    rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
    if rj is None or any(abs(rj-b)<=1 for b in v2bars): continue
    bulls.append(rj)
# pool de barras em regime BULL (p/ random)
bullbars=[bisect.bisect_left(T,s['start']) for s in segs if s['regime']=='BULL' for _ in range(1)]
bull_ranges=[(bisect.bisect_left(T,s['start']),bisect.bisect_right(T,s['end'])-1) for s in segs if s['regime']=='BULL']
bull_ranges=[(a,b) for a,b in bull_ranges if b-a>=3]
def summ(bis,m):
    rs=[];op=0
    for bi in bis:
        r,o=run(bi,m)
        if r is None: continue
        rs.append(round(r-COST,2));op+=o
    return sum(rs),(sum(rs)/len(rs) if rs else 0),(100*sum(1 for x in rs if x>0)/len(rs) if rs else 0),len(rs),op
for m in (3,5):
    ss,sa,swr,sn,sop=summ(bulls,m)
    rsums=[]
    for _ in range(200):
        rb=[random.randint(a,b-1) for a,b in bull_ranges];rs_=summ(rb,m)[0];rsums.append(rs_)
    rsums.sort();rmed=rsums[100];rp95=rsums[190]
    verd="EDGE (>p95)" if ss>rp95 else ("~beta (<=med)" if ss<=rmed else "meio-termo")
    print(f"TP={m}R horizonte-longo: BULL-reteste sumR{ss:+6.1f} avgR{sa:+.2f} WR{swr:3.0f}% N{sn} ({sop} abertos) | random med{rmed:+6.1f}/p95{rp95:+6.1f} -> {verd}")
print("\nSL=min-low30b−0.5ATR (estrutural causal), TP=múltiplo R fixo, horizonte até fim dos dados (long-run). Random=entradas aleatórias em BULL.")
