#!/usr/bin/env python3
"""
Adversarial verification of entry rule: macro_drop_atr < 3.8
Reported: n=765 WR=0.488 avgR=1.054 y24=1.152 y25=1.018 y26=0.893

DA checks (Cris ruler):
 - reproduce rule
 - avgR per YEAR (sign-flip = non-stationary)
 - leave-one-block-out (worst fold)
 - ex-top2 (carried by 1-2 trades?)
 - multiple-testing skepticism: scan a grid of thresholds to see if 3.8 is a
   genuine plateau peak or a cherry-picked spike.
 - look-ahead / near_M8 sanity (feature must be from reclaim bar)
"""
import json
from collections import defaultdict

PATH = "entry_dataset.jsonl"
rows = [json.loads(l) for l in open(PATH)]


def stats(rs):
    n = len(rs)
    if n == 0:
        return 0, 0.0, 0.0
    w = sum(1 for r in rs if r["R_reclaim"] > 0)
    s = sum(r["R_reclaim"] for r in rs)
    return n, w / n, s / n


def report(name, rs):
    n, wr, ar = stats(rs)
    print(f"{name:32s} n={n:4d} WR={wr:.3f} avgR={ar:.3f} sumR={ar*n:+.1f}")
    return n, wr, ar


print("=== BASELINE ===")
report("FULL universe", rows)

print("\n=== RULE macro_drop_atr < 3.8 ===")
sub = [r for r in rows if r["macro_drop_atr"] < 3.8]
report("rule", sub)

print("\n=== PER YEAR ===")
peryear = {}
for yr in sorted(set(r["yr"] for r in sub)):
    rs = [r for r in sub if r["yr"] == yr]
    n, wr, ar = report(f"y{yr}", rs)
    peryear[yr] = ar
# stationarity: sign flip across years?
sign_flip = (min(peryear.values()) < 0) and (max(peryear.values()) > 0)
peryear_ok = (not sign_flip) and all(v > 0 for v in peryear.values())
print("per-year all positive (no sign flip):", peryear_ok, peryear)

print("\n=== LEAVE-ONE-BLOCK-OUT ===")
blocks = sorted(set(r["block"] for r in sub))
lobo = {}
for b in blocks:
    rest = [r for r in sub if r["block"] != b]
    n, wr, ar = report(f"ex {b}", rest)
    lobo[b] = ar
worst_lobo = min(lobo.values())
print("worst leave-one-block-out avgR:", round(worst_lobo, 3))

print("\n=== PER-BLOCK (held-out single block stationarity) ===")
perblock = {}
for b in blocks:
    rs = [r for r in sub if r["block"] == b]
    n, wr, ar = report(f"block {b}", rs)
    perblock[b] = ar
block_sign_flip = (min(perblock.values()) < 0) and (max(perblock.values()) > 0)
print("per-block sign flip present:", block_sign_flip,
      "min", round(min(perblock.values()), 3), "max", round(max(perblock.values()), 3))

print("\n=== EX-TOP2 (carried by 1-2 trades?) ===")
ssub = sorted(sub, key=lambda r: r["R_reclaim"], reverse=True)
top2 = ssub[:2]
print("top2 R:", [round(r["R_reclaim"], 2) for r in top2])
extop2 = ssub[2:]
n0, wr0, ar0 = stats(sub)
n1, wr1, ar1 = stats(extop2)
print(f"with top2:  avgR={ar0:.3f}")
print(f"ex-top2:    avgR={ar1:.3f}  (drop {ar0-ar1:+.3f})")
# also full-universe ex-top2 for reference
fn, fwr, far = stats(rows)
print(f"ex-top2 still beats FULL avgR {far:.3f}?", ar1 > far)

print("\n=== MULTIPLE-TESTING: threshold grid (is 3.8 a plateau peak or spike?) ===")
print(f"{'thr':>5} {'n':>5} {'WR':>6} {'avgR':>7}")
for thr in [2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 5.0]:
    rs = [r for r in rows if r["macro_drop_atr"] < thr]
    n, wr, ar = stats(rs)
    print(f"{thr:>5} {n:>5} {wr:>6.3f} {ar:>7.3f}")

print("\n=== LOOK-AHEAD SANITY (near_M8 / R_8atr not used as feature; macro_drop from reclaim) ===")
# near_M8 distribution within rule vs full — feature should be independent input, here
# we only confirm the rule does NOT condition on outcome fields.
nm8_sub = sum(r["near_M8"] for r in sub)
print("near_M8 count in subset (informational only):", nm8_sub)

print("\nDONE")
