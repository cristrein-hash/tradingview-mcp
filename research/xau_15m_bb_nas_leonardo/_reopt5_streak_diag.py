"""
_reopt5_streak_diag.py — diagnose the 30-loser streak (no-dedup) and 2025/2026 floor.
RAW-causal. Identify which block/time the max streak lives in and its feature signature.
"""
from _reopt5_harness import ROWS
s=sorted(ROWS, key=lambda r:r['low_t'])
# find longest losing run
best=(0,0,0); cur=0; start=0
runs=[]
for i,r in enumerate(s):
    if r['win']==0:
        if cur==0: start=i
        cur+=1
        if cur>best[0]: best=(cur,start,i)
    else:
        if cur>=8: runs.append((cur,start,i-1))
        cur=0
if cur>=8: runs.append((cur,start,len(s)-1))
print("max streak:",best[0])
ln,a,b=best
seg=s[a:b+1]
from collections import Counter
print("streak block(s):",Counter(r['block'] for r in seg))
print("streak time range:", seg[0]['low_t'], "->", seg[-1]['low_t'])
# feature signature of the streak vs rest
import statistics
def med(rows,f):
    v=[r[f] for r in rows if r[f] is not None and r[f]!=-10000000.0]
    return round(statistics.median(v),2) if v else None
rest=[r for r in s if r not in seg]
for f in ['rsi','rsi_low','flow_accel','sell_skew_mig','regime_age_h','vol_low_vs_med',
          'buy_sell_ratio4','bars_since_sell','macro_bear','macro_bull','h1_trend',
          'dist_demand_atr','atr_regime','disp4_atr','low_closepos','path_eff']:
    print(f"{f:18s} streak_med={med(seg,f)!s:>8}  rest_med={med(rest,f)!s:>8}")
print("\nall losing runs >=8:")
for ln,a,b in runs:
    print(f"  len {ln} block {s[a]['block']} t {s[a]['low_t']}..{s[b]['low_t']}")
