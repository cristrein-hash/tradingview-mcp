#!/usr/bin/env python3
"""
DA verification of R2-refine lapidation filter "R_A".

RULE (CUT when true; otherwise KEEP):
  (buy_sell_ratio4 > 7 AND low_vol_rel > 1.37)
  OR (low_vol_rel > 1.37 AND sell_decel == 0)
  OR (regime_age_h <= 25.2 AND sell_skew_mig > 0)

Scope: only rows with r2_keep == 1 (the R2-kept universe).
Devil's-advocate gate:
  - look-ahead: feature provenance (handled separately, all features computed at low_t)
  - stationarity: WR-after by YEAR vs base-of-year (within r2_keep), and by BLOCK
  - winners kept >= 85%
  - combo cherry-pick / neighborhood collapse robustness
"""
import json
import collections

PATH = "dataset_r2refine.jsonl"


def load_keep():
    rows = [json.loads(l) for l in open(PATH)]
    return [r for r in rows if r["r2_keep"] == 1]


def is_cut(r):
    c1 = (r["buy_sell_ratio4"] > 7) and (r["low_vol_rel"] > 1.37)
    c2 = (r["low_vol_rel"] > 1.37) and (r["sell_decel"] == 0)
    c3 = (r["regime_age_h"] <= 25.2) and (r["sell_skew_mig"] > 0)
    return c1 or c2 or c3


def wr(rows):
    if not rows:
        return float("nan"), 0
    return sum(x["win"] for x in rows) / len(rows) * 100, len(rows)


def max_win_streak(rows):
    """streak of consecutive wins ordered by low_t (global chronological)."""
    s = sorted(rows, key=lambda r: r["low_t"])
    best = cur = 0
    for r in s:
        if r["win"] == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def report(rule_fn, label):
    keep = load_keep()
    kept = [r for r in keep if not rule_fn(r)]
    cut = [r for r in keep if rule_fn(r)]

    base_wr, base_n = wr(keep)
    new_wr, new_n = wr(kept)
    win_total = sum(r["win"] for r in keep)
    win_kept = sum(r["win"] for r in kept)
    loser_total = sum(1 - r["win"] for r in keep)
    loser_cut = sum(1 - r["win"] for r in cut)

    print(f"=== {label} ===")
    print(f"BASE  n={base_n}  WR={base_wr:.2f}  streak={max_win_streak(keep)}")
    print(f"KEPT  n={new_n}   WR={new_wr:.2f}  streak={max_win_streak(kept)}")
    print(f"CUT   n={len(cut)} WR={wr(cut)[0]:.2f}")
    print(f"winners_kept_pct = {win_kept/win_total*100:.2f}  ({win_kept}/{win_total})")
    print(f"losers_cut_pct   = {loser_cut/loser_total*100:.2f}  ({loser_cut}/{loser_total})")
    print()

    # STATIONARITY by YEAR vs base-of-year (within r2_keep)
    print("--- YEAR: base-of-year vs after ---")
    year_fail = 0
    for yr in sorted(set(r["yr"] for r in keep)):
        kb = [r for r in keep if r["yr"] == yr]
        ka = [r for r in kept if r["yr"] == yr]
        bwr, bn = wr(kb)
        awr, an = wr(ka)
        delta = awr - bwr
        flag = "WORSE" if delta < 0 else "ok"
        if delta < 0:
            year_fail += 1
        print(f"  {yr}: base={bwr:.2f} (n={bn}) -> after={awr:.2f} (n={an})  delta={delta:+.2f}  {flag}")
    print()

    # STATIONARITY by BLOCK vs base-of-block
    print("--- BLOCK: base-of-block vs after ---")
    block_worse = 0
    for blk in sorted(set(r["block"] for r in keep)):
        kb = [r for r in keep if r["block"] == blk]
        ka = [r for r in kept if r["block"] == blk]
        bwr, bn = wr(kb)
        awr, an = wr(ka)
        delta = awr - bwr
        flag = ""
        if delta < 0:
            block_worse += 1
            flag = "WORSE"
        print(f"  {blk}: base={bwr:.2f} (n={bn}) -> after={awr:.2f} (n={an})  delta={delta:+.2f}  {flag}")
    print()
    print(f"YEARS worse: {year_fail}/3   BLOCKS worse: {block_worse}/8")
    print()
    return {
        "wr_keep": new_wr,
        "streak_keep": max_win_streak(kept),
        "winners_kept_pct": win_kept / win_total * 100,
        "year_fail": year_fail,
        "block_worse": block_worse,
        "n_keep": new_n,
        "cut_n": len(cut),
    }


