#!/usr/bin/env python3
"""
Self-audit (Devil's Advocate) of the top rules from _engine_rsi_ema_momentum.py.
Checks:
  1. disp4_atr semantics / correlation with R (is it a proxy for something circular?)
  2. ex-top2 AND ex-top5 robustness for finalist rules
  3. block / time concentration (is the lift carried by a few blocks?)
  4. monthly sign stability
  5. overlap of finalists (are they the same trades?)
"""
import json
from collections import Counter, defaultdict

BASE = 0.7265
ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]

def sub_stats(name, pred):
    sub = [r for r in ROWS if pred(r)]
    R = sorted((r['R_reclaim'] for r in sub), reverse=True)
    n = len(R); avg = sum(R)/n; wr = sum(1 for x in R if x>0)/n
    ex2 = sum(R[2:])/(n-2); ex5 = sum(R[5:])/(n-5)
    runners = sum(1 for x in R if x>=5)
    by = {}
    for y in (2024,2025,2026):
        ys=[r['R_reclaim'] for r in sub if r['yr']==y]
        by[y]=(len(ys), sum(ys)/len(ys))
    # block concentration: count blocks, top-block share of sumR
    bl = defaultdict(float); bc = defaultdict(int)
    for r in sub:
        bl[r['block']] += r['R_reclaim']; bc[r['block']] += 1
    sumR = sum(R)
    topblock = max(bl.items(), key=lambda x: x[1])
    # leave-one-block-out worst case
    worst = min((sum(v for k,v in bl.items() if k!=b)/(n-bc[b]) for b in bl), default=avg)
    print(f"\n=== {name} ===")
    print(f" n={n} WR={wr*100:.1f}% avgR={avg:+.3f} lift={avg-BASE:+.3f} runners={runners}")
    print(f" ex-top2={ex2:+.3f} ex-top5={ex5:+.3f}  (base {BASE})")
    print(f" y24 n={by[2024][0]} {by[2024][1]:+.3f} | y25 n={by[2025][0]} {by[2025][1]:+.3f} | y26 n={by[2026][0]} {by[2026][1]:+.3f}")
    print(f" #blocks={len(bl)} topblock={topblock[0]} contributes {topblock[1]:+.1f}R of {sumR:+.1f}R total")
    print(f" leave-worst-block-out avgR={worst:+.3f}")
    return sub

# disp4 semantics
import statistics
d4 = [r['disp4_atr'] for r in ROWS]
print("disp4_atr: min=%.2f p25=%.2f med=%.2f p75=%.2f max=%.2f" % (
    min(d4), statistics.quantiles(d4,n=4)[0], statistics.median(d4),
    statistics.quantiles(d4,n=4)[2], max(d4)))
# correlation disp4 vs R
import math
def corr(xs, ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    cov=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    sx=math.sqrt(sum((x-mx)**2 for x in xs)); sy=math.sqrt(sum((y-my)**2 for y in ys))
    return cov/(sx*sy)
print("corr(disp4_atr, R_reclaim)=%.3f" % corr(d4, [r['R_reclaim'] for r in ROWS]))
print("corr(disp8_atr, R_reclaim)=%.3f" % corr([r['disp8_atr'] for r in ROWS], [r['R_reclaim'] for r in ROWS]))

# FINALISTS
A = sub_stats("R1: disp4<-0.758 (single)", lambda r: r['disp4_atr']<-0.758)
B = sub_stats("R2: rsi_low>=48.5 AND disp4<-0.898", lambda r: r['rsi_low']>=48.5 and r['disp4_atr']<-0.898)
C = sub_stats("R3: rsi>=48.01 AND disp4<-0.898", lambda r: r['rsi']>=48.01 and r['disp4_atr']<-0.898)
D = sub_stats("R4: disp4<-0.327 (broad)", lambda r: r['disp4_atr']<-0.327)

# overlap B vs C
setB={(r['block'],r['low_idx']) for r in B}
setC={(r['block'],r['low_idx']) for r in C}
print(f"\noverlap B&C = {len(setB&setC)} of B={len(setB)} C={len(setC)}")

# sanity: how many of disp4<-0.898 have negative disp4 (seller leg) AND what is room/macro
seg=[r for r in ROWS if r['disp4_atr']<-0.898]
print("\ndisp4<-0.898 segment: macro_bull frac=%.2f macro_bear frac=%.2f near_M8=%.2f" % (
    sum(r['macro_bull'] for r in seg)/len(seg),
    sum(r['macro_bear'] for r in seg)/len(seg),
    sum(r['near_M8'] for r in seg)/len(seg)))
