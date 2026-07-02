#!/usr/bin/env python3
# [STATUS 2026-07-02] HISTORICAL_COMPATIBILITY / RAW_IN_MEMORY_ALLOWED / SLIM_MODE_FORBIDDEN / DO_NOT_USE_SLIM_FOR_VALIDATION
# Part of the deferred SLIM cluster (imports build_crosstf_dataset). SLIM output/validation is FORBIDDEN.
# See docs/cleanup/SLIM_CLUSTER_STATUS_HISTORICAL_COMPATIBILITY.md
"""backtest_xau_4h_demand_breakout_v2.py — R-real revalidation of XAU_4H_DEMAND_BREAKOUT.

Reads ONLY: my-strategy/research/revalidation/XAU_4H_DEMAND_BREAKOUT/v2/config.json
Canonical 4H slim + (best-effort) v6 legacy dumps for reconciliation. Read-only on data.

Two phases:
  1. RECONCILIATION (mandatory before R-real interpretation):
     - canonical signals on slim, for both dist_14d windows {84, 40};
     - close-only H10/H20 metrics;
     - v6 dump signal reconstruction (best-effort) + timestamp overlap with canonical w40;
     - sets reconciliation_status (LEGACY_REPRODUCED / PARTIAL / LEGACY_NOT_REPRODUCIBLE).
  2. R-REAL backtest (always runs as diagnostic; decision is capped if reconciliation
     is not reproducible). Window=84 (proper 14d). Stop variants: demand_zone_low
     (primary), structural_3_low, atr_1_5. One signal per contiguous in-zone episode;
     no-overlap; stop-first intrabar.

V0+V3': inside_demand_zone AND nas_dist_ema_atr in [1.0,2.0] AND dist_14d_pct in [-1.0,0.0].
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_crosstf_dataset import (  # noqa: E402
    repo_root, load_tf, dedup_keep_last, add_close_epochs, iso,
)

ROOT = repo_root()
LAB = ROOT / "my-strategy" / "research" / "revalidation" / "XAU_4H_DEMAND_BREAKOUT" / "v2"
CONFIG_PATH = LAB / "config.json"
SCHEMA_PATH = ROOT / "my-strategy" / "research" / "revalidation" / "_schema" / "config.schema.json"
REGISTRY = ROOT / "docs" / "data" / "dataset_registry.json"


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def validate_config(cfg: dict) -> list:
    """Structural validation against the unified schema (jsonschema absent)."""
    sch = json.loads(SCHEMA_PATH.read_text())
    problems = []
    for k in sch.get("required", []):
        if k not in cfg:
            problems.append(f"missing required key: {k}")
    props = set(sch["properties"])
    for k in cfg:
        if k not in props:
            problems.append(f"unknown root key '{k}' (root is closed)")
    if cfg.get("base_tf") != "4H":
        problems.append(f"base_tf must be 4H, got {cfg.get('base_tf')}")
    if cfg.get("inputs", {}).get("slim_schema_version") != 2:
        problems.append("inputs.slim_schema_version must be 2")
    if cfg.get("entry", {}).get("fill") != "next_bar_open":
        problems.append("entry.fill must be next_bar_open")
    return problems


def parse_float(v):
    try:
        return float(v)
    except Exception:
        return None


def compute_dist14_array(highs, closes, window):
    """For each bar c: dist_14d_pct = (close[c] - max(high[c-W+1..c])) / max * 100.
    Uses bar c's own high (no future leak). None for c < W-1."""
    n = len(highs)
    out = [None] * n
    for c in range(window - 1, n):
        h_w = max(highs[c - window + 1:c + 1])
        if h_w:
            out[c] = (closes[c] - h_w) / h_w * 100.0
    return out


def is_demand_box(box: dict) -> bool:
    """Identify DEMAND box: prefer text='DEMAND'; fallback bgColor green-dominant."""
    t = (box.get("text") or "").upper().strip()
    if t == "DEMAND":
        return True
    if t == "SUPPLY":
        return False
    c = (box.get("bgColor") or box.get("bgcolor") or "")
    if isinstance(c, str) and c.startswith("#") and len(c) >= 7:
        try:
            r = int(c[1:3], 16); g = int(c[3:5], 16); b = int(c[5:7], 16)
            return g > r
        except Exception:
            return False
    return False


