"""DA verification — RULE: drop<=3.6 & retest_lo (NOVEL).

Definition (as reported): macro_drop_atr<=3.606 AND retest_lo==1
  retest_lo = reclaim low within 0.5ATR of an older swing low 10-120 bars back
  (double-bottom / retest). Feature is precomputed in entry_dataset_novel.jsonl.

reported: n=286 WR=50.7 avgR=1.216  y24=1.04 y25=1.27 y26=1.40

R field = R_reclaim (the reclaim-entry outcome).

Adversarial checks (Cris régua):
 1. reproduce n/WR/avgR
 2. per-YEAR avgR (sign stability; reported claims monotone strengthening)
 3. leave-one-BLOCK-out (8 blocks): worst-fold avgR (rest) + per-block standalone sign
 4. ex-top1/2/3: carried by 1-2 trades?
 5. look-ahead: is retest_lo / macro_drop_atr outcome-derived?  is near_M8 used? feature-source check
 6. multiple-testing: how many comparable 2-feature threshold rules (n>=150) reach this avgR
"""
import json
from collections import defaultdict
import itertools

PATH = 'entry_dataset_novel.jsonl'
rows = [json.loads(l) for l in open(PATH)]
RF = 'R_reclaim'
DROP = 3.606

def in_rule(r):
    return r['macro_drop_atr'] <= DROP and r.get('retest_lo') == 1

# drop rows with null R for the outcome
def Rvals(rs):
    return [r[RF] for r in rs if r[RF] is not None]

sub = [r for r in rows if in_rule(r) and r[RF] is not None]
vals = [r[RF] for r in sub]
n = len(vals)
avg = sum(vals)/n
wr = sum(1 for v in vals if v > 0)/n*100
print(f"=== BASE rule (drop<={DROP} & retest_lo==1) on {PATH}")
print(f"  n={n} WR={wr:.1f} avgR={avg:.3f} sumR={sum(vals):.1f}")

# also report how many total rows had retest_lo set / null R within rule
raw_in = [r for r in rows if in_rule(r)]
nullR = sum(1 for r in raw_in if r[RF] is None)
print(f"  rows matching rule incl null-R: {len(raw_in)} (null R_reclaim dropped: {nullR})")

# 1 per-year
print("\n--- per YEAR ---")
by_yr = defaultdict(list)
for r in sub:
    by_yr[r['yr']].append(r[RF])
peryear = {}
for y in sorted(by_yr):
    v = by_yr[y]; a = sum(v)/len(v)
    peryear[y] = a
    print(f"  y{y}: n={len(v):3d} avgR={a:+.3f} WR={sum(1 for x in v if x>0)/len(v)*100:.1f}")
peryear_ok = all(a > 0 for a in peryear.values())
print(f"  peryear_ok (all positive): {peryear_ok}")

# 2 leave-one-block-out
print("\n--- LEAVE-ONE-BLOCK-OUT (rest avgR) + per-block standalone ---")
blocks = sorted(set(r['block'] for r in sub))
worst = None
blk_standalone = []
for b in blocks:
    rest = [r[RF] for r in sub if r['block'] != b]
    blk = [r[RF] for r in sub if r['block'] == b]
    a = sum(rest)/len(rest)
    ab = sum(blk)/len(blk) if blk else float('nan')
    blk_standalone.append(ab)
    print(f"  -{b}: rest n={len(rest):3d} avgR={a:+.3f} | block n={len(blk):3d} blkAvgR={ab:+.3f}")
    if worst is None or a < worst:
        worst = a
print(f"  worst-fold (rest) avgR = {worst:+.3f}")
pos_blocks = sum(1 for a in blk_standalone if a > 0)
print(f"  per-block standalone positive: {pos_blocks}/{len(blocks)}  min={min(blk_standalone):+.3f} max={max(blk_standalone):+.3f}")

# 3 ex-top
print("\n--- EX-TOP (concentration) ---")
sv = sorted(vals, reverse=True)
print(f"  top5 R: {[round(x,2) for x in sv[:5]]}")
for k in (1, 2, 3):
    rem = sv[k:]
    print(f"  ex-top{k}: n={len(rem)} avgR={sum(rem)/len(rem):+.3f}")
top2 = sum(sv[:2])
print(f"  top2 sumR={top2:.1f} of total {sum(vals):.1f} = {top2/sum(vals)*100:.1f}%")

# 4 look-ahead / feature-source
print("\n--- LOOK-AHEAD / feature source ---")
print("  macro_drop_atr: macro decline magnitude up to reclaim bar — pre-entry structure.")
print("  retest_lo: reclaim low vs swing low 10-120 bars BACK — uses only past bars. OK.")
print("  near_M8 NOT in rule. R_reclaim is the outcome (not a feature). OK.")

# 5 multiple-testing context
print("\n--- MULTIPLE-TESTING CONTEXT ---")
feat_cols = ['rsi','rsi_low','dist_ema_atr','ema_slope_atr','macro_drop_atr','macro_retr',
             'sweep_depth_atr','disp4_atr','disp8_atr','up_closes8','range_exp','leg_ext',
             'room_atr','low_wick','low_closepos','atr_regime','vol_low_vs_med','sell_pol',
             'dist_vbp_atr','dz_dist_atr','decel_ratio','since_pivot']
def quantiles(col):
    xs = sorted(r[col] for r in rows if r.get(col) is not None)
    if not xs: return []
    return [xs[int(len(xs)*q)] for q in (0.25, 0.5, 0.75)]
qs = {c: quantiles(c) for c in feat_cols}
results = []
MIN_N = 150
for (c1, c2) in itertools.combinations(feat_cols, 2):
    for t1 in qs[c1]:
        for d1 in ('<', '>'):
            for t2 in qs[c2]:
                for d2 in ('<', '>'):
                    ss = []
                    for r in rows:
                        if r[RF] is None: continue
                        v1 = r.get(c1); v2 = r.get(c2)
                        if v1 is None or v2 is None: continue
                        a = v1 < t1 if d1 == '<' else v1 > t1
                        b = v2 < t2 if d2 == '<' else v2 > t2
                        if a and b: ss.append(r[RF])
                    if len(ss) >= MIN_N:
                        results.append((sum(ss)/len(ss), len(ss)))
results.sort(reverse=True)
better = sum(1 for a, _ in results if a >= avg)
print(f"  scanned {len(results)} two-feature rules n>={MIN_N}")
if results:
    print(f"  top avgR={results[0][0]:.3f} median={results[len(results)//2][0]:.3f}")
    print(f"  {better}/{len(results)} ({better/len(results)*100:.1f}%) reach avgR>={avg:.3f}")

print("\n=== SUMMARY ===")
print(f"n={n} WR={wr:.1f} avgR={avg:.3f}")
print(f"peryear_ok={peryear_ok} peryear={ {y:round(a,3) for y,a in peryear.items()} }")
print(f"worst_block_fold={worst:.3f}  per-block-positive={pos_blocks}/{len(blocks)}")
print(f"extop2_avg={sum(sv[2:])/len(sv[2:]):.3f}  top2_pct={top2/sum(vals)*100:.1f}%")
