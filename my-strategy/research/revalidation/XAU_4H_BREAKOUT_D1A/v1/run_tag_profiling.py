#!/usr/bin/env python3
"""XAU_4H_BREAKOUT_D1A — Tag profiling / winners-vs-losers anatomy.

RESEARCH / hypotheses-only. Reuses the Round-1 engine verbatim (no new gates,
no new thresholds, D1a always CAUSAL). Re-runs ONLY because the existing trade
outputs lack `d1a_pass` on the non-D1a tiers (T1/T8 record d1a_pass=null) — needed
for the EMA x ATR x D1a intersection anatomy. Every tag derives from already-
validated feature-mapping fields (regime_flags from gate_flags + D1a via the
causal daily join). No MFE/MAE in the engine -> marked unavailable.

READ-ONLY w.r.t. RAW + production. No plotting, MCP, Telegram, broker.
"""
import json
import bisect
import statistics
from datetime import datetime, timezone
from pathlib import Path

import run_mechanical_rebuild_v1 as eng

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

TIERS = {
    "T1": {"close_ema200", "ema_stack"},
    "T8": {"close_ema200", "ema_stack", "d1a"},
    "T4": {"close_ema200", "ema_stack", "atr_exp", "d1a"},
    "T5": {"adx", "close_ema200", "ema_stack", "slope", "atr_exp", "d1a"},
    "T6": {"close_ema200", "ema_stack", "slope", "atr_exp", "d1a"},
}


def tag_trade(t, feats, daily, d_close):
    i = t["sig_i"]
    f = feats[i]
    rf = t["regime_flags"]
    bar_open = f["time"]
    idx = bisect.bisect_right(d_close, bar_open) - 1
    drow = daily[idx] if idx >= 0 else None
    return {
        "chronological_id": t["chronological_id"], "tier": t["variant_id"],
        "entry_ts": datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).isoformat(),
        "entry_ts_unix": t["entry_ts"], "close_R": round(t["close_R"], 4),
        "exit_reason": t["exit_reason"], "be_moved": t["be_moved"],
        "duration_bars": t["exit_idx"] - t["entry_idx"],
        "winner": t["close_R"] > 0,
        # trend
        "ema_stack_pass": bool(rf.get("close_ema200") and rf.get("ema_stack")),
        "close_gt_ema200": bool(rf.get("close_ema200")),
        "ema50_gt_ema200": bool(rf.get("ema_stack")),
        "ema50_slope_pass": bool(rf.get("slope")),
        # energy
        "atr_expanding_pass": bool(rf.get("atr_exp")),
        "adx_pass": bool(rf.get("adx")),
        # macro
        "d1a_pass": bool(drow["d1a_pass"]) if drow else None,
        "d1_close_gt_ema200": bool(drow["close_gt_ema200"]) if drow else None,
        "d1_ema50_gt_ema200": bool(drow["ema50_gt_ema200"]) if drow else None,
        # premium derived
        "full_regime_pass": all(rf.get(k) for k in ("adx", "close_ema200", "ema_stack", "slope", "atr_exp")),
        "full_minus_adx_pass": all(rf.get(k) for k in ("close_ema200", "ema_stack", "slope", "atr_exp")),
        "full_minus_slope_pass": all(rf.get(k) for k in ("adx", "close_ema200", "ema_stack", "atr_exp")),
    }


def profile(tagged):
    if not tagged:
        return {"n": 0}
    # build pseudo-trades for eng.metrics
    pt = [{"entry_ts": x["entry_ts_unix"], "close_R": x["close_R"], "exit_reason": x["exit_reason"]} for x in tagged]
    m = eng.metrics(pt)
    Rs = [x["close_R"] for x in tagged]
    durs = [x["duration_bars"] for x in tagged]
    def freq(tag):
        vals = [x[tag] for x in tagged if x[tag] is not None]
        return round(sum(1 for v in vals if v) / len(vals), 3) if vals else None
    m["median_R"] = round(statistics.median(Rs), 4)
    m["median_duration_bars"] = round(statistics.median(durs), 1)
    m["pct_atr"] = freq("atr_expanding_pass")
    m["pct_d1a"] = freq("d1a_pass")
    m["pct_adx"] = freq("adx_pass")
    m["pct_slope"] = freq("ema50_slope_pass")
    return m


