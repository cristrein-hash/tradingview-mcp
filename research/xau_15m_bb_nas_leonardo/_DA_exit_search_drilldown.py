#!/usr/bin/env python3
"""DA drilldown: (a) the K=1 gb=2.0 anomaly (+82.7) — is it a different rule or just looser?
(b) fill realism on the 2 driver trades #32 #128 specifically — did their RIDER exit gap through?
(c) what happens to delta if drivers #32 #128 filled at candle-low. RAW-causal."""
import json, csv, statistics as st
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
def sim(s,cj,entry,sl,atr,K,gb,fill="trail"):
    risk=entry-sl; end=min(cj+HMAX,len(s)-1); r1=False; ridem=False; trail=sl; runhi=entry
    for k in range(cj+1,end+1):
        b=s[k]; lo,hi,cl=b["l"],b["h"],b["c"]
        if lo<=trail and (r1 or trail>sl):
            return (trail if fill=="trail" else lo)
        if lo<=sl and not r1:
            return (sl if fill=="trail" else lo)
        runhi=max(runhi,hi)
        if (hi-entry)/risk>=1: r1=True
        if (hi-entry)/risk>=K: ridem=True
        if not r1: continue
        if not ridem:
            sw=cf_low(s,k)
            if sw: trail=max(trail,sw-0.1*atr)
        else:
            trail=max(trail, runhi-gb*risk)
    return s[end]["c"]
data=[]
for tr in T170:
    num=int(tr["num"]); t=int(tr["entry_t"]); fd=FD.get(t); gt=GT.get(num)
    if not fd: continue
    pr=PRIM[fd["block"]]; s=pr["series"]; cj=fd["cj"]; i=fd["i"]; atr=s[i]["atr"]
    entry=fnum(gt["entry"]); sl=float(tr["sl"]); risk=entry-sl
    data.append(dict(num=num,s=s,cj=cj,entry=entry,sl=sl,atr=atr,risk=risk))
def Rv(ex,e,r): return max(-1.0,min(RCAP,(ex-e)/r))

print("=== (a) K=1 gb=2.0 (+82.7) — concentration check vs K=3 gb=2.0 ===")
def runcfg(K,gb,fill="trail"):
    return {d["num"]:Rv(sim(d["s"],d["cj"],d["entry"],d["sl"],d["atr"],K,gb,fill),d["entry"],d["risk"]) for d in data}
k1=runcfg(1,2.0); k3=runcfg(3,2.0); let=runcfg(1,99,)  # gb huge ~ LETRUN-ish? no -> compute LETRUN separately
# proper LETRUN
def letrun(d):
    s,cj,entry,sl,atr,risk=d["s"],d["cj"],d["entry"],d["sl"],d["atr"],d["risk"]
    end=min(cj+HMAX,len(s)-1); r1=False; trail=sl
    for k in range(cj+1,end+1):
        b=s[k]; lo=b["l"]
        if lo<=trail and (r1 or trail>sl): return trail
        if lo<=sl and not r1: return sl
        if (b["h"]-entry)/risk>=1: r1=True
        if not r1: continue
        sw=cf_low(s,k)
        if sw: trail=max(trail,sw-0.1*atr)
    return s[end]["c"]
LET={d["num"]:Rv(letrun(d),d["entry"],d["risk"]) for d in data}
print(f"sumR K1g2={round(sum(k1.values()),2)}  LETRUN={round(sum(LET.values()),2)}")
d1=sorted([(n,round(k1[n]-LET[n],2)) for n in k1 if abs(k1[n]-LET[n])>0.01],key=lambda z:-z[1])
print(f"K1g2 differs from LETRUN on {len(d1)} trades; top: {d1[:8]}")
print(f"total delta K1g2 vs LETRUN = {round(sum(x[1] for x in d1),2)}R")
print("NOTE: K=1 means trail SOLTA imediatamente apos +1R (vira basicamente um trail gb*risk puro, NAO escalonado)")

print("\n=== (b) drivers #32 #128: fill realism (trail vs candle-low) ===")
for num in (32,128):
    d=[x for x in data if x["num"]==num][0]
    ex_t=sim(d["s"],d["cj"],d["entry"],d["sl"],d["atr"],3,2.0,"trail")
    ex_l=sim(d["s"],d["cj"],d["entry"],d["sl"],d["atr"],3,2.0,"low")
    print(f"#{num}: entry={d['entry']} risk={round(d['risk'],2)} | exit@trail={round(ex_t,2)} (R={round(Rv(ex_t,d['entry'],d['risk']),2)}) "
          f"| exit@candle-low={round(ex_l,2)} (R={round(Rv(ex_l,d['entry'],d['risk']),2)}) | slip={round((ex_t-ex_l)/d['risk'],2)}R")

print("\n=== (c) delta survival under candle-low fills (whole book) ===")
RID_t=runcfg(3,2.0,"trail"); RID_l=runcfg(3,2.0,"low")
print(f"RIDER K3g2 sumR  trail-fill={round(sum(RID_t.values()),2)}  candle-low-fill={round(sum(RID_l.values()),2)}")
print(f"LETRUN already exits at trail too; apply same realism to LETRUN:")
def letrun_low(d):
    s,cj,entry,sl,atr,risk=d["s"],d["cj"],d["entry"],d["sl"],d["atr"],d["risk"]
    end=min(cj+HMAX,len(s)-1); r1=False; trail=sl
    for k in range(cj+1,end+1):
        b=s[k]; lo=b["l"]
        if lo<=trail and (r1 or trail>sl): return lo
        if lo<=sl and not r1: return lo
        if (b["h"]-entry)/risk>=1: r1=True
        if not r1: continue
        sw=cf_low(s,k)
        if sw: trail=max(trail,sw-0.1*atr)
    return s[end]["c"]
LET_l={d["num"]:Rv(letrun_low(d),d["entry"],d["risk"]) for d in data}
print(f"LETRUN sumR trail={round(sum(LET.values()),2)} candle-low={round(sum(LET_l.values()),2)}")
print(f"\nUPLIFT under realistic candle-low fill = RIDER_low {round(sum(RID_l.values()),2)} - LETRUN_low {round(sum(LET_l.values()),2)} "
      f"= {round(sum(RID_l.values())-sum(LET_l.values()),2)}R (vs claimed +4.9R)")
