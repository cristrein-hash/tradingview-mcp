#!/usr/bin/env python3
"""Exporta os trades da célula Engine7 BULL+notop+RSI<30+vozes>=4 (Cris pediu plot). entry/SL/exit let-run. -> engine7_cell_trades.csv"""
import json,bisect,csv
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
allbars={}
for pr in PRIM.values():
    for b in pr["series"]: allbars.setdefault(b["t"],b)
days={}
for t in sorted(allbars):
    b=allbars[t]; k=t//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]+[max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])) for i in range(1,len(DK))]
def atrd(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(i,n):
    c=DC[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(i,50) for i in range(len(DK))]; E100=[ema_at(i,100) for i in range(len(DK))]
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5
def raw(i):
    if i<max(2*N,40): return "RANGE"
    a=atrd(i) or 1.0; slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); eff=abs(net)/path if path>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5; s100=(E100[i]-E100[i-10])/a
    tu=eff>=eff_thr and slope>slope_thr; td=eff>=eff_thr and slope<-slope_thr
    sb=E50[i]>E100[i] and s100>0; se=E50[i]<E100[i] and s100<0
    cont=eff<eff_thr and 0.15<=pos<=0.85 and abs(slope)<slope_thr
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a; lh=max(DH[i-N:i])<max(DH[i-2*N:i-N]); bef=DC[i]<E50[i] and (E50[i]-E50[i-5])<0; bl=DC[i]<min(DL[i-N:i-2])
    if (bl and bef) or (retreat>=R_thr and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"
    if tu or (sb and pos>0.55 and not cont): return "BULL"
    return "RANGE"
rl=[raw(i) for i in range(len(DK))]; reg=[]; cur="RANGE"; pend=None; pn=0
for v in rl:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    if pn>=(Kbear if pend=="BEAR" else K): cur=pend; pend=None; pn=0
    reg.append(cur)
DAYREG={DK[i]:reg[i] for i in range(len(DK))}
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def letrun(s,cj,entry,sl,atr):
    risk=entry-sl
    if risk<=0: return None,None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)),ex
def fnum(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
out=[]
for r in ROWS:
    pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None or cj+2>=len(s): continue
    if DAYREG.get(r["cj_t"]//86400,"RANGE")!="BULL": continue
    atr=s[p]["atr"] or s[cj]["atr"]
    if not atr: continue
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"]); nt=[e["t"] for e in nas]
    a=bisect.bisect_left(nt,s[max(0,p-16)]["t"]); b=bisect.bisect_right(nt,r["cj_t"])
    nas_short=sum(1 for e in nas[a:b] if e["dir"]=="SHORT")
    zs=[z for z in pr.get("zones",[]) if "SUPPLY" in str(z.get("text","")).upper()]; lo=s[p]["l"]
    in_supply=1 if any(z.get("born_t",1e18)<=r["cj_t"] and z["low"]-0.3*atr<=lo<=z["high"]+0.3*atr for z in zs) else 0
    top=(fnum(r,"buy_bub_w",0)>fnum(r,"sell_bub_w",0) and fnum(r,"buy_bub_w",0)>=4) or nas_short>=2 or fnum(r,"rsi_low",0)>70 or in_supply==1
    if top: continue
    voices=sum([fnum(r,"sell_bub_w",0)>=2, fnum(r,"nas_long_16",0)>=1, fnum(r,"rsi_low",50)<30, fnum(r,"in_demand",0)==1])
    if voices<4: continue
    entry=s[cj]["c"]; sl=min(x["l"] for x in s[p:cj+1])-0.1*atr; R,ex=letrun(s,cj,entry,sl,atr)
    if R is None: continue
    out.append({"cj_t":r["cj_t"],"entry":round(entry,2),"sl":round(sl,2),"exit":round(ex,2),"R":round(R,2),"win":int(R>0),"yr":r["yr"]})
out.sort(key=lambda x:x["cj_t"])
for n,o in enumerate(out,1): o["num"]=n
with open(HERE/"engine7_cell_trades.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["num","cj_t","entry","sl","exit","R","win","yr"]); w.writeheader()
    for o in out: w.writerow(o)
print(f"engine7_cell_trades.csv: {len(out)} trades | WR={100*sum(o['win'] for o in out)/len(out):.0f}% sumR={sum(o['R'] for o in out):+.1f}")
