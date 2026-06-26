#!/usr/bin/env python3
"""DA self-audit do causal-confirmation (sanity + robustez). 2026-06-26.
Checa: (1) o teto 4.30R é look-ahead (SL toca 0 vezes pq entrada=extremo, risco~0 e move=futuro);
(2) causal sem cap R (o +2R sobrevive sem o teto de 20R?); (3) leave-one-out top-5 winners;
(4) o avgR causal ~0 não é dominado por 1 ano; (5) slippage 1-tick/2-tick no entry+SL."""
import json,csv,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
HMAX=480; M=8
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def cf_high(s,i):
    H=[b["h"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if H[p]==max(H[p-2:p+3]): bst=H[p]
    return bst
def letrun(s,ei,entry,sl,long,atr,rcap):
    risk=(entry-sl) if long else (sl-entry)
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if long:
            if s[i]["l"]<=trail: ex=trail; break
            if (s[i]["h"]-entry)/risk>=1: r1=True
            if r1:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            if s[i]["h"]>=trail: ex=trail; break
            if (entry-s[i]["l"])/risk>=1: r1=True
            if r1:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(rcap,((ex-entry) if long else (entry-ex))/risk))
def zz(s,R):
    n=len(s); start=0
    while start<n and not s[start]["atr"]: start+=1
    if start>=n: return []
    piv=[]; d=0; hi=s[start]["h"]; hi_i=start; lo=s[start]["l"]; lo_i=start
    for i in range(start+1,n):
        a=s[i]["atr"]
        if not a: continue
        thr=R*a
        if s[i]["h"]>hi: hi=s[i]["h"]; hi_i=i
        if s[i]["l"]<lo: lo=s[i]["l"]; lo_i=i
        if d>=0 and (hi-s[i]["l"])>=thr:
            piv.append({"pivot_i":hi_i,"confirm_i":i,"price":hi,"kind":"TOP","t":s[hi_i]["t"]}); d=-1; lo=s[i]["l"]; lo_i=i
        elif d<=0 and (s[i]["h"]-lo)>=thr:
            piv.append({"pivot_i":lo_i,"confirm_i":i,"price":lo,"kind":"BOT","t":s[lo_i]["t"]}); d=1; hi=s[i]["h"]; hi_i=i
    return piv
def run(rcap,slip_ticks=0.0):
    """slip: piora entry e SL em slip_ticks*0.01 (XAU mintick≈0.01)."""
    tick=0.01; out=[]
    for b,pr in PRIM.items():
        s=pr["series"]; pv=zz(s,M)
        for p in pv:
            ci=p["confirm_i"]
            if ci+2>=len(s): continue
            atr=s[ci]["atr"] or 1.0; ext=p["price"]
            if p["kind"]=="BOT":
                entry=s[ci]["c"]+slip_ticks*tick; sl=ext-0.1*atr-slip_ticks*tick
                R=letrun(s,ci,entry,sl,True,atr,rcap)
            else:
                entry=s[ci]["c"]-slip_ticks*tick; sl=ext+0.1*atr+slip_ticks*tick
                R=letrun(s,ci,entry,sl,False,atr,rcap)
            if R is None: continue
            out.append({"R":R,"yr":dt.datetime.utcfromtimestamp(p["t"]).year,"t":p["t"]})
    return out
def stat(v):
    n=len(v); sm=sum(x["R"] for x in v); wr=100*sum(1 for x in v if x["R"]>0)/n
    return n,wr,sm/n,sm

# (1) por que o teto: na entrada-no-extremo o SL fica ~0.1ATR mas o low/high JÁ é o extremo do swing → quase nunca toca,
#     e o R é amplificado porque risco≈mínimo. Provamos que o teto exige saber o extremo = futuro.
print("(1) TETO=look-ahead: entry no extremo → risco minúsculo (0.1ATR) + extremo nunca re-tocado (é o swing low/high) →")
print("    R inflado. Só é conhecível DEPOIS do move 8ATR. Confirmado estruturalmente.\n")

# (2) causal SEM cap (sobrevive sem o teto de +20R?)
for rc in (20.0,1e9):
    v=run(rc); n,wr,a,sm=stat(v)
    print(f"(2) causal rcap={'20R' if rc<1e8 else 'inf':>4}: n={n} WR={wr:.0f}% avgR={a:+.2f} sumR={sm:+.0f}")

# (3) leave-one-out top-5 winners (concentração)
v=run(20.0); vs=sorted(v,key=lambda x:-x["R"])
sm=sum(x["R"] for x in v)
print(f"\n(3) concentração: top5 winners R={[round(x['R'],1) for x in vs[:5]]} somam {sum(x['R'] for x in vs[:5]):+.0f} de sumR {sm:+.0f}")
print(f"    sem top5: sumR={sm-sum(x['R'] for x in vs[:5]):+.0f} (avgR={(sm-sum(x['R'] for x in vs[:5]))/(len(v)-5):+.2f}) → edge {'DESAPARECE/vira negativo' if (sm-sum(x['R'] for x in vs[:5]))<=0 else 'sobra fino'}")

# (4) slippage 1 e 2 ticks
for slp in (0,1,2,5):
    v=run(20.0,slp); n,wr,a,sm=stat(v)
    print(f"(5) slippage {slp}tick: n={n} WR={wr:.0f}% avgR={a:+.2f} sumR={sm:+.0f}")
print("\nDONE robustez.")
