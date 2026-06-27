#!/usr/bin/env python3
"""Deepen the ONLY positive lead from the exhaustive battery: BUY bubbles near the low
(D-family). Tighten timing windows, test as binary gates (group-Delta in fwd_rev), check
robustness per down-leg bucket AND per block/year. Also run the TOPS mirror (BUY-cluster
predicting forward DROP). RAW-causal."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE_BARS=16; BAR=900; K=4; HOR=192; BUF=0.25; PRE=PRE_BARS*BAR
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],
              key=lambda x:x["t"]) for k in PRIM}
def win(key,t,nback):
    bb=BUB[key]; ts=[x["t"] for x in bb]
    a=bisect.bisect_left(ts,t-nback*BAR); b=bisect.bisect_right(ts,t); cut=t+BAR
    return [x for x in bb[a:b] if x["known_at"]<=cut]
def fwd_rev(s,p):
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; ext=Lp; end=min(p+HOR,len(s)-1)
    for i in range(p+1,end+1):
        if s[i]["l"]<Lp-BUF*a: break
        ext=max(ext,s[i]["h"])
    return (ext-Lp)/a
def fwd_drop(s,p):  # for tops: downside excursion before breaching high by 0.25atr
    Hp=s[p]["h"]; a=s[p]["atr"] or 1.0; ext=Hp; end=min(p+HOR,len(s)-1)
    for i in range(p+1,end+1):
        if s[i]["h"]>Hp+BUF*a: break
        ext=min(ext,s[i]["l"])
    return (Hp-ext)/a
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(max(K,PRE_BARS),len(s)-K) if L[p]==min(L[p-K:p+K+1])]
def fractal_highs(s):
    H=[x["h"] for x in s]; return [p for p in range(max(K,PRE_BARS),len(s)-K) if H[p]==max(H[p-K:p+K+1])]
def rank(xs):
    order=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0.0]*len(xs); i=0
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
    ma=sum(a)/n; mb=sum(b)/n; cov=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    va=sum((x-ma)**2 for x in a)**.5; vb=sum((x-mb)**2 for x in b)**.5
    return cov/(va*vb) if va*vb else 0.0
def spearman(a,b): return pearson(rank(a),rank(b))

w={"S":1,"M":3,"L":10}
# ===== BOTTOMS: BUY-at-low across timing windows =====
print("="*70); print("BOTTOMS: BUY bubbles near the low — timing-window sweep")
print("="*70)
for nback in (2,3,4,6,8):
    data=[]
    for k,pr in PRIM.items():
        s=pr["series"]
        for p in fractal_lows(s):
            t=s[p]["t"]; a=s[p]["atr"] or 1.0
            wb=win(k,t,nback)
            buy_w=sum(w[x["size"]] for x in wb if x["side"]=="BUY")
            buy_L=sum(1 for x in wb if x["side"]=="BUY" and x["size"]=="L")
            dl=(s[p-PRE_BARS]["c"]-s[p]["l"])/a
            data.append((buy_w,buy_L,dl,fwd_rev(s,p),k))
    n=len(data); fwd=[d[3] for d in data]; dls=[d[2] for d in data]
    qs=sorted(dls); q=[qs[int(0.25*n)],qs[int(0.5*n)],qs[int(0.75*n)]]
    def bk(dl): return 0 if dl<q[0] else 1 if dl<q[1] else 2 if dl<q[2] else 3
    bidx=[[] for _ in range(4)]
    for i,d in enumerate(data): bidx[bk(d[2])].append(i)
    for fi,fn in [(0,"buy_w"),(1,"buy_L>=1 gate")]:
        if fi==1:
            v=[1.0 if d[1]>=1 else 0.0 for d in data]
        else:
            v=[float(d[0]) for d in data]
        ctrl=[]
        for bi in bidx:
            if len(bi)>30: ctrl.append(spearman([v[i] for i in bi],[fwd[i] for i in bi]))
        # group-Delta for gate: mean fwd when v>0 minus when v==0, within each bucket
        deltas=[]
        for bi in bidx:
            hi=[fwd[i] for i in bi if v[i]>0]; lo=[fwd[i] for i in bi if v[i]==0]
            if len(hi)>=10 and len(lo)>=10: deltas.append(st.mean(hi)-st.mean(lo))
        cs="".join("+" if x>0 else "-" for x in ctrl)
        ds=" ".join("%+.2f"%x for x in deltas)
        print(f"  nback={nback:<2} {fn:<14} ctrl_avg={sum(ctrl)/len(ctrl):+.3f} signs={cs}  bucketΔfwd(R)=[{ds}]")
    print()

# ===== Decisive: best window, per-BLOCK Delta robustness =====
print("="*70); print("BOTTOMS decisive: nback=3, buy_w>0 gate — per-block & per-year Δfwd")
print("="*70)
nback=3; data=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        t=s[p]["t"]; a=s[p]["atr"] or 1.0
        wb=win(k,t,nback)
        buy_w=sum(w[x["size"]] for x in wb if x["side"]=="BUY")
        dl=(s[p-PRE_BARS]["c"]-s[p]["l"])/a
        data.append((buy_w,dl,fwd_rev(s,p),k))
blocks=sorted(set(d[3] for d in data))
print(f"  {'block':<42} n  hasBuy meanFwd_buy meanFwd_nobuy  Δ")
glob_hi=[];glob_lo=[]
for b in blocks:
    sub=[d for d in data if d[3]==b]
    hi=[d[2] for d in sub if d[0]>0]; lo=[d[2] for d in sub if d[0]==0]
    glob_hi+=hi; glob_lo+=lo
    d=(st.mean(hi)-st.mean(lo)) if hi and lo else float('nan')
    print(f"  {b:<42} {len(sub):<3} {len(hi):<6} {st.mean(hi) if hi else 0:>10.2f} {st.mean(lo) if lo else 0:>12.2f}  {d:+.2f}")
print(f"  {'ALL':<42} {len(data):<3} {len(glob_hi):<6} {st.mean(glob_hi):>10.2f} {st.mean(glob_lo):>12.2f}  {st.mean(glob_hi)-st.mean(glob_lo):+.2f}")

# ===== TOPS mirror =====
print("\n"+"="*70); print("TOPS MIRROR: SELL bubbles near the high → forward DROP (fwd_drop)")
print("="*70)
for nback in (2,3,4):
    data=[]
    for k,pr in PRIM.items():
        s=pr["series"]
        for p in fractal_highs(s):
            t=s[p]["t"]; a=s[p]["atr"] or 1.0
            wb=win(k,t,nback)
            sell_w=sum(w[x["size"]] for x in wb if x["side"]=="SELL")
            sell_L=sum(1 for x in wb if x["side"]=="SELL" and x["size"]=="L")
            up_leg=(s[p]["h"]-s[p-PRE_BARS]["c"])/a
            data.append((sell_w,sell_L,up_leg,fwd_drop(s,p),k))
    n=len(data); fwd=[d[3] for d in data]; uls=[d[2] for d in data]
    qs=sorted(uls); q=[qs[int(0.25*n)],qs[int(0.5*n)],qs[int(0.75*n)]]
    def bk2(u): return 0 if u<q[0] else 1 if u<q[1] else 2 if u<q[2] else 3
    bidx=[[] for _ in range(4)]
    for i,d in enumerate(data): bidx[bk2(d[2])].append(i)
    for fi,fn in [(0,"sell_w"),(1,"sellL>=1 gate")]:
        v=[(1.0 if d[1]>=1 else 0.0) if fi==1 else float(d[0]) for d in data]
        ctrl=[]
        for bi in bidx:
            if len(bi)>30: ctrl.append(spearman([v[i] for i in bi],[fwd[i] for i in bi]))
        cs="".join("+" if x>0 else "-" for x in ctrl)
        print(f"  nback={nback} {fn:<14} ctrl_avg={sum(ctrl)/len(ctrl):+.3f} signs={cs}  (+ = sell predicts drop)")
    print()
