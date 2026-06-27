#!/usr/bin/env python3
"""FINAL adversarial: the user's exact thesis — a COMPLEX threshold (large bubbles weighted
heavily, small lightly, quantity-per-size as definer) for SELL clusters AND the absorption
variant. Test at the OPERATIONAL level: per-block Δfwd (mean forward rally when gate fires vs
not), within down-leg buckets. If a real bottom signal exists it must RAISE forward rally
robustly. RAW-causal."""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRE_BARS=16; BAR=900; K=4; HOR=192; BUF=0.25; PRE=PRE_BARS*BAR
BUB={k:sorted([json.loads(l) for l in (HERE/"bubbles"/f"{k}.bubbles.jsonl").read_text().splitlines() if l],
              key=lambda x:x["t"]) for k in PRIM}
def win(key,t):
    bb=BUB[key]; ts=[x["t"] for x in bb]
    a=bisect.bisect_left(ts,t-PRE); b=bisect.bisect_right(ts,t); cut=t+BAR
    return [x for x in bb[a:b] if x["known_at"]<=cut]
def fwd_rev(s,p):
    Lp=s[p]["l"]; a=s[p]["atr"] or 1.0; ext=Lp; end=min(p+HOR,len(s)-1)
    for i in range(p+1,end+1):
        if s[i]["l"]<Lp-BUF*a: break
        ext=max(ext,s[i]["h"])
    return (ext-Lp)/a
def fractal_lows(s):
    L=[x["l"] for x in s]; return [p for p in range(max(K,PRE_BARS),len(s)-K) if L[p]==min(L[p-K:p+K+1])]

w={"S":1,"M":3,"L":10}
data=[]
for k,pr in PRIM.items():
    s=pr["series"]
    for p in fractal_lows(s):
        t=s[p]["t"]; a=s[p]["atr"] or 1.0; wb=win(k,t)
        sells=[x for x in wb if x["side"]=="SELL"]
        sL=sum(1 for x in sells if x["size"]=="L"); sM=sum(1 for x in sells if x["size"]=="M")
        sell_w=sum(w[x["size"]] for x in sells)
        def cpos(x):
            rng=(x["h"]-x["l"]) or 1e-9; return (x["c"]-x["l"])/rng
        absorb_w=sum(w[x["size"]]*cpos(x) for x in sells)
        absorb_frac=absorb_w/(sell_w+1e-9)
        dl=(s[p-PRE_BARS]["c"]-s[p]["l"])/a
        data.append(dict(sL=sL,sM=sM,sell_w=sell_w,absorb_frac=absorb_frac,dl=dl,fwd=fwd_rev(s,p),blk=k))
n=len(data); blocks=sorted(set(d["blk"] for d in data))

# the candidate gates (user thesis + absorption)
gates={
 "heavy_sell_w>=15 (>=1.5L equiv)": lambda d: d["sell_w"]>=15,
 "climax_sellL>=2":                 lambda d: d["sL"]>=2,
 "climax_sellL>=2 AND absorb>=0.5": lambda d: d["sL"]>=2 and d["absorb_frac"]>=0.5,
 "heavy_sell AND absorb>=0.55":     lambda d: d["sell_w"]>=10 and d["absorb_frac"]>=0.55,
 "sellL>=1 AND absorb>=0.6 (held)": lambda d: d["sL"]>=1 and d["absorb_frac"]>=0.6,
}
def report(name,g):
    fire=[d for d in data if g(d)]; rest=[d for d in data if not g(d)]
    if len(fire)<20: print(f"  {name:<36} n_fire={len(fire)} TOO FEW"); return
    dg=st.mean([d["fwd"] for d in fire])-st.mean([d["fwd"] for d in rest])
    # per-block
    bsigns=[]
    for b in blocks:
        f=[d["fwd"] for d in data if d["blk"]==b and g(d)]
        r=[d["fwd"] for d in data if d["blk"]==b and not g(d)]
        if len(f)>=8 and r: bsigns.append(st.mean(f)-st.mean(r))
    npos=sum(1 for x in bsigns if x>0)
    print(f"  {name:<36} n_fire={len(fire):<4} Δfwd_global={dg:+.2f}R  blocks+:{npos}/{len(bsigns)}  worst={min(bsigns):+.2f} best={max(bsigns):+.2f}")
print(f"fractal lows: {n}  | mean fwd_rev all = {st.mean([d['fwd'] for d in data]):.2f}R")
print("GATE TEST (a true bottom gate must give Δfwd>0 robustly across blocks):")
for nm,g in gates.items(): report(nm,g)
print("\n+ = gate raises forward rally. Need Δfwd_global>0 AND >=6/8 blocks positive to count.")
