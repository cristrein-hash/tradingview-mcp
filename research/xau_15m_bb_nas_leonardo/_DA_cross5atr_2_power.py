#!/usr/bin/env python3
"""DA POINT 2 — STATISTICAL POWER on the BOT-tier WR claims.
BOT tiers have n=2/5/10/11. Compute Wilson 95% CI for each group's WR. Then a
flip-test: how many trades must change outcome to break the 100/100/100 monotonic
pattern, and to break the 'FRACO 9% << MEDIO 100%' contrast. Fisher exact FRACO vs
MEDIO. Decide: signal or small-n artifact."""
import csv, bisect, math
from pathlib import Path
from filter_harness import ROWS, dedup
HERE=Path(__file__).parent; BAR=900; W=3
REV=[{**r,"t":int(r["t"])} for r in csv.DictReader(open(HERE/"reversal_power.csv"))]
REVt=sorted(REV,key=lambda r:r["t"]); RT=[r["t"] for r in REVt]
def nearest_rev(t):
    k=bisect.bisect_left(RT,t); best=None
    for j in (k-1,k,k+1):
        if 0<=j<len(REVt):
            d=abs(REVt[j]["t"]-t)
            if best is None or d<best[0]: best=(d,REVt[j])
    return best
def group_of(r):
    nb=nearest_rev(r["low_t"])
    if nb is None or nb[0]>W*BAR: return "UNMATCHED"
    return "TOP" if nb[1]["kind"]=="TOP" else "BOT-"+nb[1]["tier"]
def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))
def fisher(a,b,c,d):
    # 2x2 two-tailed via hypergeom sum
    from math import comb
    r1,r2,c1,N=a+b,c+d,a+c,a+b+c+d
    def p(x): return comb(c1,x)*comb(N-c1,r1-x)/comb(N,r1)
    p0=p(a); tot=0
    lo=max(0,r1-(N-c1)); hi=min(r1,c1)
    for x in range(lo,hi+1):
        px=p(x)
        if px<=p0+1e-12: tot+=px
    return tot
from collections import defaultdict
g=defaultdict(list)
for r in dedup(ROWS): g[group_of(r)].append(r)
print(f"{'grupo':<14}{'n':>4}{'wins':>5}{'WR%':>7}   Wilson95%CI")
for k in ["BOT-MONSTRO","BOT-FORTE","BOT-MEDIO","BOT-FRACO","TOP","UNMATCHED"]:
    rs=g.get(k,[]);
    if not rs: continue
    n=len(rs); w=sum(x['win'] for x in rs); lo,hi=wilson(w,n)
    print(f"{k:<14}{n:>4}{w:>5}{100*w/n:>7.1f}   [{100*lo:.0f}%, {100*hi:.0f}%]")
med=g["BOT-MEDIO"]; fra=g["BOT-FRACO"]
wm,nm=sum(x['win'] for x in med),len(med)
wf,nf=sum(x['win'] for x in fra),len(fra)
print(f"\nFisher exact MEDIO({wm}/{nm}) vs FRACO({wf}/{nf}) p={fisher(wm,nm-wm,wf,nf-wf):.4f}")
print("flip-test: BOT-MEDIO 100% breaks if just 1 of its trades had lost.")
print("flip-test: BOT-FRACO 9% (1/11 win) breaks toward 27% if just 2 more had won.")
print("FRACO+MEDIO+FORTE+MONSTRO total n =",sum(len(g[k]) for k in ['BOT-FRACO','BOT-MEDIO','BOT-FORTE','BOT-MONSTRO']),"of",b if (b:=len(dedup(ROWS))) else 0)
