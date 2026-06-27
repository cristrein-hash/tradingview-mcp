#!/usr/bin/env python3
import json
from collections import defaultdict

PATH = "entry_dataset.jsonl"
rows = [json.loads(l) for l in open(PATH)]

# target membership: dist_ema_atr<0 AND ema_slope_atr>0
mem = [r for r in rows if r["dist_ema_atr"] < 0 and r["ema_slope_atr"] > 0]
mem.sort(key=lambda r: r["low_t"])

def is_win(r): return r["R_reclaim"] > 0
def is_los(r): return r["R_reclaim"] <= 0

def max_losing_streak(seq):
    best=cur=0
    for r in seq:
        if is_los(r): cur+=1; best=max(best,cur)
        else: cur=0
    return best

def stats(seq):
    n=len(seq); w=sum(1 for r in seq if is_win(r))
    return n, round(100*w/n,2) if n else 0.0, max_losing_streak(seq)

def yr_breakdown(seq):
    d=defaultdict(lambda:[0,0])
    for r in seq:
        d[r["yr"]][0]+=1
        if is_win(r): d[r["yr"]][1]+=1
    return {y:(c[0], round(100*c[1]/c[0],1) if c[0] else None) for y,c in sorted(d.items())}

def block_breakdown(seq):
    d=defaultdict(lambda:[0,0])
    for r in seq:
        d[r["block"]][0]+=1
        if is_win(r): d[r["block"]][1]+=1
    return {b:(c[0], round(100*c[1]/c[0],1) if c[0] else None) for b,c in sorted(d.items())}

W=[r for r in mem if is_win(r)]; L=[r for r in mem if is_los(r)]
n0,wr0,ms0=stats(mem)
print(f"BEFORE  n={n0} WR={wr0} maxstreak={ms0} winners={len(W)} losers={len(L)}")
print("  by year:", yr_breakdown(mem))
print("  by block:", block_breakdown(mem))

# FILTER: keep if disp4_atr <= -0.333
def keep(r): return r["disp4_atr"] <= -0.333
kept=[r for r in mem if keep(r)]
cut =[r for r in mem if not keep(r)]
n1,wr1,ms1=stats(kept)
kw=sum(1 for r in kept if is_win(r)); kl=sum(1 for r in kept if is_los(r))
cw=sum(1 for r in cut if is_win(r)); cl=sum(1 for r in cut if is_los(r))
wkept=100*kw/len(W); lcut=100*cl/len(L)
print(f"\nAFTER   n={n1} WR={wr1} maxstreak={ms1}")
print(f"winners_kept={wkept:.2f}% ({kw}/{len(W)})  losers_cut={lcut:.2f}% ({cl}/{len(L)})")
print(f"CUT set: {len(cut)} trades = {cw} winners + {cl} losers")
print("  AFTER by year:", yr_breakdown(kept))
print("  AFTER by block:", block_breakdown(kept))

# year delta vs base
print("\nYEAR DELTA (after - before base WR):")
yb=yr_breakdown(mem); ya=yr_breakdown(kept)
for y in sorted(yb):
    bwr=yb[y][1]; awr=ya.get(y,(0,None))[1]
    delta = round(awr-bwr,1) if (awr is not None and bwr is not None) else None
    print(f"  y{y}: before={bwr} after={awr} delta={delta} (vs global base {wr0}: {'WORSE' if awr is not None and awr<wr0 else 'ok'})")

# neighborhood robustness
print("\nTHRESHOLD NEIGHBORHOOD:")
for t in [-0.25,-0.28,-0.30,-0.333,-0.36,-0.40,-0.45]:
    k=[r for r in mem if r["disp4_atr"]<=t]
    if not k:
        print(f"  t={t}: empty"); continue
    n,wr,ms=stats(k)
    kkw=sum(1 for r in k if is_win(r)); kkl=sum(1 for r in k if is_los(r))
    wk=100*kkw/len(W); lc=100*(len(L)-kkl)/len(L)
    print(f"  t={t}: n={n} WR={wr} streak={ms} win_kept={wk:.1f}% los_cut={lc:.1f}%")
