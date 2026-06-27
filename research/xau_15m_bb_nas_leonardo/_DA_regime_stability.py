#!/usr/bin/env python3
"""DA task 3: is structural-R 'no edge for large-SELL' robust per-year/block, or does large-SELL help in some regime?
Regimes tested at the flush low (all causal, bar p):
  - uptrend: close(p) > ema21(p) AND ema21 rising over last 16 bars (dip in uptrend = best case for capitulation buy)
  - deep macro_drop>=10 / >=15 (extended leg = true capitulation)
  - RSI oversold (<30) at the low
Entry = flush-low stop (the disputed structural_R). CAUSAL known_at bubble count. R cap 20. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900; RCAP=20.0; HMAX=192
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
def selL(bb,t,entry_t):
    return sum(1 for x in bb if t-PRE<=x["t"]<=t and x["side"]=="SELL" and x["size"]=="L" and x["known_at"]<=entry_t)
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for q in range(lo,i-1):
        if L[q]==min(L[q-2:q+3]): bst=L[q]
    return bst
def sim_long(s,p):
    atr=s[p]["atr"] or 1.0; ei=p+1
    if ei+2>=len(s): return None
    entry=s[ei]["c"]; sl=s[p]["l"]-0.1*atr; risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if s[i]["l"]<=trail: ex=trail; break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk))
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(96,len(s)-4) if L[p]==min(L[p-4:p+5])]
rows=[]
for k,pr in PRIM.items():
    s=pr["series"]; bb=BUB[k]
    for p in fractal_lows(s):
        R=sim_long(s,p)
        if R is None: continue
        a=s[p]["atr"] or 1.0; lo=max(0,p-192); md=(max(b["h"] for b in s[lo:p+1])-s[p]["l"])/a
        e=s[p]["ema21"]; e16=s[p-16]["ema21"] if p>=16 else e
        up=(e is not None and s[p]["c"]>e and e16 is not None and e>e16)
        rsi=s[p]["rsi"]
        rows.append({"sL":selL(bb,s[p]["t"],s[p+1]["t"]),"R":R,"md":md,"up":up,"rsi":rsi})
def rep(v,lab):
    if len(v)<15: print(f"    {lab}: n={len(v)} (poucos)"); return
    n=len(v); sm=sum(x["R"] for x in v); wr=100*sum(1 for x in v if x["R"]>0)/n
    print(f"    {lab}: n={n} avgR={sm/n:+.2f} sumR={sm:+.0f} WR={wr:.0f}%")
print("=== REGIME: dip in confirmed UPTREND (close>ema21 & ema21 rising) ===")
sub=[x for x in rows if x["up"]]
print(f"  uptrend dips: {len(sub)}")
rep([x for x in sub if x["sL"]==0],"L-SELL=0"); rep([x for x in sub if x["sL"]>=2],"L-SELL>=2"); rep([x for x in sub if x["sL"]>=3],"L-SELL>=3")
print("=== REGIME: deep macro_drop>=15 (extreme capitulation leg) ===")
sub=[x for x in rows if x["md"]>=15]
rep([x for x in sub if x["sL"]==0],"L-SELL=0"); rep([x for x in sub if x["sL"]>=2],"L-SELL>=2")
print("=== REGIME: RSI<30 oversold at low ===")
sub=[x for x in rows if x["rsi"] is not None and x["rsi"]<30]
rep([x for x in sub if x["sL"]==0],"L-SELL=0"); rep([x for x in sub if x["sL"]>=2],"L-SELL>=2")
print("=== REGIME: uptrend AND macro_drop>=10 (dip-buy capitulation in trend) ===")
sub=[x for x in rows if x["up"] and x["md"]>=10]
rep([x for x in sub if x["sL"]==0],"L-SELL=0"); rep([x for x in sub if x["sL"]>=2],"L-SELL>=2")
import datetime
print("=== overall structural-R per-year (sanity, large-SELL>=2 vs L0) ===")
def yr(rw): return None