def robustness_legs():
    """Decompose the OR-union into its 3 legs; check each leg's WR and neighborhood."""
    keep = load_keep()
    legs = {
        "c1 ratio4>7 & vol>1.37": lambda r: (r["buy_sell_ratio4"] > 7) and (r["low_vol_rel"] > 1.37),
        "c2 vol>1.37 & decel==0": lambda r: (r["low_vol_rel"] > 1.37) and (r["sell_decel"] == 0),
        "c3 age<=25.2 & skew>0": lambda r: (r["regime_age_h"] <= 25.2) and (r["sell_skew_mig"] > 0),
    }
    print("--- LEG decomposition (cut pockets) ---")
    for name, fn in legs.items():
        c = [r for r in keep if fn(r)]
        cwr, cn = wr(c)
        print(f"  {name}: n_cut={cn}  WR_cut={cwr:.2f}")
    print()

    # neighborhood collapse: perturb thresholds +-
    print("--- threshold perturbation (cut-pocket WR; should stay loser-dense) ---")
    perturb = {
        "c1 ratio4>6": lambda r: (r["buy_sell_ratio4"] > 6) and (r["low_vol_rel"] > 1.37),
        "c1 ratio4>8": lambda r: (r["buy_sell_ratio4"] > 8) and (r["low_vol_rel"] > 1.37),
        "c2 vol>1.30": lambda r: (r["low_vol_rel"] > 1.30) and (r["sell_decel"] == 0),
        "c2 vol>1.45": lambda r: (r["low_vol_rel"] > 1.45) and (r["sell_decel"] == 0),
        "c3 age<=20": lambda r: (r["regime_age_h"] <= 20) and (r["sell_skew_mig"] > 0),
        "c3 age<=30": lambda r: (r["regime_age_h"] <= 30) and (r["sell_skew_mig"] > 0),
    }
    for name, fn in perturb.items():
        c = [r for r in keep if fn(r)]
        cwr, cn = wr(c)
        print(f"  {name}: n_cut={cn}  WR_cut={cwr:.2f}")
    print()


def streak_reconcile():
    """The claim reports streak_keep=21, base=24. My global win-streak is much larger.
    Reconcile by testing per-block max win-streak (likely the claim's definition)."""
    keep = load_keep()
    kept = [r for r in keep if not is_cut(r)]
    print("--- STREAK reconciliation (per-block max win-streak) ---")
    base_blk = max(max_win_streak([r for r in keep if r["block"] == b])
                   for b in set(r["block"] for r in keep))
    kept_blk = max(max_win_streak([r for r in kept if r["block"] == b])
                   for b in set(r["block"] for r in kept))
    print(f"  base global={max_win_streak(keep)}  kept global={max_win_streak(kept)}")
    print(f"  base per-block-max={base_blk}  kept per-block-max={kept_blk}")
    print()


def leg_loo():
    """Leave-one-leg-out: does any single leg carry the whole edge?"""
    keep = load_keep()
    base_wr, _ = wr(keep)
    legs = [
        ("c1", lambda r: (r["buy_sell_ratio4"] > 7) and (r["low_vol_rel"] > 1.37)),
        ("c2", lambda r: (r["low_vol_rel"] > 1.37) and (r["sell_decel"] == 0)),
        ("c3", lambda r: (r["regime_age_h"] <= 25.2) and (r["sell_skew_mig"] > 0)),
    ]
    print("--- LEAVE-ONE-LEG-OUT (union of remaining 2 legs) ---")
    for drop, _ in legs:
        rem = [fn for nm, fn in legs if nm != drop]
        cutfn = lambda r: any(f(r) for f in rem)
        kept = [r for r in keep if not cutfn(r)]
        w, n = wr(kept)
        win_kept = sum(r["win"] for r in kept) / sum(r["win"] for r in keep) * 100
        print(f"  drop {drop}: WR={w:.2f} (n={n})  winners_kept={win_kept:.2f}")
    print()


if __name__ == "__main__":
    report(is_cut, "R_A sell-exhaustion-into-overheat/vol cut-unions")
    robustness_legs()
    streak_reconcile()
    leg_loo()
