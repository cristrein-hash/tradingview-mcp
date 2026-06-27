#!/usr/bin/env python3
"""DA final checks: per-year of K1g2 (the unsearched better cell); robustness of K1 row;
confirm chosen-config delta concentration; binomial power on +1 runner."""
import json, csv, statistics as st, math
from pathlib import Path
HERE=Path(__file__).parent; HMAX=480; RCAP=20.0
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""): json.loads(p.read_text())
      for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIM={k[:10]:v for k,v in PRIM.items()}
FD={r["t"]:r for r in (json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines())}
GT={int(r["num"]):r for r in csv.DictReader(open(HERE/"cris_ground_truth.csv"))}
T170=list(csv.DictReader(open(HERE/"strategy_5atr_regime170_trades.csv")))
def fnum(x): return float(x) if x not in (None,"","None") else None
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(2,i-120); bst=None
    for p in range(lo,i-1):
        if L[p]==min(L[p-2:p+3]): bst=L[p]
    return bst
def sim(s,cj,entry,sl,atr,K,gb):
    risk=entry-sl; end=min(cj+HMAX,len(s)-1); r1=False; ridem=False; trail=sl; runhi=entry
    for k in range(cj+1,end+1):
        b=s[k]; lo,hi=b["l"],b["h"]
        if lo<=trail and (r1 or trail>sl): return trail
        if lo<=sl and not r1: return sl
        runhi=max(runhi,hi)
        if (hi-entry)/risk>=1: r1=True
        if (hi-entry)/risk>=K: ridem=True
        if not r1: continue
        if not ridem:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
        else: trail=max(trail, runhi-gb*risk)
    return s[end]["c"]
data=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); gt=GT.get(num)
    if not fd: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; cj=fd["cj"]; i=fd["i"]; atr=s[i]["atr"]
    entry=fnum(gt["entry"]); sl=float(tr["sl"]); risk=entry-sl
    data.append(dict(num=num,s=s,cj=cj,entry=entry,sl=sl,atr=atr,risk=risk,yr=int(fd["yr"])))
def Rv(ex,e,r): return max(-1.0,min(RCAP,(ex-e)/r))
def runy(K,gb):
    d={}
    for x in data:
        R=Rv(sim(x["s"],x["cj"],x["entry"],x["sl"],x["atr"],K,gb),x["entry"],x["risk"])
        d.setdefault(x["yr"],[]).append(R)
    return {y:round(sum(v),2) for y,v in sorted(d.items())},round(sum(sum(v) for v in d.values()),2)

print("=== K=1 (immediate gb*risk trail) per-year robustness ===")
for gb in (1.5,2.0,2.5):
    y,tot=runy(1,gb); print(f"K1 gb={gb}: total={tot} per-year={y}")
print("\n=== K=3 gb=2.0 (the CHOSEN config) per-year ===")
y,tot=runy(3,2.0); print(f"K3 gb=2.0: total={tot} per-year={y}")

print("\n=== binomial power on 'extra +1 runner' (2/25 -> 3/25) ===")
# under base capture prob p=2/25, prob of >=3 by chance with same n
def binom(n,k,p): return math.comb(n,k)*p**k*(1-p)**(n-k)
p=2/25
pge3=sum(binom(25,k,p) for k in range(3,26))
print(f"if true capture rate = base 2/25=0.08, P(>=3 of 25 captured) = {round(pge3,3)} (not significant; n trivially small)")
print(f"a single trade flips 2->3; 95% Wilson CI on 3/25 = wide, includes 2/25")
