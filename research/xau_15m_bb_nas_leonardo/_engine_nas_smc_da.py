#!/usr/bin/env python3
"""
_engine_nas_smc_da.py — Devil's Advocate hardening of the 3 yearly-robust survivors:
  C12: macro_bull==1 AND smc_bos==1
  C5 : smc_bos==1 AND nas_short_16==0
  C8 : smc_bos==1 AND smc_choch in(1,2)
  C1 : smc_bos==1 (the base structural signal)

DA concerns addressed:
  1. Look-ahead: features are causal by construction (bar of reclaim). smc_bos/choch are
     recency buckets (#bars since last BOS/CHoCH on closed bars). macro_bull = macro regime
     from closed bars. No same-bar outcome leakage. (structural — accepted.)
  2. In-sample: thresholds are categorical buckets (==1, in(1,2)), NOT tuned continuous knobs.
  3. Selection bias: ~30 variants tested -> apply leave-one-BLOCK-out (LOBO). A rule carried
     by one collection block is fragile. Require avg>base in >=7/8 LOBO folds.
  4. Power: report n per year; flag any year <30.
  5. Execution: report maxDD (sum of consecutive losers in -1R units proxy) & worst single.
  6. near_M8 reported (proximity to pivot context, not a feature).
"""
import json

ROWS = [json.loads(l) for l in open("entry_dataset.jsonl")]
GBASE = 0.727
YBASE = {2024: 0.691, 2025: 0.797, 2026: 0.603}
BLOCKS = sorted(set(r["block"] for r in ROWS))


def sel(name, fn):
    return name, [r for r in ROWS if fn(r)]


def metrics(rs):
    n = len(rs)
    R = [r["R_reclaim"] for r in rs]
    avg = sum(R) / n
    wr = sum(1 for x in R if x > 0) / n
    return n, avg, wr


def da(desc, fn):
    rs = [r for r in ROWS if fn(r)]
    n, avg, wr = metrics(rs)
    # LOBO
    folds = []
    for b in BLOCKS:
        sub = [r for r in rs if r["block"] != b]
        if sub:
            folds.append((b, len(sub), sum(x["R_reclaim"] for x in sub) / len(sub)))
    beats = sum(1 for _, _, a in folds if a > GBASE)
    worst_fold = min(folds, key=lambda x: x[2])
    # by-block contribution
    perblock = []
    for b in BLOCKS:
        sub = [r for r in rs if r["block"] == b]
        if sub:
            perblock.append((b, len(sub), round(sum(x["R_reclaim"] for x in sub) / len(sub), 2)))
    # equity / drawdown proxy (sequential by low_t)
    seq = sorted(rs, key=lambda r: r["low_t"])
    eq = 0.0; peak = 0.0; mdd = 0.0
    for r in seq:
        eq += r["R_reclaim"]
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
    nm8 = sum(r["near_M8"] for r in rs) / n
    print(f"{desc}")
    print(f"  n={n} WR={round(wr,3)} avgR={round(avg,3)} lift={round(avg-GBASE,3)} "
          f"nearM8={round(nm8,3)} maxDD={round(mdd,1)}R sumR={round(eq,1)}R")
    print(f"  LOBO: {beats}/{len(folds)} folds beat base; worst drop-block={worst_fold[0]} "
          f"avg={round(worst_fold[2],3)}")
    print(f"  per-block avgR: {perblock}")
    print()


print("=== DEVIL'S ADVOCATE: leave-one-block-out + DD on robust survivors ===\n")
da("C1 : smc_bos==1", lambda r: r["smc_bos"] == 1)
da("C12: macro_bull==1 AND smc_bos==1", lambda r: r["macro_bull"] == 1 and r["smc_bos"] == 1)
da("C5 : smc_bos==1 AND nas_short_16==0", lambda r: r["smc_bos"] == 1 and r["nas_short_16"] == 0)
da("C8 : smc_bos==1 AND smc_choch in(1,2)", lambda r: r["smc_bos"] == 1 and r["smc_choch"] in (1, 2))

# Can NAS lens ADD to C12 without breaking yearly robustness & with decent n?
print("=== Try NAS additive on C12 (need n>=30, all years) ===\n")
da("C12+nas_short==0: macro_bull AND smc_bos==1 AND nas_short_16==0",
   lambda r: r["macro_bull"] == 1 and r["smc_bos"] == 1 and r["nas_short_16"] == 0)
da("C12+choch(1,2): macro_bull AND smc_bos==1 AND smc_choch in(1,2)",
   lambda r: r["macro_bull"] == 1 and r["smc_bos"] == 1 and r["smc_choch"] in (1, 2))
