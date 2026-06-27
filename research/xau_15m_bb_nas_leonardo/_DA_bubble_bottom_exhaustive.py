#!/usr/bin/env python3
"""ADVERSARIAL exhaustive attack on the bubble-bottom thesis (XAU 15M).
GOAL: find ANY bubble-derived feature whose DOWN-LEG-CONTROLLED correlation with the
FORWARD rally (fwd_rev) is POSITIVE and robust (consistent sign across 4 down-leg buckets
AND across the 8 blocks). Lead found all naive SELL-cluster features negative.

New angles the lead did NOT fully test:
  A. ABSORPTION: large SELL bubbles where price HOLDS (close in upper half of bar, or
     next-bar reclaims, or net-flat despite selling). "heavy sell, price holds".
  B. EXHAUSTION/FLIP: escalating sell then stop; final big SELL then big BUY flip.
  C. SELL DECAY: sell pressure climaxing then drying up into the low.
  D. BUY-at-low: large BUY bubbles in last few bars (aggressive buyers stepping in).
  E. CONTEXT ratios: heavy-sell-fraction only when down_leg large (capitulation), or by RSI.
  F. bar-position / net order-flow imbalance with large weighting + quantity thresholds.
  G. NAS-LONG timing (NAS LONG AFTER the sell climax).

Causality: only bubbles with known_at <= low-bar close-time are usable. We use the bubble's
own o/h/l/c (the bar it printed on). fwd_rev = forward upside excursion before price breaches
the low by 0.25 ATR (same as lead). RAW-causal.
"""
import json,bisect,glob,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE_BARS=16; BAR=900; PRE=PRE_BARS*BAR; K=4; HOR=192; BUF=0.25
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],
              key=lambda x:x["t"]) for k in PRIM}
NAS={k:sorted([e for e in PRIM[k]["nas_events"] if e.get("t") and e.get("dir")],key=lambda x:x["t"]) for k in PRIM}

def window_bubbles(key,t):
    """All bubbles in (t-PRE, t] that are CAUSALLY known by the low's bar close-time.
    The low's bar closes at t+BAR; a bubble printed on bar t is known_at ~ t+BAR. So a bubble
    on the low bar itself IS allowed (known by the time we'd act AFTER the low confirms).
    But to be strict we require known_at <= t+BAR (bubble printed on or before the low bar)."""
    bb=BUB[key]; ts=[x["t"] for x in bb]
    a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t)
    cutoff=t+BAR
    return [x for x in bb[a:b] if x["known_at"]<=cutoff]

def fwd_rev(s,p):
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; ext=Lp; end=min(p+HOR,len(s)-1)
    for i in range(p+1,end+1):
        if s[i]["l"]<Lp-BUF*a: break
        ext=max(ext,s[i]["h"])
    return (ext-Lp)/a

def fractal_lows(s):
    L=[x["l"] for x in s]
    return [p for p in range(max(K,PRE_BARS),len(s)-K) if L[p]==min(L[p-K:p+K+1])]

def rank(xs):
    order=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0.0]*len(xs)
    i=0
    while i<len(order):
        j=i
        while j+1<len(order) and xs[order[j+1]]==xs[order[i]]: j+=1
        avg=(i+j)/2.0
        for k2 in range(i,j+1): r[order[k2]]=avg
        i=j+1
    return r
def pearson(a,b):
    n=len(a)
    if n<3: return 0.0
    ma=sum(a)/n; mb=sum(b)/n
    cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    va=sum((x-ma)**2 for x in a)**.5; vb=sum((x-mb)**2 for x in b)**.5
    return cov/(va*vb) if va*vb else 0.0
def spearman(a,b): return pearson(rank(a),rank(b))

