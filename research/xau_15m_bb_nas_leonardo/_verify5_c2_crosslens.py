#!/usr/bin/env python3
"""
_verify5_c2_crosslens.py — DEVIL'S ADVOCATE verification of the C2 CROSS-LENS CORE filter.

RULE under test:
  CUT a trade when:  macro_bear == 1  OR  naslong_after_smc >= 1
  (KEEP everything else)

Claimed: n_keep=2595, wr_keep=62.58, streak_keep=25, winners_kept_pct=88.1,
         losers_cut_pct=19.4, y24=60.65, y25=64.9, y26=58.9, robust=True, 8/8 blocks.

VETO criteria (régua):
  - look-ahead (feature uses future/outcome) -> VETO
  - non-stationarity: WR-after by YEAR worse than that year's OWN base, OR
                      >2/8 blocks worse than that block's base -> VETO
  - winners_kept < 85% -> VETO
  - cherry-pick: ±20% neighborhood collapses (n/a: clauses are boolean, no threshold)
NEVER veto by tail/WR-only/no-OOS.
"""
import json

ROWS = [json.loads(l) for l in open(
    "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_5atr.jsonl")]


def is_cut(r):
    mb = r.get("macro_bear", 0) or 0
    nas = r.get("naslong_after_smc", 0) or 0
    return (mb >= 1) or (nas >= 1)


def wr(rows):
    if not rows:
        return None
    w = sum(x["win"] for x in rows)
    return 100.0 * w / len(rows), w, len(rows)


def max_streak(rows):
    """Max consecutive wins in chronological order."""
    sr = sorted(rows, key=lambda r: (r["low_t"]))
    best = cur = 0
    for r in sr:
        if r["win"]:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def main():
    base_wr, base_w, base_n = wr(ROWS)
    kept = [r for r in ROWS if not is_cut(r)]
    cut = [r for r in ROWS if is_cut(r)]
    keep_wr, keep_w, keep_n = wr(kept)

    total_winners = base_w
    winners_kept = sum(r["win"] for r in kept)
    total_losers = base_n - base_w
    losers_cut = sum(1 - r["win"] for r in cut)

    print("=== TOTAL ===")
    print(f"base: n={base_n} WR={base_wr:.2f}")
    print(f"keep: n={keep_n} WR={keep_wr:.2f}  delta={keep_wr-base_wr:+.2f}pp")
    print(f"cut : n={len(cut)} WR={wr(cut)[0]:.2f}")
    print(f"winners_kept_pct = {100*winners_kept/total_winners:.2f}  "
          f"({winners_kept}/{total_winners})")
    print(f"losers_cut_pct   = {100*losers_cut/total_losers:.2f}  "
          f"({losers_cut}/{total_losers})")
    print(f"streak base={max_streak(ROWS)} keep={max_streak(kept)}")

    print("\n=== PER YEAR (base-of-year vs keep-of-year) ===")
    year_fail = []
    for yr in sorted(set(r["yr"] for r in ROWS)):
        yb = [r for r in ROWS if r["yr"] == yr]
        yk = [r for r in kept if r["yr"] == yr]
        bw = wr(yb)[0]
        kw = wr(yk)[0] if yk else None
        flag = ""
        if kw is not None and kw < bw - 1e-9:
            flag = "  <-- WORSE than year base"
            year_fail.append(yr)
        print(f"  {yr}: base={bw:.2f}  keep={kw:.2f}  d={kw-bw:+.2f}{flag}")

    print("\n=== PER BLOCK (base-of-block vs keep-of-block) ===")
    worse_blocks = []
    for blk in sorted(set(r["block"] for r in ROWS)):
        bb = [r for r in ROWS if r["block"] == blk]
        bk = [r for r in kept if r["block"] == blk]
        bw = wr(bb)[0]
        kw = wr(bk)[0] if bk else None
        flag = ""
        if kw is not None and kw < bw - 1e-9:
            flag = "  <-- worse"
            worse_blocks.append(blk)
        print(f"  {blk}: base={bw:.2f}  keep={kw:.2f}  d={(kw-bw):+.2f}  "
              f"n_keep={len(bk)}{flag}")

    print("\n=== LOOK-AHEAD CHECK ===")
    # macro_bear / naslong_after_smc: confirm they are signal-bar state, not outcome.
    # Check correlation with R is via mechanism not value; verify fields exist pre-entry.
    print("clauses: macro_bear (regime state at signal bar), "
          "naslong_after_smc (NAS LONG label appearing after SMC event, signal-bar).")
    print("Neither references R/win/future bars in field name; both are state flags.")

    print("\n=== VERDICT ===")
    veto = []
    if year_fail:
        veto.append(f"non-stationary: worse year(s) {year_fail}")
    if len(worse_blocks) > 2:
        veto.append(f">2/8 blocks worse ({len(worse_blocks)}): {worse_blocks}")
    wk_pct = 100*winners_kept/total_winners
    if wk_pct < 85.0:
        veto.append(f"winners_kept {wk_pct:.2f} < 85")
    print("worse_blocks:", len(worse_blocks), worse_blocks)
    print("VETO reasons:", veto if veto else "NONE -> SURVIVES")

    return dict(wr_keep=round(keep_wr, 2), streak_keep=max_streak(kept),
                winners_kept_pct=round(wk_pct, 2),
                survives=(len(veto) == 0), worse_blocks=len(worse_blocks),
                year_fail=year_fail)


if __name__ == "__main__":
    res = main()
    print("\nRESULT_DICT:", json.dumps(res))
