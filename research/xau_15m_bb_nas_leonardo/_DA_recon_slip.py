#!/usr/bin/env python3
"""DA: (1) is the dollar-bounce reconciliation a coding artifact? Gold drifted ~2400->4000 over the sample,
so corr(large-SELL, bounce$) could be a PRICE-LEVEL confound (later bars = higher price = bigger $ moves AND
maybe more L-SELL). Re-test with: (a) within-block de-meaned dollars, (b) % bounce, (c) ATR-normalized (already neg),
(d) detrend dollars by price level (bounce$/price). If the dollar edge survives de-trending it's real magnitude;
if it collapses it was a level artifact.
(2) slippage/gap realism on flush bars: how often does the NEXT bar OPEN gap below the intended entry (close of p+1)
or does the flush bar's range mean the reclaim fill is unrealistic? quantify gap at entry and at stop. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}
def selL(bb,t,entry_t):
    return sum(1 for x in bb if t-PRE<=x["t"]<=t and x["side"]=="SELL" and x["size"]=="L" and x["known_at"]<=entry_t)
def fwd_dollar(s,p):
    Lp=s[p]["l"]; end=min(p+96,len(s)-1); return max(s[i]["h"] for i in range(p+1,end+1))-Lp if end>p else 0
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(96,len(s)-4) if L[p]==min(L[p-4:p+5])]
def rank(xs):
    o=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0]*len(xs)
    for pos,i in enumerate(o): r[i]=pos
    return r
def pear(a,b):
    n=len(a);ma=sum(a)/n;mb=sum(b)/n;cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    va=sum((x-ma)**2 for x in a)**.5;vb=sum((x-mb)**2 for x in b)**.5;return cov/(va*vb) if va*vb else 0
def spear(a,b): return pear(rank(a),rank(b))

sL=[];b_usd=[];b_pct=[];b_usd_dt=[];price=[];atrs=[]
for k,pr in PRIM.items():
    s=pr["series"]; bb=BUB[k]
    for p in fractal_lows(s):
        if p+1>=len(s): continue
        a=s[p]["atr"] or 1.0; d=fwd_dollar(s,p); pl=s[p]["l"]
        sL.append(selL(bb,s[p]["t"],s[p+1]["t"])); b_usd.append(d); b_pct.append(d/pl); b_usd_dt.append(d/pl*100)
        price.append(pl); atrs.append(a)
n=len(sL)
print(f"n={n} (CAUSAL known_at bubble count)")
print(f"corr(large-SELL, bounce DÓLAR raw) = {spear(sL,b_usd):+.3f}")
print(f"corr(large-SELL, bounce %)         = {spear(sL,b_pct):+.3f}  <- detrended for price level")
print(f"corr(large-SELL, price level)      = {spear(sL,price):+.3f}  <- if high: $ corr is level-confounded")
print(f"corr(price level, bounce DÓLAR)    = {spear(price,b_usd):+.3f}  <- mechanical: higher price=bigger $")
print(f"corr(large-SELL, ATR)              = {spear(sL,atrs):+.3f}")
# partial: corr(sL, bounce$) controlling price -> use % which removes level. Already shown. Also bucket means in %:
hi=[b_pct[i]*100 for i in range(n) if sL[i]>=2]; lo=[b_pct[i]*100 for i in range(n) if sL[i]==0]
print(f"  bounce % : L-SELL>=2 ={st.mean(hi):.2f}% vs L-SELL=0 ={st.mean(lo):.2f}%  (Δ={st.mean(hi)-st.mean(lo):+.2f}pp)")
hi=[b_usd[i] for i in range(n) if sL[i]>=2]; lo=[b_usd[i] for i in range(n) if sL[i]==0]
print(f"  bounce $ : L-SELL>=2 ={st.mean(hi):.1f} vs L-SELL=0 ={st.mean(lo):.1f}")

print("\n--- SLIPPAGE / GAP realism at flush lows ---")
# at entry bar (p+1): does open differ a lot from prior close? and does flush bar have huge range (illiquid fill)?
gap_entry=[];flush_range_atr=[];entry_vs_low=[]
for k,pr in PRIM.items():
    s=pr["series"]; bb=BUB[k]
    for p in fractal_lows(s):
        if p+2>=len(s): continue
        a=s[p]["atr"] or 1.0
        sl=selL(bb,s[p]["t"],s[p+1]["t"])
        if sl<2: continue   # only large-SELL flushes (where execution risk is worst)
        g=abs(s[p+1]["o"]-s[p]["c"])/a
        gap_entry.append(g)
        flush_range_atr.append((s[p]["h"]-s[p]["l"])/a)
        entry_vs_low.append((s[p+1]["c"]-s[p]["l"])/a)
if gap_entry:
    print(f"  large-SELL flushes n={len(gap_entry)}")
    print(f"  gap |open(p+1)-close(p)| : median={st.median(gap_entry):.2f}ATR  p90={sorted(gap_entry)[int(0.9*len(gap_entry))]:.2f}ATR")
    print(f"  flush bar range          : median={st.median(flush_range_atr):.2f}ATR  p90={sorted(flush_range_atr)[int(0.9*len(flush_range_atr))]:.2f}ATR")
    print(f"  entry(close p+1)-flush_low: median={st.median(entry_vs_low):.2f}ATR (how far above the low we buy)")
    print("  -> if gaps & ranges are large, real fills/stops slip; flush-low stop especially is optimistic.")