# ---- collect candidate lows with rich feature dict ----
data=[]  # each: dict of raw counts + derived + fwd + dl + block
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        t=s[p]["t"]; a=s[p]["atr"] or 1.0
        wb=window_bubbles(k,t)
        Lp=s[p]["l"]
        # bucket bubbles
        c={"sS":0,"sM":0,"sL":0,"bS":0,"bM":0,"bL":0}
        sells=[]; buys=[]
        for x in wb:
            sd=("s" if x["side"]=="SELL" else "b")
            c[sd+x["size"]]+=1
            (sells if sd=="s" else buys).append(x)
        # --- ABSORPTION features (A) ---
        # close-position of each SELL bar: (c-l)/(h-l); high => bar closed strong despite sell
        def cpos(x):
            rng=(x["h"]-x["l"]) or 1e-9; return (x["c"]-x["l"])/rng
        # absorbed large sells: L-SELL whose close is in upper half of its bar
        absorb_sL=sum(1 for x in sells if x["size"]=="L" and cpos(x)>=0.5)
        absorb_sAll=sum(1 for x in sells if cpos(x)>=0.5)
        # weighted absorption: large weighted heavily
        w={"S":1,"M":3,"L":10}
        absorb_w=sum(w[x["size"]]*cpos(x) for x in sells)
        sell_w_tot=sum(w[x["size"]] for x in sells)+1e-9
        absorb_frac=absorb_w/sell_w_tot   # avg close-position weighted by sell size
        # net-flat despite sell: total sell weight high but price near top of its own bar
        # last (most recent) sell bubble close-position
        last_sell_cpos=cpos(sells[-1]) if sells else 0.5
        # --- EXHAUSTION/FLIP (B) ---
        # final large SELL then a BUY after it (within window, later t)
        flip=0
        if sells:
            last_sL_t=max((x["t"] for x in sells if x["size"]=="L"),default=None)
            if last_sL_t is not None:
                flip=1 if any(b2["t"]>last_sL_t for b2 in buys) else 0
        flip_big=0
        if sells:
            last_sL_t=max((x["t"] for x in sells if x["size"]=="L"),default=None)
            if last_sL_t is not None:
                flip_big=1 if any(b2["t"]>last_sL_t and b2["size"] in("M","L") for b2 in buys) else 0
        # escalating then stop: sells in first half of window, none in last 4 bars
        recent_cut=t-4*BAR
        sell_recent=sum(1 for x in sells if x["t"]>recent_cut)
        sell_early=len(sells)-sell_recent
        decay=sell_early-sell_recent  # positive => climaxed early then dried up
        decay_w=sum(w[x["size"]] for x in sells if x["t"]<=recent_cut)-sum(w[x["size"]] for x in sells if x["t"]>recent_cut)
        # --- BUY-at-low (D) ---
        buy_recent_L=sum(1 for x in buys if x["t"]>recent_cut and x["size"]=="L")
        buy_recent_w=sum(w[x["size"]] for x in buys if x["t"]>recent_cut)
        buy_at_low_any=sum(1 for x in buys if x["t"]>recent_cut)
        # --- NAS-LONG timing (G) ---
        ne=NAS[k]; nt=[e["t"] for e in ne]
        i=bisect.bisect_left(nt,t-PRE); j=bisect.bisect_right(nt,t)
        nas_long=sum(1 for e in ne[i:j] if e["dir"]=="LONG")
        # NAS LONG after last big sell
        nas_long_after=0
        if sells:
            last_sL_t=max((x["t"] for x in sells if x["size"]=="L"),default=None)
            if last_sL_t is not None:
                nas_long_after=sum(1 for e in ne[i:j] if e["dir"]=="LONG" and e["t"]>last_sL_t)
        # --- context ---
        rsi=s[p].get("rsi") or 50
        dl=(s[p-PRE_BARS]["c"]-Lp)/a
        rec=dict(c)
        rec.update(dict(
            absorb_sL=absorb_sL,absorb_sAll=absorb_sAll,absorb_frac=absorb_frac,
            last_sell_cpos=last_sell_cpos,flip=flip,flip_big=flip_big,
            decay=decay,decay_w=decay_w,buy_recent_L=buy_recent_L,buy_recent_w=buy_recent_w,
            buy_at_low_any=buy_at_low_any,nas_long=nas_long,nas_long_after=nas_long_after,
            rsi=rsi,dl=dl,fwd=fwd_rev(s,p),block=k,
            n_sell=len(sells),n_buy=len(buys),sell_w=sell_w_tot,
        ))
        data.append(rec)
n=len(data); print(f"fractal lows: {n}")

