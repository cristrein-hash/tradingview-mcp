#!/usr/bin/env python3
"""
XAUUSD 1H AUCTION CONFLUENCE LAB v1.

5 Auction-Theory archetypes tested on the 1H slim:
  A1  DEMAND_ABSORPTION_LONG       — sell pressure + reclaim at demand zone
  A2  CLEAN_DEMAND_REJECTION_LONG  — clean reject, no sell pressure, no buy climax
  A3  BAD_FALLING_KNIFE_LONG       — sell pressure + no reclaim (diagnostic negative)
  A4  SUPPLY_REJECTION_SHORT       — clean reject at supply zone (regime-agnostic)
  A5  BAD_SHORT_IN_BULL_REGIME     — short at supply while 1D macro is bullish

Read-only on slim. Writes to:
  my-strategy/research/revalidation/XAUUSD_1H_AUCTION_CONFLUENCE_LAB/v1/

NO TradingView/MCP calls. NO production change. NO optimization. v1 answers
the directional question "does any archetype have raw historical edge?" — it
does not select filters or promote strategy.
"""
import json
import bisect
import glob
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
SLIM_BASE = "/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "my-strategy/research/revalidation/XAUUSD_1H_AUCTION_CONFLUENCE_LAB/v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Config (no sweep)
# ----------------------------------------------------------------------
WARMUP_BARS = 200
TIMEOUT_BARS = 20                  # 20 1H bars
STOP_BUFFER_ATR_MULT = 0.1
TARGET_2_R = 2.0
TARGET_1_R = 1.0
MAX_RISK_VS_ATR = 8.0
MIN_BODY_PCT = 0.40
SELL_PRESSURE_LOOKBACK = 5         # bars for NAS short count in A1
SUPPLY_FAR_ATR_MULT = 2.0          # for A2 cleanness criterion
DEMAND_FAR_ATR_MULT = 2.0          # for A4 cleanness criterion

STRATEGY_ID = "XAUUSD_1H_AUCTION_CONFLUENCE_LAB"
CONFIG_ID = "AUCTION_v1"


# ----------------------------------------------------------------------
# Slim loading
# ----------------------------------------------------------------------
def load_slim_tf(tf):
    files = sorted(glob.glob(f"{SLIM_BASE}/{tf}/*.jsonl"))
    files = [f for f in files if not f.endswith("report.json")]
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
    idx = bisect.bisect_right(parent_ts_list, child_ts) - 1
    return idx if idx >= 0 else None


# ----------------------------------------------------------------------
# 1D EMA50 / EMA200 (for A5 regime check)
# ----------------------------------------------------------------------
def ema(arr, p):
    a = 2 / (p + 1)
    out = [None] * len(arr)
    if len(arr) < p:
        return out
    s = sum(arr[:p]) / p
    out[p - 1] = s
    for i in range(p, len(arr)):
        s = arr[i] * a + s * (1 - a)
        out[i] = s
    return out


def is_d1a_bullish(close, e50, e200):
    if e50 is None or e200 is None:
        return False
    return close > e200 and e50 > e200


# ----------------------------------------------------------------------
# Regime by entry year
# ----------------------------------------------------------------------
def regime_for_year(y):
    if y <= 2018: return "pre_covid"
    if y == 2019: return "bull_pre_covid"
    if y == 2020: return "covid_rally"
    if y == 2021: return "chop_post_covid"
    if y == 2022: return "chop_inflation_bear"
    if y == 2023: return "chop_macro"
    return "bull_recent"


# ----------------------------------------------------------------------
# Diagnostic classifiers (recorded per trade, NOT used as filters)
# ----------------------------------------------------------------------
def rsi_context(bar):
    if bar.get("rsi_div_bearish_event"): return "bear_divergence"
    if bar.get("rsi_div_bullish_event"): return "bull_confirmation"
    r = bar.get("rsi")
    if r is None: return "unclear"
    if r >= 70: return "overextended"
    if r <= 30: return "exhaustion"
    if 45 <= r <= 55: return "neutral_no_trigger"
    return "unclear"


