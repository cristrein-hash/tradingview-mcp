#!/usr/bin/env python3
"""DA ENGINE 8 — realism / look-ahead audit.
 Q3: SHORT stream wide-stop distribution + slippage stress + no-knife-gate fragility.
 Q4: regime gate causality — regime_at(t) uses the SAME calendar day as the intraday entry.
     The daily bar for that day is NOT closed at intraday entry time -> same-day daily look-ahead.
     Test: shift regime to PRIOR day (regime_at(t-1d)) and re-measure combo. If result collapses, gate was peeking.
 SHORT stop-width in R-units (risk vs atr) + slippage on R.
"""
import json,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
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
DAYIDX={DK[i]:i for i in range(len(DK))}
REG_SAME={DK[i]:reg[i] for i in range(len(DK))}   # engine8 behaviour: same calendar day
REG_PREV={DK[i]:reg[i-1] if i>0 else "RANGE" for i in range(len(DK))}  # causal: prior closed day
def regime_same(t): return REG_SAME.get(t//86400,"RANGE")
def regime_prev(t): return REG_PREV.get(t//86400,"RANGE")
HMAX=480; RCAP=20.0
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def cf_high(s,i):
    Hh=[b["h"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if Hh[p]==max(Hh[p-2:p+3]): bst=Hh[p]
    return bst
def letrun_long(s,cj,entry,sl,atr,slip=0.0):
    risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["l"]<=trail: ex=trail; break
        if (s[k]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,((ex-entry)-slip)/risk)),risk,atr
def letrun_short(s,cj,entry,sl,atr,slip=0.0):
    risk=sl-entry
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(cj+HMAX,len(s)-1)
    for k in range(cj+1,end+1):
        if s[k]["h"]>=trail: ex=trail; break
        if (entry-s[k]["l"])/risk>=1: r1=True
        if r1:
            sw=cf_high(s,k)
            if sw: trail=min(trail,sw+0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,((entry-ex)-slip)/risk)),risk,atr
def f(r,k,d=None):
    v=r.get(k); return v if isinstance(v,(int,float)) and not isinstance(v,bool) else d
ROWS=[json.loads(l) for l in (HERE/"entry_candidates_htf.jsonl").read_text().splitlines()]
def knife_v2(r):
    a=f(r,"buy_bub_w",0)>=8 and f(r,"buy_bub_w",0)>f(r,"sell_bub_w",0)
    b=(f(r,"downleg_eff",0)>=0.45 and f(r,"atr_regime",1)>1.2 and f(r,"reclaim_atr",9)<1.0 and f(r,"up_closes_pc",9)<=1
       and (f(r,"sell_bub_w",0)<8 or f(r,"htf_demand_any",0)==0 or f(r,"swept_prior_low",0)==0))
    return a or b
# build longs/shorts with risk and atr tracked, plus slippage variant
def build(slip=0.0):
    longs=[]
    for r in ROWS:
        pr=PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
        p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
        if p is None or cj is None or cj+2>=len(s) or knife_v2(r): continue
        atr=s[p]["atr"] or s[cj]["atr"]
        if not atr: continue
        res=letrun_long(s,cj,s[cj]["c"],min(x["l"] for x in s[p:cj+1])-0.1*atr,atr,slip)
        if res is None: continue
        R,risk,a=res
        longs.append({"t":r["cj_t"],"R":R,"risk":risk,"atr":a,"yr":r["yr"]})
    shorts=[]
    for bkey,pr in PRIMK.items():
        s=pr["series"]; nn=len(s); Hh=[b["h"] for b in s]; last=-99
        for p in range(96,nn-4):
            if Hh[p]!=max(Hh[p-3:p+4]): continue
            cj=p+3
            if cj>=nn-2 or cj-last<3: continue
            atr=s[p]["atr"]
            if not atr: continue
            last=cj; entry=s[cj]["c"]; sl=max(x["h"] for x in s[p:cj+1])+0.1*atr
            res=letrun_short(s,cj,entry,sl,atr,slip)
            if res is None: continue
            R,risk,a=res
            shorts.append({"t":s[cj]["t"],"R":R,"risk":risk,"atr":a,"yr":dt.datetime.utcfromtimestamp(s[cj]["t"]).year})
    return longs,shorts
longs,shorts=build(0.0)
def sumR(rows): return round(sum(x["R"] for x in rows),1)
def py(rows): return {y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}

print("="*100)
print("Q3 — SHORT stop-width distribution (risk / atr) — wide-stop fragility")
rr=[x["risk"]/x["atr"] for x in shorts if x["atr"]>0]
rr.sort()
print(f"  short risk/atr: median={st.median(rr):.2f}  p75={rr[int(.75*len(rr))]:.2f}  p90={rr[int(.90*len(rr))]:.2f}  max={max(rr):.2f}")
print(f"  shorts with stop > 3 ATR: {100*sum(1 for x in rr if x>3)/len(rr):.0f}%  ; > 5 ATR: {100*sum(1 for x in rr if x>5)/len(rr):.0f}%")
ll=[x["risk"]/x["atr"] for x in longs if x["atr"]>0]; ll.sort()
print(f"  long  risk/atr: median={st.median(ll):.2f}  p90={ll[int(.90*len(ll))]:.2f}  max={max(ll):.2f}")

print("="*100)
print("Q3 — slippage stress on COMBO (per-side $ slip applied to entry+exit)")
for slip in (0.0,0.10,0.25,0.50):
    lo,sh=build(slip)
    L_br=[x for x in lo if regime_same(x["t"]) in ("BULL","RANGE")]
    S_b=[x for x in sh if regime_same(x["t"])=="BEAR"]
    cmb=L_br+S_b
    print(f"  slip=${slip:<5} COMBO sumR={sumR(cmb):+7.1f}  short-in-bear sumR={sumR(S_b):+6.1f}  yr {py(cmb)}")

print("="*100)
print("Q4 — REGIME GATE CAUSALITY: same-calendar-day vs prior-closed-day")
# engine8 uses regime_at(cj_t) = same calendar day. The daily bar of that day is not closed intraday.
L_br_same=[x for x in longs if regime_same(x["t"]) in ("BULL","RANGE")]
S_b_same=[x for x in shorts if regime_same(x["t"])=="BEAR"]
cmb_same=L_br_same+S_b_same
L_br_prev=[x for x in longs if regime_prev(x["t"]) in ("BULL","RANGE")]
S_b_prev=[x for x in shorts if regime_prev(x["t"])=="BEAR"]
cmb_prev=L_br_prev+S_b_prev
print(f"  SAME-day gate (engine8): COMBO n={len(cmb_same)} sumR={sumR(cmb_same):+.1f} yr {py(cmb_same)}")
print(f"  PREV-day gate (causal) : COMBO n={len(cmb_prev)} sumR={sumR(cmb_prev):+.1f} yr {py(cmb_prev)}")
print(f"  short-in-bear SAME n={len(S_b_same)} sumR={sumR(S_b_same):+.1f} | PREV n={len(S_b_prev)} sumR={sumR(S_b_prev):+.1f}")
# how many trades flip regime label between same and prev day?
flips=sum(1 for x in longs+shorts if regime_same(x["t"])!=regime_prev(x["t"]))
print(f"  trades whose regime label differs same-vs-prev day: {flips}/{len(longs)+len(shorts)}")
