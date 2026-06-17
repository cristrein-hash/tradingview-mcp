#!/usr/bin/env python3
"""Metrics-only extraction for BREAKOUT/D1a x L2/BPT (reads the per-event dump; NO backtest, NO RAW).

Reads results/l2_bpt_events_full.jsonl (produced by run_l2bpt_breakout_test.py with the same
locked params) and computes concrete comparable metrics + paired groups A-H. No new rule, no
threshold, no slim. Gross R. Primary comparison target = R4 (also reports R3).
"""
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
E = [json.loads(l) for l in (RESULTS / "l2_bpt_events_full.jsonl").read_text().splitlines() if l.strip()]
NOV = [e for e in E if e["no_overlap"]]


def block(rs, exits=None):
    if not rs:
        return {"n": 0}
    w = sum(1 for x in rs if x > 0)
    wins = [x for x in rs if x > 0]; loss = [x for x in rs if x <= 0]
    pf = round(sum(wins) / abs(sum(loss)), 3) if loss and sum(loss) != 0 else None
    cum = peak = mdd = streak = mstreak = 0.0
    for x in rs:
        cum += x; peak = max(peak, cum); mdd = min(mdd, cum - peak)
        if x <= 0:
            streak += 1; mstreak = max(mstreak, streak)
        else:
            streak = 0
    out = {"n": len(rs), "WR": round(w / len(rs), 3), "sumR": round(sum(rs), 1),
           "avgR": round(sum(rs) / len(rs), 3), "medianR": round(statistics.median(rs), 3),
           "PF": pf, "maxDD_R": round(mdd, 1), "losing_streak": int(mstreak)}
    if exits:
        for r in ("target", "stop", "time_limit"):
            out[r] = sum(1 for x in exits if x == r)
        out["stop_be"] = 0  # BE disabled in this clean comparison
    return out


def immediate(pool, tk):
    rs = [e[f"imm_{tk}"] for e in pool if e[f"imm_{tk}"] is not None]
    ex = [e[f"imm_{tk}_exit"] for e in pool if e[f"imm_{tk}"] is not None]
    return block(rs, ex)


def l2f(pool, tk):
    rs = [e[f"l2f_{tk}"] for e in pool if e["l2f_filled"] and e[f"l2f_{tk}"] is not None]
    ex = [e[f"l2f_{tk}_exit"] for e in pool if e["l2f_filled"] and e[f"l2f_{tk}"] is not None]
    return block(rs, ex)


def l2r(pool):
    rs = [e["l2r_R3"] for e in pool if e["l2r_filled"] and e["l2r_R3"] is not None]
    ex = [e["l2r_R3_exit"] for e in pool if e["l2r_filled"] and e["l2r_R3"] is not None]
    return block(rs, ex)


def yearly(pool, getR):
    by = {}
    for e in pool:
        r = getR(e)
        if r is not None:
            by.setdefault(e["year"], []).append(r)
    return {str(y): {"n": len(v), "sumR": round(sum(v), 1), "WR": round(sum(1 for x in v if x > 0) / len(v), 3)}
            for y, v in sorted(by.items())}


out = {
    "source": "results/l2_bpt_events_full.jsonl (per-event dump; metrics-only, no backtest/RAW/slim)",
    "gross": True, "costs_slippage_considered": False, "target_primary": "R4 (R3 also reported)",
    "universe": {"events_total": len(E), "no_overlap": len(NOV)},
    "A_immediate_T8": {"R4": immediate(NOV, "R4"), "R3": immediate(NOV, "R3"),
                       "TRAIN_R4": immediate([e for e in NOV if e["year"] < 2023], "R4"),
                       "HOLDOUT_R4": immediate([e for e in NOV if e["year"] >= 2023], "R4")},
    "B_l2_touch_fix1_Pminus1ATR": {"R4": l2f(NOV, "R4"), "R3": l2f(NOV, "R3"),
                       "TRAIN_R4": l2f([e for e in NOV if e["year"] < 2023], "R4"),
                       "HOLDOUT_R4": l2f([e for e in NOV if e["year"] >= 2023], "R4"),
                       "filled": sum(1 for e in NOV if e["l2f_filled"]),
                       "unfilled": sum(1 for e in NOV if not e["l2f_filled"])},
    "C_l2_reclaim_fix1": {"R3": l2r(NOV), "filled": sum(1 for e in NOV if e["l2r_filled"])},
    "D_runaways_no_retest": {
        "never_retested": sum(1 for e in NOV if not e["retested"]),
        "imm_R4_win(runaway_lost)": sum(1 for e in NOV if not e["retested"] and (e["imm_R4"] or 0) > 0),
        "imm_R4_loss(toploss_avoided)": sum(1 for e in NOV if not e["retested"] and (e["imm_R4"] or 0) <= 0)},
}

