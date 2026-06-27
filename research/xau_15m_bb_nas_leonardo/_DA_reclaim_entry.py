#!/usr/bin/env python3
"""DA DECISIVO (Cris thesis): large-SELL capitulation = bottom that bounces hard in DOLLARS.
Flush-low stop gives huge risk -> R-neutral. TEST: enter on RECLAIM (retest/CHoCH) with a TIGHTER stop
below the reclaim swing low, NOT the full flush. Does large-SELL THEN become a real positive-R edge?

CAUSALITY HARDENING vs prior scripts:
  - bubble count uses known_at<=entry_time (BigBeluga repaints ~1-2 bars; counting by t leaks future).
  - reclaim/stop levels only use bars at or before the bar that triggers entry.
  - entry at NEXT bar close after the reclaim trigger.

Reclaim defs:
  A) close back ABOVE flush_low + 0.25*ATR within W bars after the flush low.
  B) close ABOVE the HIGH of the flush bar (stronger reclaim).
  C) micro-CHoCH: close above the most recent micro swing-high formed during the flush/retrace.
Stop = below the lowest low since the flush low up to entry (the reclaim swing low) - 0.1*ATR (tight).
let-run trailing on swing lows. R capped 20. Per-year + per-block stability. 2026-06-26."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE=16*900; RCAP=20.0; HMAX=192; RECW=16   # reclaim must happen within 16 bars (4h) of the flush low

BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],key=lambda x:x["t"]) for k in PRIM}

def selL(bb,t,entry_t):
    """CAUSAL large-SELL count in [t-PRE,t], only bubbles KNOWN by entry_t."""
    return sum(1 for x in bb if t-PRE<=x["t"]<=t and x["side"]=="SELL" and x["size"]=="L" and x["known_at"]<=entry_t)

def cf_low(s,i):
    """most recent confirmed 5-bar fractal low strictly before bar i (look-back only)."""
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for q in range(lo,i-1):
        if L[q]==min(L[q-2:q+3]): bst=L[q]
    return bst

def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(96,len(s)-4) if L[p]==min(L[p-4:p+5])]

def find_reclaim(s,p,mode):
    """return entry bar index ei (enter at ei close) once reclaim triggers, else None.
    Only uses bars in (p, p+RECW]. Trigger bar = j; entry at j (close of trigger bar)."""
    atr=s[p]["atr"] or 1.0; flush_low=s[p]["l"]; flush_high=s[p]["h"]
    end=min(p+RECW,len(s)-1)
    # micro swing-high tracker for CHoCH: a bar whose high is local max over +-2 within (p,j)
    for j in range(p+1,end+1):
        c=s[j]["c"]
        if mode=="A":
            if c>=flush_low+0.25*atr: return j
        elif mode=="B":
            if c>flush_high: return j
        elif mode=="C":
            # micro-CHoCH: close above the highest high seen since the flush low (excluding current bar)
            if j>=p+3:
                prior_hi=max(s[q]["h"] for q in range(p+1,j))
                if c>prior_hi and c>flush_low+0.10*atr: return j
    return None

def sim_reclaim(s,p,mode):
    """enter at reclaim trigger bar close; stop = lowest low from flush_low..entry - 0.1*ATR (tight reclaim stop)."""
    atr=s[p]["atr"] or 1.0
    ei=find_reclaim(s,p,mode)
    if ei is None or ei+1>=len(s): return None
    entry=s[ei]["c"]
    swing_low=min(s[q]["l"] for q in range(p,ei+1))   # reclaim base, known at ei
    sl=swing_low-0.1*atr; risk=entry-sl
    if risk<=0: return None
    trail=sl; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        if s[i]["l"]<=trail: ex=trail; break
        if (s[i]["h"]-entry)/risk>=1: r1=True
        if r1:
            sw=cf_low(s,i)
            if sw: trail=max(trail,sw-0.1*atr)
    if ex is None: ex=s[end]["c"]
    return max(-1.0,min(RCAP,(ex-entry)/risk)),risk/atr

def sim_flush(s,p):
    """baseline: flush-low stop (the prior _DA_structural_R entry) for comparison, causal."""
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
    return max(-1.0,min(RCAP,(ex-entry)/risk)),risk/atr

def yr(t):
    import datetime; return datetime.datetime.utcfromtimestamp(t).year

def rep(v,lab):
    if len(v)<15: print(f"    {lab}: n={len(v)} (poucos)"); return
    n=len(v); sm=sum(x["R"] for x in v); wr=100*sum(1 for x in v if x["R"]>0)/n
    rr=st.mean([x["risk"] for x in v])
    print(f"    {lab}: n={n} avgR={sm/n:+.2f} sumR={sm:+.0f} WR={wr:.0f}% (avg risk={rr:.1f}ATR)")

# ---- collect for each mode ----
for mode,desc in [("A","reclaim: close>=flush_low+0.25ATR"),("B","reclaim: close>flush_bar_high"),("C","reclaim: micro-CHoCH")]:
    print(f"\n===== MODE {mode} ({desc}) =====")
    rows=[]
    for k,pr in PRIM.items():
        s=pr["series"]; bb=BUB[k]
        for p in fractal_lows(s):
            res=sim_reclaim(s,p,mode)
            if res is None: continue
            R,risk=res
            et=s[min(p+RECW,len(s)-1)]["t"]  # conservative known-by time (entry happens <=this)
            # use actual entry time for known_at: recompute ei
            ei=find_reclaim(s,p,mode); et=s[ei]["t"]
            sL=selL(bb,s[p]["t"],et)
            rows.append({"sL":sL,"R":R,"risk":risk,"yr":yr(s[p]["t"]),"blk":k})
    print(f"  total reclaim entries: {len(rows)} (fill rate vs {sum(len(fractal_lows(pr['series'])) for pr in PRIM.values())} lows)")
    print("  by large-SELL bucket:")
    for lo,hi,lab in [(0,1,"L-SELL=0"),(1,2,"L-SELL=1"),(2,99,"L-SELL>=2"),(3,99,"L-SELL>=3")]:
        sub=[x for x in rows if (lo<=x["sL"]<hi if hi!=99 else x["sL"]>=lo)]
        rep(sub,lab)
    # per-year stability for L-SELL>=2 vs L-SELL=0
    print("  per-YEAR  [L-SELL=0]  vs  [L-SELL>=2]:")
    for y in sorted(set(x["yr"] for x in rows)):
        z=[x for x in rows if x["yr"]==y and x["sL"]==0]; h=[x for x in rows if x["yr"]==y and x["sL"]>=2]
        zs=f"n={len(z)} avgR={st.mean([x['R'] for x in z]):+.2f}" if len(z)>=10 else f"n={len(z)}(few)"
        hs=f"n={len(h)} avgR={st.mean([x['R'] for x in h]):+.2f}" if len(h)>=5 else f"n={len(h)}(few)"
        print(f"    {y}:  L0 {zs}   |   L>=2 {hs}")
    # per-block stability for L-SELL>=2
    print("  per-BLOCK [L-SELL>=2]:")
    for k in PRIM:
        h=[x for x in rows if x["blk"]==k and x["sL"]>=2]
        if h: print(f"    {k[:21]}: n={len(h)} avgR={st.mean([x['R'] for x in h]):+.2f} sumR={sum(x['R'] for x in h):+.0f}")
