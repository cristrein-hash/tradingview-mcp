#!/usr/bin/env python3
"""
DEVIL'S ADVOCATE verification of entry rule:
  DISCOUNT+UPTREND + macro discount:
    dist_ema_atr < 0  AND  ema_slope_atr > 0  AND  macro_retr > 0.7

Reported: n=190 WR=45 avgR=1.64 y24=1.45 y25=1.78 y26=1.55, ex-top5 +1.15.

Outcome column: R_reclaim (the R of the trade at reclaim entry).
Audits:
  - reproduce n / WR / avgR
  - avgR per YEAR
  - leave-one-BLOCK-out (worst fold avgR)
  - ex-top1 / ex-top2 / ex-top5 (drop the most positive R trades)
  - look-ahead / leakage check on the feature columns used
"""
import json
from collections import defaultdict

PATH = "entry_dataset.jsonl"
rows = [json.loads(l) for l in open(PATH)]

OUT = "R_reclaim"  # realized R of the entry


def rule(r):
    de = r.get("dist_ema_atr")
    es = r.get("ema_slope_atr")
    mr = r.get("macro_retr")
    if de is None or es is None or mr is None:
        return False
    return (de < 0) and (es > 0) and (mr > 0.7)


def stats(sub):
    n = len(sub)
    if n == 0:
        return 0, 0.0, 0.0
    Rs = [s[OUT] for s in sub if s[OUT] is not None]
    n = len(Rs)
    wr = 100.0 * sum(1 for x in Rs if x > 0) / n if n else 0.0
    avg = sum(Rs) / n if n else 0.0
    return n, wr, avg


sel = [r for r in rows if rule(r) and r.get(OUT) is not None]
n, wr, avg = stats(sel)
print(f"=== FULL RULE on {OUT} ===")
print(f"n={n}  WR={wr:.1f}%  avgR={avg:.3f}  sumR={sum(s[OUT] for s in sel):.1f}")

# per year
print("\n=== per YEAR ===")
by_yr = defaultdict(list)
for s in sel:
    by_yr[s["yr"]].append(s)
for yr in sorted(by_yr):
    ny, wy, ay = stats(by_yr[yr])
    print(f"  y{yr}: n={ny}  WR={wy:.1f}%  avgR={ay:.3f}")

# leave-one-block-out
print("\n=== leave-one-BLOCK-out (avgR of the REMAINING data) ===")
blocks = sorted(set(s["block"] for s in sel))
folds = []
for b in blocks:
    rest = [s for s in sel if s["block"] != b]
    nb, wb, ab = stats(rest)
    held = [s for s in sel if s["block"] == b]
    nh, wh, ah = stats(held)
    folds.append((b, ab, nh, ah))
    print(f"  drop {b}: remaining n={nb} avgR={ab:.3f}  |  held-out block n={nh} avgR={ah:.3f}")
worst_fold = min(folds, key=lambda x: x[1])
print(f"  WORST remaining-fold avgR = {worst_fold[1]:.3f} (when dropping {worst_fold[0]})")

# also per-block avgR sign check (non-stationarity)
print("\n=== per-BLOCK avgR (sign / stability) ===")
neg_blocks = 0
for b in blocks:
    held = [s for s in sel if s["block"] == b]
    nh, wh, ah = stats(held)
    flag = " <-- NEG" if ah < 0 else ""
    if ah < 0:
        neg_blocks += 1
    print(f"  {b}: n={nh}  avgR={ah:.3f}{flag}")
print(f"  blocks with negative avgR: {neg_blocks}/{len(blocks)}")

# ex-topK
print("\n=== ex-topK (remove K most-positive trades) ===")
Rs = sorted([s[OUT] for s in sel], reverse=True)
for K in [0, 1, 2, 5]:
    rem = Rs[K:]
    a = sum(rem) / len(rem) if rem else 0.0
    print(f"  ex-top{K}: n={len(rem)}  avgR={a:.3f}  top removed={Rs[:K]}")

# concentration: share of total positive R from top trades
pos_sum = sum(x for x in Rs if x > 0)
print(f"\n  total sumR={sum(Rs):.1f}  pos_sum={pos_sum:.1f}")
print(f"  top1 R={Rs[0]:.2f} = {100*Rs[0]/sum(Rs):.0f}% of net sumR")
print(f"  top2 R sum={sum(Rs[:2]):.2f} = {100*sum(Rs[:2])/sum(Rs):.0f}% of net sumR")
print(f"  top5 R sum={sum(Rs[:5]):.2f} = {100*sum(Rs[:5])/sum(Rs):.0f}% of net sumR")

# leakage check: is rule using any outcome-derived feature?
print("\n=== leakage / look-ahead check ===")
print("features used: dist_ema_atr, ema_slope_atr, macro_retr")
print("none of these are outcome columns (R_reclaim/runner/R_8atr/held8/near_M8).")
print("ema_slope_atr>0 = UPTREND condition; conflicts with the stated DISCOUNT name but not look-ahead.")

# ---- power / dispersion (DA questions 4 & 5) ----
import math
Rsel = [s[OUT] for s in sel]
mean = sum(Rsel) / len(Rsel)
sd = math.sqrt(sum((x - mean) ** 2 for x in Rsel) / (len(Rsel) - 1))
se = sd / math.sqrt(len(Rsel))
print("\n=== power / dispersion ===")
print(f"mean={mean:.3f} sd={sd:.2f} se={se:.3f} t={mean/se:.2f} lower95(mean-2se)={mean-2*se:.3f}")
print(f"full losers (R<=-0.99): {sum(1 for x in Rsel if x <= -0.99)}/{len(Rsel)}")
print(f"cap winners (R>=18): {sum(1 for x in Rsel if x >= 18)}/{len(Rsel)}")
# the 20.0 R values are CAPS (R_8atr style cap) -> convexity, not single-trade artifact

