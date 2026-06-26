"""DA: cap sensitivity + WR<50 + win/loss anatomy for the rule subset.
RULE: macro_drop_atr<4 & disp4_atr<-0.5 on R_reclaim, all rows.
"""
import json
rows=[json.loads(l) for l in open('entry_dataset.jsonl')]
s=[r for r in rows if r['macro_drop_atr']<4 and r['disp4_atr']<-0.5]
v=[r['R_reclaim'] for r in s]
n=len(v)
print(f"n={n} avgR={sum(v)/n:.3f} WR={sum(1 for x in v if x>0)/n*100:.1f}")
# cap occupancy
caps=sum(1 for x in v if x>=19.99)
print(f"trades at +20R cap: {caps} ({caps/n*100:.1f}%)  sumR from caps={caps*20} of {sum(v):.0f}")
# distribution
losers=[x for x in v if x<=0]; winners=[x for x in v if x>0]
print(f"losers n={len(losers)} avg={sum(losers)/len(losers):.3f}")
print(f"winners n={len(winners)} avg={sum(winners)/len(winners):.3f}")
# recompute avgR with cap lowered to +10R and +5R (robustness to convexity assumption)
for cap in [20,10,5,3]:
    vc=[min(x,cap) for x in v]
    print(f"  cap={cap:2d}R -> avgR={sum(vc)/n:.3f}")
# how many distinct winners drive sumR: cumulative
sv=sorted(v,reverse=True)
import itertools
cum=0; tot=sum(v)
for k in (5,10,20,30):
    print(f"  top{k} contribute {sum(sv[:k]):.0f}R = {sum(sv[:k])/tot*100:.0f}% of sumR")
