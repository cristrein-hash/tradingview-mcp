#!/usr/bin/env python3
"""XAU_4H_BREAKOUT_D1A — Concept Composition round (tiers T0-T9 + overlap analysis).

RESEARCH / hypotheses-only. Reuses the Round-1 engine (run_mechanical_rebuild_v1)
verbatim — NO new gates, NO new thresholds, NO stop/target change, D1a always CAUSAL.
Adds tier definitions (combinations of EXISTING gates) and a SIGNAL-SET overlap
analysis (which T0 trigger signals each layer keeps/drops, winners vs losers cut).

READ-ONLY w.r.t. RAW + production. No plotting, MCP, Telegram, broker.

Metrics table = no-overlap engine (comparable to Round 1).
Overlap analysis = independent per-signal outcomes (clean subset logic; ALL tiers
are subsets of T0 since every tier = trigger T1-T4 + extra gates).
"""
import json
import bisect
import argparse
from datetime import datetime, timezone
from pathlib import Path

import run_mechanical_rebuild_v1 as eng

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

# Tiers = combinations of EXISTING gate keys (close_ema200, ema_stack, slope, atr_exp, adx, d1a)
EMA_STACK = {"close_ema200", "ema_stack"}
TIERS = {
    "T0": set(),                                            # trigger baseline
    "T1": set(EMA_STACK),                                   # + EMA stack
    "T2": {"atr_exp"},                                      # + ATR expanding
    "T3": EMA_STACK | {"atr_exp"},                          # + EMA stack + ATR
    "T4": EMA_STACK | {"atr_exp", "d1a"},                   # T3 + D1a
    "T5": {"adx", "close_ema200", "ema_stack", "slope", "atr_exp", "d1a"},  # full regime + D1a (=V7)
    "T6": {"close_ema200", "ema_stack", "slope", "atr_exp", "d1a"},         # full regime - ADX
    "T7": {"adx", "close_ema200", "ema_stack", "atr_exp", "d1a"},           # full regime - slope
    "T8": EMA_STACK | {"d1a"},                              # EMA stack + D1a
    "T9": {"atr_exp", "d1a"},                               # ATR expanding + D1a
}


def tier_admits(i, feats, gates, daily, d_close):
    """Does bar i pass trigger + the tier's gate subset? (independent of no-overlap)."""
    gf = eng.gate_flags(feats[i])
    if gf is None:
        return False
    trigger, regime, _ = gf
    if not trigger:
        return False
    regime_keys = gates - {"d1a"}
    if regime_keys:
        if regime is None or not all(regime.get(k) for k in regime_keys):
            return False
    if "d1a" in gates:
        bar_open = feats[i]["time"]
        idx = bisect.bisect_right(d_close, bar_open) - 1
        if idx < 0:
            return False
        if not daily[idx]["d1a_pass"]:
            return False
    return True


def independent_outcome(i, feats):
    """Simulate the trade from signal bar i ignoring no-overlap (for subset analysis)."""
    sim = eng.simulate(feats, i)
    if sim is None:
        return None
    return sim["close_R"]