# ---- feature definitions (the adversarial battery) ----
def feats(c):
    sS,sM,sL,bS,bM,bL=c["sS"],c["sM"],c["sL"],c["bS"],c["bM"],c["bL"]
    F={}
    # A absorption
    F["A_absorb_sL"]=c["absorb_sL"]
    F["A_absorb_sAll"]=c["absorb_sAll"]
    F["A_absorb_frac"]=c["absorb_frac"]
    F["A_last_sell_cpos"]=c["last_sell_cpos"]
    F["A_heavySell_x_holds"]=(sM+5*sL)*c["absorb_frac"]   # heavy sell AND price holds
    F["A_absorb_minus_pierce"]=c["absorb_sAll"]-(c["n_sell"]-c["absorb_sAll"])
    F["A_absorb_only_if_heavy"]=c["absorb_frac"] if (sM+sL)>=2 else 0.0
    # B exhaustion/flip
    F["B_flip"]=float(c["flip"])
    F["B_flip_big"]=float(c["flip_big"])
    F["B_flip_x_heavysell"]=c["flip_big"]*(sM+5*sL)
    # C decay
    F["C_decay"]=float(c["decay"])
    F["C_decay_w"]=float(c["decay_w"])
    F["C_decay_if_climax"]=float(c["decay_w"]) if (sM+sL)>=2 else 0.0
    # D buy-at-low
    F["D_buy_recent_L"]=float(c["buy_recent_L"])
    F["D_buy_recent_w"]=float(c["buy_recent_w"])
    F["D_buy_at_low_any"]=float(c["buy_at_low_any"])
    F["D_buyL_minus_sellL"]=float(bL-sL)
    F["D_buyrecent_minus_sellrecent"]=float(c["buy_recent_w"]-c["decay_w"] if False else c["buy_recent_w"])
    # E context ratios
    F["E_heavysellfrac_if_bigdl"]=((sM+5*sL)/(c["sell_w"])) if c["dl"]>3 else 0.0
    F["E_sellL_if_oversold"]=float(sL) if c["rsi"]<35 else 0.0
    F["E_absorb_if_oversold"]=c["absorb_frac"] if c["rsi"]<35 else 0.0
    # F net flow with quantity threshold + large weighting
    F["F_netflow_w"]=(bS+3*bM+10*bL)-(sS+3*sM+10*sL)
    F["F_netflow_if_ge2L"]=((bS+3*bM+10*bL)-(sS+3*sM+10*sL)) if (sL+bL)>=2 else 0.0
    F["F_buyw_div_sellw"]=(bS+3*bM+10*bL)/(sS+3*sM+10*sL+1)
    # G nas timing
    F["G_nas_long_after"]=float(c["nas_long_after"])
    F["G_nas_long_after_x_heavysell"]=c["nas_long_after"]*(sM+5*sL)
    F["G_nas_long_x_absorb"]=c["nas_long"]*c["absorb_frac"]
    return F

names=list(feats(data[0]).keys())
fwd=[c["fwd"] for c in data]; dls=[c["dl"] for c in data]
qs=sorted(dls); q=[qs[int(0.25*n)],qs[int(0.5*n)],qs[int(0.75*n)]]
def bucket(dl): return 0 if dl<q[0] else 1 if dl<q[1] else 2 if dl<q[2] else 3
bidx=[[] for _ in range(4)]
for i,c in enumerate(data): bidx[bucket(c["dl"])].append(i)
blocks=sorted(set(c["block"] for c in data))
binx={b:[i for i,c in enumerate(data) if c["block"]==b] for b in blocks}

allF={f:[feats(c)[f] for c in data] for f in names}
print(f"\n{'feature':<28} raw     ctrl(4bkt)  bkt_signs        nblk+  worst_blk")
res=[]
for f in names:
    v=allF[f]
    raw=spearman(v,fwd)
    bkt=[]
    for bi in bidx:
        if len(bi)>30: bkt.append(spearman([v[i] for i in bi],[fwd[i] for i in bi]))
    ctrl=sum(bkt)/len(bkt) if bkt else 0
    signs="".join("+" if x>0 else "-" for x in bkt)
    # per-block raw corr (within-block, controls for regime/period drift)
    blkc=[]
    for b in blocks:
        idx=binx[b]
        if len(idx)>40 and len(set(v[i] for i in idx))>1:
            blkc.append(spearman([v[i] for i in idx],[fwd[i] for i in idx]))
    npos=sum(1 for x in blkc if x>0)
    worst=min(blkc) if blkc else 0
    res.append((f,raw,ctrl,signs,npos,len(blkc),worst,bkt))
res.sort(key=lambda x:-x[2])
for f,raw,ctrl,signs,npos,nblk,worst,bkt in res:
    flag=""
    if ctrl>0.06 and signs.count("+")>=3 and npos>=nblk*0.6: flag="  <== CANDIDATE"
    elif ctrl>0.04: flag="  (hint)"
    print(f"  {f:<26} {raw:+.3f}  {ctrl:+.3f}     {signs:<6} {npos}/{nblk}    {worst:+.3f}{flag}")
print("\nCANDIDATE = ctrl>0.06 AND >=3/4 buckets positive AND >=60% blocks positive.")
print("Per-bucket ctrl corr for top-3:")
for f,raw,ctrl,signs,npos,nblk,worst,bkt in res[:3]:
    print(f"  {f}: buckets={['%+.3f'%x for x in bkt]}")
