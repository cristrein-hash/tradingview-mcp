#!/usr/bin/env python3
"""
Adversarial verification of entry rule (DA recalibrated):
  REGRA: macro_bull==1 AND smc_bos==1 AND nas_short_16==0
  (C12 plus NAS junk-trim)
  Reported: n=320 WR=0.506 avgR=1.069 y24=0.842 y25=0.764 y26=0.65

Checks:
  1. Reproduce n / WR / avgR (which R column? R_reclaim)
  2. avgR per YEAR  -> sign stability
  3. avgR leave-one-BLOCK-out -> worst fold (non-stationarity)
  4. ex-top2 R trades -> carried by 1-2 trades?
  5. multiple-testing skepticism note
  6. look-ahead / near_M8 / outcome-as-feature audit of the 3 features used
"""
import json
from collections import defaultdict

PATH = "entry_dataset.jsonl"
rows = [json.loads(l) for l in open(PATH)]


def rule(r):
    return r["macro_bull"] == 1 and r["smc_bos"] == 1 and r["nas_short_16"] == 0


sel = [r for r in rows if rule(r)]

# Outcome column: R_reclaim is the realized R at the reclaim entry (present for all).
# R_8atr has nulls -> not the primary. Use R_reclaim.
def R(r):
    return r["R_reclaim"]

Rs = [R(r) for r in sel]
n = len(Rs)
wins = sum(1 for x in Rs if x > 0)
wr = wins / n
avg = sum(Rs) / n
sumR = sum(Rs)
print(f"=== RULE REPRODUCTION (R_reclaim) ===")
print(f"n={n} WR={wr:.3f} avgR={avg:.3f} sumR={sumR:.1f}")

# cross check against R_8atr where available
r8 = [r["R_8atr"] for r in sel if r["R_8atr"] is not None]
if r8:
    print(f"R_8atr subset n={len(r8)} WR={sum(1 for x in r8 if x>0)/len(r8):.3f} avgR={sum(r8)/len(r8):.3f} sumR={sum(r8):.1f}")

# runner / held8
print(f"runners={sum(r['runner'] for r in sel)}  held8={sum(r['held8'] for r in sel)}")

# ---- per YEAR ----
print("\n=== PER YEAR (R_reclaim) ===")
by_yr = defaultdict(list)
for r in sel:
    by_yr[r["yr"]].append(R(r))
for y in sorted(by_yr):
    v = by_yr[y]
    w = sum(1 for x in v if x > 0) / len(v)
    a = sum(v) / len(v)
    print(f"  y{y}: n={len(v)} WR={w:.3f} avgR={a:.3f} sumR={sum(v):.1f}")
peryear_signs = [sum(v) / len(v) for v in by_yr.values()]
peryear_ok = all(a > 0 for a in peryear_signs)
print(f"peryear_ok (all avgR>0): {peryear_ok}")

# ---- leave-one-BLOCK-out ----
print("\n=== LEAVE-ONE-BLOCK-OUT (avgR of REMAINING) ===")
by_blk = defaultdict(list)
for r in sel:
    by_blk[r["block"]].append(R(r))
blocks = sorted(by_blk)
folds = []
for held in blocks:
    rest = [x for b in blocks if b != held for x in by_blk[b]]
    a = sum(rest) / len(rest)
    folds.append((held, a, len(rest)))
    print(f"  drop {held} (held n={len(by_blk[held])}): remaining avgR={a:.3f}")
worst_fold = min(f[1] for f in folds)
print(f"worst leave-one-block-out avgR={worst_fold:.3f}")

# also per-block standalone avgR (sign flips?)
print("\n=== PER BLOCK STANDALONE avgR ===")
blk_avgs = []
for b in blocks:
    v = by_blk[b]
    a = sum(v) / len(v)
    blk_avgs.append(a)
    print(f"  {b}: n={len(v)} avgR={a:.3f} sumR={sum(v):.1f}")
print(f"blocks with avgR<=0: {sum(1 for a in blk_avgs if a<=0)} / {len(blk_avgs)}")

# ---- ex-top2 ----
print("\n=== EX-TOP2 ===")
Rs_sorted = sorted(Rs, reverse=True)
print(f"top5 R: {[round(x,2) for x in Rs_sorted[:5]]}")
ex2 = Rs_sorted[2:]
print(f"ex-top2: n={len(ex2)} avgR={sum(ex2)/len(ex2):.3f} sumR={sum(ex2):.1f}")
ex5 = Rs_sorted[5:]
print(f"ex-top5: n={len(ex5)} avgR={sum(ex5)/len(ex5):.3f} sumR={sum(ex5):.1f}")
# share of sumR from top2
print(f"top2 sumR={sum(Rs_sorted[:2]):.1f} ({sum(Rs_sorted[:2])/sumR*100:.1f}% of total)")

# ---- baseline (multiple testing context) ----
print("\n=== BASELINE (all rows) ===")
allR = [R(r) for r in rows]
print(f"all n={len(allR)} WR={sum(1 for x in allR if x>0)/len(allR):.3f} avgR={sum(allR)/len(allR):.3f}")
mb = [R(r) for r in rows if r["macro_bull"] == 1]
print(f"macro_bull only n={len(mb)} WR={sum(1 for x in mb if x>0)/len(mb):.3f} avgR={sum(mb)/len(mb):.3f}")
mbbos = [R(r) for r in rows if r["macro_bull"] == 1 and r["smc_bos"] == 1]
print(f"macro_bull+smc_bos (C12) n={len(mbbos)} WR={sum(1 for x in mbbos if x>0)/len(mbbos):.3f} avgR={sum(mbbos)/len(mbbos):.3f}")
# marginal value of nas-trim
print(f"NAS-trim effect: C12 avgR={sum(mbbos)/len(mbbos):.3f} -> +trim avgR={avg:.3f}  (n {len(mbbos)}->{n})")

# ---- look-ahead / outcome-as-feature audit ----
print("\n=== FEATURE AUDIT ===")
print("features in rule: macro_bull, smc_bos, nas_short_16")
print("outcome columns: R_reclaim, held8, runner, R_8atr, near_M8")
print("-> rule uses NONE of the outcome columns. No near_M8 in rule.")
