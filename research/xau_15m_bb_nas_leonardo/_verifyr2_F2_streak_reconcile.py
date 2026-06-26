#!/usr/bin/env python3
"""Reconcile streak metric vs prompt (base streak=24) and recompute keep streak
under the matching definition. Also re-test the single WORSE block 2024-08-25."""
import json

ROWS = [json.loads(l) for l in open(
    "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl")]
KEEP = sorted([r for r in ROWS if r["r2_keep"] == 1], key=lambda r: r["low_t"])


def chop_score(r):
    return ((r["buy_sell_ratio4"] >= 7) + (-2 <= r["flow_accel"] <= 0)
            + (r["absorption"] == 1) + (r["low_vol_rel"] > 1.5)
            + (r["regime_age_h"] < 25.2))


def is_cut(r):
    return chop_score(r) >= 3


def streak(rs, key):
    best = cur = 0
    for x in rs:
        if key(x):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


keys = {
    "win==1": lambda x: x["win"] == 1,
    "R>=1": lambda x: x["R"] >= 1,
    "R>=1 (strict win)": lambda x: x["win"] == 1 and x["R"] >= 1,
}
kept = [r for r in KEEP if not is_cut(r)]
print("metric              base   kept")
for name, k in keys.items():
    print(f"  {name:18s} {streak(KEEP,k):>4d} {streak(kept,k):>4d}")

# focus the WORSE block
blk = [r for r in KEEP if r["block"] == "2024-08-25"]
bkept = [r for r in blk if not is_cut(r)]
bw = 100 * sum(r["win"] for r in blk) / len(blk)
kw = 100 * sum(r["win"] for r in bkept) / len(bkept)
print(f"\n2024-08-25: base {bw:.2f}(n{len(blk)}) kept {kw:.2f}(n{len(bkept)}) "
      f"Δ={kw-bw:+.2f}pp  cut={len(blk)-len(bkept)} "
      f"cutW={sum(r['win'] for r in blk if is_cut(r))} "
      f"cutL={sum(1 for r in blk if is_cut(r) and r['win']==0)}")
