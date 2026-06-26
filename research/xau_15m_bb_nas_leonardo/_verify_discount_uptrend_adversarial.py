#!/usr/bin/env python3
"""
Second-pass adversarial checks on DISCOUNT+UPTREND rule.
  - R distribution / cap concentration (is avgR carried by a few +20R caps?)
  - WR robustness vs 20% drop (statistical power)
  - multiple-testing context: how strong is this vs a random AND of two
    centered cut features? (crude permutation of which two features)
  - is the rule a disguise of macro_bull / outcome leakage?
  - look-ahead: features are all bar-of-reclaim snapshots; confirm none is outcome.
"""
import json, collections, random, math

PATH="entry_dataset.jsonl"
rows=[json.loads(l) for l in open(PATH)]

def sel_rule(rs):
    return [r for r in rs if r["dist_ema_atr"]<0 and r["ema_slope_atr"]>0]

sel=sel_rule(rows)
Rs=[r["R_reclaim"] for r in sel]
n=len(sel); avg=sum(Rs)/n; wr=sum(1 for x in Rs if x>0)/n

# R distribution
caps=[x for x in Rs if x>=19.9]
print(f"n={n} avgR={avg:.3f} WR={wr*100:.1f}%")
print(f"count R>=19.9 (cap hits): {len(caps)}  sum from caps={sum(caps):.1f} ({100*sum(caps)/sum(Rs):.0f}% of total sumR)")
hist=collections.Counter(round(x) for x in Rs)
print("R rounded hist (top):", dict(sorted(hist.items())))

# how much avgR from top-k
srt=sorted(Rs,reverse=True)
for k in [1,2,5,10,20]:
    rem=srt[k:]
    print(f"  ex-top{k}: avgR={sum(rem)/len(rem):.3f}")

# WR power: Wilson 95% lower bound on WR
def wilson_lo(k,n,z=1.96):
    if n==0: return float('nan')
    p=k/n
    d=1+z*z/n
    c=p+z*z/(2*n)
    m=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)
    return (c-m)/d
k=sum(1 for x in Rs if x>0)
print(f"\nWR={wr*100:.1f}% Wilson95 lower={wilson_lo(k,n)*100:.1f}% (n={n}) -> 20% relative drop = {wr*0.8*100:.1f}%; detectable? lower bound {'above' if wilson_lo(k,n)>wr*0.8 else 'below'} 0.8*WR")

# circularity: overlap with macro_bull
mb=[r for r in sel if r.get("macro_bull")==1]
print(f"\nmacro_bull within rule: {len(mb)}/{n}")
print("ema_slope>0 essentially = uptrend; correlate with macro_bull on full set:")
full_slope=[r for r in rows if r['ema_slope_atr']>0]
print(f"  ema_slope>0: {len(full_slope)}, of which macro_bull=1: {sum(1 for r in full_slope if r.get('macro_bull')==1)}")

# Multiple-testing crude null: take all numeric features, for each pick a sign cut at 0
# and form AND with a second feature; how many random 2-feature ANDs beat avgR=1.238?
num_keys=[k for k in rows[0] if isinstance(rows[0][k],(int,float)) and k not in
          ('R_reclaim','R_8atr','held8','runner','near_M8','yr','low_t','low_idx','reclaim_idx')]
random.seed(7)
beat=0; trials=2000; valid_trials=0
for _ in range(trials):
    a,b=random.sample(num_keys,2)
    sa=random.choice([1,-1]); sb=random.choice([1,-1])
    s=[r for r in rows if (r[a]*sa>0) and (r[b]*sb>0)]
    if len(s)<150: continue
    valid_trials+=1
    aa=sum(r['R_reclaim'] for r in s)/len(s)
    if aa>=1.238: beat+=1
print(f"\nMulti-test null: random 2-feature sign-ANDs (n>=150): {beat}/{valid_trials} beat avgR>=1.238 ({100*beat/max(valid_trials,1):.1f}%)")

# stationarity sign check already done; confirm no year/block negative
by_year=collections.defaultdict(list); by_block=collections.defaultdict(list)
for r in sel:
    by_year[r['yr']].append(r['R_reclaim']); by_block[r['block']].append(r['R_reclaim'])
print("\nyear avgR signs:", {y:round(sum(v)/len(v),2) for y,v in sorted(by_year.items())})
print("block avgR signs:", {b:round(sum(v)/len(v),2) for b,v in sorted(by_block.items())})
print("any negative year:", any(sum(v)/len(v)<0 for v in by_year.values()))
print("any negative block:", any(sum(v)/len(v)<0 for v in by_block.values()))
