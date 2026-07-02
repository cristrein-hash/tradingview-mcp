#!/usr/bin/env python3
"""LAB DE ENTRADAS (exploração ampla multi-lógica, ancorada na V2). ~12 lógicas de entrada CAUSAIS de trajetória (swept,
reclaim, double-bottom, rsi-turn, higher-low, ema-reclaim, deep-pull-bull, range-reject, capit-deep, compression-break,
regime-transition, momentum-div). Todas: entry no close da barra i, SL=swing-low recente−0.5ATR, exit let-run HZ120,
cooldown 5b. Painel (N/WR/sumR/avgR/DD/STREAK) + validação vs 200 draws random. Ranking. custo 0.35. Multi-lógica+trajetória+null."""
import json,io,contextlib,sys,bisect,random
from pathlib import Path
from statistics import mean
random.seed(20260701);COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;O=getattr(P,'O',C);n4=len(C)
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
def regime_at(bi):
    t=T[bi]
    for s in segs:
        if s['start']<=t<=s['end']: return s['regime']
    return '?'
# pré-computar
TR=[0.0]*n4
for i in range(1,n4): TR[i]=max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1]))
ATR=[0.0]*n4
for i in range(14,n4): ATR[i]=mean(TR[i-13:i+1])
def rsi(i,k=14):
    g=l=0
    for j in range(i-k+1,i+1):
        d=C[j]-C[j-1]
        if d>0:g+=d
        else:l-=d
    if g+l==0:return 50
    return 100-100/(1+(g/k)/((l/k) if l>0 else 1e-9))
EMA50=[C[0]]*n4;EMA20=[C[0]]*n4
for i in range(1,n4):
    EMA50[i]=EMA50[i-1]+(2/51)*(C[i]-EMA50[i-1]);EMA20[i]=EMA20[i-1]+(2/21)*(C[i]-EMA20[i-1])
def dpos(i,n):
    lo=min(L[i-n+1:i+1]);hi=max(H[i-n+1:i+1]);return (C[i]-lo)/(hi-lo) if hi>lo else .5
def SL(i): return min(L[max(0,i-4):i+1])-0.5*ATR[i]
def letrun(bi,entry,sl):
    if entry-sl<=0:return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl:return -1.0
    return (C[end]-entry)/(entry-sl)
# lógicas: cada é um predicado(i)->bool
def swept_reclaim(i): return L[i]<min(L[i-20:i]) and C[i]>C[i-1]
def double_bottom(i):
    lo=min(L[i-40:i-10]); return abs(L[i]-lo)<0.3*ATR[i] and C[i]>C[i-1] and dpos(i,40)<0.35
def rsi_turn(i):
    r0=rsi(i-1);r1=rsi(i);return r0<33 and r1>r0+2
def higher_low(i):
    return (max(H[i-20:i])-L[i])>3*ATR[i] and L[i]>L[i-2] and C[i]>C[i-1] and dpos(i,40)<0.4
def ema50_reclaim(i): return C[i-1]<EMA50[i-1] and C[i]>EMA50[i]
def deep_pull_bull(i): return regime_at(i)=='BULL' and dpos(i,40)<0.30 and C[i]>C[i-1]
def range_reject(i):
    return dpos(i,40)<0.25 and (H[i]-L[i])>0 and (C[i]-L[i])/(H[i]-L[i])>0.6
def capit_deep(i): return dpos(i,60)<0.15 and C[i]>C[i-1]
def compression(i):
    av=mean(ATR[i-20:i]); return ATR[i-1]<0.7*av and TR[i]>1.5*av and C[i]>C[i-1]
def regime_trans(i): return regime_at(i)=='BULL' and regime_at(i-1)!='BULL'
def momentum_div(i):
    return L[i]<min(L[i-10:i]) and (C[i]-C[i-5])>(C[i-5]-C[i-10]) and C[i]>C[i-1]
def ema20_pullback(i):
    return regime_at(i)=='BULL' and L[i]<=EMA20[i]<=H[i] and C[i]>EMA20[i] and C[i]>C[i-1]
LOGICS=[("swept_reclaim",swept_reclaim),("double_bottom",double_bottom),("rsi_turn",rsi_turn),
        ("higher_low",higher_low),("ema50_reclaim",ema50_reclaim),("deep_pull_bull",deep_pull_bull),
        ("range_reject",range_reject),("capit_deep",capit_deep),("compression",compression),
        ("regime_trans",regime_trans),("momentum_div",momentum_div),("ema20_pullback",ema20_pullback)]
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
def panel(ents):
    rs=[round(letrun(bi,e,sl)-COST,2) for bi,e,sl in ents if letrun(bi,e,sl) is not None]
    n=len(rs)
    if n==0: return None
    w=sum(1 for x in rs if x>0);s=sum(rs)
    cum=peak=dd=0;st=mx=0
    for x in rs:
        cum+=x;peak=max(peak,cum);dd=min(dd,cum-peak);st=st+1 if x<=0 else 0;mx=max(mx,st)
    return n,100*w/n,s,s/n,dd,mx,sum(1 for x in rs if x>=3)
def rand_p95(N):
    sums=[]
    for _ in range(150):
        bis=[random.randint(60,n4-HZ-1) for _ in range(N)]
        rs=[round(letrun(b,C[b],SL(b))-COST,2) for b in bis if C[b]-SL(b)>0 and letrun(b,C[b],SL(b)) is not None]
        sums.append(sum(rs))
    sums.sort();return sums[int(0.5*len(sums))],sums[int(0.95*len(sums))]
res=[]
for name,pred in LOGICS:
    ents=gen(pred);pa=panel(ents)
    if pa is None: continue
    n,wr,s,avg,dd,mx,big=pa;rmed,rp95=rand_p95(n)
    edge="EDGE" if s>rp95 else ("~rnd" if s<=rmed else "mid")
    res.append((name,n,wr,s,avg,dd,mx,big,rmed,rp95,edge))
res.sort(key=lambda x:-x[4])  # ranking por avgR
print(f"{'LÓGICA':16}{'N':>4}{'WR':>5}{'sumR':>8}{'avgR':>7}{'DD':>7}{'STRK':>5}{'big':>4}  {'rnd med/p95':>16} {'':>6}")
print(f"{'V2 (ref)':16}{17:>4}{53:>4}%{36.2:>8.1f}{2.13:>7.2f}{-4.1:>7.1f}{3:>5}{5:>4}  {'—':>16}")
for name,n,wr,s,avg,dd,mx,big,rmed,rp95,edge in res:
    print(f"{name:16}{n:>4}{wr:>4.0f}%{s:>8.1f}{avg:>7.2f}{dd:>7.1f}{mx:>5}{big:>4}  {rmed:>7.1f}/{rp95:>6.1f} {edge:>6}")
