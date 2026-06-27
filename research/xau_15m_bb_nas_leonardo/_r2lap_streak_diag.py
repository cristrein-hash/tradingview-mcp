#!/usr/bin/env python3
"""
_r2lap_streak_diag.py
Diagnose WHERE the max-losing-streak (24) sits in R2-KEPT, and whether any
orthogonal flow/context feature flags those specific losers. If the streak
losers share no removable signature, no filter can lower the streak without
also cutting winners -> teaches that losers are dispersed/auction-irreducible
within R2-KEPT. RAW-causal.
"""
import json
ROWS=[json.loads(l) for l in open('dataset_r2refine.jsonl')]
KEPT=sorted([r for r in ROWS if r['r2_keep']==1],key=lambda r:r['low_t'])
N=len(KEPT);WINS=sum(r['win'] for r in KEPT)

# locate the longest losing run
best=[];cur=[]
for r in KEPT:
    if r['win']==0: cur.append(r)
    else:
        if len(cur)>len(best): best=cur
        cur=[]
if len(cur)>len(best): best=cur
print(f"Longest losing run = {len(best)} trades, block {best[0]['block']}..{best[-1]['block']}")
feats=['bars_since_buycross','buy_sell_ratio4','buy_L_recent','low_closepos',
       'flow_accel','sell_decel','sell_skew_mig','is_deadzone','is_london_open',
       'is_ny_overlap','absorption']
# compare the run vs overall winners on each feature (mean)
import statistics as st
def mean(rows,f):
    v=[x[f] for x in rows if isinstance(x[f],(int,float)) and abs(x[f])<1e7]
    return round(st.mean(v),3) if v else None
winners=[r for r in KEPT if r['win']==1]
print(f"\n{'feat':<22}{'streak-run':>12}{'all-winners':>13}")
for f in feats:
    print(f"{f:<22}{str(mean(best,f)):>12}{str(mean(winners,f)):>13}")

# Could ANY filter remove a streak bar without it being indistinguishable from a winner?
# Count how many of the 24 streak losers would be cut by best candidate cut.
def anycut2(r):
    return (r['buy_sell_ratio4']<=2.0 and r['low_closepos']<0.3) or \
           (r['is_deadzone']==1 and r['buy_sell_ratio4']<=2.0)
cut_in_run=sum(1 for r in best if anycut2(r))
print(f"\nBest candidate cut removes {cut_in_run}/{len(best)} of the streak losers")

# How many distinct losing runs >= 10? streak distribution
runs=[];cur=0
for r in KEPT:
    if r['win']==0: cur+=1
    else:
        if cur: runs.append(cur)
        cur=0
if cur: runs.append(cur)
runs.sort(reverse=True)
print(f"Top losing runs: {runs[:12]}")
print(f"Total losing runs: {len(runs)}, losers total: {N-WINS}")
