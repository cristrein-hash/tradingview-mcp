#!/usr/bin/env python3
"""
XAUUSD INTRADAY BB CONFLUENCE — Historical Lab v1.

Hypothesis: ZONE_REJECTION_v1.
- A 15M bar that enters a 1H or 4H DEMAND/SUPPLY zone (Custom OB canonical
  representation of BigBeluga-style zones) and closes with a directional bias
  is a candidate intraday trade.
- Stop is at the zone boundary plus a small ATR buffer.
- Targets are at +1R and +2R; primary outcome is whether +2R is hit before
  stop within 20 15M-bars (5 hours).

Read-only on slim data. Writes to:
  my-strategy/research/revalidation/XAUUSD_INTRADAY_BB_CONFLUENCE/v1/

NO TradingView/MCP calls. NO production change. NO optimization (single
config, sensible defaults; v1 answers "is there a raw edge?" not "which
threshold").
"""
import json
import bisect
import glob
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
SLIM_BASE = "/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "my-strategy/research/revalidation/XAUUSD_INTRADAY_BB_CONFLUENCE/v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Config (no sweep, single set of values; v1 anti-overfit)
# ------------------------------------------------------------------
WARMUP_BARS = 200            # 15M bars before signals (let ATR/RSI stabilize)
TIMEOUT_BARS = 20            # primary outcome window in 15M bars (= 5 hours)
SECONDARY_TIMEOUT_BARS = 40  # secondary measurement (separate stats, no filter)
STOP_BUFFER_ATR_MULT = 0.1   # stop is set 0.1*ATR_15M beyond the zone edge
TARGET_2_R = 2.0             # primary target multiple
TARGET_1_R = 1.0             # intermediate (for MFE bookkeeping)
MAX_RISK_VS_ATR = 8.0        # if (entry - stop) > 8 * ATR_15M, skip (zone too wide)
MIN_BODY_PCT_LONG = 0.30     # 15M bullish candle must have body >= 30% of range
MIN_BODY_PCT_SHORT = 0.30    # 15M bearish candle must have body >= 30% of range

STRATEGY_ID = "XAUUSD_INTRADAY_BB_CONFLUENCE"
CONFIG_ID = "ZONE_REJECTION_v1"

# ------------------------------------------------------------------
# Loaders
# ------------------------------------------------------------------
def load_slim_tf(tf):
    """Load all segments of a TF; dedup by ts keep-last; sort by ts."""
    files = sorted(glob.glob(f"{SLIM_BASE}/{tf}/*.jsonl"))
    files = [f for f in files if not f.endswith(".report.json")]
    raw = []
    for fp in files:
        with open(fp) as f:
            for line in f:
                raw.append(json.loads(line))
    seen = {}
    for b in raw:
        seen[b["ts"]] = b
    return sorted(seen.values(), key=lambda x: x["ts"])


def find_parent_idx(parent_ts_list, child_ts):
    """Return idx of the most recent parent bar with ts <= child_ts."""
    idx = bisect.bisect_right(parent_ts_list, child_ts) - 1
    return idx if idx >= 0 else None


# ------------------------------------------------------------------
# Regime by entry year (consistent with 4H BREAKOUT_CONTINUATION schema)
# ------------------------------------------------------------------
def regime_for_year(year):
    if year <= 2018: return "pre_covid"
    if year == 2019: return "bull_pre_covid"
    if year == 2020: return "covid_rally"
    if year == 2021: return "chop_post_covid"
    if year == 2022: return "chop_inflation_bear"
    if year == 2023: return "chop_macro"
    return "bull_recent"


# ------------------------------------------------------------------
# Auction / RSI / Bubble classifiers
# ------------------------------------------------------------------
def classify_bubble_context(bar):
    """Coarse classification; v1 errs toward 'unclear'."""
    if not bar.get("bubble_active"):
        return "none"
    buy_cur = bool(bar.get("bubble_buy_current"))
    sell_cur = bool(bar.get("bubble_sell_current"))
    buy_rec = bool(bar.get("bubble_buy_recent"))
    sell_rec = bool(bar.get("bubble_sell_recent"))
    large = bool(bar.get("bubble_large_current"))
    if sell_cur and large: return "rejection_supply"
    if buy_cur and large:  return "absorption_base"
    if buy_cur or buy_rec: return "continuation_support"
    if sell_cur or sell_rec: return "unclear"
    return "unclear"


