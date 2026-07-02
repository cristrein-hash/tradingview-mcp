#!/usr/bin/env python3
"""Cris: LIMITA 1 entrada APÓS cada uma das 10 capitulações (máx +10 trades), os melhores possíveis. CAUSAL: para cada
capitulação, o PRIMEIRO sinal de continuação na perna de alta seguinte (janela até regime virar BEAR / preço < fundo-capit
/ +150b). Testa 5 lógicas de continuação, painel capit(10)+cont p/ cada + por-ano. Escolhe a melhor (avgR alto, STREAK baixo).
exit let-run HZ120, SL swing-low−0.5ATR, custo 0.35."""
import json,io,contextlib,sys,bisect,csv,datetime as dt
from pathlib import Path
from statistics import mean
from collections import defaultdict
COST=0.35;HZ=120
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
# capitulação V2 (10) — bi + fundo
Dr=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
capit=[]
for r in csv.DictReader(open(Dr/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);entry=float(r["entry"]);sl=float(r["sl"]);t=T[bi];idx=seg_idx(t)
    if idx is None or idx==0 or entry-sl<=0: continue
    s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo'];zdeep=bear_deep(idx)
    i0=bisect.bisect_left(T,s['start']);rmin=min(L[i0:bi+1]);rmax=max(H[i0:bi+1]);pos=(entry-rmin)/(rmax-rmin) if rmax>rmin else .5
    if (s['regime']=='BEAR' and zdeep and zdeep[0]<=entry<=zdeep[1]) or (s['regime']=='RANGE' and pos<0.25):
        rr=letrun(bi,entry,sl)
        if rr is not None: capit.append({"bi":bi,"low":min(L[max(0,bi-4):bi+1]),"R":round(rr-COST,2)})
capit.sort(key=lambda x:x['bi'])
# lógicas de continuação (primeiro sinal na janela)
def deep_pull(i): return regime_at(i)=='BULL' and dpos(i,40)<0.30 and C[i]>C[i-1]
def swept(i): return L[i]<min(L[i-20:i]) and C[i]>C[i-1]
def ema20_pull(i): return L[i]<=EMA20[i]*1.005 and C[i]>EMA20[i] and C[i]>C[i-1]
def higher_low(i): return L[i]>L[i-2] and C[i]>C[i-1] and dpos(i,20)<0.5
def bull_break(i): return C[i]>max(H[i-10:i]) and C[i]>C[i-1]
LOG={"deep_pull":deep_pull,"swept":swept,"ema20_pull":ema20_pull,"higher_low":higher_low,"bull_break":bull_break}
def cont_after(pred):
    out=[];used=set()
    for c in capit:
        cb=c['bi'];endw=cb+150
        # janela: até regime BEAR ou preço < fundo capit
        add=None
        for i in range(cb+2,min(endw,n4-HZ-1)):
            if regime_at(i)=='BEAR': break
            if C[i]<c['low']: break
            if i in used: continue
            try:
                if pred(i):
                    sl=SL(i)
                    if C[i]-sl>0:
                        r=letrun(i,C[i],sl)
                        if r is not None: add=(i,round(r-COST,2));break
            except: pass
        if add: out.append(add);used.add(add[0])
    return out
def stats(rows):
    rows=sorted(rows);n=len(rows)
    if n==0: return None
    w=sum(1 for _,r in rows if r>0);s=sum(r for _,r in rows)
    cum=peak=dd=0;st=mx=0
    for _,r in rows:
        cum+=r;peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if r<=0 else 0;mx=max(mx,st)
    return n,100*w/n,s,s/n,dd,mx,sum(1 for _,r in rows if r>=3)
caprows=[(c['bi'],c['R']) for c in capit]
cs=stats(caprows)
print(f"CAPITULAÇÃO só: N={cs[0]} WR={cs[1]:.0f}% sumR={cs[2]:+.1f} avgR={cs[3]:+.2f} DD={cs[4]:.1f} STREAK={cs[5]}\n")
print(f"{'+1-após-capit via':16}{'Nadd':>5}{'N':>4}{'WR':>5}{'sumR':>8}{'avgR':>7}{'DD':>7}{'STRK':>5}{'big':>4}")
for name,pred in LOG.items():
    add=cont_after(pred);comb=caprows+add;st=stats(comb)
    n,wr,s,avg,dd,mx,big=st
    print(f"{name:16}{len(add):>5}{n:>4}{wr:>4.0f}%{s:>8.1f}{avg:>7.2f}{dd:>7.1f}{mx:>5}{big:>4}")
