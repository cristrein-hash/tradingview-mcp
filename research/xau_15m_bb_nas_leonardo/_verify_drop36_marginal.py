"""DA marginal-lift test: does retest_lo do real work over drop<=3.6 alone?

If drop-alone ~= rule, then retest_lo is a free multiple-testing parameter.
Also: complement (drop & NOT retest) — is it materially worse?
And per-block lift to see if lift is stable or carried by one block.
"""
import json
from collections import defaultdict

rows = [json.loads(l) for l in open('entry_dataset_novel.jsonl')]
RF = 'R_reclaim'
DROP = 3.606

def stats(rs):
    v = [r[RF] for r in rs if r[RF] is not None]
    if not v: return (0, 0.0, 0.0, 0.0)
    return (len(v), sum(1 for x in v if x>0)/len(v)*100, sum(v)/len(v), sum(v))

drop = [r for r in rows if r['macro_drop_atr'] <= DROP and r[RF] is not None]
rule = [r for r in drop if r.get('retest_lo') == 1]
comp = [r for r in drop if r.get('retest_lo') != 1]

print("=== MARGINAL LIFT of retest_lo within drop<=3.606 ===")
for name, rs in (("drop ALONE", drop), ("drop & retest_lo (RULE)", rule), ("drop & NOT retest", comp)):
    n, wr, a, s = stats(rs)
    print(f"  {name:26s}: n={n:3d} WR={wr:5.1f} avgR={a:+.3f} sumR={s:+.1f}")

na, _, aa, _ = stats(drop)
nr, _, ar, _ = stats(rule)
print(f"  lift avgR (rule - dropAlone) = {ar-aa:+.3f}")

print("\n=== per-BLOCK lift (rule vs drop-alone) ===")
blocks = sorted(set(r['block'] for r in drop))
lifts = []
for b in blocks:
    da = [r for r in drop if r['block']==b]
    ru = [r for r in rule if r['block']==b]
    _, _, ada, _ = stats(da)
    _, _, aru, _ = stats(ru)
    lift = aru - ada
    lifts.append(lift)
    print(f"  {b}: dropAlone avgR={ada:+.3f} (n={len(da)}) | rule avgR={aru:+.3f} (n={len(ru)}) | lift={lift:+.3f}")
pos = sum(1 for l in lifts if l>0)
print(f"  blocks where retest_lo helps: {pos}/{len(blocks)}")

print("\n=== near_M8 contamination check (is outcome-ish feature in universe?) ===")
# near_M8 is whether entry sits near a 'true M8 reversal'. Confirm it is NOT in rule and
# show rule performance partitioned by near_M8 to detect if edge depends on it.
for v in (0, 1):
    rs = [r for r in rule if r.get('near_M8') == v]
    n, wr, a, s = stats(rs)
    print(f"  near_M8={v}: n={n:3d} WR={wr:5.1f} avgR={a:+.3f}")
