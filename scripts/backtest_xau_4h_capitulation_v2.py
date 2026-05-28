#!/usr/bin/env python3
"""backtest_xau_4h_capitulation_v2.py — R-real revalidation of XAU_4H_REVERSAL_CAPITULATION.

Reads ONLY the lab config:
  my-strategy/research/revalidation/XAU_4H_REVERSAL_CAPITULATION/v2/config.json
Uses ONLY canonical data (slim_features schema 2: 4H base + 1D context). Read-only
on all data. Reuses the verified time/join functions of build_crosstf_dataset.py
(dedup by bar_close_time, close_epoch = next-open, as-of backward join) so the 1D
RSI context carries zero future leak. The ISO `ts` field (replay cursor) is never
used for join/order/regime; epochs from bar_close_time are authoritative.

Outputs (normal run) into the lab v2 dir: trades.jsonl (gitignored), report.json,
summary.md. --dry-run validates + reports the signal funnel without writing.

This fixes v1's two input bugs: signal read the near-dead study field instead of
the NAS pine-label, and ATR used Wilder instead of the legacy SMA. v2 reads the
canonical slim fields (atr14_sma_tr, atr14_sma30_ratio) and the NAS label fields.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# verified time/join primitives from the canonical cross-TF builder
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_crosstf_dataset import (  # noqa: E402
    repo_root, load_tf, dedup_keep_last, add_close_epochs, asof, iso, NOMINAL_INTERVAL_S,
)

ROOT = repo_root()
LAB_DIR = ROOT / "my-strategy" / "research" / "revalidation" / "XAU_4H_REVERSAL_CAPITULATION" / "v2"
CONFIG_PATH = LAB_DIR / "config.json"
SCHEMA_PATH = ROOT / "my-strategy" / "research" / "revalidation" / "_schema" / "config.schema.json"
REGISTRY = ROOT / "docs" / "data" / "dataset_registry.json"


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def validate_config(cfg: dict) -> list:
    """Lightweight structural validation against the schema's required keys (jsonschema absent)."""
    problems = []
    sch = json.loads(SCHEMA_PATH.read_text())
    for k in sch.get("required", []):
        if k not in cfg:
            problems.append(f"missing required key: {k}")
    if cfg.get("base_tf") != "4H":
        problems.append(f"base_tf must be 4H, got {cfg.get('base_tf')}")
    if cfg.get("inputs", {}).get("slim_schema_version") != 2:
        problems.append("inputs.slim_schema_version must be 2")
    if cfg.get("signal", {}).get("official_mode") not in ("primary", "sensitivity"):
        problems.append("signal.official_mode invalid")
    if cfg.get("entry", {}).get("fill") != "next_bar_open":
        problems.append("entry.fill must be next_bar_open")
    return problems


def sma(vals, n, i):
    """SMA over vals[i-n+1 .. i]; None if not enough non-None history."""
    if i < n - 1:
        return None
    window = vals[i - n + 1:i + 1]
    if any(v is None for v in window):
        return None
    return sum(window) / n


def recompute_legacy_atr(highs, lows, closes):
    """Legacy formula: TR=max(h-l,|h-pc|,|l-pc|); ATR14=SMA(TR,14); ATR_MA30=SMA(ATR14,30);
    ratio=ATR14/ATR_MA30. Returns (atr14, ratio) lists (None where undefined)."""
    n = len(highs)
    tr = [None] * n
    for i in range(n):
        if i == 0:
            tr[i] = highs[i] - lows[i]
        else:
            pc = closes[i - 1]
            tr[i] = max(highs[i] - lows[i], abs(highs[i] - pc), abs(lows[i] - pc))
    atr14 = [sma(tr, 14, i) for i in range(n)]
    atr30 = [sma(atr14, 30, i) for i in range(n)]
    ratio = [(atr14[i] / atr30[i]) if (atr14[i] is not None and atr30[i] not in (None, 0)) else None
             for i in range(n)]
    return atr14, ratio