def classify_rsi_context(bar):
    if bar.get("rsi_div_bearish_event"): return "bear_divergence"
    if bar.get("rsi_div_bullish_event"): return "bull_confirmation"
    rsi = bar.get("rsi")
    if rsi is None: return "unclear"
    if rsi >= 70: return "overextended"
    if rsi <= 30: return "exhaustion"
    if 45 <= rsi <= 55: return "neutral_no_trigger"
    return "unclear"


def derive_auction_dims(bar, direction):
    """Coarse auction dimensions from 15M Custom OB distances."""
    atr = bar.get("atr14_wilder") or 1.0
    nd = bar.get("nearest_demand_dist")
    ns = bar.get("nearest_supply_dist")

    def bucket(dist):
        if dist is None: return "unclear"
        if dist > 5 * atr: return "none"
        if dist > 2 * atr: return "moderate"
        return "strong"

    supply_overhead = bucket(ns)
    demand_below    = bucket(nd)

    if direction == "LONG":
        if demand_below in ("strong", "moderate") and supply_overhead == "none":
            loc = "good"
        elif demand_below in ("strong", "moderate"):
            loc = "acceptable"
        elif supply_overhead == "strong":
            loc = "bad"
        else:
            loc = "unclear"
    else:  # SHORT
        if supply_overhead in ("strong", "moderate") and demand_below == "none":
            loc = "good"
        elif supply_overhead in ("strong", "moderate"):
            loc = "acceptable"
        elif demand_below == "strong":
            loc = "bad"
        else:
            loc = "unclear"

    return {
        "location_quality": loc,
        "supply_overhead": supply_overhead,
        "demand_below": demand_below,
    }


def lookback_count_15m(slim_15m, i, n, field):
    start = max(0, i - n + 1)
    return sum(1 for k in range(start, i + 1) if slim_15m[k].get(field))


# ------------------------------------------------------------------
# Outcome simulation
# ------------------------------------------------------------------
def simulate_outcome(slim_15m, entry_idx, entry_price, stop_price,
                     target_1, target_2, direction, timeout_bars):
    """
    Walk forward from entry_idx + 1 up to timeout_bars bars.
    Stop-first intrabar check.
    Returns (exit_idx, exit_price, exit_reason, R_multiple, MFE_R, MAE_R, bars_held).
    """
    risk = abs(entry_price - stop_price)
    if risk <= 0:
        return None

    mfe = 0.0
    mae = 0.0
    end = min(len(slim_15m), entry_idx + 1 + timeout_bars)
    for j in range(entry_idx + 1, end):
        b = slim_15m[j]
        if direction == "LONG":
            # Track MAE/MFE on excursion
            mfe_j = (b["high"] - entry_price) / risk
            mae_j = (b["low"] - entry_price) / risk
        else:
            mfe_j = (entry_price - b["low"]) / risk
            mae_j = (entry_price - b["high"]) / risk
        if mfe_j > mfe: mfe = mfe_j
        if mae_j < mae: mae = mae_j

        # Stop first
        if direction == "LONG":
            if b["low"] <= stop_price:
                return dict(exit_idx=j, exit_price=stop_price,
                            exit_reason="hit_stop", R=-1.0,
                            MFE_R=mfe, MAE_R=mae, bars_held=j - entry_idx)
            if b["high"] >= target_2:
                return dict(exit_idx=j, exit_price=target_2,
                            exit_reason="hit_target_2", R=TARGET_2_R,
                            MFE_R=mfe, MAE_R=mae, bars_held=j - entry_idx)
        else:
            if b["high"] >= stop_price:
                return dict(exit_idx=j, exit_price=stop_price,
                            exit_reason="hit_stop", R=-1.0,
                            MFE_R=mfe, MAE_R=mae, bars_held=j - entry_idx)
            if b["low"] <= target_2:
                return dict(exit_idx=j, exit_price=target_2,
                            exit_reason="hit_target_2", R=TARGET_2_R,
                            MFE_R=mfe, MAE_R=mae, bars_held=j - entry_idx)

    # Timeout
    if end - 1 < len(slim_15m):
        last = slim_15m[end - 1]
        exit_price = last["close"]
        if direction == "LONG":
            r = (exit_price - entry_price) / risk
        else:
            r = (entry_price - exit_price) / risk
        return dict(exit_idx=end - 1, exit_price=exit_price,
                    exit_reason="timeout", R=r,
                    MFE_R=mfe, MAE_R=mae, bars_held=end - 1 - entry_idx)
    return None


