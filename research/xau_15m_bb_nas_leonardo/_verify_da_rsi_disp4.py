#!/usr/bin/env python3
"""
DEVIL'S ADVOCATE verification of candidate entry rule:
  rsi_low >= 48.5 AND disp4_atr < -0.898
Reported: n=226 WR=0.531 avgR=1.937 y24=2.135 y25=1.846 y26=1.877

Régua (Cris): do NOT veto for tail/WR-only/no-OOS. VETO only for:
  - look-ahead (feature uses future)
  - non-stationarity (avgR flips sign across years OR blocks)
  - carried by 1-2 trades (ex-top2 collapses)
  - fragile n
  - near_M8 / outcome used as feature

Outcome field = R_reclaim. Features used by the rule: rsi_low, disp4_atr.
"""
import json
from collections import defaultdict

PATH = "entry_dataset.jsonl"
ROWS = [json.loads(l) for l in open(PATH)]


def rule(r):
    return (r["rsi_low"] >= 48.5) and (r["disp4_atr"] < -0.898)


def stats(rows):
    n = len(rows)
    if n == 0:
        return dict(n=0, wr=None, avgR=None, sumR=None)
    Rs = [r["R_reclaim"] for r in rows]
    wins = sum(1 for x in Rs if x > 0)
    return dict(n=n, wr=wins / n, avgR=sum(Rs) / n, sumR=sum(Rs))


def main():
    sel = [r for r in ROWS if rule(r)]
    base = stats(sel)
    print("=== FULL RULE (replicate reported) ===")
    print(base)

    # per YEAR
    print("\n=== avgR PER YEAR ===")
    by_year = defaultdict(list)
    for r in sel:
        by_year[r["yr"]].append(r)
    for y in sorted(by_year):
        print(y, stats(by_year[y]))

    # per BLOCK + leave-one-block-out
    print("\n=== avgR PER BLOCK ===")
    by_block = defaultdict(list)
    for r in sel:
        by_block[r["block"]].append(r)
    for b in sorted(by_block):
        print(b, stats(by_block[b]))

    print("\n=== LEAVE-ONE-BLOCK-OUT (avgR of remainder) ===")
    worst = None
    all_blocks = sorted(set(r["block"] for r in ROWS))
    for b in all_blocks:
        rem = [r for r in sel if r["block"] != b]
        s = stats(rem)
        print(f"drop {b}: n={s['n']} avgR={s['avgR']:.3f} wr={s['wr']:.3f}")
        if worst is None or s["avgR"] < worst[1]:
            worst = (b, s["avgR"])
    print(f"WORST fold (lowest avgR remainder): {worst}")

    # ex-top2 (remove 2 largest R)
    print("\n=== EX-TOP2 (remove 2 best R trades) ===")
    srt = sorted(sel, key=lambda r: r["R_reclaim"], reverse=True)
    top2 = srt[:2]
    print("top2 R:", [round(r["R_reclaim"], 2) for r in top2])
    extop2 = srt[2:]
    print("ex-top2:", stats(extop2))

    # ex-top5 for extra context
    print("ex-top5:", stats(srt[5:]))

    # R distribution
    print("\n=== R DISTRIBUTION ===")
    Rs = sorted(r["R_reclaim"] for r in sel)
    print("min", round(Rs[0], 2), "max", round(Rs[-1], 2))
    print("top10 R:", [round(x, 2) for x in Rs[-10:]])
    print("# trades with R>5:", sum(1 for x in Rs if x > 5))
    print("# trades with R>10:", sum(1 for x in Rs if x > 10))
    sumR = sum(Rs)
    print("sumR", round(sumR, 1))
    print("share of sumR from top2:", round(sum(x for x in Rs[-2:]) / sumR, 3))
    print("share of sumR from top5:", round(sum(x for x in Rs[-5:]) / sumR, 3))

    # near_M8 / outcome leakage check: are rule features outcome-derived?
    # rsi_low, disp4_atr are pre-entry context (RSI at swing low, displacement of prior 4 bars).
    # Confirm they are NOT near_M8/runner/held8/R_8atr etc.
    print("\n=== FEATURE LEAKAGE NOTE ===")
    print("rule features: rsi_low, disp4_atr (both pre-reclaim context, not outcome)")

    # multiple-testing skepticism: how strong is the threshold tuning?
    # sensitivity around thresholds
    print("\n=== THRESHOLD SENSITIVITY (multiple-testing proxy) ===")
    for rl in [46, 47, 48.5, 50]:
        for dp in [-0.7, -0.898, -1.1]:
            ss = stats([r for r in ROWS if r["rsi_low"] >= rl and r["disp4_atr"] < dp])
            print(f"rsi_low>={rl:<4} disp4<{dp:<6} -> n={ss['n']:<4} avgR={ss['avgR'] if ss['avgR'] is not None else None}")


if __name__ == "__main__":
    main()
