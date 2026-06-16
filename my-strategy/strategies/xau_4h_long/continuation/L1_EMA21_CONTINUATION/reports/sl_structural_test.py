import sys, json
from pathlib import Path
from datetime import datetime, timezone
L1=Path("my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0,str(L1)); sys.path.insert(0,"my-strategy/core")
import scanner
S=scanner.build_series()
c34=json.load(open('/tmp/c34.json'))  # ids + et
def idx_of(et): 
    return S.idx.get(et) or min(range(S.N),key=lambda k:abs(S.T[k]-et))
items=[(z["id"], idx_of(z["et"])) for z in c34]

def walk(i, entry, sl, target, mx=60):
    if entry-sl<=0: return "BADSL",0.0
    for k in range(i+1,min(i+1+mx,S.N)):
        if S.L[k]<=sl: return "STOP",-1.0
        if S.H[k]>=target: return "TARGET",3.0
    e=min(i+mx,S.N-1); return "TIME",round((S.C[e]-entry)/(entry-sl),2)

def sl_rule(i, name):
    entry=S.C[i]; atr=S.ATR14[i] or 0; dz=scanner.demand_zone(S,i)
    zlo=(dz[1] if dz else S.EMA21[i-1])
    sw6=min(S.L[max(0,i-5):i+1]); sw10=min(S.L[max(0,i-9):i+1]); sw3=min(S.L[max(0,i-2):i+1])
    barlow=S.L[i]
    R={
      "v1_zone-0.1ATR": zlo-0.1*atr,
      "zone_exact": zlo,
      "zone-0.25ATR": zlo-0.25*atr,
      "zone-0.5ATR": zlo-0.5*atr,
      "swing6-0.1ATR": sw6-0.1*atr,
      "swing10-0.1ATR": sw10-0.1*atr,
      "swing3-0.1ATR": sw3-0.1*atr,
      "entrybar_low-0.1ATR": barlow-0.1*atr,
      "min(zone,swing6)-0.1ATR": min(zlo,sw6)-0.1*atr,
      "max(zone,swing6)-0.1ATR": max(zlo,sw6)-0.1*atr,
    }
    return R[name], atr
RULES=["v1_zone-0.1ATR","zone_exact","zone-0.25ATR","zone-0.5ATR","swing6-0.1ATR","swing10-0.1ATR","swing3-0.1ATR","entrybar_low-0.1ATR","min(zone,swing6)-0.1ATR","max(zone,swing6)-0.1ATR"]
print(f"{'SL rule':28} | n  T  S  TM  badSL | winrate% | sumR  | avgR  | PF")
res={}
for rule in RULES:
    out=[]
    for cid,i in items:
        entry=S.C[i]; sl,atr=sl_rule(i,rule); risk=entry-sl
        if risk<=0: out.append(("BADSL",0.0)); continue
        r,R=walk(i,entry,sl,entry+3*risk); out.append((r,R))
    T=sum(1 for r,_ in out if r=="TARGET");Sx=sum(1 for r,_ in out if r=="STOP")
    TM=sum(1 for r,_ in out if r=="TIME");bad=sum(1 for r,_ in out if r=="BADSL")
    sr=round(sum(R for _,R in out),1); n=len(out)
    pos=sum(R for _,R in out if R>0);neg=abs(sum(R for _,R in out if R<0))
    pf=round(pos/neg,2) if neg else None; wr=round(100*T/n)
    res[rule]=(n,T,Sx,TM,bad,wr,sr,round(sr/n,2),pf)
    print(f"{rule:28} | {n:2} {T:2} {Sx:2} {TM:2}  {bad:2}   |   {wr:3}    | {sr:5} | {round(sr/n,2):5} | {pf}")