# ------------------------------------------------------------------
# Pick best zone (1H or 4H) for a given direction
# ------------------------------------------------------------------
def pick_zone(bar15, parent_1h, parent_4h, direction):
    """
    Choose 1H or 4H zone (the one whose edge is closer to current 15M close).
    Returns dict(zone_tf, zone_type, zone_low, zone_high, distance) or None.
    """
    candidates = []
    close = bar15["close"]
    if direction == "LONG":
        for tf, p in [("1H", parent_1h), ("4H", parent_4h)]:
            if not p: continue
            zl = p.get("nearest_demand_low")
            zh = p.get("nearest_demand_high")
            if zl is None or zh is None: continue
            # distance from close to upper edge of demand zone
            dist = close - zh  # may be negative (inside zone)
            candidates.append((tf, "DEMAND", zl, zh, dist))
    else:
        for tf, p in [("1H", parent_1h), ("4H", parent_4h)]:
            if not p: continue
            zl = p.get("nearest_supply_low")
            zh = p.get("nearest_supply_high")
            if zl is None or zh is None: continue
            dist = zl - close  # may be negative (inside zone)
            candidates.append((tf, "SUPPLY", zl, zh, dist))
    if not candidates: return None
    # Prefer the zone whose boundary is closest to current price (smallest |dist|)
    candidates.sort(key=lambda c: abs(c[4]))
    tf, zt, zl, zh, dist = candidates[0]
    return dict(zone_tf=tf, zone_type=zt, zone_low=zl, zone_high=zh, distance=dist)


# ------------------------------------------------------------------
# Signal trigger
# ------------------------------------------------------------------
def long_trigger(bar15, zone):
    """Bar entered demand zone, closed bullish, body sufficient."""
    if zone is None or zone["zone_type"] != "DEMAND": return False
    if bar15["low"] > zone["zone_high"]:    return False  # never entered
    if bar15["close"] <= zone["zone_low"]:  return False  # closed below the zone (broken)
    if bar15["close"] <= bar15["open"]:     return False  # not bullish
    body = abs(bar15["close"] - bar15["open"])
    rng = max(bar15["high"] - bar15["low"], 1e-9)
    if body / rng < MIN_BODY_PCT_LONG:      return False
    return True


