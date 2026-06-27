#!/usr/bin/env python3
"""DA audit of diag_direction_bug.py (Cris 2026-06-27).
Verifies: (3) overlap M8-TOP vs regime BEAR (is TOP a proxy for regime?);
(4) is near-TOP 'should be SHORT' or just 'should be SKIP' (avgR, hypothetical short PnL);
(5) power on n=5/n=29 subgroups; plus full-256 BOT/TOP split strength + temporal-side check.
Reuses exact loader logic from diag_direction_bug.py. RAW-causal diagnosis only."""
import json, csv, bisect
from pathlib import Path
HERE = Path(__file__).parent

TR = []
with open(HERE/"strategy_5atr_a2_trades.csv") as f:
    for r in csv.DictReader(f):
        TR.append(dict(num=int(r["num"]), t=int(r["entry_t"]), entry=float(r["entry"]),
                       R=float(r["R"]), win=int(r["win"])))
M8 = []
with open(HERE/"true_reversals_M8.csv") as f:
    for r in csv.DictReader(f):
        M8.append(dict(t=int(r["t"]), kind=r["kind"], price=float(r["price"])))
M8.sort(key=lambda x: x["t"]); M8T=[x["t"] for x in M8]
MR = json.load(open(HERE/"macro_regime_4h.json"))["bars_4h"]
MR.sort(key=lambda x: x["t_end"]); MRend=[x["t_end"] for x in MR]
def regime_asof(t):
    k=bisect.bisect_right(MRend,t)-1
    return MR[k]["macro"] if k>=0 else "NA"
BAR=900
def nearest_m8(t):
    k=bisect.bisect_left(M8T,t); cands=[]
    for j in (k-1,k):
        if 0<=j<len(M8): cands.append(M8[j])
    if not cands: return None,None,None
    best=min(cands,key=lambda x:abs(x["t"]-t))
    return best["kind"],(t-best["t"])//BAR,best["price"]

rows=[]
for tr in TR:
    kind,db,mp=nearest_m8(tr["t"])
    rows.append({**tr,"reg":regime_asof(tr["t"]),"m8kind":kind,"m8db":db})

def stat(g):
    if not g: return (0,0,0.0,0.0)
    w=sum(r["win"] for r in g); sm=sum(r["R"] for r in g)
    return (len(g),w,sm,sm/len(g))

print("=== (3) OVERLAP: is M8-TOP label just a proxy for BEAR regime? ===")
# crosstab m8kind x regime
from collections import Counter
ct=Counter((r["m8kind"],r["reg"]) for r in rows)
print("crosstab (m8kind, regime) -> count:")
for k in ("BOT","TOP",None):
    line=f"  {str(k):<5}: " + "  ".join(f"{reg}={ct.get((k,reg),0)}" for reg in ("BULL","NEUTRAL","BEAR"))
    print(line)
# Of near-TOP losers, how many are BEAR? (proxy test). And does near-TOP add signal WITHIN non-BEAR?
topnb=[r for r in rows if r["m8kind"]=="TOP" and r["reg"]!="BEAR"]
botnb=[r for r in rows if r["m8kind"]=="BOT" and r["reg"]!="BEAR"]
print("\nWITHIN non-BEAR only (controls for regime):")
print(f"  near-TOP non-BEAR: n={stat(topnb)[0]} WR={100*stat(topnb)[1]/max(1,stat(topnb)[0]):.1f}% sumR={stat(topnb)[2]:+.1f} avgR={stat(topnb)[3]:+.2f}")
print(f"  near-BOT non-BEAR: n={stat(botnb)[0]} WR={100*stat(botnb)[1]/max(1,stat(botnb)[0]):.1f}% sumR={stat(botnb)[2]:+.1f} avgR={stat(botnb)[3]:+.2f}")
# WITHIN BEAR only: does TOP vs BOT separate?
topb=[r for r in rows if r["m8kind"]=="TOP" and r["reg"]=="BEAR"]
botb=[r for r in rows if r["m8kind"]=="BOT" and r["reg"]=="BEAR"]
print("WITHIN BEAR only:")
print(f"  near-TOP BEAR: n={stat(topb)[0]} WR={100*stat(topb)[1]/max(1,stat(topb)[0]):.1f}% avgR={stat(topb)[3]:+.2f}")
print(f"  near-BOT BEAR: n={stat(botb)[0]} WR={100*stat(botb)[1]/max(1,stat(botb)[0]):.1f}% avgR={stat(botb)[3]:+.2f}")

print("\n=== (4) SHORT vs SKIP: avgR of candidates; hypothetical mirror-short PnL ===")
# A LONG that hit SL (-1R) at top: would a SHORT have won? We only know long R, not short outcome.
# Proxy: if the long lost, a mirror short MIGHT have won, but exit geometry differs -> NOT derivable from this data.
for label,pred in [("near-TOP all", lambda r:r["m8kind"]=="TOP"),
                   ("near-TOP <=8b", lambda r:r["m8kind"]=="TOP" and r["m8db"] is not None and abs(r["m8db"])<=8),
                   ("BEAR all", lambda r:r["reg"]=="BEAR"),
                   ("BEAR & TOP<=8b", lambda r:r["reg"]=="BEAR" and r["m8kind"]=="TOP" and r["m8db"] is not None and abs(r["m8db"])<=8)]:
    g=[r for r in rows if pred(r)]; n,w,sm,a=stat(g)
    print(f"  {label:<18} n={n:>3} WR={100*w/max(1,n):4.1f}% sumR={sm:+6.1f} avgR={a:+.2f}")

print("\n=== (5) POWER: 95% Wilson CI on small subgroups ===")
import math
def wilson(w,n,z=1.96):
    if n==0: return (0,0)
    p=w/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))
for label,pred in [("BEAR&TOP<=8b (n=5)", lambda r:r["reg"]=="BEAR" and r["m8kind"]=="TOP" and r["m8db"] is not None and abs(r["m8db"])<=8),
                   ("TOP<=8b (n=29)", lambda r:r["m8kind"]=="TOP" and r["m8db"] is not None and abs(r["m8db"])<=8),
                   ("near-TOP all (n=137)", lambda r:r["m8kind"]=="TOP"),
                   ("near-BOT all (n=119)", lambda r:r["m8kind"]=="BOT")]:
    g=[r for r in rows if pred(r)]; n,w,sm,a=stat(g); lo,hi=wilson(w,n)
    print(f"  {label:<22} WR={100*w/max(1,n):4.1f}% Wilson95=[{100*lo:.0f}%,{100*hi:.0f}%]")

print("\n=== (2) temporal SIDE of nearest M8 (is anchor before or after entry?) ===")
# m8db = (t_entry - t_m8)//BAR ; positive => M8 reversal is in the PAST (causal-available timing),
# negative => nearest reversal is in the FUTURE (only knowable later -> look-ahead in the label).
fut=[r for r in rows if r["m8db"] is not None and r["m8db"]<0]
past=[r for r in rows if r["m8db"] is not None and r["m8db"]>=0]
print(f"  nearest M8 in FUTURE of entry (db<0): {len(fut)}/{len(rows)}  ({100*len(fut)/len(rows):.0f}%)")
print(f"  nearest M8 in PAST/at  entry (db>=0): {len(past)}/{len(rows)}")
# for the <=8b TOP anchors specifically:
t8=[r for r in rows if r["m8kind"]=="TOP" and r["m8db"] is not None and abs(r["m8db"])<=8]
print(f"  of TOP<=8b anchors, in FUTURE: {sum(1 for r in t8 if r['m8db']<0)}/{len(t8)}")