def auction_dims_for_direction(bar, direction):
    atr = bar.get("atr14_wilder") or 1.0
    nd = bar.get("nearest_demand_dist")
    ns = bar.get("nearest_supply_dist")

    def b(d):
        if d is None: return "unclear"
        if d > 5 * atr: return "none"
        if d > 2 * atr: return "moderate"
        return "strong"

    supply_overhead = b(ns)
    demand_below = b(nd)
    if direction == "LONG":
        if demand_below in ("strong", "moderate") and supply_overhead == "none":
            loc = "good"
        elif demand_below in ("strong", "moderate"):
            loc = "acceptable"
        elif supply_overhead == "strong":
            loc = "bad"
        else:
            loc = "unclear"
    else:
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


def lookback_count(slim, i, n, key):
    start = max(0, i - n + 1)
    return sum(1 for k in range(start, i + 1) if slim[k].get(key))


def smc_direction(bar):
    bd = bar.get("smc_last_swing_bos_direction")
    cd = bar.get("smc_last_swing_choch_direction")
    if cd == "bull" or bd == "bull": return "bull"
    if cd == "bear" or bd == "bear": return "bear"
    return None


# ----------------------------------------------------------------------
# Zone picking (1H or 4H Custom OB)
# ----------------------------------------------------------------------
def pick_zone(bar, parent_1h_zone, parent_4h_zone, direction):
    """
    parent_1h_zone, parent_4h_zone: dicts with nearest_demand_* / nearest_supply_*
    (we pass the actual bar at the parent index here; nearest_demand/supply
    fields come from that parent bar's Custom OB tracking).
    """
    candidates = []
    close = bar["close"]
    for tf, p in [("1H", parent_1h_zone), ("4H", parent_4h_zone)]:
        if not p:
            continue
        if direction == "LONG":
            zl, zh = p.get("nearest_demand_low"), p.get("nearest_demand_high")
            if zl is None or zh is None: continue
            candidates.append((tf, "DEMAND", zl, zh, close - zh))
        else:
            zl, zh = p.get("nearest_supply_low"), p.get("nearest_supply_high")
            if zl is None or zh is None: continue
            candidates.append((tf, "SUPPLY", zl, zh, zl - close))
    if not candidates:
        return None
    candidates.sort(key=lambda c: abs(c[4]))
    tf, zt, zl, zh, dist = candidates[0]
    return dict(zone_tf=tf, zone_type=zt, zone_low=zl, zone_high=zh, distance=dist)


# ----------------------------------------------------------------------
# Trigger predicates
# ----------------------------------------------------------------------
def long_basic_trigger(bar, zone):
    if zone is None or zone["zone_type"] != "DEMAND": return False
    if bar["low"] > zone["zone_high"]: return False
    if bar["close"] <= zone["zone_low"]: return False
    return True


def short_basic_trigger(bar, zone):
    if zone is None or zone["zone_type"] != "SUPPLY": return False
    if bar["high"] < zone["zone_low"]: return False
    if bar["close"] >= zone["zone_high"]: return False
    return True