def outcome_groups(tagged):
    g = {}
    for reason in ("target", "stop", "stop_be", "time_limit"):
        sub = [x for x in tagged if x["exit_reason"] == reason]
        g[reason] = profile(sub) if sub else {"n": 0}
    g["winners"] = profile([x for x in tagged if x["winner"]])
    g["losers"] = profile([x for x in tagged if not x["winner"]])
    return g


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    series, rsi_map = eng.reconstruct_4h()
    feats, rsi_cov = eng.build_features(series, rsi_map)
    daily = eng.load_daily()
    d_close = [d["close_time"] for d in daily]
    eng.VARIANTS.update(TIERS)

    tagged = {}
    for tid in TIERS:
        trades, _, _ = eng.run_variant(tid, feats, daily, d_close)
        tagged[tid] = [tag_trade(t, feats, daily, d_close) for t in trades]

    T1, T8 = tagged["T1"], tagged["T8"]

    # Universes
    universes = {
        "A_T1_all": T1,
        "B_T8_all": T8,
        "C_T1_d1a_fail": [x for x in T1 if x["d1a_pass"] is False],
        "D_T8_with_ATR": [x for x in T8 if x["atr_expanding_pass"]],
        "E_T8_without_ATR": [x for x in T8 if not x["atr_expanding_pass"]],
        "F_premium_T4": tagged["T4"], "F_premium_T5": tagged["T5"], "F_premium_T6": tagged["T6"],
    }
    uni_profiles = {k: profile(v) for k, v in universes.items()}
    uni_outcomes = {k: outcome_groups(v) for k, v in universes.items() if k in ("A_T1_all", "B_T8_all")}

    # Intersections within T1
    def part(pred):
        return [x for x in T1 if pred(x)]
    intersections = {
        "EMA_only": part(lambda x: not x["atr_expanding_pass"] and x["d1a_pass"] is False),
        "EMA_ATR": part(lambda x: x["atr_expanding_pass"] and x["d1a_pass"] is False),
        "EMA_D1a": part(lambda x: not x["atr_expanding_pass"] and x["d1a_pass"] is True),
        "EMA_ATR_D1a": part(lambda x: x["atr_expanding_pass"] and x["d1a_pass"] is True),
    }
    inter_profiles = {k: profile(v) for k, v in intersections.items()}

    summary = {
        "round": "tag_profiling", "gross": True, "not_validation": True,
        "rsi_coverage": round(rsi_cov / len(feats), 4),
        "mfe_mae": "unavailable (engine does not compute)",
        "tags_available": ["ema_stack_pass", "close_gt_ema200", "ema50_gt_ema200", "ema50_slope_pass",
                           "atr_expanding_pass", "adx_pass", "d1a_pass", "d1_close_gt_ema200",
                           "d1_ema50_gt_ema200", "full_regime_pass", "full_minus_adx_pass",
                           "full_minus_slope_pass", "exit_reason", "winner", "duration_bars"],
        "tags_unavailable": ["MFE_R", "MAE_R"],
        "universe_n": {k: len(v) for k, v in universes.items()},
        "universe_profiles": uni_profiles,
        "outcome_groups_T1_T8": uni_outcomes,
        "T1_intersections": {k: {"n": len(v)} | inter_profiles[k] for k, v in intersections.items()},
    }
    (RESULTS / "tag_profiling_summary.json").write_text(json.dumps(summary, indent=2))

    # tables CSV
    with open(RESULTS / "tag_profiling_tables.csv", "w") as f:
        cols = ["group", "n", "sumR", "avgR", "median_R", "PF", "WR", "maxDD_R",
                "max_losing_streak", "targets", "stops", "stop_be", "time_limit",
                "pct_atr", "pct_d1a", "pct_adx", "pct_slope"]
        f.write(",".join(cols) + "\n")
        rows = list(uni_profiles.items()) + [("T1_" + k, inter_profiles[k]) for k in intersections]
        for name, m in rows:
            f.write(",".join(str(m.get(c, "")) if c != "group" else name for c in cols) + "\n")

    # plot sets md
    def ids(lst, k=15):
        return [(x["chronological_id"], x["entry_ts"][:10], x["close_R"]) for x in lst[:k]]
    biggest_win = sorted(T8, key=lambda x: -x["close_R"])
    biggest_loss = sorted(T8, key=lambda x: x["close_R"])
    sets = [
        ("1. T8 targets", [x for x in T8 if x["exit_reason"] == "target"], "ver se targets têm energia/contexto visual coerente"),
        ("2. T8 full losers/stops", [x for x in T8 if x["exit_reason"] in ("stop", "stop_be")], "anatomia dos stops: breakout falso? chase?"),
        ("3. T1 winners cut by D1a", [x for x in T1 if x["d1a_pass"] is False and x["winner"]], "D1a corta winners bons? quantos e por quê"),
        ("4. T1 losers cut by D1a", [x for x in T1 if x["d1a_pass"] is False and not x["winner"]], "D1a corta losers (bom)? confirmar visual"),
        ("5. T8+ATR targets", [x for x in T8 if x["atr_expanding_pass"] and x["exit_reason"] == "target"], "ATR+target = breakout explosivo?"),
        ("6. T8 sem ATR winners", [x for x in T8 if not x["atr_expanding_pass"] and x["winner"]], "T8 sem energia ainda ganha? como?"),
        ("7. T8 sem ATR losers", [x for x in T8 if not x["atr_expanding_pass"] and not x["winner"]], "T8 sem energia falha mais?"),
        ("8. Premium (T5) losers", [x for x in tagged["T5"] if not x["winner"]], "o que o premium NÃO resolveu"),
        ("9. Biggest winners (T8)", biggest_win, "qual padrão visual dos maiores ganhos (cap +4R)"),
        ("10. Biggest losers (T8)", biggest_loss, "piores trades — MAE/contexto (MAE unavailable, plotar p/ ver)"),
    ]
    lines = ["# Tag Profiling — Plot Sets (candidatos p/ futura plotagem canônica)\n",
             "**NÃO plotar agora.** Listas para `CANONICAL_TRADE_PLOTTING.md` em bloco futuro autorizado.\n"]
    for title, lst, why in sets:
        lines.append(f"\n## {title}  (n={len(lst)})\n- **Por que plotar:** {why}\n- **Pergunta visual:** ver §título.\n- **Amostra (id, data, R):** {ids(lst)}\n")
    (RESULTS / "tag_profiling_plot_sets.md").write_text("".join(lines))

    print(json.dumps({"universe_n": summary["universe_n"],
                      "universe_profiles": {k: {kk: uni_profiles[k].get(kk) for kk in
                                               ("n", "sumR", "avgR", "PF", "WR", "maxDD_R", "max_losing_streak",
                                                "median_R", "pct_atr", "pct_d1a", "pct_adx", "pct_slope")}
                                            for k in universes},
                      "T1_intersections": {k: {kk: inter_profiles[k].get(kk) for kk in
                                              ("n", "sumR", "avgR", "PF", "WR", "maxDD_R", "max_losing_streak",
                                               "targets", "stops", "stop_be", "time_limit")} for k in intersections},
                      "outcome_T1": {g: {kk: uni_outcomes["A_T1_all"][g].get(kk) for kk in ("n", "avgR", "median_R", "pct_atr", "pct_d1a", "pct_adx")} for g in uni_outcomes["A_T1_all"]},
                      "outcome_T8": {g: {kk: uni_outcomes["B_T8_all"][g].get(kk) for kk in ("n", "avgR", "median_R", "pct_atr", "pct_d1a", "pct_adx")} for g in uni_outcomes["B_T8_all"]},
                      }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
