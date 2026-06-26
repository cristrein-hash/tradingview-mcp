#!/usr/bin/env python3
"""
Adversarial verification of the DISCOUNT+UPTREND core entry rule.

RULE (reported): dist_ema_atr < 0 AND ema_slope_atr > 0
  reclaim happens below the EMA while EMA slope is still positive
  = pullback in an intact uptrend.
Reported: n=411 WR=45 avgR=1.238 y24=1.17 y25=1.30 y26=1.16

Régua (Cris) — veto ONLY for:
  - look-ahead (feature uses future info)
  - non-stationarity (avgR changes sign across years OR across blocks)
  - carried by 1-2 trades (ex-top2 collapses)
  - fragile n
  - near_M8 / outcome used as a feature

Outcome column = R_reclaim (the realized R per the reported avgR scale).
WR defined as R_reclaim > 0.
"""
import json
import collections

PATH = "entry_dataset.jsonl"

def load():
    return [json.loads(l) for l in open(PATH)]

def select(rows):
    """Apply the rule on the reclaim-bar features."""
    out = []
    for r in rows:
        d = r.get("dist_ema_atr")
        s = r.get("ema_slope_atr")
        R = r.get("R_reclaim")
        if d is None or s is None or R is None:
            continue
        if d < 0 and s > 0:
            out.append(r)
    return out

def stats(sel):
    n = len(sel)
    Rs = [r["R_reclaim"] for r in sel]
    wr = 100.0 * sum(1 for x in Rs if x > 0) / n if n else float("nan")
    avg = sum(Rs) / n if n else float("nan")
    return n, wr, avg

def main():
    rows = load()
    # How many rows even have a valid outcome?
    valid = [r for r in rows if r.get("R_reclaim") is not None]
    print(f"total rows={len(rows)} rows_with_R_reclaim={len(valid)}")

    sel = select(rows)
    n, wr, avg = stats(sel)
    print(f"\n=== FULL RULE (dist_ema_atr<0 AND ema_slope_atr>0) ===")
    print(f"n={n} WR={wr:.1f}% avgR={avg:.3f}")

    # Per year
    print("\n--- per YEAR ---")
    by_year = collections.defaultdict(list)
    for r in sel:
        by_year[r["yr"]].append(r["R_reclaim"])
    for y in sorted(by_year):
        Rs = by_year[y]
        w = 100.0*sum(1 for x in Rs if x>0)/len(Rs)
        a = sum(Rs)/len(Rs)
        print(f"  y{y}: n={len(Rs)} WR={w:.1f}% avgR={a:.3f} sumR={sum(Rs):.1f}")
    peryear_signs = [1 if sum(by_year[y])/len(by_year[y])>0 else -1 for y in by_year]
    peryear_ok = all(s>0 for s in peryear_signs)

    # Leave-one-BLOCK-out (worst fold = avgR of the held-OUT block? or of remaining?)
    # Interpretation: per-block avgR (does any single block flip sign?) AND
    # leave-one-block-out remaining avgR (robustness of aggregate to dropping a block).
    print("\n--- per BLOCK (held-out block stats) ---")
    by_block = collections.defaultdict(list)
    for r in sel:
        by_block[r["block"]].append(r["R_reclaim"])
    block_avgs = {}
    for b in sorted(by_block):
        Rs = by_block[b]
        w = 100.0*sum(1 for x in Rs if x>0)/len(Rs)
        a = sum(Rs)/len(Rs)
        block_avgs[b] = a
        print(f"  {b}: n={len(Rs)} WR={w:.1f}% avgR={a:.3f} sumR={sum(Rs):.1f}")

    print("\n--- leave-one-block-out (avgR of REMAINING data) ---")
    allRs = [r["R_reclaim"] for r in sel]
    loo = {}
    for b in sorted(by_block):
        keep = [r["R_reclaim"] for r in sel if r["block"] != b]
        a = sum(keep)/len(keep)
        loo[b] = a
        print(f"  drop {b}: n={len(keep)} avgR={a:.3f}")
    worst_loo = min(loo.values())
    worst_loo_block = min(loo, key=loo.get)
    print(f"  WORST leave-one-block-out avgR = {worst_loo:.3f} (dropping {worst_loo_block})")

    # also worst single held-out block avgR (a block that on its own loses)
    worst_block = min(block_avgs, key=block_avgs.get)
    print(f"  WORST single-block avgR = {block_avgs[worst_block]:.3f} ({worst_block})")
    block_signs_ok = all(a>0 for a in block_avgs.values())
    print(f"  any block with negative avgR? {'YES' if not block_signs_ok else 'no'}")

    # ex-top2: remove the 2 largest R_reclaim contributors
    print("\n--- ex-top2 (drop 2 largest R_reclaim) ---")
    srt = sorted(sel, key=lambda r: r["R_reclaim"], reverse=True)
    print(f"  top5 R_reclaim: {[round(r['R_reclaim'],2) for r in srt[:5]]}")
    ex2 = srt[2:]
    n2, wr2, avg2 = stats(ex2)
    print(f"  ex-top2: n={n2} WR={wr2:.1f}% avgR={avg2:.3f}")
    ex5 = srt[5:]
    n5, wr5, avg5 = stats(ex5)
    print(f"  ex-top5: n={n5} WR={wr5:.1f}% avgR={avg5:.3f}")

    # Baseline: avgR over ALL rows with valid R_reclaim (is the rule even lifting?)
    baseRs = [r["R_reclaim"] for r in valid]
    base_avg = sum(baseRs)/len(baseRs)
    base_wr = 100.0*sum(1 for x in baseRs if x>0)/len(baseRs)
    print(f"\n--- BASELINE (all rows w/ R_reclaim) ---")
    print(f"  n={len(baseRs)} WR={base_wr:.1f}% avgR={base_avg:.3f}")
    print(f"  LIFT avgR: rule {avg:.3f} vs base {base_avg:.3f} -> {avg-base_avg:+.3f}")

    # Decompose the AND: each half alone
    print("\n--- decompose each half ---")
    for name, pred in [
        ("dist_ema_atr<0 only", lambda r: r["dist_ema_atr"]<0),
        ("ema_slope_atr>0 only", lambda r: r["ema_slope_atr"]>0),
    ]:
        s = [r for r in valid if pred(r)]
        nn,ww,aa = stats(s)
        print(f"  {name}: n={nn} WR={ww:.1f}% avgR={aa:.3f}")

    print("\n=== SUMMARY ===")
    print(f"peryear_ok (all years avgR>0) = {peryear_ok}")
    print(f"worst leave-one-block-out avgR = {worst_loo:.3f}")
    print(f"worst single-block avgR = {block_avgs[worst_block]:.3f}")
    print(f"ex-top2 avgR = {avg2:.3f} (vs full {avg:.3f})")

if __name__ == "__main__":
    main()