# ----------------------------------------------------------------------
# Archetype classification
# ----------------------------------------------------------------------
def classify_long_archetype(bar, zone, slim, i):
    """Return archetype id or None. A1/A2/A3 are exclusive by construction."""
    body = abs(bar["close"] - bar["open"])
    rng = max(bar["high"] - bar["low"], 1e-9)
    body_pct = body / rng
    bullish = bar["close"] > bar["open"]
    rsi = bar.get("rsi") or 50

    sell_pressure_recent = bool(bar.get("bubble_sell_recent")) or \
                           lookback_count(slim, i, SELL_PRESSURE_LOOKBACK, "nas_label_short_event") >= 1
    buy_climax = bool(bar.get("bubble_buy_recent"))
    reclaim = bar["close"] > zone["zone_high"]
    auc = auction_dims_for_direction(bar, "LONG")

    # A2: clean
    supply_far = (bar.get("nearest_supply_dist") is None) or \
                 (bar.get("nearest_supply_dist", 0) > SUPPLY_FAR_ATR_MULT * (bar.get("atr14_wilder") or 1.0))
    if (not sell_pressure_recent and not buy_climax and supply_far and
            bullish and body_pct >= MIN_BODY_PCT):
        return "A2_CLEAN_DEMAND_REJECTION_LONG"

    # A1: absorption (sell pressure + reclaim)
    if sell_pressure_recent and reclaim and bullish and rsi > 30 and body_pct >= MIN_BODY_PCT:
        return "A1_DEMAND_ABSORPTION_LONG"

    # A3: falling knife (sell pressure + no reclaim + bad/unclear location + smc bear bias)
    smc_bear = (bar.get("smc_has_recent_bos") and bar.get("smc_last_swing_bos_direction") == "bear") or \
               (bar.get("smc_has_recent_choch") and bar.get("smc_last_swing_choch_direction") == "bear")
    if (sell_pressure_recent and not reclaim and
            auc["location_quality"] in ("bad", "unclear") and smc_bear):
        return "A3_BAD_FALLING_KNIFE_LONG"

    return None


def classify_short_archetype(bar, zone, slim, i, parent_1d_bullish):
    body = abs(bar["close"] - bar["open"])
    rng = max(bar["high"] - bar["low"], 1e-9)
    body_pct = body / rng
    bearish = bar["close"] < bar["open"]

    buy_pressure_recent = bool(bar.get("bubble_buy_recent")) or \
                          lookback_count(slim, i, SELL_PRESSURE_LOOKBACK, "nas_label_long_event") >= 1
    sell_climax = bool(bar.get("bubble_sell_recent"))
    demand_far = (bar.get("nearest_demand_dist") is None) or \
                 (bar.get("nearest_demand_dist", 0) > DEMAND_FAR_ATR_MULT * (bar.get("atr14_wilder") or 1.0))

    if not bearish or body_pct < MIN_BODY_PCT:
        return None
    if buy_pressure_recent or sell_climax or not demand_far:
        return None

    # A5 if 1D regime bullish (per D1a); else A4
    return "A5_BAD_SHORT_IN_BULL_REGIME" if parent_1d_bullish else "A4_SUPPLY_REJECTION_SHORT"


