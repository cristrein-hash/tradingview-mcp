#!/usr/bin/env python3
"""
DA verification of F2 (chop_score>=3) lapidation filter on R2-KEPT subset.

RULE: cut when chop_score>=3, where chop_score = count of 5 orthogonal chop-symptoms:
  S1 one-sided buying : buy_sell_ratio4 >= 7
  S2 flat flow        : flow_accel in [-2, 0]
  S3 absorption       : absorption == 1
  S4 high-vol-noise   : low_vol_rel > 1.5
  S5 young-regime     : regime_age_h < 25.2
KEEP = not cut. Operates only on r2_keep==1.

DA gates:
  - look-ahead: predicate uses only pre-entry state (no R/win/h1/h4). CHECK below.
  - stationarity: WR-after by YEAR vs BASE-OF-YEAR (within r2_keep), and by BLOCK.
    Veta if any year worse than its own base, OR >2/8 blocks worse.
  - winners kept: veta if <85%.
  - cherry-pick: neighborhood collapse (sensitivity on threshold).
"""
import json
from collections import defaultdict

ROWS = [json.loads(l) for l in open(
    "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl")]
KEEP = [r for r in ROWS if r["r2_keep"] == 1]

PRED_FIELDS = ["buy_sell_ratio4", "flow_accel", "absorption", "low_vol_rel", "regime_age_h"]
OUTCOME_FIELDS = ["R", "win"]  # must NOT appear in predicate


def chop_score(r):
    s = 0
    s += 1 if r["buy_sell_ratio4"] >= 7 else 0
    s += 1 if (-2 <= r["flow_accel"] <= 0) else 0
    s += 1 if r["absorption"] == 1 else 0
    s += 1 if r["low_vol_rel"] > 1.5 else 0
    s += 1 if r["regime_age_h"] < 25.2 else 0
    return s


def is_cut(r, thr=3):
    return chop_score(r) >= thr


def wr(rows):
    if not rows:
        return None, 0
    return 100 * sum(x["win"] for x in rows) / len(rows), len(rows)


def max_streak(rows):
    # rows assumed time-ordered; streak of consecutive wins
    best = cur = 0
    for x in rows:
        if x["win"] == 1:
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
    print(f"BASE r2_keep: n={bn} WR={bw:.2f} streak={max_streak(base_rows)}")
    print()

    kept = ordered([r for r in KEEP if not is_cut(r)])
    cut = [r for r in KEEP if is_cut(r)]
    kw, kn = wr(kept)
    cw, cn = wr(cut)
    print(f"KEPT  : n={kn} WR={kw:.2f} streak={max_streak(kept)}")
    print(f"CUT   : n={cn} WR={cw:.2f}")
    print()

    # winners kept
    base_winners = sum(r["win"] for r in KEEP)
    kept_winners = sum(r["win"] for r in kept)
    cut_winners = sum(r["win"] for r in cut)
    wk_pct = 100 * kept_winners / base_winners
    print(f"winners: base={base_winners} kept={kept_winners} cut={cut_winners} "
          f"-> winners_kept={wk_pct:.1f}%")
    print(f"losers cut: {sum(1 for r in cut if r['win']==0)} / "
          f"{sum(1 for r in KEEP if r['win']==0)} = "
          f"{100*sum(1 for r in cut if r['win']==0)/sum(1 for r in KEEP if r['win']==0):.1f}%")
    print()

    # cut-winner R distribution (claim: cheap scratch winners, <=2 with R>=2)
    cw_R = sorted([r["R"] for r in cut if r["win"] == 1], reverse=True)
    print(f"cut WINNER R top: {cw_R[:8]}")
    print(f"cut winners R>=2: {sum(1 for x in cw_R if x>=2)}  max={max(cw_R) if cw_R else 'NA'}")
    import statistics
    print(f"cut winner avgR={statistics.mean(cw_R):.2f}  kept winner avgR="
          f"{statistics.mean([r['R'] for r in kept if r['win']==1]):.2f}")
    print()

    # PER YEAR vs base-of-year (within r2_keep)
    print("=== PER YEAR (base-of-year within r2_keep) ===")
    year_fail = []
    for yr in sorted(set(r["yr"] for r in KEEP)):
        yk = [r for r in KEEP if r["yr"] == yr]
        ykept = [r for r in yk if not is_cut(r)]
        bwy, bny = wr(yk)
        kwy, kny = wr(ykept)
        delta = (kwy - bwy) if kwy is not None else None
        flag = "WORSE" if (delta is not None and delta < 0) else "ok"
        if flag == "WORSE":
            year_fail.append(yr)
        print(f"  {yr}: base WR={bwy:.2f}(n{bny}) -> kept WR={kwy:.2f}(n{kny}) "
              f"Δ={delta:+.2f}pp [{flag}]")
    print()

    # PER BLOCK (LOBO-style lift = kept WR - base-of-block WR)
    print("=== PER BLOCK (lift = kept - base-of-block) ===")
    block_worse = []
    for blk in sorted(set(r["block"] for r in KEEP)):
        bk = [r for r in KEEP if r["block"] == blk]
        bkept = [r for r in bk if not is_cut(r)]
        bwb, bnb = wr(bk)
        kwb, knb = wr(bkept)
        lift = (kwb - bwb) if kwb is not None else None
        flag = "WORSE" if (lift is not None and lift < 0) else "ok"
        if flag == "WORSE":
            block_worse.append(blk)
        print(f"  {blk}: base WR={bwb:.2f}(n{bnb}) -> kept WR={kwb:.2f}(n{knb}) "
              f"lift={lift:+.2f}pp [{flag}] cut={sum(1 for r in bk if is_cut(r))}")
    print(f"\nblocks worse: {len(block_worse)}/8 -> {block_worse}")
    print(f"years worse: {year_fail}")
    print()

    # NEIGHBORHOOD COLLAPSE (threshold sensitivity)
    print("=== NEIGHBORHOOD (threshold sensitivity) ===")
    for thr in [2, 3, 4, 5]:
        kk = [r for r in KEEP if not is_cut(r, thr)]
        w, nn = wr(kk)
        cw2 = [r for r in KEEP if is_cut(r, thr)]
        ww = 100 * sum(r["win"] for r in cw2) / len(cw2) if cw2 else None
        wkp = 100 * sum(r["win"] for r in kk) / base_winners
        print(f"  thr>={thr}: kept n={nn} WR={w:.2f} streak={max_streak(ordered(kk))} "
              f"| cut n={len(cw2)} cutWR={ww if ww is None else round(ww,2)} "
              f"| winners_kept={wkp:.1f}%")
    print()

    # LOOK-AHEAD audit: confirm predicate fields are pre-entry, no outcome leakage
    print("=== LOOK-AHEAD AUDIT ===")
    print(f"predicate fields: {PRED_FIELDS}")
    print(f"outcome fields excluded: {OUTCOME_FIELDS}")
    print("none of predicate fields are R/win/h1_eff/h4_pos -> OK by construction")

    return dict(wr_keep=round(kw, 2), streak_keep=max_streak(kept),
                winners_kept_pct=round(wk_pct, 1),
                year_fail=year_fail, block_worse=block_worse, n_keep=kn)


if __name__ == "__main__":
    res = main()
    print("\nSUMMARY:", res)
