#!/usr/bin/env python3
"""
DA verification of F1 lapidation filter on R2-KEPT subset.

RULE (F1 CUT[flow_flat & lowest_fresh]):
  CUT rows where flow_accel in (-2, 0]  (no acceleration, i.e. -2 < flow_accel <= 0)
                 AND bars_since_lowest <= 44 (unseasoned knife).
  KEEP = not cut. Operates only on r2_keep==1.

Claimed: n_keep=1979, wr_keep=70.49, streak_keep=23, winners_kept=86.4%,
         losers_cut=21.2%, y24=68.9 y25=72.9 y26=65.5, robust (8/8 non-worse).

DA gates (recalibrated — do NOT veto on tail/WR-only/no-OOS):
  - look-ahead: predicate uses only pre-entry state (no R/win/outcome). CHECK.
  - stationarity: WR-after by YEAR vs BASE-OF-YEAR (within r2_keep), and by BLOCK.
    Veta if any year worse than its own base, OR >2/8 blocks worse.
  - winners kept: veta if <85%.
  - cherry-pick: neighborhood collapse (sensitivity on both thresholds).

NOTE on "(-2, 0]" interpretation. The rule string says "flow_accel in (-2,0]
(no acceleration)". F2 script used the closed band [-2,0] for the same
"flat flow" symptom. We test BOTH interpretations explicitly so the choice
is not a hidden cherry-pick. Primary = literal "(-2,0]" i.e. {-1, 0}.
"""
import json
import statistics
from collections import defaultdict

ROWS = [json.loads(l) for l in open(
    "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_r2refine.jsonl")]
KEEP = [r for r in ROWS if r["r2_keep"] == 1]

PRED_FIELDS = ["flow_accel", "bars_since_lowest"]
OUTCOME_FIELDS = ["R", "win"]  # must NOT appear in predicate


def is_cut(r, lo=-2, hi=0, bsl=44, inclusive_lo=False):
    """flow_flat band AND fresh-lowest.
    inclusive_lo=False -> literal '(-2,0]' i.e. lo < fa <= hi  -> {-1,0}
    inclusive_lo=True  -> '[-2,0]' i.e. lo <= fa <= hi          -> {-2,-1,0}
    """
    fa = r["flow_accel"]
    if inclusive_lo:
        flat = (lo <= fa <= hi)
    else:
        flat = (lo < fa <= hi)
    fresh = r["bars_since_lowest"] <= bsl
    return flat and fresh


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


def max_loss_streak(rows):
    """The prompt's 'streak' metric = max consecutive LOSS run (lower is better).
    Reconciled: base=24, F1-kept=23 (claim). Time-ordered."""
    best = cur = 0
    for x in rows:
        if x["win"] == 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def ordered(rows):
    return sorted(rows, key=lambda r: r["low_t"])


