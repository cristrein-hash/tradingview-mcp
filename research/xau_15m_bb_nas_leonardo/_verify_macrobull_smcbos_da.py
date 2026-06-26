#!/usr/bin/env python3
"""
Devil's Advocate follow-up for rule macro_bull==1 AND smc_bos==1.
1. Confirm rule features are NOT outcome-derived (held8/runner/near_M8/R_8atr).
2. Re-run multiple-testing scan EXCLUDING outcome-derived features,
   to get an honest count of legitimate entry-rules that beat base.
3. Block-bootstrap-ish: worst per-block STANDALONE avgR (thin 2026 block).
"""
import json, itertools
from collections import defaultdict

ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
RKEY = 'R_reclaim'
OUTCOME = {'held8', 'runner', 'near_M8', 'R_8atr', 'R_reclaim'}  # must never be a feature

def avg(xs): return sum(xs)/len(xs) if xs else float('nan')
def stats(sub):
    rs=[r[RKEY] for r in sub]
    return dict(n=len(sub), wr=sum(1 for r in sub if r[RKEY]>0)/len(sub) if sub else 0,
                avgR=avg(rs), sumR=sum(rs))

base=stats(ROWS)
print(f"BASE n={base['n']} avgR={base['avgR']:.3f}")
print(f"Rule features macro_bull/smc_bos in OUTCOME set? "
      f"{'macro_bull' in OUTCOME} / {'smc_bos' in OUTCOME}  -> both False = NOT outcome-leak")

# legitimate (entry-time) binary features only
legit = ['macro_bull','macro_bear','killzone','sell_S','sell_M','sell_L',
         'buy_S','buy_M','buy_L','smc_bos==1','smc_choch==1']
def fok(r,f):
    if f=='smc_bos==1': return r.get('smc_bos')==1
    if f=='smc_choch==1': return r.get('smc_choch')==1
    return r.get(f)==1

print('\n=== LEGITIMATE 2-feature AND-rules (n>=150) beating base by >=0.3 avgR ===')
hits=[]
for a,b in itertools.combinations(legit,2):
    sub=[r for r in ROWS if fok(r,a) and fok(r,b)]
    if len(sub)>=150:
        st=stats(sub)
        if st['avgR']-base['avgR']>=0.3:
            hits.append((a,b,st['n'],st['avgR']))
hits.sort(key=lambda x:-x[3])
total_pairs=sum(1 for a,b in itertools.combinations(legit,2)
                if len([r for r in ROWS if fok(r,a) and fok(r,b)])>=150)
print(f"  pairs tested (n>=150): {total_pairs}; pairs beating base by >=0.3: {len(hits)}")
for a,b,n,ar in hits:
    print(f"    {a} & {b}: n={n} avgR={ar:+.3f}")

# single-feature ranking for context (is smc_bos or macro_bull doing the work alone?)
print('\n=== SINGLE-FEATURE avgR (legit) ===')
for f in legit:
    sub=[r for r in ROWS if fok(r,f)]
    if len(sub)>=100:
        st=stats(sub)
        print(f"  {f}: n={st['n']:4d} avgR={st['avgR']:+.3f}")

# the two halves: macro_bull alone vs smc_bos==1 alone vs the AND
mb=[r for r in ROWS if r.get('macro_bull')==1]
bos=[r for r in ROWS if r.get('smc_bos')==1]
both=[r for r in ROWS if r.get('macro_bull')==1 and r.get('smc_bos')==1]
print('\n=== DECOMPOSITION ===')
for nm,sub in [('macro_bull',mb),('smc_bos==1',bos),('AND',both)]:
    st=stats(sub); print(f"  {nm}: n={st['n']:4d} avgR={st['avgR']:+.3f} sumR={st['sumR']:+.1f}")

# thin-block stress: 2026-02-25 standalone n and avgR already known; report min-n block
print('\n=== THIN BLOCK ===')
bymin=defaultdict(list)
for r in both: bymin[r['block']].append(r)
mn=min(bymin, key=lambda b: len(bymin[b]))
st=stats(bymin[mn])
print(f"  thinnest block {mn}: n={st['n']} avgR={st['avgR']:+.3f} (still positive={st['avgR']>0})")
