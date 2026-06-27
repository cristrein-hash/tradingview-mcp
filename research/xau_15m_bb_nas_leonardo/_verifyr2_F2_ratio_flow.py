#!/usr/bin/env python3
"""
DA verification of proposed F2 lapidation filter on R2-KEPT subset.

PROPOSED RULE (CUT-when):
  CUT if (buy_sell_ratio4 > 5) AND (flow_accel in (-2, 0])   i.e. -2 < flow_accel <= 0
  "drop over-eager buying with flat flow"
  Operates only on r2_keep == 1.

DA gates (recalibrated — do NOT veto on tail/WR-only/no-OOS):
  - look-ahead: predicate fields must be pre-entry, no R/win/h leakage.
  - stationarity: WR-after by YEAR vs BASE-OF-YEAR (within r2_keep), and by BLOCK.
      VETO if any year worse than its own base, OR >2/8 blocks worse.
  - winners kept: VETO if <85%.
  - cherry-pick: neighborhood collapse (sensitivity on the two thresholds).
"""
import json
import statistics
from collections import Counter

PATH = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl"
ROWS = [json.loads(l) for l in open(PATH)]
KEEP = [r for r in ROWS if r["r2_keep"] == 1]

PRED_FIELDS = ["buy_sell_ratio4", "flow_accel"]
OUTCOME_FIELDS = ["R", "win"]


def is_cut(r, ratio_thr=5, lo=-2, hi=0):
    return (r["buy_sell_ratio4"] > ratio_thr) and (lo < r["flow_accel"] <= hi)


def wr(rows):
    if not rows:
        return None, 0
    return 100 * sum(x["win"] for x in rows) / len(rows), len(rows)


def max_streak(rows):
    best = cur = 0
    for x in rows:
        if x["win"] == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def max_loss_streak_blockreset(rows):
    """Max consecutive LOSERS, reset at block boundaries (8 discontiguous
    3-month windows). This is the 'streak' metric used in the proposal:
    base=24, lower is better. Win-streak (76/67) crosses block edges and
    is artificial across discontiguous windows."""
    best = cur = 0
    last = None
    for x in rows:
        if x["block"] != last:
            cur = 0
            last = x["block"]
        if x["win"] == 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def ordered(rows):
    return sorted(rows, key=lambda r: r["low_t"])