def report(label, cutfn):
    print(f"\n########## {label} ##########")
    base_rows = ordered(KEEP)
    bw, bn = wr(base_rows)
    print(f"BASE r2_keep: n={bn} WR={bw:.2f} winstreak={max_streak(base_rows)} "
          f"lossstreak={max_loss_streak(base_rows)}")

    kept = ordered([r for r in KEEP if not cutfn(r)])
    cut = [r for r in KEEP if cutfn(r)]
    kw, kn = wr(kept)
    cw, cn = wr(cut)
    print(f"KEPT  : n={kn} WR={kw:.2f} winstreak={max_streak(kept)} "
          f"lossstreak={max_loss_streak(kept)} (<-prompt 'streak')")
    print(f"CUT   : n={cn} WR={cw if cw is None else round(cw,2)}")

    base_winners = sum(r["win"] for r in KEEP)
    kept_winners = sum(r["win"] for r in kept)
    base_losers = sum(1 for r in KEEP if r["win"] == 0)
    cut_losers = sum(1 for r in cut if r["win"] == 0)
    cut_winners = sum(r["win"] for r in cut)
    wk_pct = 100 * kept_winners / base_winners
    lc_pct = 100 * cut_losers / base_losers
    print(f"winners: base={base_winners} kept={kept_winners} cut={cut_winners} "
          f"-> winners_kept={wk_pct:.1f}%")
    print(f"losers : base={base_losers} cut={cut_losers} -> losers_cut={lc_pct:.1f}%")

    if cut_winners:
        cw_R = sorted([r["R"] for r in cut if r["win"] == 1], reverse=True)
        print(f"cut WINNER R top: {cw_R[:8]}  R>=2:{sum(1 for x in cw_R if x>=2)}")

    print("--- PER YEAR (kept WR vs base-of-year within r2_keep) ---")
    year_fail = []
    for yr in sorted(set(r["yr"] for r in KEEP)):
        yk = [r for r in KEEP if r["yr"] == yr]
        ykept = [r for r in yk if not cutfn(r)]
        bwy, bny = wr(yk)
        kwy, kny = wr(ykept)
        delta = (kwy - bwy) if kwy is not None else None
        flag = "WORSE" if (delta is not None and delta < 0) else "ok"
        if flag == "WORSE":
            year_fail.append(yr)
        print(f"  {yr}: base WR={bwy:.2f}(n{bny}) -> kept WR={kwy:.2f}(n{kny}) "
              f"Δ={delta:+.2f}pp [{flag}]")

    print("--- PER BLOCK (lift = kept - base-of-block) ---")
    block_worse = []
    for blk in sorted(set(r["block"] for r in KEEP)):
        bk = [r for r in KEEP if r["block"] == blk]
        bkept = [r for r in bk if not cutfn(r)]
        bwb, bnb = wr(bk)
        kwb, knb = wr(bkept)
        lift = (kwb - bwb) if kwb is not None else None
        flag = "WORSE" if (lift is not None and lift < 0) else "ok"
        if flag == "WORSE":
            block_worse.append(blk)
        print(f"  {blk}: base WR={bwb:.2f}(n{bnb}) -> kept WR={kwb:.2f}(n{knb}) "
              f"lift={lift if lift is None else round(lift,2):+}pp [{flag}] "
              f"cut={sum(1 for r in bk if cutfn(r))}")
    print(f"blocks worse: {len(block_worse)}/8 -> {block_worse}")
    print(f"years worse : {year_fail}")

    return dict(n_keep=kn, wr_keep=round(kw, 2), streak_keep=max_loss_streak(kept),
                winners_kept_pct=round(wk_pct, 1), losers_cut_pct=round(lc_pct, 1),
                year_fail=year_fail, block_worse=block_worse,
                y24=round([wr([r for r in KEEP if r["yr"]==2024 and not cutfn(r)])][0][0],1),
                y25=round([wr([r for r in KEEP if r["yr"]==2025 and not cutfn(r)])][0][0],1),
                y26=round([wr([r for r in KEEP if r["yr"]==2026 and not cutfn(r)])][0][0],1))


def main():
    # LOOK-AHEAD audit
    print("=== LOOK-AHEAD AUDIT ===")
    print(f"predicate fields: {PRED_FIELDS}")
    print(f"outcome fields excluded: {OUTCOME_FIELDS}")
    print("flow_accel & bars_since_lowest are pre-entry state computed at/before "
          "the swing low -> no R/win/future leakage by construction.")

    # Primary: literal "(-2,0]"  -> {-1,0}
    res_lit = report("PRIMARY  (-2,0] literal  {fa in -1,0}, bsl<=44",
                     lambda r: is_cut(r, inclusive_lo=False))
    # Alt: "[-2,0]" closed band (matches F2 chop S2)
    res_inc = report("ALT      [-2,0] closed    {fa in -2,-1,0}, bsl<=44",
                     lambda r: is_cut(r, inclusive_lo=True))

    # NEIGHBORHOOD COLLAPSE: vary bsl threshold and the flat band edge
    print("\n=== NEIGHBORHOOD (bsl threshold sensitivity, literal band) ===")
    for bsl in [30, 40, 44, 50, 60]:
        kk = ordered([r for r in KEEP if not is_cut(r, bsl=bsl, inclusive_lo=False)])
        w, nn = wr(kk)
        bw_all = sum(r["win"] for r in KEEP)
        wkp = 100 * sum(r["win"] for r in kk) / bw_all
        print(f"  bsl<={bsl}: kept n={nn} WR={w:.2f} streak={max_streak(kk)} "
              f"winners_kept={wkp:.1f}%")

    print("\n=== NEIGHBORHOOD (flat-band sensitivity, bsl<=44) ===")
    bands = [("(-2,0] {-1,0}", dict(inclusive_lo=False)),
             ("[-2,0] {-2,-1,0}", dict(inclusive_lo=True)),
             ("(-3,0] approx", dict(lo=-3, inclusive_lo=False)),
             ("(-1,0] {0}", dict(lo=-1, inclusive_lo=False))]
    bw_all = sum(r["win"] for r in KEEP)
    for name, kw_ in bands:
        kk = ordered([r for r in KEEP if not is_cut(r, **kw_)])
        w, nn = wr(kk)
        wkp = 100 * sum(r["win"] for r in kk) / bw_all
        print(f"  band {name}: kept n={nn} WR={w:.2f} streak={max_streak(kk)} "
              f"winners_kept={wkp:.1f}%")

    print("\nSUMMARY PRIMARY:", res_lit)
    print("SUMMARY ALT    :", res_inc)
    return res_lit, res_inc


if __name__ == "__main__":
    main()
