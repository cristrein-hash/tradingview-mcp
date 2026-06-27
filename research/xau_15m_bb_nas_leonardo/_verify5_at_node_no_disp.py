#!/usr/bin/env python3
"""
_verify5_at_node_no_disp.py — DEVIL'S ADVOCATE verification of the 5ATR CUT rule.

RULE UNDER TEST:
  CUT if (vpnode_dist_atr < 1.07) AND (disp4_atr < 0.78).  [at_node AND no_disp]
  KEEP otherwise.

Régua: NÃO vetar por tail/WR-only/sem-OOS.
VETAR só por:
  - look-ahead (feature usa futuro/outcome?)
  - estacionariedade: WR-depois por ANO vs BASE-DO-ANO e por BLOCO;
       PIORA em algum ano OU >2/8 blocos worse -> veta
  - corta winners < 85%
  - cherry-pick: vizinhança ±20% colapsa (WR_keep stability)

Dataset: dataset_5atr.jsonl  (3047 rows, win in {0,1}, R real).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "dataset_5atr.jsonl")

VP_THR = 1.07
DISP_THR = 0.78


def load():
    return [json.loads(l) for l in open(PATH)]


def keep(r, vp=VP_THR, disp=DISP_THR):
    """KEEP unless (at_node AND no_disp)."""
    at_node = r["vpnode_dist_atr"] < vp
    no_disp = r["disp4_atr"] < disp
    cut = at_node and no_disp
    return not cut


def wr(rows):
    if not rows:
        return None
    return 100.0 * sum(x["win"] for x in rows) / len(rows)


def max_win_streak(rows):
    """Longest consecutive win streak in chronological order."""
    best = cur = 0
    for r in rows:
        if r["win"] == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def chrono(rows):
    return sorted(rows, key=lambda r: r["low_t"])


def main():
    rows = chrono(load())
    n = len(rows)

    kept = [r for r in rows if keep(r)]
    cut = [r for r in rows if not keep(r)]

    base_wr = wr(rows)
    keep_wr = wr(kept)

    total_winners = sum(r["win"] for r in rows)
    total_losers = n - total_winners
    winners_kept = sum(r["win"] for r in kept)
    losers_cut = sum(1 for r in cut if r["win"] == 0)

    winners_kept_pct = 100.0 * winners_kept / total_winners
    losers_cut_pct = 100.0 * losers_cut / total_losers

    print("=== TOTALS ===")
    print(f"n total          {n}")
    print(f"n keep           {len(kept)}")
    print(f"n cut            {len(cut)}")
    print(f"BASE WR          {base_wr:.2f}")
    print(f"KEEP WR          {keep_wr:.2f}   delta {keep_wr-base_wr:+.2f}")
    print(f"streak base      {max_win_streak(rows)}")
    print(f"streak keep      {max_win_streak(kept)}")
    print(f"winners_kept_pct {winners_kept_pct:.2f}")
    print(f"losers_cut_pct   {losers_cut_pct:.2f}")
    print(f"sumR base        {sum(r['R'] for r in rows):.2f}")
    print(f"sumR keep        {sum(r['R'] for r in kept):.2f}")

    print("\n=== PER YEAR (WR base -> WR keep) ===")
    year_worse = []
    for y in sorted(set(r["yr"] for r in rows)):
        yr_all = [r for r in rows if r["yr"] == y]
        yr_keep = [r for r in yr_all if keep(r)]
        b = wr(yr_all)
        k = wr(yr_keep)
        flag = ""
        if k is not None and k < b - 1e-9:
            flag = "  <-- WORSE"
            year_worse.append(y)
        print(f"  {y}: base {b:.2f}  keep {k:.2f}  n_keep {len(yr_keep)}{flag}")

    print("\n=== PER BLOCK (WR base -> WR keep) ===")
    block_worse = []
    for blk in sorted(set(r["block"] for r in rows)):
        bl_all = [r for r in rows if r["block"] == blk]
        bl_keep = [r for r in bl_all if keep(r)]
        b = wr(bl_all)
        k = wr(bl_keep)
        flag = ""
        if k is not None and k < b - 1e-9:
            flag = "  <-- WORSE"
            block_worse.append(blk)
        kk = f"{k:.2f}" if k is not None else "NA"
        print(f"  {blk}: base {b:.2f}  keep {kk}  n_keep {len(bl_keep)}{flag}")

    print(f"\nyears worse: {year_worse}")
    print(f"blocks worse: {len(block_worse)} -> {block_worse}")

    print("\n=== JITTER +/-20% on both thresholds (cherry-pick check) ===")
    for fv in (0.8, 0.9, 1.0, 1.1, 1.2):
        for fd in (0.8, 0.9, 1.0, 1.1, 1.2):
            kk = [r for r in rows if keep(r, VP_THR * fv, DISP_THR * fd)]
            print(f"  vp*{fv:.1f}={VP_THR*fv:.3f} disp*{fd:.1f}={DISP_THR*fd:.3f}: "
                  f"WR {wr(kk):.2f}  n {len(kk)}")

    # min/max WR across jitter grid
    grid = []
    for fv in (0.8, 0.9, 1.0, 1.1, 1.2):
        for fd in (0.8, 0.9, 1.0, 1.1, 1.2):
            kk = [r for r in rows if keep(r, VP_THR * fv, DISP_THR * fd)]
            grid.append(wr(kk))
    print(f"\njitter WR range: {min(grid):.2f} .. {max(grid):.2f}  spread {max(grid)-min(grid):.2f}")

    # VERDICT logic
    survives = True
    reasons = []
    if year_worse:
        survives = False
        reasons.append(f"WR worse in year(s) {year_worse}")
    if len(block_worse) > 2:
        survives = False
        reasons.append(f"{len(block_worse)}/8 blocks worse (>2)")
    if winners_kept_pct < 85.0:
        survives = False
        reasons.append(f"winners_kept {winners_kept_pct:.1f} < 85")
    if max(grid) - min(grid) > 3.0:
        survives = False
        reasons.append(f"jitter spread {max(grid)-min(grid):.2f} > 3 (cherry-pick)")

    print("\n=== VERDICT ===")
    print("SURVIVES" if survives else "VETO")
    print("reasons:", reasons if reasons else "none")


if __name__ == "__main__":
    main()