# Paired groups (no-overlap, both have R4 outcome -> l2f filled). Winner = R4>0.
paired = [e for e in NOV if e["l2f_filled"] and e["imm_R4"] is not None and e["l2f_R4"] is not None]
def grp(pred): return [e for e in paired if pred(e)]
gE = grp(lambda e: e["imm_R4"] <= 0 and e["l2f_R4"] > 0)
gF = grp(lambda e: e["imm_R4"] > 0 and e["l2f_R4"] <= 0)
gG = grp(lambda e: e["imm_R4"] > 0 and e["l2f_R4"] > 0)
gH = grp(lambda e: e["imm_R4"] <= 0 and e["l2f_R4"] <= 0)
out["paired_R4_same_events"] = {
    "n_paired": len(paired),
    "E_imm_lose_retest_win": len(gE),
    "F_imm_win_retest_lose": len(gF),
    "G_both_win": len(gG),
    "H_both_lose": len(gH),
    "F_extended_unfilled_but_imm_R4_win": sum(1 for e in NOV if not e["l2f_filled"] and (e["imm_R4"] or 0) > 0),
    "imm_sumR_on_paired": round(sum(e["imm_R4"] for e in paired), 1),
    "retest_sumR_on_paired": round(sum(e["l2f_R4"] for e in paired), 1),
}
out["yearly_R4"] = {"immediate": yearly(NOV, lambda e: e["imm_R4"]),
                    "l2_touch_fix1": yearly([e for e in NOV if e["l2f_filled"]], lambda e: e["l2f_R4"])}

(RESULTS / "l2_bpt_metrics_only_summary.json").write_text(json.dumps(out, indent=2))

# tables.csv
with open(RESULTS / "l2_bpt_metrics_only_tables.csv", "w") as f:
    cols = ["group", "n", "WR", "sumR", "avgR", "medianR", "PF", "maxDD_R", "losing_streak", "target", "stop", "time_limit"]
    f.write(",".join(cols) + "\n")
    rows = [("A_immediate_R4", out["A_immediate_T8"]["R4"]), ("A_immediate_R3", out["A_immediate_T8"]["R3"]),
            ("A_imm_R4_TRAIN", out["A_immediate_T8"]["TRAIN_R4"]), ("A_imm_R4_HOLDOUT", out["A_immediate_T8"]["HOLDOUT_R4"]),
            ("B_l2touchfix1_R4", out["B_l2_touch_fix1_Pminus1ATR"]["R4"]), ("B_l2touchfix1_R3", out["B_l2_touch_fix1_Pminus1ATR"]["R3"]),
            ("B_l2_R4_TRAIN", out["B_l2_touch_fix1_Pminus1ATR"]["TRAIN_R4"]), ("B_l2_R4_HOLDOUT", out["B_l2_touch_fix1_Pminus1ATR"]["HOLDOUT_R4"]),
            ("C_l2reclaimfix1_R3", out["C_l2_reclaim_fix1"]["R3"])]
    for name, m in rows:
        f.write(",".join(str(m.get(c, "")) if c != "group" else name for c in cols) + "\n")

print(json.dumps(out, indent=2))