# ----------------------------------------------------------------------
# Outcome simulation (1H bars)
# ----------------------------------------------------------------------
def simulate_outcome(slim, entry_idx, entry_price, stop_price, target_2,
                     direction, timeout):
    risk = abs(entry_price - stop_price)
    if risk <= 0:
        return None
    mfe = 0.0
    mae = 0.0
    end = min(len(slim), entry_idx + 1 + timeout)
    for j in range(entry_idx + 1, end):
        b = slim[j]
        if direction == "LONG":
            mfe_j = (b["high"] - entry_price) / risk
            mae_j = (b["low"] - entry_price) / risk
        else:
            mfe_j = (entry_price - b["low"]) / risk
            mae_j = (entry_price - b["high"]) / risk
        if mfe_j > mfe: mfe = mfe_j
        if mae_j < mae: mae = mae_j

        if direction == "LONG":
            if b["low"] <= stop_price:
                return dict(exit_idx=j, exit_price=stop_price, exit_reason="hit_stop",
                            R=-1.0, MFE_R=mfe, MAE_R=mae, bars_held=j - entry_idx)
            if b["high"] >= target_2:
                return dict(exit_idx=j, exit_price=target_2, exit_reason="hit_target_2",
                            R=TARGET_2_R, MFE_R=mfe, MAE_R=mae, bars_held=j - entry_idx)
        else:
            if b["high"] >= stop_price:
                return dict(exit_idx=j, exit_price=stop_price, exit_reason="hit_stop",
                            R=-1.0, MFE_R=mfe, MAE_R=mae, bars_held=j - entry_idx)
            if b["low"] <= target_2:
                return dict(exit_idx=j, exit_price=target_2, exit_reason="hit_target_2",
                            R=TARGET_2_R, MFE_R=mfe, MAE_R=mae, bars_held=j - entry_idx)

    if end - 1 < len(slim):
        last = slim[end - 1]
        ep = last["close"]
        r = ((ep - entry_price) / risk) if direction == "LONG" else ((entry_price - ep) / risk)
        return dict(exit_idx=end - 1, exit_price=ep, exit_reason="timeout",
                    R=r, MFE_R=mfe, MAE_R=mae, bars_held=end - 1 - entry_idx)
    return None


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    print(f"[1H auction lab v1] loading slims …")
    slim_1h = load_slim_tf("1H")
    slim_4h = load_slim_tf("4H")
    slim_1d = load_slim_tf("1D")
    print(f"  1H={len(slim_1h)}  4H={len(slim_4h)}  1D={len(slim_1d)}")

    ts_4h = [b["ts"] for b in slim_4h]
    ts_1d = [b["ts"] for b in slim_1d]

    # 1D EMAs for A5 regime
    closes_1d = [b["close"] for b in slim_1d]
    e50_1d = ema(closes_1d, 50)
    e200_1d = ema(closes_1d, 200)

    trades = []
    long_last_exit_idx = -1
    short_last_exit_idx = -1
    n_no_zone_long = 0
    n_no_zone_short = 0
    n_atr_null = 0
    n_risk_skip = 0

    arch_counter = Counter()

    print(f"[1H auction lab v1] iterating 1H bars (warmup={WARMUP_BARS}) …")
    for i in range(WARMUP_BARS, len(slim_1h) - TIMEOUT_BARS):
        bar = slim_1h[i]
        atr = bar.get("atr14_wilder")
        if atr is None:
            n_atr_null += 1
            continue

        p4 = find_parent_idx(ts_4h, bar["ts"])
        p1d = find_parent_idx(ts_1d, bar["ts"])
        if p4 is None or p1d is None:
            continue
        parent_4h_bar = slim_4h[p4]
        parent_1d_bar = slim_1d[p1d]

        # 1D regime bullishness at signal time
        d_bull = is_d1a_bullish(closes_1d[p1d], e50_1d[p1d], e200_1d[p1d])

        for direction in ("LONG", "SHORT"):
            if direction == "LONG" and i <= long_last_exit_idx:
                continue
            if direction == "SHORT" and i <= short_last_exit_idx:
                continue
            zone = pick_zone(bar, bar, parent_4h_bar, direction)  # 1H "parent" = own bar (zone fields are 1H)
            if not zone:
                if direction == "LONG":
                    n_no_zone_long += 1
                else:
                    n_no_zone_short += 1
                continue
            if direction == "LONG" and not long_basic_trigger(bar, zone):
                continue
            if direction == "SHORT" and not short_basic_trigger(bar, zone):
                continue

            if direction == "LONG":
                arch = classify_long_archetype(bar, zone, slim_1h, i)
            else:
                arch = classify_short_archetype(bar, zone, slim_1h, i, d_bull)
            if not arch:
                continue

            entry = bar["close"]
            buf = STOP_BUFFER_ATR_MULT * atr
            if direction == "LONG":
                stop = zone["zone_low"] - buf
                risk = entry - stop
            else:
                stop = zone["zone_high"] + buf
                risk = stop - entry
            if risk <= 0 or risk > MAX_RISK_VS_ATR * atr:
                n_risk_skip += 1
                continue
            if direction == "LONG":
                target_1 = entry + TARGET_1_R * risk
                target_2 = entry + TARGET_2_R * risk
            else:
                target_1 = entry - TARGET_1_R * risk
                target_2 = entry - TARGET_2_R * risk

            out = simulate_outcome(slim_1h, i, entry, stop, target_2,
                                   direction, TIMEOUT_BARS)
            if not out:
                continue

            auc = auction_dims_for_direction(bar, direction)
            rctx = rsi_context(bar)
            entry_year = int(slim_1h[i + 1]["ts"][:4]) if i + 1 < len(slim_1h) else int(bar["ts"][:4])
            regime = regime_for_year(entry_year)

            # acceptance_quality: trade outcome-derived for v1 diagnostic
            if out["exit_reason"] == "hit_target_2":
                acceptance = "accepted"
            elif out["exit_reason"] == "hit_stop":
                acceptance = "rejected"
            else:
                acceptance = "pending"

            t = {
                "strategy_id": STRATEGY_ID,
                "config_id": CONFIG_ID,
                "archetype": arch,
                "direction": direction,
                "signal_bar_1h": i,
                "signal_iso": bar["ts"],
                "entry_bar_1h": i + 1,
                "entry_iso": slim_1h[i + 1]["ts"] if i + 1 < len(slim_1h) else bar["ts"],
                "exit_bar_1h": out["exit_idx"],
                "exit_iso": slim_1h[out["exit_idx"]]["ts"],
                "entry_price": entry,
                "stop_price": stop,
                "target_1_price": target_1,
                "target_2_price": target_2,
                "exit_price": out["exit_price"],
                "atr14_1h": atr,
                "risk": risk,
                "R_multiple": out["R"],
                "MFE_R": out["MFE_R"],
                "MAE_R": out["MAE_R"],
                "exit_reason": out["exit_reason"],
                "bars_held": out["bars_held"],
                "zone_tf": zone["zone_tf"],
                "zone_type": zone["zone_type"],
                "zone_low": zone["zone_low"],
                "zone_high": zone["zone_high"],
                "distance_to_zone": zone["distance"],
                "distance_to_opposing_zone": (
                    bar.get("nearest_supply_dist") if direction == "LONG" else bar.get("nearest_demand_dist")
                ),
                "regime_1d": regime,
                "d1a_1d_bullish": bool(d_bull),
                "location_quality": auc["location_quality"],
                "supply_overhead": auc["supply_overhead"],
                "demand_below": auc["demand_below"],
                "acceptance_quality": acceptance,
                "entry_timing": "unclear",
                "rsi_value": bar.get("rsi"),
                "rsi_context": rctx,
                "rsi_above_ma": bar.get("rsi_above_ma"),
                "rsi_div_bullish_event": bool(bar.get("rsi_div_bullish_event")),
                "rsi_div_bearish_event": bool(bar.get("rsi_div_bearish_event")),
                "bubble_buy_current": bool(bar.get("bubble_buy_current")),
                "bubble_sell_current": bool(bar.get("bubble_sell_current")),
                "bubble_buy_recent": bool(bar.get("bubble_buy_recent")),
                "bubble_sell_recent": bool(bar.get("bubble_sell_recent")),
                "bubble_large_current": bool(bar.get("bubble_large_current")),
                "bubble_size_rank": bar.get("bubble_size_rank"),
                "bubble_activations_window": bar.get("bubble_activations_window"),
                "nas_long_recent": bool(bar.get("nas_label_long_event")),
                "nas_short_recent": bool(bar.get("nas_label_short_event")),
                "nas_long_count_15": lookback_count(slim_1h, i, 15, "nas_label_long_event"),
                "nas_short_count_15": lookback_count(slim_1h, i, 15, "nas_label_short_event"),
                "smc_bos_recent": bool(bar.get("smc_has_recent_bos")),
                "smc_choch_recent": bool(bar.get("smc_has_recent_choch")),
                "smc_direction": smc_direction(bar),
            }
            trades.append(t)
            arch_counter[arch] += 1
            if direction == "LONG":
                long_last_exit_idx = out["exit_idx"]
            else:
                short_last_exit_idx = out["exit_idx"]

    print(f"[1H auction lab v1] trades collected: {len(trades)}")
    print(f"  per-archetype: {dict(arch_counter)}")
    print(f"  discards: atr_null={n_atr_null}  zone_missing_long={n_no_zone_long}  zone_missing_short={n_no_zone_short}  risk_skip={n_risk_skip}")

    # write trades.jsonl
    trades_path = OUT_DIR / "trades.jsonl"
    with open(trades_path, "w") as f:
        for t in trades:
            f.write(json.dumps(t) + "\n")
    print(f"[1H auction lab v1] wrote {trades_path}")

    # summarize helper
    def summarize(group):
        n = len(group)
        if n == 0:
            return dict(n=0, wins=0, win_rate=0.0, total_R=0.0, avg_R=0.0,
                        PF=0.0, mfe_avg=0.0, mae_avg=0.0, exit_reasons={})
        wins = sum(1 for t in group if t["R_multiple"] > 0)
        total_R = sum(t["R_multiple"] for t in group)
        win_R = sum(t["R_multiple"] for t in group if t["R_multiple"] > 0)
        loss_R = sum(-t["R_multiple"] for t in group if t["R_multiple"] < 0)
        pf = (win_R / loss_R) if loss_R > 0 else (float("inf") if win_R > 0 else 0.0)
        mfe = sum(t["MFE_R"] for t in group) / n
        mae = sum(t["MAE_R"] for t in group) / n
        return dict(n=n, wins=wins, win_rate=wins / n, total_R=total_R, avg_R=total_R / n,
                    PF=pf, mfe_avg=mfe, mae_avg=mae,
                    exit_reasons=dict(Counter(t["exit_reason"] for t in group)))

    def by_field(field):
        keys = sorted({t.get(field) for t in trades})
        return {str(k): summarize([t for t in trades if t.get(field) == k]) for k in keys}

    def by_field_within(arch, field):
        sub = [t for t in trades if t["archetype"] == arch]
        keys = sorted({t.get(field) for t in sub})
        return {str(k): summarize([t for t in sub if t.get(field) == k]) for k in keys}

    report = {
        "strategy_id": STRATEGY_ID,
        "config_id": CONFIG_ID,
        "lab_version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_window": {
            "1H_first": slim_1h[0]["ts"], "1H_last": slim_1h[-1]["ts"],
            "4H_first": slim_4h[0]["ts"], "4H_last": slim_4h[-1]["ts"],
            "1D_first": slim_1d[0]["ts"], "1D_last": slim_1d[-1]["ts"],
        },
        "config": {
            "warmup_bars": WARMUP_BARS,
            "timeout_bars": TIMEOUT_BARS,
            "stop_buffer_atr_mult": STOP_BUFFER_ATR_MULT,
            "target_R": TARGET_2_R,
            "min_body_pct": MIN_BODY_PCT,
            "max_risk_vs_atr": MAX_RISK_VS_ATR,
            "sell_pressure_lookback_bars": SELL_PRESSURE_LOOKBACK,
            "supply_far_atr_mult": SUPPLY_FAR_ATR_MULT,
            "demand_far_atr_mult": DEMAND_FAR_ATR_MULT,
            "zone_definition": "Custom OB (canonical BigBeluga-style zone proxy from slim). Parent 1H zone = current 1H bar's own nearest_demand/supply fields. Parent 4H zone via bisect_right(ts) - 1.",
            "no_overlap_per_direction": True,
        },
        "discards": {
            "atr_null_skip": n_atr_null,
            "zone_missing_long_skip": n_no_zone_long,
            "zone_missing_short_skip": n_no_zone_short,
            "risk_skip": n_risk_skip,
        },
        "totals": summarize(trades),
        "by_archetype": by_field("archetype"),
        "by_direction": by_field("direction"),
        "by_zone_tf": by_field("zone_tf"),
        "by_zone_type": by_field("zone_type"),
        "by_regime_1d": by_field("regime_1d"),
        "by_location_quality": by_field("location_quality"),
        "by_acceptance_quality": by_field("acceptance_quality"),
        "by_rsi_context": by_field("rsi_context"),
        "by_bubble_buy_recent": {"yes": summarize([t for t in trades if t["bubble_buy_recent"]]),
                                  "no":  summarize([t for t in trades if not t["bubble_buy_recent"]])},
        "by_bubble_sell_recent": {"yes": summarize([t for t in trades if t["bubble_sell_recent"]]),
                                   "no":  summarize([t for t in trades if not t["bubble_sell_recent"]])},
        "by_nas_long_in_15": {"yes": summarize([t for t in trades if t["nas_long_count_15"] > 0]),
                               "no":  summarize([t for t in trades if t["nas_long_count_15"] == 0])},
        "by_nas_short_in_15": {"yes": summarize([t for t in trades if t["nas_short_count_15"] > 0]),
                                "no":  summarize([t for t in trades if t["nas_short_count_15"] == 0])},
        "by_smc_bos_recent": {"yes": summarize([t for t in trades if t["smc_bos_recent"]]),
                              "no":  summarize([t for t in trades if not t["smc_bos_recent"]])},
        "by_smc_choch_recent": {"yes": summarize([t for t in trades if t["smc_choch_recent"]]),
                                 "no":  summarize([t for t in trades if not t["smc_choch_recent"]])},
        # within archetype breakdowns (key insight: combine archetype with location)
        "A1_by_location_quality": by_field_within("A1_DEMAND_ABSORPTION_LONG", "location_quality"),
        "A2_by_location_quality": by_field_within("A2_CLEAN_DEMAND_REJECTION_LONG", "location_quality"),
        "A3_by_location_quality": by_field_within("A3_BAD_FALLING_KNIFE_LONG", "location_quality"),
        "A4_by_regime_1d": by_field_within("A4_SUPPLY_REJECTION_SHORT", "regime_1d"),
        "A5_by_regime_1d": by_field_within("A5_BAD_SHORT_IN_BULL_REGIME", "regime_1d"),
    }
    with open(OUT_DIR / "report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"[1H auction lab v1] wrote {OUT_DIR / 'report.json'}")

    # summary.md
    def md_row(label, s):
        return (f"| {label} | {s['n']} | {s['win_rate']:.3f} | "
                f"{s['avg_R']:+.3f} | {s['total_R']:+.2f} | {s['PF']:.3f} | "
                f"{s['mfe_avg']:+.2f} | {s['mae_avg']:+.2f} |")

    md = []
    md.append("# XAUUSD 1H AUCTION CONFLUENCE LAB v1 — Summary\n")
    md.append(f"- Strategy: `{STRATEGY_ID}`")
    md.append(f"- Config: `{CONFIG_ID}`")
    md.append(f"- Generated: {report['generated_at']}")
    md.append(f"- 1H window: {report['data_window']['1H_first']} → {report['data_window']['1H_last']}")
    md.append(f"- Bars: 1H={len(slim_1h)} 4H={len(slim_4h)} 1D={len(slim_1d)}")
    md.append(f"- **Trades:** {len(trades)}")
    md.append(f"- Per-archetype counts: {dict(arch_counter)}")
    md.append(f"- Discards: atr_null={n_atr_null} no_zone_long={n_no_zone_long} no_zone_short={n_no_zone_short} risk_skip={n_risk_skip}")
    md.append("")
    md.append("## Totals\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    md.append(md_row("ALL", report["totals"]))
    md.append("")
    md.append("## By archetype\n")
    md.append("| Archetype | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_archetype"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By direction\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_direction"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By zone_tf\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_zone_tf"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By location_quality\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_location_quality"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By rsi_context\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, s in report["by_rsi_context"].items():
        md.append(md_row(k, s))
    md.append("")
    md.append("## By Bubbles (buy_recent / sell_recent)\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    md.append(md_row("BUY recent yes", report["by_bubble_buy_recent"]["yes"]))
    md.append(md_row("BUY recent no",  report["by_bubble_buy_recent"]["no"]))
    md.append(md_row("SELL recent yes",report["by_bubble_sell_recent"]["yes"]))
    md.append(md_row("SELL recent no", report["by_bubble_sell_recent"]["no"]))
    md.append("")
    md.append("## By NAS labels (last 15 bars)\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    md.append(md_row("NAS LONG present",  report["by_nas_long_in_15"]["yes"]))
    md.append(md_row("NAS LONG absent",   report["by_nas_long_in_15"]["no"]))
    md.append(md_row("NAS SHORT present", report["by_nas_short_in_15"]["yes"]))
    md.append(md_row("NAS SHORT absent",  report["by_nas_short_in_15"]["no"]))
    md.append("")
    md.append("## By SMC BOS / CHoCH recent\n")
    md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    md.append(md_row("BOS present",   report["by_smc_bos_recent"]["yes"]))
    md.append(md_row("BOS absent",    report["by_smc_bos_recent"]["no"]))
    md.append(md_row("CHoCH present", report["by_smc_choch_recent"]["yes"]))
    md.append(md_row("CHoCH absent",  report["by_smc_choch_recent"]["no"]))
    md.append("")
    md.append("## Within-archetype breakdowns\n")
    for arch_key, title in [
        ("A1_by_location_quality", "A1_DEMAND_ABSORPTION_LONG × location_quality"),
        ("A2_by_location_quality", "A2_CLEAN_DEMAND_REJECTION_LONG × location_quality"),
        ("A3_by_location_quality", "A3_BAD_FALLING_KNIFE_LONG × location_quality"),
        ("A4_by_regime_1d", "A4_SUPPLY_REJECTION_SHORT × regime_1d"),
        ("A5_by_regime_1d", "A5_BAD_SHORT_IN_BULL_REGIME × regime_1d"),
    ]:
        md.append(f"### {title}")
        md.append("")
        md.append("| Group | n | win_rate | avg_R | total_R | PF | MFE | MAE |")
        md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for k, s in report[arch_key].items():
            md.append(md_row(k, s))
        md.append("")
    md.append("## Notes")
    md.append("- Zones use Custom OB (canonical slim representation of BigBeluga-style zones).")
    md.append("- Parent 4H zone looked up by `bisect_right(ts) - 1` (no lookahead).")
    md.append("- 1D regime bullishness (used for A5) = `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D` (D1a definition from BREAKOUT_CONTINUATION revalidation).")
    md.append("- All archetypes use the same entry/stop/target rule (entry=close, stop=zone edge ± 0.1×ATR_1H, target=2R, timeout=20 1H bars).")
    md.append("- No-overlap is per-direction (LONG and SHORT can run concurrently).")
    md.append("- v1 has no parameter sweep, no filter selection, no threshold tuning.")
    with open(OUT_DIR / "summary.md", "w") as f:
        f.write("\n".join(md) + "\n")
    print(f"[1H auction lab v1] wrote {OUT_DIR / 'summary.md'}")

    print()
    print("=== TOTALS ===")
    for k, v in report["totals"].items():
        if k != "exit_reasons":
            print(f"  {k}: {v}")
    print(f"  exit_reasons: {report['totals']['exit_reasons']}")
    print()
    print("=== BY ARCHETYPE ===")
    for k, s in report["by_archetype"].items():
        print(f"  {k}: n={s['n']} wr={s['win_rate']:.3f} totR={s['total_R']:+.2f} PF={s['PF']:.3f}")


if __name__ == "__main__":
    main()