def rel_err_stats(a_list, b_list):
    """median + p95 + max relative error between two aligned lists where both defined."""
    errs = []
    for a, b in zip(a_list, b_list):
        if a is None or b is None or b == 0:
            continue
        errs.append(abs(a - b) / abs(b))
    if not errs:
        return {"n": 0}
    errs.sort()
    return {"n": len(errs), "median": errs[len(errs) // 2],
            "p95": errs[int(0.95 * (len(errs) - 1))], "max": errs[-1]}


def regime_of(epoch, buckets):
    yr = int(iso(epoch)[:4])
    for rng, label in buckets.items():
        lo, hi = rng.split("-") if "-" in rng else (rng, rng)
        if int(lo) <= yr <= int(hi):
            return label
    return "unknown"


def agg(rs):
    """Aggregate a list of R multiples."""
    n = len(rs)
    if n == 0:
        return {"n": 0, "win_pct": 0.0, "avg_r": 0.0, "median_r": 0.0, "sum_r": 0.0,
                "profit_factor": None}
    wins = [r for r in rs if r > 0]
    pos = sum(wins)
    neg = -sum(r for r in rs if r < 0)
    srt = sorted(rs)
    return {"n": n, "win_pct": round(100.0 * len(wins) / n, 2),
            "avg_r": round(sum(rs) / n, 4), "median_r": round(srt[n // 2], 4),
            "sum_r": round(sum(rs), 4),
            "profit_factor": round(pos / neg, 4) if neg > 0 else None}


def max_losing_streak(rs):
    cur = best = 0
    for r in rs:
        if r < 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description="CAPITULATION v2 revalidation backtest (reads lab config.json)")
    ap.add_argument("--dry-run", action="store_true", help="validate + signal funnel; no writes")
    args = ap.parse_args()

    cfg = json.loads(CONFIG_PATH.read_text())
    problems = validate_config(cfg)
    if problems:
        print("CONFIG INVALID:", file=sys.stderr)
        for p in problems:
            print("  -", p, file=sys.stderr)
        return 2

    sig = cfg["signal"]
    atr_ratio_min = sig["atr_ratio_min"]
    rsi_max = sig["rsi_1d_max"]
    recency_max = sig["nas_recency_max_bars"]
    ev_field = sig["nas_event_field"]
    rec_field = sig["nas_recent_field"]
    recbars_field = sig["nas_recent_bars_field"]
    ratio_field = sig["atr_ratio_field"]
    atr_field = cfg["stop"]["atr_field"]
    atr_mult = cfg["stop"]["atr_mult"]
    struct_lb = cfg["stop"]["structural_lookback_bars"]
    targets_r = cfg["targets"]["r_multiples"]
    primary_r = cfg["targets"]["primary_r"]
    horizon = cfg["time_limit_bars"]
    costs = cfg["costs_usd_roundtrip"]
    buckets = cfg["regimes"]["buckets"]
    gates = cfg["decision_gates"]

    # ---- load canonical slims (read-only) ----
    reg = json.loads(REGISTRY.read_text())
    ext_parent = Path(os.path.dirname(reg["_meta"]["external_root"]))
    if not ext_parent.is_dir():
        print(f"ERROR: external drive not mounted: {ext_parent}", file=sys.stderr)
        return 1

    h4_raw, h4_reg, h4_paths = load_tf(reg, ext_parent, "4H")
    d1_raw, d1_reg, d1_paths = load_tf(reg, ext_parent, "1D")
    h4, h4_drop, h4_null = dedup_keep_last(h4_raw)
    d1, d1_drop, d1_null = dedup_keep_last(d1_raw)
    add_close_epochs(h4, "4H")
    add_close_epochs(d1, "1D")
    N = len(h4)

    O = [r.get("open") for r in h4]
    H = [r.get("high") for r in h4]
    L = [r.get("low") for r in h4]
    C = [r.get("close") for r in h4]

    # ---- ATR legacy validation (recompute vs slim; refute Wilder) ----
    rc_atr14, rc_ratio = recompute_legacy_atr(H, L, C)
    slim_atr14 = [r.get("atr14_sma_tr") for r in h4]
    slim_ratio = [r.get("atr14_sma30_ratio") for r in h4]
    slim_wilder = [r.get("atr14_wilder") for r in h4]
    atr_validation = {
        "recompute_vs_slim_atr14": rel_err_stats(rc_atr14, slim_atr14),
        "recompute_vs_slim_ratio": rel_err_stats(rc_ratio, slim_ratio),
        "slim_atr14_vs_wilder": rel_err_stats(slim_atr14, slim_wilder),
        "note": "boundary warm-up disagreements expected (recompute over concatenated series vs per-block extraction). "
                "slim is the source of truth; recompute confirms the legacy SMA formula and refutes Wilder.",
    }
    legacy_formula_confirmed = (atr_validation["recompute_vs_slim_atr14"].get("median", 1) < 0.02
                                and atr_validation["slim_atr14_vs_wilder"].get("median", 0) > 0.02)

    # ---- 1D RSI as-of (no future leak) ----
    d1_match = asof(h4, d1, "_close_epoch")
    rsi1d = [(d1_match[i].get(sig["rsi_1d_field"]) if d1_match[i] else None) for i in range(N)]
    leak_rsi = sum(1 for i in range(N) if d1_match[i] is not None
                   and d1_match[i]["_close_epoch"] > h4[i]["_close_epoch"])

    def cond(c):
        if h4[c].get(rec_field) is not True:
            return False
        rb = h4[c].get(recbars_field)
        if rb is None or rb > recency_max:
            return False
        rr = h4[c].get(ratio_field)
        if rr is None or rr <= atr_ratio_min:
            return False
        r = rsi1d[c]
        return r is not None and r < rsi_max

    events = [i for i in range(N) if h4[i].get(ev_field) is True]

    def gen_signals(mode):
        """Return dict signal_bar_c -> event_e (first event producing it)."""
        sigs = {}
        for e in events:
            if mode == "primary":
                hit = next((c for c in range(e, min(e + recency_max, N - 1) + 1) if cond(c)), None)
            else:  # event_only
                hit = e if cond(e) else None
            if hit is not None and hit not in sigs:
                sigs[hit] = e
        return sigs

    def build_trades(sigs, mode):
        trades = []
        open_until = -1
        skipped_overlap = skipped_risk = skipped_noentry = 0
        for c in sorted(sigs):
            e = sigs[c]
            ei = c + 1
            if ei >= N:
                skipped_noentry += 1
                continue
            if ei <= open_until:
                skipped_overlap += 1
                continue
            entry = O[ei]
            structural_stop = min(L[c - struct_lb + 1:c + 1]) if c - struct_lb + 1 >= 0 else min(L[0:c + 1])
            atr14 = h4[c].get(atr_field)
            if atr14 is None:
                skipped_risk += 1
                continue
            atr_stop = entry - atr_mult * atr14
            stop = min(structural_stop, atr_stop)
            risk = entry - stop
            if risk <= 0:
                skipped_risk += 1
                continue
            end = min(ei + horizon - 1, N - 1)
            first_stop = None
            first_tgt = {rt: None for rt in targets_r}
            for j in range(ei, end + 1):
                if first_stop is None and L[j] <= stop:
                    first_stop = j
                for rt in targets_r:
                    if first_tgt[rt] is None and H[j] >= entry + rt * risk:
                        first_tgt[rt] = j

            def resolve(rt):
                tb, sb = first_tgt[rt], first_stop
                if tb is not None and (sb is None or tb < sb):   # stop-first on tie (tb<sb strict)
                    return "target", entry + rt * risk, tb, float(rt), False
                if sb is not None:
                    return "stop", stop, sb, -1.0, False
                censored = end < ei + horizon - 1
                return "time_limit", C[end], end, round((C[end] - entry) / risk, 4), censored

            reason, exit_price, exit_bar, gR, censored = resolve(primary_r)
            mfe = max((H[j] - entry) / risk for j in range(ei, exit_bar + 1))
            mae = min((L[j] - entry) / risk for j in range(ei, exit_bar + 1))
            by_target = {}
            for rt in targets_r:
                rr_reason, rr_px, rr_bar, rr_R, rr_cens = resolve(rt)
                by_target[f"{rt:g}R"] = {"exit_reason": rr_reason, "R": rr_R}
            net_by_cost = {f"{cst:g}": round(gR - cst / risk, 4) for cst in costs}
            ep = int(h4[ei]["bar_close_time"])
            trades.append({
                "mode": mode,
                "nas_event_bar": e, "nas_event_iso": iso(h4[e]["bar_close_time"]),
                "signal_bar": c, "signal_iso": iso(h4[c]["bar_close_time"]),
                "signal_offset_from_event": c - e,
                "entry_bar": ei, "entry_iso": iso(ep), "entry_price": round(entry, 4),
                "entry_replay_cursor_ts": h4[ei].get("ts"),
                "structural_stop": round(structural_stop, 4), "atr14": round(atr14, 4),
                "atr_stop": round(atr_stop, 4), "stop_price": round(stop, 4),
                "risk": round(risk, 4), "target_price_primary": round(entry + primary_r * risk, 4),
                "atr_ratio": round(h4[c].get(ratio_field), 4), "rsi_1d_asof": round(rsi1d[c], 2),
                "exit_bar": exit_bar, "exit_iso": iso(h4[exit_bar]["bar_close_time"]),
                "exit_price": round(exit_price, 4), "exit_reason": reason,
                "R_multiple": gR, "MFE_R": round(mfe, 4), "MAE_R": round(mae, 4),
                "time_in_trade_bars": exit_bar - ei, "right_censored": censored,
                "regime": regime_of(ep, buckets),
                "by_target": by_target, "net_R_by_cost": net_by_cost,
                "registry_entry": h4[c].get("registry_entry"),
            })
            open_until = exit_bar
        return trades, {"skipped_overlap": skipped_overlap, "skipped_nonpositive_risk": skipped_risk,
                        "skipped_no_entry_bar": skipped_noentry}

    sig_primary = gen_signals("primary")
    sig_event = gen_signals("event_only")
    trades_primary, skip_p = build_trades(sig_primary, "primary")
    trades_event, skip_e = build_trades(sig_event, "event_only")

    official = trades_primary
    Rs = [t["R_multiple"] for t in official]

    # ---- aggregate (official = primary, primary target gross R) ----
    base_agg = agg(Rs)
    srt_desc = sorted(Rs, reverse=True)
    aggregate = {**base_agg,
                 "max_losing_streak": max_losing_streak(Rs),
                 "sum_r_ex_top5": round(sum(srt_desc[5:]), 4),
                 "sum_r_ex_top10": round(sum(srt_desc[10:]), 4),
                 "mfe_r_mean": round(sum(t["MFE_R"] for t in official) / len(official), 4) if official else 0.0,
                 "mae_r_mean": round(sum(t["MAE_R"] for t in official) / len(official), 4) if official else 0.0,
                 "exit_reason_mix": {r: sum(1 for t in official if t["exit_reason"] == r)
                                     for r in ("target", "stop", "time_limit")}}

    # by regime + views
    by_regime = {}
    for lab in set(t["regime"] for t in official):
        by_regime[lab] = agg([t["R_multiple"] for t in official if t["regime"] == lab])
    ex_covid = [t["R_multiple"] for t in official if t["regime"] != "covid"]
    covid_only = [t["R_multiple"] for t in official if t["regime"] == "covid"]
    by_regime["_total"] = agg(Rs)
    by_regime["_ex_covid"] = agg(ex_covid)
    by_regime["_covid_only"] = agg(covid_only)

    by_cost = {}
    for cst in costs:
        nets = [t["net_R_by_cost"][f"{cst:g}"] for t in official]
        a = agg(nets)
        by_cost[f"{cst:g}"] = {"sum_net_r": a["sum_r"], "avg_net_r": a["avg_r"], "win_pct": a["win_pct"]}

    by_target = {}
    for rt in targets_r:
        rts = [t["by_target"][f"{rt:g}R"]["R"] for t in official]
        a = agg(rts)
        by_target[f"{rt:g}R"] = {"n": a["n"], "win_pct": a["win_pct"], "avg_r": a["avg_r"],
                                 "sum_r": a["sum_r"],
                                 "exit_mix": {r: sum(1 for t in official if t["by_target"][f"{rt:g}R"]["exit_reason"] == r)
                                              for r in ("target", "stop", "time_limit")}}

    # ---- STAGE 1 technical validity ----
    entry_ok = all(t["entry_bar"] == t["signal_bar"] + 1 and t["entry_price"] == round(O[t["entry_bar"]], 4)
                   for t in official + trades_event)
    stop_ok = all(t["risk"] > 0 for t in official + trades_event)
    no_leak = (leak_rsi == 0)
    technically_valid = no_leak and entry_ok and stop_ok

    # ---- STAGE 2 decision ----
    n = aggregate["n"]
    pf = aggregate["profit_factor"]
    avg_r = aggregate["avg_r"]
    ex_covid_sum = by_regime["_ex_covid"]["sum_r"]
    ex_top5_sum = aggregate["sum_r_ex_top5"]
    if not technically_valid:
        status, rationale = "inconclusive", "Stage-1 technical validity failed; metrics not interpreted."
    elif n < gates["min_n_needs_more_data"]:
        status, rationale = "needs_more_data", f"n={n} < {gates['min_n_needs_more_data']}."
    elif n < gates["min_n_candidate"]:
        status, rationale = "inconclusive", f"moderate sample n={n} (< {gates['min_n_candidate']})."
    elif avg_r <= 0 or (pf is not None and pf < 1.0):
        status, rationale = "fail", f"avg_R={avg_r}, PF={pf} — no edge."
    elif (avg_r > 0 and pf is not None and pf >= gates["pf_min"]
          and ex_covid_sum > 0 and ex_top5_sum > 0 and n >= gates["min_n_candidate"]):
        status = "candidate_for_VALIDATED"
        rationale = (f"n={n}, avg_R={avg_r}, PF={pf}, ex-COVID sum_R={ex_covid_sum}>0, "
                     f"ex-top5 sum_R={ex_top5_sum}>0 — full bundle, robust.")
    else:
        status = "pass"
        rationale = (f"positive but fragile (n={n}, avg_R={avg_r}, PF={pf}, "
                     f"ex-COVID sum_R={ex_covid_sum}, ex-top5 sum_R={ex_top5_sum}).")
    transition_map = {
        "candidate_for_VALIDATED": {"validation_status": "VALIDATED", "deployment_status": "SHADOW->LIVE after human sign-off"},
        "pass": {"validation_status": "ACTIVE_CANDIDATE", "deployment_status": "keep SHADOW/WATCH_ONLY"},
        "inconclusive": {"validation_status": "RESEARCH", "deployment_status": "unchanged"},
        "needs_more_data": {"validation_status": "RESEARCH", "deployment_status": "unchanged; collect more"},
        "fail": {"validation_status": "REJECTED", "deployment_status": "DISABLED/NOT_DEPLOYED"},
        "reject_or_downgrade": {"validation_status": "downgrade", "deployment_status": "downgrade"},
    }

    funnel = {"raw_nas_events": len(events), "signals_primary": len(sig_primary),
              "signals_event_only": len(sig_event), "trades_after_no_overlap": len(official),
              "right_censored": sum(1 for t in official if t["right_censored"])}

    report = {
        "strategy_id": cfg["strategy_id"], "revalidation_version": cfg["revalidation_version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {"code_commit": git_commit(), "config_path": str(CONFIG_PATH.relative_to(ROOT)),
                       "inputs": {"4H": {"registry_entries": h4_reg, "raw_paths": h4_paths,
                                         "dedup_extra_dropped": h4_drop, "bars": N},
                                  "1D": {"registry_entries": d1_reg, "raw_paths": d1_paths,
                                         "dedup_extra_dropped": d1_drop, "bars": len(d1)}},
                       "horizon_definition": "walk [entry_bar, entry_bar+time_limit_bars-1]; time-limit exit at close of last bar"},
        "atr_validation": {**atr_validation, "legacy_formula_confirmed": legacy_formula_confirmed},
        "signal_funnel": funnel,
        "aggregate": aggregate,
        "by_regime": by_regime, "by_cost": by_cost, "by_target": by_target,
        "mode_comparison": {
            "primary": {"signals": len(sig_primary), "trades": len(official), **skip_p},
            "event_only": {"signals": len(sig_event), "trades": len(trades_event), **skip_e},
            "delta_signals": len(sig_primary) - len(sig_event),
            "legacy_n_reference": 86,
            "approximates_legacy_better": "primary" if abs(len(sig_primary) - 86) <= abs(len(sig_event) - 86) else "event_only"},
        "validations": {"no_future_leak": no_leak, "future_leak_rsi_count": leak_rsi,
                        "entry_is_next_bar_open": entry_ok, "all_stop_distance_positive": stop_ok,
                        "report_generated": True, "technically_valid": technically_valid},
        "decision": {"result_status": status, "recommended_catalog_transition": transition_map[status],
                     "rationale": rationale},
        "warnings": [],
    }
    if not no_leak:
        report["warnings"].append(f"FUTURE LEAK rsi count={leak_rsi}")
    if not legacy_formula_confirmed:
        report["warnings"].append("ATR legacy-formula confirmation weak; inspect atr_validation")
    if n < gates["min_n_candidate"]:
        report["warnings"].append(f"sample n={n} below candidate gate {gates['min_n_candidate']}")

    # ---- console ----
    print(f"signal funnel: raw_events={funnel['raw_nas_events']} | primary={funnel['signals_primary']} | "
          f"event_only={funnel['signals_event_only']} | trades(primary,post-overlap)={funnel['trades_after_no_overlap']}")
    print(f"technically_valid={technically_valid} (leak={leak_rsi}, entry_ok={entry_ok}, stop_ok={stop_ok})")
    print(f"aggregate: n={n} win%={aggregate['win_pct']} avg_R={avg_r} sum_R={aggregate['sum_r']} PF={pf} "
          f"maxLoseStreak={aggregate['max_losing_streak']}")
    print(f"ex-COVID sum_R={ex_covid_sum} | ex-top5 sum_R={ex_top5_sum} | exit_mix={aggregate['exit_reason_mix']}")
    print(f"ATR legacy confirmed={legacy_formula_confirmed} "
          f"(recompute~slim med={atr_validation['recompute_vs_slim_atr14'].get('median')}, "
          f"slim~wilder med={atr_validation['slim_atr14_vs_wilder'].get('median')})")
    print(f"DECISION: {status} — {rationale}")
    if report["warnings"]:
        print("warnings:", report["warnings"])

    if args.dry_run:
        print("[dry-run] not writing trades/report/summary")
        return 0

    # ---- write outputs ----
    LAB_DIR.mkdir(parents=True, exist_ok=True)
    trades_path = LAB_DIR / "trades.jsonl"
    report_path = LAB_DIR / "report.json"
    summary_path = LAB_DIR / "summary.md"
    with trades_path.open("w", encoding="utf-8") as f:
        for t in official + trades_event:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(render_summary(report), encoding="utf-8")

    # reopen check
    reopened = json.loads(report_path.read_text())
    tline = sum(1 for _ in trades_path.open())
    print(f"wrote {trades_path.name} ({tline} lines, gitignored), {report_path.name}, {summary_path.name}")
    print(f"reopen report.json ok={reopened['decision']['result_status']==status}")
    return 0


def render_summary(r: dict) -> str:
    a = r["aggregate"]
    f = r["signal_funnel"]
    d = r["decision"]
    mc = r["mode_comparison"]
    lines = [
        f"# {r['strategy_id']} — Revalidation {r['revalidation_version']} (summary)",
        "",
        f"Generated: {r['generated_at']}  ·  code_commit: `{r['provenance']['code_commit'][:10]}`",
        "",
        "## Decision (recommendation only — lab never writes catalog)",
        f"**result_status: `{d['result_status']}`**",
        f"- recommended: validation_status → `{d['recommended_catalog_transition'].get('validation_status')}`, "
        f"deployment → `{d['recommended_catalog_transition'].get('deployment_status')}`",
        f"- rationale: {d['rationale']}",
        "",
        "## Technical validity (Stage 1)",
        f"- no_future_leak: {r['validations']['no_future_leak']} (rsi leak count {r['validations']['future_leak_rsi_count']})",
        f"- entry == next-bar open: {r['validations']['entry_is_next_bar_open']}",
        f"- all stop_distance > 0: {r['validations']['all_stop_distance_positive']}",
        f"- **technically_valid: {r['validations']['technically_valid']}**",
        "",
        "## Signal funnel",
        f"- raw NAS LONG events: {f['raw_nas_events']}",
        f"- primary full-condition signals: {f['signals_primary']}",
        f"- event-only signals: {f['signals_event_only']}",
        f"- trades (primary, post no-overlap): {f['trades_after_no_overlap']}  "
        f"(right-censored: {f['right_censored']})",
        f"- mode that better approximates legacy n≈86: **{mc['approximates_legacy_better']}** "
        f"(primary {mc['primary']['signals']} vs event-only {mc['event_only']['signals']})",
        "",
        "## Aggregate (primary mode, 2R target, gross R)",
        f"- n: {a['n']}  ·  win%: {a['win_pct']}  ·  avg_R: {a['avg_r']}  ·  median_R: {a['median_r']}",
        f"- sum_R: {a['sum_r']}  ·  PF: {a['profit_factor']}  ·  max losing streak: {a['max_losing_streak']}",
        f"- sum_R ex-top5: {a['sum_r_ex_top5']}  ·  ex-top10: {a['sum_r_ex_top10']}",
        f"- MFE_R mean: {a['mfe_r_mean']}  ·  MAE_R mean: {a['mae_r_mean']}",
        f"- exit mix: {a['exit_reason_mix']}",
        "",
        "## By regime (sum_R / n / win%)",
    ]
    for k in ("_total", "_ex_covid", "_covid_only"):
        g = r["by_regime"][k]
        lines.append(f"- {k}: sum_R {g['sum_r']} / n {g['n']} / win% {g['win_pct']}")
    for k in sorted(x for x in r["by_regime"] if not x.startswith("_")):
        g = r["by_regime"][k]
        lines.append(f"- {k}: sum_R {g['sum_r']} / n {g['n']} / win% {g['win_pct']}")
    lines += ["", "## By cost (net R)"]
    for c, g in r["by_cost"].items():
        lines.append(f"- cost {c}: sum_net_R {g['sum_net_r']} / avg {g['avg_net_r']} / win% {g['win_pct']}")
    lines += ["", "## By target"]
    for t, g in r["by_target"].items():
        lines.append(f"- {t}: n {g['n']} / win% {g['win_pct']} / sum_R {g['sum_r']} / mix {g['exit_mix']}")
    if r["warnings"]:
        lines += ["", "## Warnings"] + [f"- {w}" for w in r["warnings"]]
    lines += ["", "_See report.json for full provenance + ATR validation. trades.jsonl is gitignored "
              "(regenerable from config.json + canonical data + the recorded commit)._", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