def main():
    ap = argparse.ArgumentParser(description="Concept composition round (read-only).")
    ap.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)

    series, rsi_map = eng.reconstruct_4h()
    feats, rsi_cov = eng.build_features(series, rsi_map)
    daily = eng.load_daily()
    d_close = [d["close_time"] for d in daily]
    n = len(feats)

    # --- Metrics (no-overlap engine, comparable to Round 1) ---
    eng.VARIANTS.update(TIERS)
    metrics = {}
    shift = {}
    all_trades = []
    for tid in TIERS:
        trades, m, sh = eng.run_variant(tid, feats, daily, d_close)
        metrics[tid] = m
        shift[tid] = sh
        for t in trades:
            t["tier"] = tid
        all_trades.extend(trades)

    # --- Overlap analysis (independent per-signal outcomes; subset logic) ---
    # Base = all T0 trigger signals with a valid independent trade.
    base = []  # list of (i, R)
    for i in range(eng.WARMUP, n - 1):
        if not tier_admits(i, feats, set(), daily, d_close):
            continue
        R = independent_outcome(i, feats)
        if R is None:
            continue
        base.append((i, R))
    base_bars = [i for i, _ in base]
    base_R = {i: R for i, R in base}

    # membership: per tier, set of base bars admitted
    member = {}
    for tid, gates in TIERS.items():
        member[tid] = set(i for i in base_bars if tier_admits(i, feats, gates, daily, d_close))

    def wl(bars):
        w = sum(1 for i in bars if base_R[i] > 0)
        l = len(bars) - w
        sumR = round(sum(base_R[i] for i in bars), 2)
        return {"n": len(bars), "winners": w, "losers": l, "sumR_indep": sumR}

    # pairwise overlap among key tiers + drop analysis for key transitions
    key = ["T0", "T1", "T2", "T3", "T4", "T5"]
    overlap_rows = []
    # T1 vs T2 complementarity
    s1, s2, s3 = member["T1"], member["T2"], member["T3"]
    overlap_rows.append({"pair": "T1(EMA)_vs_T2(ATR)", "T1_only": wl(s1 - s2)["n"],
                         "T2_only": wl(s2 - s1)["n"], "common": wl(s1 & s2)["n"],
                         "union": len(s1 | s2), "jaccard": round(len(s1 & s2) / len(s1 | s2), 3) if (s1 | s2) else 0})
    # transitions where stricter ⊆ looser: how many winners/losers cut
    transitions = [("T1->T3", "T1", "T3"), ("T2->T3", "T2", "T3"),
                   ("T3->T4(+D1a)", "T3", "T4"), ("T4->T5(+ADX+slope)", "T4", "T5"),
                   ("T5->T6(-ADX)", "T6", "T5"), ("T5->T7(-slope)", "T7", "T5")]
    drop_rows = []
    for label, looser, stricter in transitions:
        a, b = member[looser], member[stricter]
        # b should be subset of a for stack-adds; for -ADX/-slope a=stricter-removed is superset
        if b <= a:
            dropped = a - b
            drop_rows.append({"transition": label, "kept": len(b), "dropped": len(dropped),
                              **{f"dropped_{k}": v for k, v in wl(dropped).items() if k != "n"}})
        else:
            # not a subset (rare); report symmetric diff
            drop_rows.append({"transition": label, "kept": len(b), "dropped": len(a ^ b),
                              "note": "not_subset"})

    # yearly stability (std of yearly sumR) per tier from no-overlap metrics
    def yearly_stability(m):
        if m.get("n", 0) == 0 or "yearly" not in m:
            return None
        ys = [v["sumR"] for v in m["yearly"].values()]
        neg_years = sum(1 for v in ys if v < 0)
        return {"years": len(ys), "neg_years": neg_years,
                "min_year": round(min(ys), 2), "max_year": round(max(ys), 2)}

    summary = {
        "round": "concept_composition", "gross": True, "not_validation": True,
        "bars_4h": n, "rsi_coverage": round(rsi_cov / n, 4),
        "base_T0_signals_independent": len(base),
        "tiers": {tid: sorted(g) for tid, g in TIERS.items()},
        "metrics": metrics,
        "shift_audit": shift,
        "overlap": {
            "membership_n": {tid: len(m) for tid, m in member.items()},
            "pairwise": overlap_rows,
            "transitions_drop": drop_rows,
        },
        "yearly_stability": {tid: yearly_stability(metrics[tid]) for tid in TIERS},
    }
    (RESULTS / "concept_composition_summary.json").write_text(json.dumps(summary, indent=2))

    # overlap CSV
    with open(RESULTS / "concept_composition_overlap.csv", "w") as f:
        f.write("transition,kept,dropped,dropped_winners,dropped_losers,dropped_sumR_indep\n")
        for r in drop_rows:
            f.write(f'{r["transition"]},{r["kept"]},{r["dropped"]},'
                    f'{r.get("dropped_winners","")},{r.get("dropped_losers","")},'
                    f'{r.get("dropped_sumR_indep","")}\n')
        f.write("\npair,T1_only,T2_only,common,union,jaccard\n")
        for r in overlap_rows:
            f.write(f'{r["pair"]},{r["T1_only"]},{r["T2_only"]},{r["common"]},{r["union"]},{r["jaccard"]}\n')

    # trades + plot-ready (no-overlap, all tiers)
    with open(RESULTS / "concept_composition_trades.jsonl", "w") as f:
        for t in all_trades:
            d1a = t.get("d1a") or {}
            f.write(json.dumps({
                "chronological_id": t["chronological_id"], "tier": t["tier"],
                "entry_ts": datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).isoformat(),
                "entry_price": round(t["entry"], 4), "stop_price": round(t["stop"], 4),
                "target_price": round(t["target"], 4),
                "exit_ts": datetime.fromtimestamp(t["exit_ts"], tz=timezone.utc).isoformat(),
                "exit_price": round(t["exit_price"], 4), "close_R": round(t["close_R"], 4),
                "result_class": "winner" if t["close_R"] > 0 else "loser",
                "exit_reason": t["exit_reason"], "d1a_pass": d1a.get("d1a_pass"),
                "regime_flags": t["regime_flags"], "regime_year": t["regime_year"]}) + "\n")
    with open(RESULTS / "concept_composition_plot_ready.csv", "w") as f:
        f.write("chronological_id,tier,entry_ts,entry_price,stop_price,target_price,"
                "exit_ts,exit_price,close_R,result_class,exit_reason,color_hint\n")
        for t in all_trades:
            color = "#1a8917" if t["close_R"] > 0 else "#cc0000"
            f.write(f'{t["chronological_id"]},{t["tier"]},'
                    f'{datetime.fromtimestamp(t["entry_ts"],tz=timezone.utc).isoformat()},'
                    f'{round(t["entry"],4)},{round(t["stop"],4)},{round(t["target"],4)},'
                    f'{datetime.fromtimestamp(t["exit_ts"],tz=timezone.utc).isoformat()},'
                    f'{round(t["exit_price"],4)},{round(t["close_R"],4)},'
                    f'{"winner" if t["close_R"]>0 else "loser"},{t["exit_reason"]},{color}\n')

    print(json.dumps({
        "metrics": {tid: {k: metrics[tid].get(k) for k in
                          ("n", "sumR", "avgR", "PF", "WR", "maxDD_R", "max_losing_streak",
                           "targets", "stops", "stop_be", "time_limit")} for tid in TIERS},
        "shift_audit": {tid: {k: shift[tid][k] for k in
                              ("with_d1a", "total_d1a_eval", "same_day_selected",
                               "close_time_gt_bar_open", "missing_daily")} for tid in TIERS},
        "overlap": summary["overlap"],
        "yearly_stability": summary["yearly_stability"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