def short_trigger(bar15, zone):
    if zone is None or zone["zone_type"] != "SUPPLY": return False
    if bar15["high"] < zone["zone_low"]:    return False  # never entered
    if bar15["close"] >= zone["zone_high"]: return False  # closed above the zone (broken)
    if bar15["close"] >= bar15["open"]:     return False  # not bearish
    body = abs(bar15["close"] - bar15["open"])
    rng = max(bar15["high"] - bar15["low"], 1e-9)
    if body / rng < MIN_BODY_PCT_SHORT:     return False
    return True


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    print(f"[lab v1] loading slims …")
    slim_15m = load_slim_tf("15M")
    slim_30m = load_slim_tf("30M")
    slim_1h  = load_slim_tf("1H")
    slim_4h  = load_slim_tf("4H")
    slim_1d  = load_slim_tf("1D")
    print(f"  15M={len(slim_15m)}  30M={len(slim_30m)}  1H={len(slim_1h)}  4H={len(slim_4h)}  1D={len(slim_1d)}")

    ts_1h = [b["ts"] for b in slim_1h]
    ts_4h = [b["ts"] for b in slim_4h]
    ts_1d = [b["ts"] for b in slim_1d]

    # iterate 15M
    trades = []
    n_long_trig = 0
    n_short_trig = 0
    n_zone_missing = 0
    n_risk_skip = 0
    n_atr_null = 0

    no_overlap_last_exit_idx = -1

    print(f"[lab v1] iterating 15M bars (warmup={WARMUP_BARS}) …")
    for i in range(WARMUP_BARS, len(slim_15m) - SECONDARY_TIMEOUT_BARS):
        bar = slim_15m[i]
        # no-overlap: skip if we are still inside a previous trade
        if i <= no_overlap_last_exit_idx:
            continue
        atr = bar.get("atr14_wilder")
        if atr is None:
            n_atr_null += 1
            continue

        # parent lookups
        p1h_idx = find_parent_idx(ts_1h, bar["ts"])
        p4h_idx = find_parent_idx(ts_4h, bar["ts"])
        p1d_idx = find_parent_idx(ts_1d, bar["ts"])
        if p1h_idx is None or p4h_idx is None or p1d_idx is None:
            continue
        parent_1h = slim_1h[p1h_idx]
        parent_4h = slim_4h[p4h_idx]
        parent_1d = slim_1d[p1d_idx]

        # pick LONG zone first
        for direction, trig_fn in [("LONG", long_trigger), ("SHORT", short_trigger)]:
            zone = pick_zone(bar, parent_1h, parent_4h, direction)
            if not zone:
                n_zone_missing += 1
                continue
            if not trig_fn(bar, zone):
                continue

            # compute entry/stop/targets
            entry = bar["close"]
            buf = STOP_BUFFER_ATR_MULT * atr
            if direction == "LONG":
                stop = zone["zone_low"] - buf
                risk = entry - stop
            else:
                stop = zone["zone_high"] + buf
                risk = stop - entry

            if risk <= 0:
                n_risk_skip += 1
                continue
            if risk > MAX_RISK_VS_ATR * atr:
                n_risk_skip += 1
                continue

            if direction == "LONG":
                target_1 = entry + TARGET_1_R * risk
                target_2 = entry + TARGET_2_R * risk
            else:
                target_1 = entry - TARGET_1_R * risk
                target_2 = entry - TARGET_2_R * risk

            # outcome primary
            out = simulate_outcome(slim_15m, i, entry, stop,
                                   target_1, target_2, direction, TIMEOUT_BARS)
            if not out:
                continue

            # outcome secondary (40 bars) — for sanity comparison only, no filter
            out_sec = simulate_outcome(slim_15m, i, entry, stop,
                                       target_1, target_2, direction,
                                       SECONDARY_TIMEOUT_BARS)

            # contextual fields
            bub_ctx = classify_bubble_context(bar)
            rsi_ctx = classify_rsi_context(bar)
            auc = derive_auction_dims(bar, direction)
            short_count_10 = lookback_count_15m(slim_15m, i, 10,
                                                "nas_label_short_event")
            short_count_15 = lookback_count_15m(slim_15m, i, 15,
                                                "nas_label_short_event")
            long_count_10  = lookback_count_15m(slim_15m, i, 10,
                                                "nas_label_long_event")
            long_count_15  = lookback_count_15m(slim_15m, i, 15,
                                                "nas_label_long_event")

            # regime (by entry year)
            entry_year = int(slim_15m[i + 1]["ts"][:4]) if i + 1 < len(slim_15m) else int(bar["ts"][:4])
            regime = regime_for_year(entry_year)

            t = {
                "strategy_id": STRATEGY_ID,
                "config_id": CONFIG_ID,
                "direction": direction,
                "signal_bar_15m": i,
                "signal_iso": bar["ts"],
                "entry_bar_15m": i + 1,
                "entry_iso": slim_15m[i + 1]["ts"] if i + 1 < len(slim_15m) else bar["ts"],
                "exit_bar_15m": out["exit_idx"],
                "exit_iso": slim_15m[out["exit_idx"]]["ts"],
                "entry_price": entry,
                "stop_price": stop,
                "target_1_price": target_1,
                "target_2_price": target_2,
                "exit_price": out["exit_price"],
                "atr14_15m": atr,
                "risk": risk,
                "R_multiple": out["R"],
                "MFE_R": out["MFE_R"],
                "MAE_R": out["MAE_R"],
                "exit_reason": out["exit_reason"],
                "bars_held": out["bars_held"],
                "outcome_status": out["exit_reason"],  # alias for schema clarity
                "zone_tf": zone["zone_tf"],
                "zone_type": zone["zone_type"],
                "zone_low": zone["zone_low"],
                "zone_high": zone["zone_high"],
                "distance_to_zone": zone["distance"],
                "regime_1d": regime,
                "rsi_value": bar.get("rsi"),
                "rsi_context": rsi_ctx,
                "rsi_above_ma": bar.get("rsi_above_ma"),
                "bubble_context": bub_ctx,
                "bubble_buy_current": bool(bar.get("bubble_buy_current")),
                "bubble_sell_current": bool(bar.get("bubble_sell_current")),
                "bubble_buy_recent": bool(bar.get("bubble_buy_recent")),
                "bubble_sell_recent": bool(bar.get("bubble_sell_recent")),
                "bubble_large_current": bool(bar.get("bubble_large_current")),
                "bubble_size_rank": bar.get("bubble_size_rank"),
                "bubble_activations_window": bar.get("bubble_activations_window"),
                "nas_short_count_10": short_count_10,
                "nas_short_count_15": short_count_15,
                "nas_long_count_10": long_count_10,
                "nas_long_count_15": long_count_15,
                "smc_has_recent_bos": bool(bar.get("smc_has_recent_bos")),
                "smc_has_recent_choch": bool(bar.get("smc_has_recent_choch")),
                "smc_last_bos_dir": bar.get("smc_last_swing_bos_direction"),
                "smc_last_choch_dir": bar.get("smc_last_swing_choch_direction"),
                "location_quality": auc["location_quality"],
                "supply_overhead_15m": auc["supply_overhead"],
                "demand_below_15m": auc["demand_below"],
                "entry_timing": "unclear",  # v1: not derivable robustly without forward look; left for v2
                "acceptance_quality": (
                    "accepted" if out["exit_reason"] == "hit_target_2"
                    else "rejected" if out["exit_reason"] == "hit_stop"
                    else "pending"
                ),
                "secondary_40bar_R": out_sec["R"] if out_sec else None,
                "secondary_40bar_exit_reason": out_sec["exit_reason"] if out_sec else None,
            }
            trades.append(t)
            no_overlap_last_exit_idx = out["exit_idx"]
            if direction == "LONG":
                n_long_trig += 1
            else:
                n_short_trig += 1
            break  # one trade per 15M bar

    print(f"[lab v1] trades collected: {len(trades)}  "
          f"(long_trig={n_long_trig}, short_trig={n_short_trig}, "
          f"atr_null_skip={n_atr_null}, zone_missing_skip={n_zone_missing}, risk_skip={n_risk_skip})")

    # ------------------------------------------------------------------
    # Write trades.jsonl
    # ------------------------------------------------------------------
    trades_path = OUT_DIR / "trades.jsonl"
    with open(trades_path, "w") as f:
        for t in trades:
            f.write(json.dumps(t) + "\n")
    print(f"[lab v1] wrote {trades_path}")

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    def summarize(group):
        n = len(group)
        if n == 0:
            return dict(n=0, wins=0, win_rate=0.0, total_R=0.0, avg_R=0.0,
                        PF=0.0, mfe_avg=0.0, mae_avg=0.0)
        wins = sum(1 for t in group if t["R_multiple"] > 0)
        total_R = sum(t["R_multiple"] for t in group)
        win_R = sum(t["R_multiple"] for t in group if t["R_multiple"] > 0)
        loss_R = sum(-t["R_multiple"] for t in group if t["R_multiple"] < 0)
        pf = (win_R / loss_R) if loss_R > 0 else (float("inf") if win_R > 0 else 0.0)
        mfe = sum(t["MFE_R"] for t in group) / n
        mae = sum(t["MAE_R"] for t in group) / n
        return dict(n=n, wins=wins, win_rate=wins / n, total_R=total_R,
                    avg_R=total_R / n, PF=pf, mfe_avg=mfe, mae_avg=mae)

    report = {
        "strategy_id": STRATEGY_ID,
        "config_id": CONFIG_ID,
        "lab_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_window": {
            "15M_first": slim_15m[0]["ts"], "15M_last": slim_15m[-1]["ts"],
            "1H_first": slim_1h[0]["ts"], "1H_last": slim_1h[-1]["ts"],
            "4H_first": slim_4h[0]["ts"], "4H_last": slim_4h[-1]["ts"],
            "1D_first": slim_1d[0]["ts"], "1D_last": slim_1d[-1]["ts"],
        },
        "config": {
            "warmup_bars": WARMUP_BARS,
            "timeout_bars_primary": TIMEOUT_BARS,
            "timeout_bars_secondary": SECONDARY_TIMEOUT_BARS,
            "stop_buffer_atr_mult": STOP_BUFFER_ATR_MULT,
            "target_R": TARGET_2_R,
            "min_body_pct": MIN_BODY_PCT_LONG,
            "max_risk_vs_atr": MAX_RISK_VS_ATR,
            "zone_definition": "Custom OB (custom_ob_demand_active / custom_ob_supply_active) "
                               "as canonical BigBeluga-style zone proxy from slim. "
                               "nearest_demand_high/low and nearest_supply_high/low "
                               "from the parent 1H or 4H bar at signal time (no lookahead).",
            "no_overlap": True,
            "intrabar": "stop_first",
        },
        "totals": summarize(trades),
        "by_direction": {
            "LONG": summarize([t for t in trades if t["direction"] == "LONG"]),
            "SHORT": summarize([t for t in trades if t["direction"] == "SHORT"]),
        },
        "by_zone_tf": {
            "1H": summarize([t for t in trades if t["zone_tf"] == "1H"]),
            "4H": summarize([t for t in trades if t["zone_tf"] == "4H"]),
        },
        "by_zone_type": {
            "DEMAND": summarize([t for t in trades if t["zone_type"] == "DEMAND"]),
            "SUPPLY": summarize([t for t in trades if t["zone_type"] == "SUPPLY"]),
        },
        "by_regime_1d": {
            k: summarize([t for t in trades if t["regime_1d"] == k])
            for k in sorted({t["regime_1d"] for t in trades})
        },
        "by_bubble_context": {
            k: summarize([t for t in trades if t["bubble_context"] == k])
            for k in sorted({t["bubble_context"] for t in trades})
        },
        "by_rsi_context": {
            k: summarize([t for t in trades if t["rsi_context"] == k])
            for k in sorted({t["rsi_context"] for t in trades})
        },
        "by_location_quality": {
            k: summarize([t for t in trades if t["location_quality"] == k])
            for k in sorted({t["location_quality"] for t in trades})
        },
        "by_smc_recent_bos": {
            "True": summarize([t for t in trades if t["smc_has_recent_bos"]]),
            "False": summarize([t for t in trades if not t["smc_has_recent_bos"]]),
        },
        "by_smc_recent_choch": {
            "True": summarize([t for t in trades if t["smc_has_recent_choch"]]),
            "False": summarize([t for t in trades if not t["smc_has_recent_choch"]]),
        },
        "by_nas_long_in_last_15": {
            "yes": summarize([t for t in trades if t["nas_long_count_15"] > 0]),
            "no":  summarize([t for t in trades if t["nas_long_count_15"] == 0]),
        },
        "by_nas_short_in_last_15": {
            "yes": summarize([t for t in trades if t["nas_short_count_15"] > 0]),
            "no":  summarize([t for t in trades if t["nas_short_count_15"] == 0]),
        },
        "by_bubble_buy_recent": {
            "yes": summarize([t for t in trades if t["bubble_buy_recent"]]),
            "no":  summarize([t for t in trades if not t["bubble_buy_recent"]]),
        },
        "by_bubble_sell_recent": {
            "yes": summarize([t for t in trades if t["bubble_sell_recent"]]),
            "no":  summarize([t for t in trades if not t["bubble_sell_recent"]]),
        },
        "exit_reasons": dict(Counter(t["exit_reason"] for t in trades)),
        "discard_counters": {
            "atr_null_skip": n_atr_null,
            "zone_missing_skip": n_zone_missing,
            "risk_skip": n_risk_skip,
        },
    }
    report_path = OUT_DIR / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[lab v1] wrote {report_path}")

    # ------------------------------------------------------------------
    # Summary.md
    # ------------------------------------------------------------------
    def md_row(label, s):
        return (f"| {label} | {s['n']} | {s['win_rate']:.3f} | "
                f"{s['avg_R']:+.3f} | {s['total_R']:+.2f} | {s['PF']:.3f} | "
                f"{s['mfe_avg']:+.2f} | {s['mae_avg']:+.2f} |")

    md = []
    md.append("# XAUUSD INTRADAY BB CONFLUENCE — Historical Lab v1 — Summary\n")
    md.append(f"- Strategy: `{STRATEGY_ID}`\n")
    md.append(f"- Config: `{CONFIG_ID}`\n")
    md.append(f"- Generated: {report['generated_at']}\n")
    md.append(f"- 15M window: {report['data_window']['15M_first']} → {report['data_window']['15M_last']}\n")
    md.append(f"- Bars: 15M={len(slim_15m)}  1H={len(slim_1h)}  4H={len(slim_4h)}  1D={len(slim_1d)}\n")
    md.append(f"- Trades collected: **{len(trades)}** (LONG={n_long_trig}, SHORT={n_short_trig})\n")
    md.append(f"- Discards: zone_missing={n_zone_missing}  risk_skip={n_risk_skip}  atr_null={n_atr_null}\n")
    md.append("")
    md.append("## Totals (primary outcome at 20 15M-bars)\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    md.append(md_row("ALL", report["totals"]))
    md.append("")
    md.append("## By direction\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in ("LONG", "SHORT"):
        md.append(md_row(k, report["by_direction"][k]))
    md.append("")
    md.append("## By zone_tf\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in ("1H", "4H"):
        md.append(md_row(k, report["by_zone_tf"][k]))
    md.append("")
    md.append("## By zone_type\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in ("DEMAND", "SUPPLY"):
        md.append(md_row(k, report["by_zone_type"][k]))
    md.append("")
    md.append("## By regime_1d (entry year bucket)\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_regime_1d"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By bubble_context\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_bubble_context"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By rsi_context\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_rsi_context"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By location_quality (auction)\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_location_quality"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By SMC recent BOS / CHoCH\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    md.append(md_row("BOS present", report["by_smc_recent_bos"]["True"]))
    md.append(md_row("BOS absent",  report["by_smc_recent_bos"]["False"]))
    md.append(md_row("CHoCH present", report["by_smc_recent_choch"]["True"]))
    md.append(md_row("CHoCH absent",  report["by_smc_recent_choch"]["False"]))
    md.append("")
    md.append("## By NAS labels in last 15 bars\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    md.append(md_row("NAS LONG present",  report["by_nas_long_in_last_15"]["yes"]))
    md.append(md_row("NAS LONG absent",   report["by_nas_long_in_last_15"]["no"]))
    md.append(md_row("NAS SHORT present", report["by_nas_short_in_last_15"]["yes"]))
    md.append(md_row("NAS SHORT absent",  report["by_nas_short_in_last_15"]["no"]))
    md.append("")
    md.append("## By Bubble buy/sell recent\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE_avg | MAE_avg |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    md.append(md_row("BUY bubble recent",  report["by_bubble_buy_recent"]["yes"]))
    md.append(md_row("no BUY bubble",      report["by_bubble_buy_recent"]["no"]))
    md.append(md_row("SELL bubble recent", report["by_bubble_sell_recent"]["yes"]))
    md.append(md_row("no SELL bubble",     report["by_bubble_sell_recent"]["no"]))
    md.append("")
    md.append(f"## Exit reasons\n")
    for k, c in report["exit_reasons"].items():
        md.append(f"- `{k}`: {c}")
    md.append("")
    md.append("## Notes\n")
    md.append("- Zones use Custom OB (canonical slim representation of BigBeluga-style zones).")
    md.append("- Parent 1H/4H bars looked up by `bisect_right(ts) - 1` (no lookahead).")
    md.append("- Primary outcome window = 20 15M-bars (5 hours). Secondary 40-bar window recorded per-trade in `secondary_40bar_R` for inspection but not aggregated here.")
    md.append("- v1 has no optimization, no filter sweep, no threshold tuning.")
    md.append("- Auction dimensions (location_quality, supply_overhead, demand_below) are diagnostic only.")

    summary_path = OUT_DIR / "summary.md"
    with open(summary_path, "w") as f:
        f.write("\n".join(md) + "\n")
    print(f"[lab v1] wrote {summary_path}")

    # quick stdout
    print()
    print("=== TOTALS ===")
    for k, v in report["totals"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
