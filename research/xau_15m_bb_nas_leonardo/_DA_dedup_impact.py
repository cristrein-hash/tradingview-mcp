#!/usr/bin/env python3
"""DA part 3: quantify whether the 7 cross-block OHLC conflicts (last-writer-wins) actually
change any 4H macro label. Rebuild macro both ways (first-writer vs last-writer) and diff. 2026-06-26."""
import json
from pathlib import Path
HERE=Path(__file__).parent; BUCKET=14400; K=2
PRIM=sorted((HERE/"primitives").glob("*.primitives.json"))
def build(first_wins):
    bars={}
    for p in PRIM:
        for b in json.load(open(p))["series"]:
            t=b["t"]
            if first_wins and t in bars: continue
            bars[t]=b
    ts=sorted(bars); buck={}
    for t in ts:
        b=bars[t]; k=t//BUCKET
        if k not in buck: buck[k]={"h":b["h"],"l":b["l"],"c":b["c"]}
        else:
            z=buck[k]; z["h"]=max(z["h"],b["h"]); z["l"]=min(z["l"],b["l"]); z["c"]=b["c"]
    H4=[buck[k] for k in sorted(buck)]
    Hh=[x["h"] for x in H4]; Ll=[x["l"] for x in H4]
    ema=None; kE=2/51; out=[]
    for i,x in enumerate(H4):
        ema=x["c"] if ema is None else x["c"]*kE+ema*(1-kE)
        sh,sl=[],[]
        for j in range(K,i-K+1):
            if Hh[j]==max(Hh[j-K:j+K+1]): sh.append(Hh[j])
            if Ll[j]==min(Ll[j-K:j+K+1]): sl.append(Ll[j])
        sd=0
        if len(sh)>=2 and len(sl)>=2:
            if sh[-1]>sh[-2] and sl[-1]>sl[-2]: sd=1
            elif sh[-1]<sh[-2] and sl[-1]<sl[-2]: sd=-1
        ep=1 if x["c"]>=ema else -1
        out.append("BULL" if (sd>0 and ep>0) else ("BEAR" if (sd<0 and ep<0) else "NEUTRAL"))
    return out
last=build(False); first=build(True)
n=min(len(last),len(first))
diff=sum(1 for a,b in zip(last[:n],first[:n]) if a!=b)
print(f"4H bars last-writer={len(last)} first-writer={len(first)}")
print(f"macro labels differ between dedup policies: {diff}/{n}")
print("→ if 0: the 7 OHLC conflicts are immaterial to macro; dedup policy is cosmetic.")