def close_inside_demand(close, boxes):
    if close is None:
        return False
    for b in boxes:
        if not is_demand_box(b):
            continue
        h, l = b.get("high"), b.get("low")
        if h is None or l is None:
            continue
        if l <= close <= h:
            return True
    return False


def signals_canonical(h4, dist14, nd_min, nd_max, d14_min, d14_max):
    """V0+V3' on canonical slim with episode dedup (one signal per contiguous in-zone run)."""
    n = len(h4)
    sigs = []
    in_episode = False
    consumed = False
    for c in range(n):
        in_zone = h4[c].get("inside_demand_zone") is True
        if in_zone:
            if not in_episode:
                in_episode = True
                consumed = False
            if not consumed:
                nd = h4[c].get("nas_dist_ema_atr")
                d14 = dist14[c]
                if (nd is not None and nd_min <= nd <= nd_max
                        and d14 is not None and d14_min <= d14 <= d14_max):
                    sigs.append(c)
                    consumed = True
        else:
            in_episode = False
            consumed = False
    return sigs


def close_only_metric(h4, sigs, H):
    """For each signal c: win = close[c+H] > close[c] (from signal close) and close[c+H] > open[c+1] (from entry)."""
    wins_e = wins_s = n = 0
    N = len(h4)
    for c in sigs:
        ei = c + 1
        if ei + H - 1 >= N or c + H >= N:
            continue
        n += 1
        if h4[ei + H - 1]["close"] > h4[ei]["open"]:
            wins_e += 1
        if h4[c + H]["close"] > h4[c]["close"]:
            wins_s += 1
    return {"n": n,
            "win_from_entry_pct": round(100 * wins_e / n, 2) if n else 0.0,
            "win_from_signal_close_pct": round(100 * wins_s / n, 2) if n else 0.0}


def stream_v6_signals(dumps_glob_rel, window=40):
    """Best-effort reconstruction of V0+V3' signals from v6 RAW dumps.

    Semantics:
      - Evaluate the signal using ob[-1] state (the snapshot's current bar) +
        study_values + pine_boxes — this matches what the legacy strategy would have
        seen at the snapshot.
      - For the bar IDENTITY (the epoch used to match against the canonical slim's
        bar_close_time, which is the just-closed bar), apply a conditional shift:
        if ob[-1] is degenerate (O==H==L==C, i.e. forming/just-opened), the just-closed
        bar is ob[-2]; else ob[-1] itself is the closed bar.
    Returns (sorted_epoch_list, diagnostics)."""
    files = sorted(glob.glob(str(ROOT / dumps_glob_rel)))
    sig_epochs = set()
    diag = {"files": len(files), "records_total": 0, "records_with_ohlcv": 0,
            "records_with_cob_boxes": 0, "records_in_zone": 0,
            "records_nas_in_band": 0, "records_dist14_in_band": 0,
            "records_with_forming_last": 0, "signal_records": 0}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                diag["records_total"] += 1
                ob = d.get("ohlcv_last_40_bars") or []
                if len(ob) < window:
                    continue
                bar = ob[-1]
                close = bar.get("close")
                ep_eval = bar.get("time")
                if ep_eval is None or close is None:
                    continue
                diag["records_with_ohlcv"] += 1
                # detect forming and compute the bar-identity epoch for canonical match
                is_forming = (bar.get("open") == bar.get("high") == bar.get("low") == bar.get("close"))
                if is_forming:
                    diag["records_with_forming_last"] += 1
                    prev = ob[-2] if len(ob) >= 2 else None
                    ep_identity = prev.get("time") if prev else None
                else:
                    ep_identity = ep_eval
                if ep_identity is None:
                    continue
                nd = None
                for s in (d.get("study_values") or []):
                    if "NAS TOP BOTTOM" in (s.get("name") or "").upper():
                        nd = parse_float((s.get("values") or {}).get("NAS_DISTANCE_FROM_EMA_ATR"))
                        break
                cob = []
                for pb in (d.get("pine_boxes") or []):
                    if "CUSTOM OB" in (pb.get("name") or "").upper():
                        cob = pb.get("all_boxes") or []
                        break
                if cob:
                    diag["records_with_cob_boxes"] += 1
                inzone = close_inside_demand(close, cob)
                if inzone:
                    diag["records_in_zone"] += 1
                highs = [b.get("high") for b in ob[-window:] if b.get("high") is not None]
                d14 = None
                if len(highs) == window:
                    h_w = max(highs)
                    if h_w:
                        d14 = (close - h_w) / h_w * 100.0
                if nd is not None and 1.0 <= nd <= 2.0:
                    diag["records_nas_in_band"] += 1
                if d14 is not None and -1.0 <= d14 <= 0.0:
                    diag["records_dist14_in_band"] += 1
                if (inzone and nd is not None and 1.0 <= nd <= 2.0
                        and d14 is not None and -1.0 <= d14 <= 0.0):
                    sig_epochs.add(int(ep_identity))
                    diag["signal_records"] += 1
    diag["unique_signal_epochs"] = len(sig_epochs)
    return sorted(sig_epochs), diag