def main():
    base_rows = ordered(KEEP)
    bw, bn = wr(base_rows)
    base_streak = max_loss_streak_blockreset(base_rows)
    print(f"BASE r2_keep: n={bn} WR={bw:.2f} lossStreak={base_streak} "
          f"(winStreak={max_streak(base_rows)})")
    print()

    kept = ordered([r for r in KEEP if not is_cut(r)])
    cut = [r for r in KEEP if is_cut(r)]
    kw, kn = wr(kept)
    cw, cn = wr(cut)
    keep_streak = max_loss_streak_blockreset(kept)
    print(f"KEPT  : n={kn} WR={kw:.2f} lossStreak={keep_streak} "
          f"(winStreak={max_streak(kept)})")
    print(f"CUT   : n={cn} WR={cw if cw is None else round(cw,2)}")
    print()

    base_winners = sum(r["win"] for r in KEEP)
    kept_winners = sum(r["win"] for r in kept)
    cut_winners = sum(r["win"] for r in cut)
    base_losers = sum(1 for r in KEEP if r["win"] == 0)
    cut_losers = sum(1 for r in cut if r["win"] == 0)
    wk_pct = 100 * kept_winners / base_winners
    print(f"winners: base={base_winners} kept={kept_winners} cut={cut_winners} "
          f"-> winners_kept={wk_pct:.1f}%")
    print(f"losers cut: {cut_losers}/{base_losers} = "
          f"{100*cut_losers/base_losers:.1f}%")
    print()

    if cut:
        cw_R = sorted([r["R"] for r in cut if r["win"] == 1], reverse=True)
        print(f"cut WINNER R top: {cw_R[:8]}  (#winners cut={cut_winners})")
        print(f"cut total R = {sum(r['R'] for r in cut):+.2f}")
    print()

    # PER YEAR vs base-of-year
    print("=== PER YEAR (base-of-year within r2_keep) ===")
    year_fail = []
    for yr in sorted(set(r["yr"] for r in KEEP)):
        yk = [r for r in KEEP if r["yr"] == yr]
        ykept = [r for r in yk if not is_cut(r)]
        bwy, bny = wr(yk)
        kwy, kny = wr(ykept)
        ncut = sum(1 for r in yk if is_cut(r))
        delta = (kwy - bwy) if kwy is not None else None
        flag = "WORSE" if (delta is not None and delta < 0) else "ok"
        if flag == "WORSE":
            year_fail.append(yr)
        print(f"  {yr}: base WR={bwy:.2f}(n{bny}) -> kept WR={kwy:.2f}(n{kny}) "
              f"Δ={delta:+.2f}pp cut={ncut} [{flag}]")
    print()

    # PER BLOCK
    print("=== PER BLOCK (lift = kept - base-of-block) ===")
    block_worse = []
    for blk in sorted(set(r["block"] for r in KEEP)):
        bk = [r for r in KEEP if r["block"] == blk]
        bkept = [r for r in bk if not is_cut(r)]
        bwb, bnb = wr(bk)
        kwb, knb = wr(bkept)
        ncut = sum(1 for r in bk if is_cut(r))
        lift = (kwb - bwb) if kwb is not None else None
        flag = "WORSE" if (lift is not None and lift < 0) else "ok"
        if flag == "WORSE":
            block_worse.append(blk)
        print(f"  {blk}: base WR={bwb:.2f}(n{bnb}) -> kept WR={kwb:.2f}(n{knb}) "
              f"lift={lift:+.2f}pp cut={ncut} [{flag}]")
    print(f"\nblocks worse: {len(block_worse)}/8 -> {block_worse}")
    print(f"years worse: {year_fail}")
    print()

    # NEIGHBORHOOD COLLAPSE
    print("=== NEIGHBORHOOD (threshold sensitivity) ===")
    print("-- ratio_thr sweep (flow window fixed (-2,0]) --")
    for rt in [3, 4, 5, 6]:
        kk = [r for r in KEEP if not is_cut(r, ratio_thr=rt)]
        w, nn = wr(kk)
        cc = [r for r in KEEP if is_cut(r, ratio_thr=rt)]
        ww = wr(cc)[0]
        wkp = 100 * sum(r["win"] for r in kk) / base_winners
        print(f"  ratio>{rt}: kept n={nn} WR={w:.2f} streak={max_streak(ordered(kk))} "
              f"| cut n={len(cc)} cutWR={ww if ww is None else round(ww,2)} "
              f"| winners_kept={wkp:.1f}%")
    print("-- flow window sweep (ratio>5 fixed) --")
    for lo, hi in [(-2, 0), (-4, 0), (-2, 2), (-6, 0), (-1, 0)]:
        kk = [r for r in KEEP if not is_cut(r, lo=lo, hi=hi)]
        w, nn = wr(kk)
        cc = [r for r in KEEP if is_cut(r, lo=lo, hi=hi)]
        ww = wr(cc)[0]
        wkp = 100 * sum(r["win"] for r in kk) / base_winners
        print(f"  flow({lo},{hi}]: kept n={nn} WR={w:.2f} streak={max_streak(ordered(kk))} "
              f"| cut n={len(cc)} cutWR={ww if ww is None else round(ww,2)} "
              f"| winners_kept={wkp:.1f}%")
    print()

    # CUT composition diagnostics
    print("=== CUT COMPOSITION ===")
    print(f"cut buy_sell_ratio4 values: {Counter(r['buy_sell_ratio4'] for r in cut)}")
    print(f"cut flow_accel values: {Counter(r['flow_accel'] for r in cut)}")
    print(f"cut by year: {Counter(r['yr'] for r in cut)}")
    print(f"cut by block: {Counter(r['block'] for r in cut)}")
    print()

    # LOOK-AHEAD audit
    print("=== LOOK-AHEAD AUDIT ===")
    print(f"predicate fields: {PRED_FIELDS}")
    print(f"outcome fields excluded: {OUTCOME_FIELDS}")
    print("buy_sell_ratio4 / flow_accel are pre-entry flow features; "
          "no R/win/horizon leakage -> OK by construction")

    return dict(wr_keep=round(kw, 2), streak_keep=keep_streak,
                winners_kept_pct=round(wk_pct, 1),
                n_keep=kn, year_fail=year_fail, block_worse=block_worse,
                cut_n=cn, cut_winners=cut_winners, cut_losers=cut_losers)


if __name__ == "__main__":
    res = main()
    print("\nSUMMARY:", res)
