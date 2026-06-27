"""DA verification — REQUESTED RULE (2026-06-26).

RULE: macro_drop_atr <= 3.606  AND  in_demand == 1
  ("drop<=3.6 & in_demand": low NOT an overextended flush AND low inside a
   pre-existing RAW demand zone, zone born_t <= low_t).
Reported: n=562 WR=49.8 avgR=1.24 y24=1.3 y25=1.21 y26=1.22

IMPORTANT: in_demand only exists in entry_dataset_novel.jsonl (NOT entry_dataset.jsonl).
R field = R_reclaim (matches the reported reproduction convention of sibling _verify_*.py).

Checks (Cris régua — veto only on these):
 1. per-year avgR sign stability
 2. leave-one-block-out (8 blocks) -> worst remaining-fold avgR AND held-out block avgR sign
 3. ex-top1/2/3 — carried by 1-2 trades?
 4. look-ahead: rule features bar-of-reclaim, in_demand causal (born_t<=low_t guarded in builder), no outcome field
 5. multiple-testing: rank of this avgR among many 2-feature threshold rules (n>=MIN_N)
"""
import json, itertools
from collections import defaultdict

DS = 'entry_dataset_novel.jsonl'
RF = 'R_reclaim'
rows = [json.loads(l) for l in open(DS)]

def sel(r):
    return r.get('macro_drop_atr', 99) <= 3.606 and r.get('in_demand', 0) == 1

s = [r for r in rows if sel(r)]
vals = [r[RF] for r in s]
n = len(vals)
avg = sum(vals)/n
wr = sum(1 for v in vals if v > 0)/n*100
print(f"=== BASE: n={n} WR={wr:.1f} avgR={avg:.3f} sumR={sum(vals):.1f}")

# 1. per year
print("\n--- per YEAR ---")
by_yr = defaultdict(list)
for r in s:
    by_yr[r['yr']].append(r[RF])
peryear_signs = []
for y in sorted(by_yr):
    v = by_yr[y]
    a = sum(v)/len(v)
    peryear_signs.append(a)
    print(f"  y{y}: n={len(v):3d} avgR={a:.3f} WR={sum(1 for x in v if x>0)/len(v)*100:.1f}")
peryear_ok = all(a > 0 for a in peryear_signs)
print(f"  peryear_ok (all positive): {peryear_ok}")

# 2. leave-one-block-out
print("\n--- LEAVE-ONE-BLOCK-OUT ---")
blocks = sorted(set(r['block'] for r in s))
worst_rest = None
block_avgs = []
for b in blocks:
    v = [r[RF] for r in s if r['block'] != b]
    a = sum(v)/len(v)
    vb = [r[RF] for r in s if r['block'] == b]
    ab = sum(vb)/len(vb) if vb else float('nan')
    block_avgs.append((b, ab, len(vb)))
    print(f"  drop {b}: rest n={len(v):3d} avgR={a:.3f} | block n={len(vb):3d} blkAvgR={ab:.3f}")
    if worst_rest is None or a < worst_rest:
        worst_rest = a
print(f"  worst-fold (rest) avgR = {worst_rest:.3f}")
blk_pos = sum(1 for _, ab, _ in block_avgs if ab > 0)
print(f"  per-block standalone positive: {blk_pos}/{len(block_avgs)}  "
      f"min block avgR={min(ab for _,ab,_ in block_avgs):.3f}")

# 3. ex-top
print("\n--- EX-TOP ---")
sv = sorted(vals, reverse=True)
print(f"  top5 R: {[round(x,2) for x in sv[:5]]}")
extop = {}
for k in [1, 2, 3]:
    rem = sv[k:]
    a = sum(rem)/len(rem)
    extop[k] = a
    print(f"  ex-top{k}: n={len(rem)} avgR={a:.3f}")
top2sum = sum(sv[:2])
print(f"  top2 sumR={top2sum:.1f} of total {sum(vals):.1f} = {top2sum/sum(vals)*100:.1f}%")

# 4. look-ahead
print("\n--- LOOK-AHEAD ---")
print("  features: macro_drop_atr (pre-low macro decline), in_demand (zone born_t<=low_t, guarded causal in builder).")
print("  neither is an outcome field (R_reclaim/held8/runner/R_8atr/near_M8).")

# 5. multiple-testing context
print("\n--- MULTIPLE-TESTING CONTEXT ---")
feat_cols = ['rsi','rsi_low','dist_ema_atr','ema_slope_atr','macro_drop_atr','macro_retr',
             'sweep_depth_atr','disp4_atr','disp8_atr','up_closes8','range_exp','leg_ext',
             'room_atr','low_wick','low_closepos','atr_regime','vol_low_vs_med','sell_pol',
             'dz_dist_atr','dist_vbp_atr','decel_ratio']
def quantiles(col):
    xs = sorted(r[col] for r in rows if r.get(col) is not None)
    if not xs: return []
    return [xs[int(len(xs)*q)] for q in (0.25, 0.5, 0.75)]
qs = {c: quantiles(c) for c in feat_cols}
results = []
MIN_N = 300
for (c1, c2) in itertools.combinations(feat_cols, 2):
    for t1 in qs[c1]:
        for d1 in ('<', '>'):
            for t2 in qs[c2]:
                for d2 in ('<', '>'):
                    ss = []
                    for r in rows:
                        v1 = r.get(c1); v2 = r.get(c2)
                        if v1 is None or v2 is None: continue
                        a1 = v1 < t1 if d1 == '<' else v1 > t1
                        b1 = v2 < t2 if d2 == '<' else v2 > t2
                        if a1 and b1:
                            ss.append(r[RF])
                    if len(ss) >= MIN_N:
                        results.append((sum(ss)/len(ss), len(ss), f"{c1}{d1}{t1:.3g} & {c2}{d2}{t2:.3g}"))
results.sort(reverse=True)
if results:
    better = sum(1 for a, _, _ in results if a >= avg)
    print(f"  scanned {len(results)} rules n>={MIN_N}; top avgR={results[0][0]:.3f} "
          f"median={results[len(results)//2][0]:.3f}")
    print(f"  rules reaching avgR>={avg:.3f}: {better}/{len(results)} ({better/len(results)*100:.1f}%)")

# summary
print("\n=== SUMMARY ===")
print(f"avgR={avg:.3f} WR={wr:.1f} n={n}")
print(f"peryear_ok={peryear_ok} signs={[round(a,3) for a in peryear_signs]}")
print(f"worst_block_rest_fold={worst_rest:.3f}")
print(f"per-block standalone positive {blk_pos}/{len(block_avgs)}")
print(f"ex-top2 avgR={extop[2]:.3f} (vs base {avg:.3f})")
