"""Which component carries survival: drop<=3.6 alone vs the novel retest_lo add?
Per-block standalone sign for drop-alone, plus a permutation check:
how often does a RANDOM binary feature with same marginal frequency (~40%)
produce a >=+0.156 lift inside the drop universe (multiple-testing null)?
"""
import json, random
from collections import defaultdict

rows = [json.loads(l) for l in open('entry_dataset_novel.jsonl')]
RF = 'R_reclaim'
DROP = 3.606
drop = [r for r in rows if r['macro_drop_atr'] <= DROP and r[RF] is not None]

def avg(rs):
    v=[r[RF] for r in rs]; return sum(v)/len(v) if v else 0.0

print("=== drop<=3.606 ALONE, per-block standalone ===")
blocks = sorted(set(r['block'] for r in drop))
da_signs=[]
for b in blocks:
    rs=[r for r in drop if r['block']==b]
    a=avg(rs); da_signs.append(a)
    print(f"  {b}: n={len(rs):3d} avgR={a:+.3f}")
print(f"  drop-alone per-block positive: {sum(1 for a in da_signs if a>0)}/{len(blocks)} min={min(da_signs):+.3f}")

# permutation null for the +0.156 lift
base_avg = avg(drop)
rule = [r for r in drop if r.get('retest_lo')==1]
real_lift = avg(rule) - base_avg
frac = len(rule)/len(drop)
Rs = [r[RF] for r in drop]
N = len(Rs); k = len(rule)
print(f"\n=== permutation null: random subset of size {k} (frac {frac:.2f}) of drop universe ===")
random.seed(0)
hits=0; TRIALS=20000
for _ in range(TRIALS):
    samp = random.sample(Rs, k)
    lift = sum(samp)/k - base_avg
    if lift >= real_lift: hits+=1
print(f"  real lift={real_lift:+.3f}  p(random subset >= lift)={hits/TRIALS:.3f}")
print("  (high p = lift indistinguishable from a random {0}-subset of drop universe)".format(k))
