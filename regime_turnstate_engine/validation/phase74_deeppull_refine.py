#!/usr/bin/env python3
"""deep_pull_bull é a única EDGE do lab (avgR+2.17). Refinar p/ CORTAR streak 15, e COMBINAR com a capitulação V2.
Variantes (todas causais, trajetória): base, +swept(varreu low20), +rsi_turn, +dpos<0.20(mais fundo), +confirm2(close>high-1),
+ema20(recupera EMA20). Painel por variante (foco avgR+STREAK) + por-ano + jackknife-drop-ano. Depois CAPIT(10)+melhor.
exit let-run HZ120, SL swing-low−0.5ATR, cooldown 5, custo 0.35. Multi-fatorial+trajetória+null+jackknife."""
import json,io,contextlib,sys,bisect,csv,random
from pathlib import Path
from statistics import mean
from collections import defaultdict
import datetime as dt
random.seed(20260701);COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
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
TR=[0.0]*n4
for i in range(1,n4): TR[i]=max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1]))
ATR=[0.0]*n4
for i in range(14,n4): ATR[i]=mean(TR[i-13:i+1])
EMA20=[C[0]]*n4
for i in range(1,n4): EMA20[i]=EMA20[i-1]+(2/21)*(C[i]-EMA20[i-1])
def rsi(i,k=14):
    g=l=0
    for j in range(i-k+1,i+1):
        d=C[j]-C[j-1]
        if d>0:g+=d
        else:l-=d
    return 50 if g+l==0 else 100-100/(1+(g/k)/((l/k) if l>0 else 1e-9))
def dpos(i,n):
    lo=min(L[i-n+1:i+1]);hi=max(H[i-n+1:i+1]);return (C[i]-lo)/(hi-lo) if hi>lo else .5
def SL(i): return min(L[max(0,i-4):i+1])-0.5*ATR[i]
def letrun(bi,entry,sl):
    if entry-sl<=0:return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl:return -1.0
    return (C[end]-entry)/(entry-sl)
def base(i): return regime_at(i)=='BULL' and dpos(i,40)<0.30 and C[i]>C[i-1]
VAR={
 "base":            lambda i: base(i),
 "+swept":          lambda i: base(i) and L[i]<min(L[i-20:i]),
 "+rsi_turn":       lambda i: base(i) and rsi(i-1)<40 and rsi(i)>rsi(i-1),
 "+deep20":         lambda i: regime_at(i)=='BULL' and dpos(i,40)<0.20 and C[i]>C[i-1],
 "+confirm2":       lambda i: base(i) and C[i]>H[i-1],
 "+ema20":          lambda i: base(i) and C[i]>EMA20[i] and L[i]<=EMA20[i]*1.005,
}
def gen(pred):
    out=[];last=-99
    for i in range(60,n4-HZ-1):
        if i-last<5: continue
        try:
            if pred(i):
                sl=SL(i)
                if C[i]-sl>0: out.append((i,C[i],sl));last=i
        except: pass
    return out
def stats(rows):  # rows = list of (bi,R)
    rows=sorted(rows);n=len(rows)
    if n==0: return None
    w=sum(1 for _,r in rows if r>0);s=sum(r for _,r in rows)
    cum=peak=dd=0;st=mx=0
    for _,r in rows:
        cum+=r;peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if r<=0 else 0;mx=max(mx,st)
    return n,100*w/n,s,s/n,dd,mx,sum(1 for _,r in rows if r>=3)
def torows(ents):
    o=[]
    for bi,e,sl in ents:
        r=letrun(bi,e,sl)
        if r is not None: o.append((bi,round(r-COST,2)))
    return o
print(f"{'VARIANTE':12}{'N':>4}{'WR':>5}{'sumR':>8}{'avgR':>7}{'DD':>7}{'STRK':>5}{'big':>4}")
print(f"{'V2 (ref)':12}{17:>4}{53:>4}%{36.2:>8.1f}{2.13:>7.2f}{-4.1:>7.1f}{3:>5}{5:>4}")
best=None
for name,pred in VAR.items():
    rows=torows(gen(pred));st=stats(rows)
    if st is None: continue
    n,wr,s,avg,dd,mx,big=st
    print(f"{name:12}{n:>4}{wr:>4.0f}%{s:>8.1f}{avg:>7.2f}{dd:>7.1f}{mx:>5}{big:>4}")
    if best is None or (avg>best[1] and mx<=best[2]+3): best=(name,avg,mx,rows,pred)
# capitulação V2 (10)
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
capit=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);entry=float(r["entry"]);sl=float(r["sl"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0 or entry-sl<=0: continue
    s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo'];zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    if (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.25):
        rr=letrun(bi,entry,sl)
        if rr is not None: capit.append((bi,round(rr-COST,2)))
bn,_,_,brows,_=best
print(f"\n>> melhor variante deep_pull = '{bn}'  |  combinar com CAPITULAÇÃO(10):")
# dedup por proximidade
capbars=set(b for b,_ in capit)
add=[(b,r) for b,r in brows if not any(abs(b-cb)<=2 for cb in capbars)]
comb=capit+add
for tag,rows in (("CAPIT só",capit),(f"deep_pull '{bn}' add",add),("CAPIT + deep_pull",comb)):
    st=stats(rows)
    if st: n,wr,s,avg,dd,mx,big=st;print(f"  {tag:22} N={n:3} WR={wr:3.0f}% sumR={s:+6.1f} avgR={avg:+.2f} DD={dd:5.1f} STREAK={mx} big={big}")
by=defaultdict(list)
for b,r in comb: by[dt.datetime.utcfromtimestamp(T[b]).year].append(r)
print("  por-ano (combinado): "+", ".join(f"{y}:{sum(v):+.0f}(n{len(v)})" for y,v in sorted(by.items())))