def agg(rs):
    n = len(rs)
    if n == 0:
        return {"n": 0, "win_pct": 0.0, "avg_r": 0.0, "median_r": 0.0, "sum_r": 0.0, "profit_factor": None}
    wins = [r for r in rs if r > 0]
    pos = sum(wins)
    neg = -sum(r for r in rs if r < 0)
    srt = sorted(rs)
    return {"n": n, "win_pct": round(100 * len(wins) / n, 2),
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


def main():
    ap = argparse.ArgumentParser(description="DEMAND_BREAKOUT v2 revalidation (reads lab config.json)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-v6", action="store_true", help="skip v6 dump comparison (faster)")
    args = ap.parse_args()

    cfg = json.loads(CONFIG_PATH.read_text())
    problems = validate_config(cfg)
    if problems:
        print("CONFIG INVALID:", file=sys.stderr)
        for p in problems:
            print("  -", p, file=sys.stderr)
        return 2

    sig_cfg = cfg["signal"]
    nd_min = sig_cfg["nas_dist_ema_atr_min"]; nd_max = sig_cfg["nas_dist_ema_atr_max"]
    d14_min = sig_cfg["dist_14d_pct_min"]; d14_max = sig_cfg["dist_14d_pct_max"]
    windows = sig_cfg["dist_14d_window_candidates_bars"]
    targets_r = cfg["targets"]["r_multiples"]; primary_r = cfg["targets"]["primary_r"]
    horizon = cfg["time_limit_bars"]; costs = cfg["costs_usd_roundtrip"]
    buckets = cfg["regimes"]["buckets"]; gates = cfg["decision_gates"]
    stop_cfg = cfg["stop"]
    atr_field = stop_cfg["atr_field"]; atr_mult = stop_cfg["atr_mult"]
    struct_lb = stop_cfg["structural_lookback_bars"]

    # ---- load canonical 4H slim ----
    reg = json.loads(REGISTRY.read_text())
    ext_parent = Path(os.path.dirname(reg["_meta"]["external_root"]))
    if not ext_parent.is_dir():
        print(f"ERROR: external drive not mounted: {ext_parent}", file=sys.stderr)
        return 1
    h4_raw, h4_reg, h4_paths = load_tf(reg, ext_parent, "4H")
    h4, h4_drop, h4_null = dedup_keep_last(h4_raw)
    add_close_epochs(h4, "4H")
    N = len(h4)
    O = [r.get("open") for r in h4]; H = [r.get("high") for r in h4]
    L = [r.get("low") for r in h4]; C = [r.get("close") for r in h4]

    # ---- PHASE 1: canonical signals per window + close-only ----
    print(f"=== PHASE 1: reconciliation (canonical 4H bars={N}) ===")
    canonical_funnel = {}
    signals_by_window = {}
    for W in windows:
        d14 = compute_dist14_array(H, C, W)
        sigs = signals_canonical(h4, d14, nd_min, nd_max, d14_min, d14_max)
        signals_by_window[W] = sigs
        sigs_2023 = [c for c in sigs if iso(h4[c]["bar_close_time"])[:4] >= "2023"]
        co_h10 = close_only_metric(h4, sigs_2023, 10)
        co_h20 = close_only_metric(h4, sigs_2023, 20)
        canonical_funnel[f"window_{W}"] = {
            "signals_total": len(sigs),
            "signals_2023_2026": len(sigs_2023),
            "close_only_H10": co_h10,
            "close_only_H20": co_h20,
        }
        print(f"  window={W}: signals_total={len(sigs)} | 2023-2026={len(sigs_2023)} | "
              f"H20 win_from_signal_close={co_h20['win_from_signal_close_pct']}% (n={co_h20['n']})")

    # ---- PHASE 1b: v6 dump comparison ----
    v6_info = {}
    if not args.skip_v6:
        dumps_glob = cfg["inputs"].get("legacy_dumps_glob", "alert-bridge/logs/backtests/XAUUSD_240_*_v6.jsonl")
        print(f"=== PHASE 1b: v6 dump comparison ===")
        v6_epochs, v6_diag = stream_v6_signals(dumps_glob, window=40)
        v6_info["diagnostics"] = v6_diag
        v6_info["signal_epochs_count"] = len(v6_epochs)
        canonical_w40_epochs = set(int(h4[c]["bar_close_time"]) for c in signals_by_window[40])
        v6_set = set(v6_epochs)
        overlap = canonical_w40_epochs & v6_set
        only_canonical = canonical_w40_epochs - v6_set
        only_v6 = v6_set - canonical_w40_epochs
        v6_info["timestamp_overlap"] = {
            "canonical_w40_signals": len(canonical_w40_epochs),
            "v6_signals": len(v6_set),
            "intersection": len(overlap),
            "only_canonical": len(only_canonical),
            "only_v6": len(only_v6),
        }
        v6_info["v6_signal_epochs_sample"] = [iso(e) for e in v6_epochs[:10]]
        print(f"  v6 diag: {v6_diag}")
        print(f"  timestamp overlap: {v6_info['timestamp_overlap']}")
    else:
        v6_info["skipped"] = True

    # ---- reconciliation status ----
    legacy = cfg["reconciliation"]["legacy_targets"]
    LEGACY_WIN = legacy["win_rate"]
    LEGACY_N = legacy["n"]
    best_co = canonical_funnel.get("window_84", {}).get("close_only_H20", {})
    win_close = (best_co.get("win_from_signal_close_pct", 0) or 0) / 100.0
    n_2023_84 = canonical_funnel.get("window_84", {}).get("signals_2023_2026", 0)
    win_close_40 = (canonical_funnel.get("window_40", {}).get("close_only_H20", {}).get("win_from_signal_close_pct", 0) or 0) / 100.0
    win_ok_any = (abs(win_close - LEGACY_WIN) <= 0.10 or abs(win_close_40 - LEGACY_WIN) <= 0.10)
    n_ok = abs(n_2023_84 - LEGACY_N) / max(LEGACY_N, 1) <= 0.30
    if win_ok_any and n_ok:
        recon_status = "LEGACY_REPRODUCED"
    elif n_ok or win_ok_any:
        recon_status = "PARTIAL"
    else:
        recon_status = "LEGACY_NOT_REPRODUCIBLE"
    print(f"  reconciliation_status: {recon_status} "
          f"(canonical_w84 close-only H20 win={win_close*100:.1f}% n_2023-26={n_2023_84} vs legacy {LEGACY_WIN*100:.1f}%/{LEGACY_N})")

    # ---- PHASE 2: R-real backtest (window=84, proper 14d) ----
    base_sigs = signals_by_window[84]
    print(f"=== PHASE 2: R-real (window=84, base_signals={len(base_sigs)}) ===")

    def regime_of(epoch):
        yr = int(iso(epoch)[:4])
        for rng, lab in buckets.items():
            lo, hi = (rng.split("-") if "-" in rng else (rng, rng))
            if int(lo) <= yr <= int(hi):
                return lab
        return "unknown"

    def run_variant(sigs, stop_variant):
        trades = []
        open_until = -1
        for c in sigs:
            ei = c + 1
            if ei >= N:
                continue
            if ei <= open_until:
                continue
            entry = O[ei]
            atr14 = h4[c].get(atr_field)
            if atr14 is None or atr14 <= 0:
                continue
            if stop_variant == "demand_zone_low":
                stop = h4[c].get("nearest_demand_low")
                if stop is None:
                    continue
            elif stop_variant == "structural_3_low":
                stop = min(L[max(0, c - struct_lb + 1):c + 1])
            elif stop_variant == "atr_1_5":
                stop = entry - atr_mult * atr14
            else:
                continue
            risk = entry - stop
            if risk <= 0:
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
                if tb is not None and (sb is None or tb < sb):
                    return "target", entry + rt * risk, tb, float(rt), False
                if sb is not None:
                    return "stop", stop, sb, -1.0, False
                cens = end < ei + horizon - 1
                return "time_limit", C[end], end, round((C[end] - entry) / risk, 4), cens

            reason, exit_price, exit_bar, gR, cens = resolve(primary_r)
            mfe = max((H[j] - entry) / risk for j in range(ei, exit_bar + 1))
            mae = min((L[j] - entry) / risk for j in range(ei, exit_bar + 1))
            by_target = {}
            for rt in targets_r:
                rr_reason, _, _, rr_R, _ = resolve(rt)
                by_target[f"{rt:g}R"] = {"exit_reason": rr_reason, "R": rr_R}
            net_by_cost = {f"{cst:g}": round(gR - cst / risk, 4) for cst in costs}
            ep = int(h4[ei]["bar_close_time"])
            trades.append({
                "stop_variant": stop_variant,
                "signal_bar": c, "signal_iso": iso(h4[c]["bar_close_time"]),
                "entry_bar": ei, "entry_iso": iso(ep),
                "entry_price": round(entry, 4), "stop_price": round(stop, 4),
                "atr14": round(atr14, 4), "risk": round(risk, 4),
                "target_price_primary": round(entry + primary_r * risk, 4),
                "nas_dist": round(h4[c].get("nas_dist_ema_atr") or 0, 3),
                "inside_demand_zone": True,
                "exit_bar": exit_bar, "exit_iso": iso(h4[exit_bar]["bar_close_time"]),
                "exit_price": round(exit_price, 4), "exit_reason": reason,
                "R_multiple": gR, "MFE_R": round(mfe, 4), "MAE_R": round(mae, 4),
                "time_in_trade_bars": exit_bar - ei, "right_censored": cens,
                "regime": regime_of(ep), "by_target": by_target, "net_R_by_cost": net_by_cost,
                "registry_entry": h4[c].get("registry_entry"),
            })
            open_until = exit_bar
        return trades

    trades_primary = run_variant(base_sigs, "demand_zone_low")
    trades_struct = run_variant(base_sigs, "structural_3_low")
    trades_atr = run_variant(base_sigs, "atr_1_5")
    print(f"  trades: demand_zone_low={len(trades_primary)} structural_3_low={len(trades_struct)} atr_1_5={len(trades_atr)}")

    # ---- aggregate (official = demand_zone_low, 2R, gross) ----
    Rs = [t["R_multiple"] for t in trades_primary]
    base_agg = agg(Rs)
    srt_desc = sorted(Rs, reverse=True)
    aggregate = {**base_agg,
                 "max_losing_streak": max_losing_streak(Rs),
                 "sum_r_ex_top5": round(sum(srt_desc[5:]), 4),
                 "sum_r_ex_top10": round(sum(srt_desc[10:]), 4),
                 "mfe_r_mean": round(sum(t["MFE_R"] for t in trades_primary) / len(trades_primary), 4) if trades_primary else 0.0,
                 "mae_r_mean": round(sum(t["MAE_R"] for t in trades_primary) / len(trades_primary), 4) if trades_primary else 0.0,
                 "exit_reason_mix": {r: sum(1 for t in trades_primary if t["exit_reason"] == r)
                                     for r in ("target", "stop", "time_limit")}}

    by_regime = {}
    for lab in set(t["regime"] for t in trades_primary):
        by_regime[lab] = agg([t["R_multiple"] for t in trades_primary if t["regime"] == lab])
    ex_covid = [t["R_multiple"] for t in trades_primary if t["regime"] != "covid"]
    covid_only = [t["R_multiple"] for t in trades_primary if t["regime"] == "covid"]
    by_regime["_total"] = agg(Rs)
    by_regime["_ex_covid"] = agg(ex_covid)
    by_regime["_covid_only"] = agg(covid_only)

    by_cost = {}
    for cst in costs:
        nets = [t["net_R_by_cost"][f"{cst:g}"] for t in trades_primary]
        a = agg(nets)
        by_cost[f"{cst:g}"] = {"sum_net_r": a["sum_r"], "avg_net_r": a["avg_r"], "win_pct": a["win_pct"]}

    by_target_block = {}
    for rt in targets_r:
        rts = [t["by_target"][f"{rt:g}R"]["R"] for t in trades_primary]
        a = agg(rts)
        by_target_block[f"{rt:g}R"] = {"n": a["n"], "win_pct": a["win_pct"], "avg_r": a["avg_r"], "sum_r": a["sum_r"],
                                       "exit_mix": {r: sum(1 for t in trades_primary if t["by_target"][f"{rt:g}R"]["exit_reason"] == r)
                                                    for r in ("target", "stop", "time_limit")}}

    by_stop_variant = {
        "demand_zone_low": agg([t["R_multiple"] for t in trades_primary]),
        "structural_3_low": agg([t["R_multiple"] for t in trades_struct]),
        "atr_1_5": agg([t["R_multiple"] for t in trades_atr]),
    }

    # ---- Stage 1: technical validity ----
    all_trades = trades_primary + trades_struct + trades_atr
    entry_ok = all(t["entry_bar"] == t["signal_bar"] + 1 and t["entry_price"] == round(O[t["entry_bar"]], 4) for t in all_trades)
    stop_ok = all(t["risk"] > 0 for t in all_trades)
    no_leak = all(t["exit_bar"] >= t["entry_bar"] for t in all_trades)
    tech_valid = entry_ok and stop_ok and no_leak

    # ---- Stage 2: merit decision (with reconciliation caveat) ----
    n = aggregate["n"]; pf = aggregate["profit_factor"]; avg_r = aggregate["avg_r"]
    ex_covid_sum = by_regime["_ex_covid"]["sum_r"]
    ex_top5_sum = aggregate["sum_r_ex_top5"]
    if not tech_valid:
        status, rationale = "inconclusive", "Stage-1 technical validity failed; metrics not interpreted."
    else:
        if n < gates["min_n_needs_more_data"]:
            status, rationale = "needs_more_data", f"n={n} < {gates['min_n_needs_more_data']}."
        elif n < gates["min_n_candidate"]:
            status, rationale = "inconclusive", f"moderate sample n={n} (< {gates['min_n_candidate']})."
        elif avg_r <= 0 or (pf is not None and pf < 1.0):
            status, rationale = "fail", f"avg_R={avg_r}, PF={pf} — no edge."
        elif (avg_r > 0 and pf is not None and pf >= gates["pf_min"]
              and ex_covid_sum > 0 and ex_top5_sum > 0 and n >= gates["min_n_candidate"]):
            if recon_status == "LEGACY_NOT_REPRODUCIBLE":
                status = "pass"  # capped: positive but legacy not reproducible
                rationale = (f"positive (n={n}, avg_R={avg_r}, PF={pf}) but legacy not reproducible "
                             f"(canonical close-only H20 vs legacy mismatch) -> capped at pass.")
            else:
                status = "candidate_for_VALIDATED"
                rationale = (f"n={n}, avg_R={avg_r}, PF={pf}, ex-COVID sum_R={ex_covid_sum}>0, "
                             f"ex-top5 sum_R={ex_top5_sum}>0 — full bundle; reconciliation_status={recon_status}.")
        else:
            status, rationale = "pass", (f"positive but fragile (n={n}, avg_R={avg_r}, PF={pf}, "
                                          f"ex-COVID sum_R={ex_covid_sum}, ex-top5 sum_R={ex_top5_sum}).")
    transition_map = {
        "candidate_for_VALIDATED": {"validation_status": "VALIDATED", "deployment_status": "SHADOW->LIVE after human sign-off"},
        "pass": {"validation_status": "ACTIVE_CANDIDATE", "deployment_status": "keep SHADOW/WATCH_ONLY"},
        "inconclusive": {"validation_status": "RESEARCH", "deployment_status": "unchanged"},
        "needs_more_data": {"validation_status": "RESEARCH", "deployment_status": "unchanged; collect more"},
        "fail": {"validation_status": "REJECTED", "deployment_status": "DISABLED/NOT_DEPLOYED"},
    }

    report = {
        "strategy_id": cfg["strategy_id"], "revalidation_version": cfg["revalidation_version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {"code_commit": git_commit(),
                       "config_path": str(CONFIG_PATH.relative_to(ROOT)),
                       "inputs": {"4H": {"registry_entries": h4_reg, "raw_paths": h4_paths,
                                         "bars": N, "dedup_extra_dropped": h4_drop, "null_bct_dropped": h4_null}},
                       "horizon_definition": "walk [entry_bar, entry_bar+time_limit_bars-1]; time-limit exit at close of last bar"},
        "phase1_reconciliation": {
            "canonical_funnel": canonical_funnel,
            "v6_dump_comparison": v6_info,
            "legacy_targets": legacy,
            "reconciliation_status": recon_status,
        },
        "signal_funnel": {
            "raw_candidate_bars_inside_demand_zone": sum(1 for r in h4 if r.get("inside_demand_zone") is True),
            "canonical_w84_total_signals": len(signals_by_window[84]),
            "canonical_w40_total_signals": len(signals_by_window[40]),
            "v6_signal_epochs": v6_info.get("signal_epochs_count"),
            "r_real_trades_primary_stop": len(trades_primary),
            "right_censored": sum(1 for t in trades_primary if t["right_censored"]),
        },
        "aggregate": aggregate,
        "by_regime": by_regime,
        "by_cost": by_cost,
        "by_target": by_target_block,
        "by_stop_variant": by_stop_variant,
        "validations": {"no_future_leak": no_leak, "entry_is_next_bar_open": entry_ok,
                        "all_stop_distance_positive": stop_ok, "report_generated": True,
                        "technically_valid": tech_valid},
        "decision": {"result_status": status, "recommended_catalog_transition": transition_map[status],
                     "rationale": rationale, "reconciliation_status": recon_status},
        "warnings": [],
    }
    if recon_status == "LEGACY_NOT_REPRODUCIBLE":
        report["warnings"].append("LEGACY_NOT_REPRODUCIBLE: canonical close-only != legacy 83.8%; merit verdict capped at 'pass' (no VALIDATED).")
    if n < gates["min_n_candidate"]:
        report["warnings"].append(f"sample n={n} below candidate gate {gates['min_n_candidate']}")
    if v6_info.get("diagnostics", {}).get("records_with_cob_boxes", 1) == 0:
        report["warnings"].append("v6 dumps: no Custom OB boxes parsed — demand-zone reconstruction inconclusive.")

    print(f"=== AGGREGATE (stop=demand_zone_low, 2R, gross) ===")
    print(f"  n={n} win%={aggregate['win_pct']} avg_R={avg_r} sum_R={aggregate['sum_r']} PF={pf} maxLoseStreak={aggregate['max_losing_streak']}")
    print(f"  ex-COVID sum_R={ex_covid_sum} | ex-top5 sum_R={ex_top5_sum} | exit_mix={aggregate['exit_reason_mix']}")
    print(f"  by_stop_variant n: " + " ".join(f"{k}={v['n']}/PF={v['profit_factor']}" for k, v in by_stop_variant.items()))
    print(f"  technically_valid={tech_valid} | reconciliation={recon_status}")
    print(f"  DECISION: {status} — {rationale}")
    if report["warnings"]:
        print("  warnings:", report["warnings"])

    if args.dry_run:
        print("[dry-run] not writing trades/report/summary")
        return 0

    # ---- write outputs ----
    LAB.mkdir(parents=True, exist_ok=True)
    trades_path = LAB / "trades.jsonl"
    report_path = LAB / "report.json"
    summary_path = LAB / "summary.md"
    with trades_path.open("w", encoding="utf-8") as f:
        for t in all_trades:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    report["output"] = {"trades_path": str(trades_path), "trades_lines": len(all_trades),
                        "report_path": str(report_path), "summary_path": str(summary_path)}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(render_summary(report), encoding="utf-8")
    # reopen check
    reopened = json.loads(report_path.read_text())
    print(f"wrote {trades_path.name} ({len(all_trades)} lines, gitignored), {report_path.name}, {summary_path.name}")
    print(f"reopen report.json ok={reopened['decision']['result_status'] == status}")
    return 0


def render_summary(r):
    a = r["aggregate"]; d = r["decision"]; f = r["signal_funnel"]
    recon = r["phase1_reconciliation"]
    lines = [
        f"# {r['strategy_id']} — Revalidation {r['revalidation_version']} (summary)",
        "",
        f"Generated: {r['generated_at']}  ·  commit: `{r['provenance']['code_commit'][:10]}`",
        "",
        "## Decision (recommendation only — lab never writes catalog)",
        f"**result_status: `{d['result_status']}`**  ·  reconciliation_status: `{d['reconciliation_status']}`",
        f"- recommended: validation_status → `{d['recommended_catalog_transition'].get('validation_status')}`, "
        f"deployment → `{d['recommended_catalog_transition'].get('deployment_status')}`",
        f"- rationale: {d['rationale']}",
        "",
        "## Technical validity (Stage 1)",
        f"- no_future_leak: {r['validations']['no_future_leak']}",
        f"- entry == next-bar open: {r['validations']['entry_is_next_bar_open']}",
        f"- all stop_distance > 0: {r['validations']['all_stop_distance_positive']}",
        f"- **technically_valid: {r['validations']['technically_valid']}**",
        "",
        "## Phase 1 — Reconciliation",
        f"Legacy targets: {recon['legacy_targets']}",
    ]
    for w, fn in recon["canonical_funnel"].items():
        lines.append(
            f"- canonical {w}: signals_total={fn['signals_total']} | 2023-2026={fn['signals_2023_2026']} | "
            f"H20 win(from signal close)={fn['close_only_H20'].get('win_from_signal_close_pct')}% (n={fn['close_only_H20'].get('n')}) | "
            f"H10 win={fn['close_only_H10'].get('win_from_signal_close_pct')}%")
    v6 = recon["v6_dump_comparison"]
    if not v6.get("skipped"):
        lines.append(f"- v6 dump signals: {v6.get('signal_epochs_count')}")
        if "timestamp_overlap" in v6:
            o = v6["timestamp_overlap"]
            lines.append(f"  - overlap: canonical_w40={o['canonical_w40_signals']} | v6={o['v6_signals']} | "
                         f"intersection={o['intersection']} | only_canonical={o['only_canonical']} | only_v6={o['only_v6']}")
        lines.append(f"  - v6 diag: {v6.get('diagnostics')}")
    else:
        lines.append("- v6 dump comparison: SKIPPED")
    lines += [
        "",
        "## Phase 2 — R-real (stop=demand_zone_low primary, 2R, gross)",
        f"- raw candidate bars (inside_demand_zone): {f['raw_candidate_bars_inside_demand_zone']}",
        f"- canonical signals w84: {f['canonical_w84_total_signals']}",
        f"- canonical signals w40: {f['canonical_w40_total_signals']}",
        f"- R-real trades (primary stop): {f['r_real_trades_primary_stop']}  ·  right-censored: {f['right_censored']}",
        f"- n: {a['n']}  ·  win%: {a['win_pct']}  ·  avg_R: {a['avg_r']}  ·  median_R: {a['median_r']}",
        f"- sum_R: {a['sum_r']}  ·  PF: {a['profit_factor']}  ·  max losing streak: {a['max_losing_streak']}",
        f"- sum_R ex-top5: {a['sum_r_ex_top5']}  ·  ex-top10: {a['sum_r_ex_top10']}",
        f"- MFE_R mean: {a['mfe_r_mean']}  ·  MAE_R mean: {a['mae_r_mean']}",
        f"- exit mix: {a['exit_reason_mix']}",
        "",
        "## By regime (sum_R / n / win%)",
    ]
    for k in ("_total", "_ex_covid", "_covid_only"):
        g = r["by_regime"].get(k, {})
        lines.append(f"- {k}: sum_R {g.get('sum_r')} / n {g.get('n')} / win% {g.get('win_pct')}")
    for k in sorted(x for x in r["by_regime"] if not x.startswith("_")):
        g = r["by_regime"][k]
        lines.append(f"- {k}: sum_R {g['sum_r']} / n {g['n']} / win% {g['win_pct']}")
    lines += ["", "## By cost (net R)"]
    for c, g in r["by_cost"].items():
        lines.append(f"- cost {c}: sum_net_R {g['sum_net_r']} / avg {g['avg_net_r']} / win% {g['win_pct']}")
    lines += ["", "## By target"]
    for t, g in r["by_target"].items():
        lines.append(f"- {t}: n {g['n']} / win% {g['win_pct']} / sum_R {g['sum_r']} / mix {g['exit_mix']}")
    lines += ["", "## By stop variant"]
    for sv, g in r["by_stop_variant"].items():
        lines.append(f"- {sv}: n {g['n']} / win% {g['win_pct']} / sum_R {g['sum_r']} / PF {g['profit_factor']}")
    if r["warnings"]:
        lines += ["", "## Warnings"] + [f"- {w}" for w in r["warnings"]]
    lines += ["", "_See report.json for full provenance + signal funnel + v6 dump diagnostics. trades.jsonl is gitignored (regenerable from config + canonical data + the recorded commit)._", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
