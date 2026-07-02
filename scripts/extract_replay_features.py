#!/usr/bin/env python3
# [STATUS 2026-07-02] HISTORICAL_COMPATIBILITY / RAW_IN_MEMORY_ALLOWED / SLIM_MODE_FORBIDDEN / DO_NOT_USE_SLIM_FOR_VALIDATION
# SLIM output mode is FORBIDDEN. Only RAW-in-memory reuse of the interpreter is allowed
# (sustains D1A/Breakout Continuation ACTIVE_CANDIDATE). See docs/cleanup/SLIM_CLUSTER_STATUS_HISTORICAL_COMPATIBILITY.md
"""extract_replay_features.py — Canonical Feature Extraction Layer (schema v2).

Official, single extractor. Reads RAW replay .jsonl.gz (registry source-of-truth)
and emits a slim feature file under slim_features/ that interprets each indicator
from its CORRECT RAW source (audit 2026-05-27). See docs/data/FEATURE_EXTRACTION_POLICY.md.
  - NAS Top Bottom -> pine_labels (text LONG/SHORT), recency max_x-x<=5 (legacy monitor logic).
                     study_values NAS_* kept ONLY as deprecated diagnostics.
  - Market Order Bubbles -> pine_shapes_bubbles activations (absolute time); buy=plot_0/2/4,
                     sell=plot_6/8/10, POC=plot_12; size by plot order (medium-high).
  - LuxAlgo SMC -> pine_labels (CHoCH/BOS/EQH/EQL; textColor=direction, size=internal/swing)
                   + pine_boxes (OB bull/bear via bgColor).
  - Custom OB -> pine_boxes text DEMAND/SUPPLY (separated); presence=active (Pine v11);
                 state via bgColor alpha.
  - RSI -> study_values (RSI, RSI-based MA) + crosses.
  - RSI divergences -> study_values Regular Bullish/Bearish (+Label = event), confidence medium.
  - OHLCV-derived -> ATR (legacy SMA: SMA(TR,14)/SMA30(SMA(TR,14))) + Wilder compare,
                     swing_high/low(10 prior), body_pct, range, range/ATR.

Does NOT touch RAW, manifests or registry. Slim v1 is DEPRECATED (delete-candidate).
Usage: python3 scripts/extract_replay_features.py --timeframe 4H --start-date 2023-01-03 [--dry-run]
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "docs" / "data" / "dataset_registry.json"
SCHEMA_VERSION = 2
NAS_RECENT_N = 5          # legacy monitor: max_x - x <= 5
SMC_RECENT_N = 5          # documented; "recent" structure event window
BUBBLE_RECENT_BARS = 3    # activation within last N closed bars = "event_recent"
SMC_STRUCT_VOCAB = {"CHoCH", "BOS", "EQH", "EQL"}
NAS_GROUP = "NAS TOP BOTTOM DETECTOR"
SMC_NAME = "LuxAlgo"
COB_NAME = "OB Detector"


def norm_num(v, pe=None, field=None):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("−", "-").replace(",", "")
        if s in ("", "n/a", "NaN", "—"):
            return None
        try:
            return float(s)
        except ValueError:
            if pe is not None:
                pe.append(field or "num")
            return None
    if pe is not None:
        pe.append(field or "type")
    return None


def zone_dist(close, high, low):
    if close is None or high is None or low is None:
        return None
    hi, lo = (high, low) if high >= low else (low, high)
    if lo <= close <= hi:
        return 0.0
    return (lo - close) if close < lo else (close - hi)


def find_block(reg, tf, start_date):
    for e in reg["datasets"]:
        if e["timeframe"] == tf and e["start_date"] == start_date and e["status"] == "active":
            return e
    raise SystemExit(f"ERROR: block not found in registry: {tf} {start_date} active")


def extract_record(rec, prev_nas_ids, prev_smc_ids, prov):
    pe = []
    av = rec.get("_feature_availability") or {}
    obars = sorted((rec.get("ohlcv") or []), key=lambda b: b.get("time", 0))
    closed = obars[-2] if len(obars) >= 2 else None
    forming = obars[-1] if obars else None
    close = closed.get("close") if closed else None
    bar_close_time = closed.get("time") if closed else None

    sv = {st.get("name"): (st.get("values") or {}) for st in (rec.get("study_values") or []) if isinstance(st, dict)}
    rsi_v = sv.get("Relative Strength Index", {})
    nas_v = sv.get(NAS_GROUP, {})

    # ---- NAS: pine_labels (LONG/SHORT), recency max_x - x <= 5 ----
    labels_studies = rec.get("pine_labels") or []
    nas_grp = next((g for g in labels_studies if "NAS" in (g.get("name") or "").upper()), None)
    nas_labels = (nas_grp.get("labels") or []) if nas_grp else []
    nas_xs = [l.get("x") for l in nas_labels if l.get("x") is not None]
    nas_max_x = max(nas_xs) if nas_xs else None
    labels_capped = any((s.get("showing") or 0) < (s.get("total_labels") or 0) for s in labels_studies)

    def nas_recent(text):
        if nas_max_x is None:
            return False, None
        best = None
        for l in nas_labels:
            if (l.get("text") or "").upper() == text and l.get("x") is not None:
                d = nas_max_x - l.get("x")
                if 0 <= d <= NAS_RECENT_N and (best is None or d < best):
                    best = d
        return (best is not None), best

    long_recent, long_bars = nas_recent("LONG")
    short_recent, short_bars = nas_recent("SHORT")

    # NAS events via id-diff (new id this snapshot) + price-match to current bar (exclude historical dump)
    this_nas_ids = {l.get("id") for l in nas_labels if l.get("id") is not None}
    new_ids = this_nas_ids - prev_nas_ids
    nas_long_event = nas_short_event = False
    nas_event_type = nas_event_price = nas_event_id = None
    lo = closed.get("low") if closed else None
    hi = closed.get("high") if closed else None
    for l in nas_labels:
        if l.get("id") not in new_ids:
            continue
        txt = (l.get("text") or "").upper()
        if txt not in ("LONG", "SHORT"):
            continue
        px = norm_num(l.get("price"))
        if px is None or lo is None or hi is None or not (lo * 0.97 <= px <= hi * 1.03):
            continue
        if txt == "LONG" and not nas_long_event:
            nas_long_event = True
            if nas_event_type is None:
                nas_event_type, nas_event_price, nas_event_id = "LONG", px, l.get("id")
        elif txt == "SHORT" and not nas_short_event:
            nas_short_event = True
            if nas_event_type is None:
                nas_event_type, nas_event_price, nas_event_id = "SHORT", px, l.get("id")

    # ---- Custom OB: pine_boxes DEMAND/SUPPLY (separated) ----
    boxes = rec.get("pine_boxes") or []
    cob = next((s for s in boxes if COB_NAME in (s.get("name") or "")), None)
    cob_boxes = (cob.get("all_boxes") or []) if cob else []
    cob_x2s = [b.get("x2") for b in cob_boxes if b.get("x2") is not None]
    cob_max_x2 = max(cob_x2s) if cob_x2s else None

    def nearest(pred):
        best = None
        for b in cob_boxes:
            if not pred(b):
                continue
            d = zone_dist(close, b.get("high"), b.get("low"))
            if d is None:
                continue
            if best is None or d < best[0]:
                best = (d, b)
        return best

    is_dem = lambda b: (b.get("text") or "").upper() == "DEMAND"
    is_sup = lambda b: (b.get("text") or "").upper() == "SUPPLY"
    nd = nearest(is_dem)
    ns = nearest(is_sup)
    inside_demand = (close is not None and any(zone_dist(close, b.get("high"), b.get("low")) == 0.0 for b in cob_boxes if is_dem(b)))
    inside_supply = (close is not None and any(zone_dist(close, b.get("high"), b.get("low")) == 0.0 for b in cob_boxes if is_sup(b)))
    # Pine v11 (audited): presence of box = ACTIVE zone (violated/aged are box.delete'd, obshowbb=false).
    # x2 is creation coord (extend.right) -> NOT used for active. State via bgColor alpha (transp 70/80/90 -> alpha 77/51/25).
    dem_active = any(is_dem(b) for b in cob_boxes)
    sup_active = any(is_sup(b) for b in cob_boxes)

    def ob_state(b):
        c = b.get("bgColor")
        if c is None:
            return None
        a = (int(c) >> 24) & 255
        return "fresh" if a >= 65 else ("touched" if a >= 38 else "mitigated")
    nd_state = ob_state(nd[1]) if nd else None
    ns_state = ob_state(ns[1]) if ns else None

    # ---- SMC: labels (structure) + boxes (zones) ----
    smc_lbl = next((s for s in labels_studies if SMC_NAME in (s.get("name") or "")), None)
    smc_labels = (smc_lbl.get("labels") or []) if smc_lbl else []
    smc_xs = [l.get("x") for l in smc_labels if l.get("x") is not None]
    smc_max_x = max(smc_xs) if smc_xs else None
    struct = [l for l in smc_labels if l.get("text") in SMC_STRUCT_VOCAB]
    last_struct = max(struct, key=lambda l: l.get("x", -1)) if struct else None
    smc_last_bars_ago = (smc_max_x - last_struct.get("x")) if (last_struct and smc_max_x is not None) else None
    this_smc_ids = {l.get("id") for l in struct if l.get("id") is not None}
    smc_struct_new = bool(this_smc_ids - prev_smc_ids)

    def smc_recent(text):
        if smc_max_x is None:
            return False
        return any(l.get("text") == text and l.get("x") is not None and 0 <= smc_max_x - l.get("x") <= SMC_RECENT_N for l in smc_labels)

    smc_box = next((s for s in boxes if SMC_NAME in (s.get("name") or "")), None)
    smc_boxes = (smc_box.get("all_boxes") or []) if smc_box else []
    smc_nz = None
    for b in smc_boxes:
        d = zone_dist(close, b.get("high"), b.get("low"))
        if d is not None and (smc_nz is None or d < smc_nz[0]):
            smc_nz = (d, b)
    smc_box_x2s = [b.get("x2") for b in smc_boxes if b.get("x2") is not None]
    smc_box_max_x2 = max(smc_box_x2s) if smc_box_x2s else None
    smc_zone_active = any(b.get("x2") is not None and smc_box_max_x2 is not None and b.get("x2") >= smc_box_max_x2 - 1 for b in smc_boxes)

    # SMC direction via textColor (green g>b = bull; blue b>g = bear; anchored by EQH=bear/EQL=bull); kind via size (tiny=internal else swing)
    def _argb(c):
        c = int(c); return ((c >> 16) & 255, (c >> 8) & 255, c & 255)  # (r,g,b)
    def smc_dir(l):
        c = l.get("textColor")
        if c is None:
            return None
        r, g, b = _argb(c)
        return "bull" if g > b else "bear"
    def smc_kind(l):
        return "internal" if (l.get("size") == "tiny") else "swing"
    new_struct = [l for l in struct if l.get("id") in (this_smc_ids - prev_smc_ids)]
    smc_evt = max(new_struct, key=lambda l: l.get("x", -1)) if new_struct else None
    smc_evt_type = smc_evt.get("text") if smc_evt else None
    smc_evt_dir = smc_dir(smc_evt) if smc_evt else None
    smc_evt_kind = smc_kind(smc_evt) if smc_evt else None
    smc_evt_price = norm_num(smc_evt.get("price")) if smc_evt else None

    def last_swing_dir(text):
        sw = [l for l in smc_labels if l.get("text") == text and l.get("size") != "tiny" and l.get("x") is not None]
        return smc_dir(max(sw, key=lambda l: l.get("x", -1))) if sw else None
    smc_last_swing_bos_dir = last_swing_dir("BOS")
    smc_last_swing_choch_dir = last_swing_dir("CHoCH")

    def strong_price(text):
        s = [l for l in smc_labels if l.get("text") == text and l.get("x") is not None]
        return norm_num(max(s, key=lambda l: l.get("x", -1)).get("price")) if s else None
    smc_strong_high_price = strong_price("Strong High")
    smc_strong_low_price = strong_price("Strong Low")

    # SMC OB zones split by bgColor (bull: r>b; bear: b>r)
    def box_dir(b):
        c = b.get("bgColor")
        if c is None:
            return None
        r, g, bb = _argb(c)
        return "bull" if r > bb else "bear"
    def nearest_ob(direction):
        best = None
        for b in smc_boxes:
            if box_dir(b) != direction:
                continue
            d = zone_dist(close, b.get("high"), b.get("low"))
            if d is None:
                continue
            if best is None or d < best[0]:
                best = (d, b)
        return best
    smc_bull_ob = nearest_ob("bull")
    smc_bear_ob = nearest_ob("bear")

    # ---- Bubbles: pine_shapes_bubbles activations (absolute time) ----
    acts = []
    for st in (rec.get("pine_shapes_bubbles") or []):
        acts += st.get("activations") or []
    at_bar = [a for a in acts if a.get("time") == bar_close_time] if bar_close_time is not None else []
    bubble_plots = sorted({k for a in at_bar for k in (a.get("shapes") or {}).keys()})
    recent_times = {b.get("time") for b in obars[-(BUBBLE_RECENT_BARS + 1):-1]} if len(obars) > 1 else set()
    bubble_event_recent = any(a.get("time") in recent_times for a in acts)
    # Bubbles mapping (audit 2026-05-27, stat+visual+memory): BUY=plot_0/2/4, SELL=plot_6/8/10, POC=plot_12; size by plot order
    BUY_PLOTS = {"plot_0": "small", "plot_2": "medium", "plot_4": "large"}
    SELL_PLOTS = {"plot_6": "small", "plot_8": "medium", "plot_10": "large"}
    SIZE_RANK = {"small": 1, "medium": 2, "large": 3}
    bub_sizes_cur = [BUY_PLOTS[p] for p in bubble_plots if p in BUY_PLOTS] + [SELL_PLOTS[p] for p in bubble_plots if p in SELL_PLOTS]
    bubble_size_current = max(bub_sizes_cur, key=lambda s: SIZE_RANK[s]) if bub_sizes_cur else None
    bubble_buy_current = any(p in BUY_PLOTS for p in bubble_plots)
    bubble_sell_current = any(p in SELL_PLOTS for p in bubble_plots)
    recent_plots = set()
    for a in acts:
        if a.get("time") in recent_times:
            recent_plots |= set((a.get("shapes") or {}).keys())
    bubble_buy_recent = any(p in BUY_PLOTS for p in recent_plots)
    bubble_sell_recent = any(p in SELL_PLOTS for p in recent_plots)

    # ---- RSI ----
    rsi = norm_num(rsi_v.get("RSI"), pe, "RSI")
    rsi_ma = norm_num(rsi_v.get("RSI-based MA"), pe, "RSI-based MA")

    row = {
        "schema_version": SCHEMA_VERSION,
        "symbol": rec.get("symbol"), "timeframe": rec.get("timeframe"),
        "ts": rec.get("replay_current_dt"), "bar_index": rec.get("bar_index"),
        "bar_close_time": bar_close_time, "raw_gz_path": prov["raw_gz_path"],
        "registry_entry": prov["registry_entry"],
        # ohlcv (last closed)
        "open": closed.get("open") if closed else None, "high": closed.get("high") if closed else None,
        "low": closed.get("low") if closed else None, "close": close,
        "volume": closed.get("volume") if closed else None,
        "forming_close": forming.get("close") if forming else None,
        # NAS (labels) — fidelity layer
        "nas_label_long_recent": bool(long_recent), "nas_label_short_recent": bool(short_recent),
        "nas_label_recent_long_bars": long_bars, "nas_label_recent_short_bars": short_bars,
        "nas_label_long_event": bool(nas_long_event), "nas_label_short_event": bool(nas_short_event),
        "nas_label_event_type": nas_event_type,
        "nas_label_event_price": nas_event_price, "nas_label_event_id": nas_event_id,
        "nas_label_event_source": "pine_labels:NAS TOP BOTTOM DETECTOR",
        # NAS study_values — DEPRECATED diagnostics (proven inadequate, audit 2026-05-27)
        "nas_signal_study_long": flag(norm_num(nas_v.get("NAS_LONG_SIGNAL"))),
        "nas_signal_study_short": flag(norm_num(nas_v.get("NAS_SHORT_SIGNAL"))),
        "nas_signal_study_bottom": flag(norm_num(nas_v.get("NAS_BOTTOM_SIGNAL"))),
        "nas_signal_study_top": flag(norm_num(nas_v.get("NAS_TOP_SIGNAL"))),
        "nas_dist_ema_atr": norm_num(nas_v.get("NAS_DISTANCE_FROM_EMA_ATR")),
        "nas_rsi": norm_num(nas_v.get("NAS_RSI")),
        # Bubbles (mapping: BUY=plot_0/2/4, SELL=plot_6/8/10, POC=plot_12; size by plot order)
        "bubble_active": bool(at_bar), "bubble_raw_plot_ids": bubble_plots,
        "bubble_buy_current": bool(bubble_buy_current), "bubble_sell_current": bool(bubble_sell_current),
        "bubble_buy_recent": bool(bubble_buy_recent), "bubble_sell_recent": bool(bubble_sell_recent),
        "bubble_size_current": bubble_size_current, "bubble_size_rank": SIZE_RANK.get(bubble_size_current),
        "bubble_large_current": bubble_size_current == "large",
        "bubble_medium_current": bubble_size_current == "medium",
        "bubble_small_current": bubble_size_current == "small",
        "bubble_poc_current": "plot_12" in bubble_plots, "bubble_poc_recent": "plot_12" in recent_plots,
        "bubble_event_recent": bool(bubble_event_recent), "bubble_activations_window": len(acts),
        "bubble_event_price": None,  # unavailable (no y in RAW activation)
        "bubble_mapping_confidence": {"direction": "high", "size": "medium", "poc": "high", "price": "unavailable"},
        "bubble_mapping_method": "plot_id: buy=0/2/4 sell=6/8/10, size by order; POC=plot_12 (stat+visual+memory)",
        # SMC — labels (text + textColor=direction + size=internal/swing) + boxes (OB bull/bear via bgColor)
        "smc_last_structure_event": (last_struct.get("text") if last_struct else None),
        "smc_last_structure_price": norm_num(last_struct.get("price")) if last_struct else None,
        "smc_last_structure_bars_ago": smc_last_bars_ago,
        "smc_structure_event_new": bool(smc_struct_new),
        "smc_structure_event_type": smc_evt_type, "smc_structure_event_direction": smc_evt_dir,
        "smc_structure_event_kind": smc_evt_kind, "smc_structure_event_price": smc_evt_price,
        "smc_last_swing_bos_direction": smc_last_swing_bos_dir,
        "smc_last_swing_choch_direction": smc_last_swing_choch_dir,
        "smc_recent_eqh": smc_recent("EQH"), "smc_recent_eql": smc_recent("EQL"),
        "smc_strong_high_price": smc_strong_high_price, "smc_strong_low_price": smc_strong_low_price,
        "smc_nearest_bullish_ob_dist": (smc_bull_ob[0] if smc_bull_ob else None),
        "smc_nearest_bullish_ob_high": (smc_bull_ob[1].get("high") if smc_bull_ob else None),
        "smc_nearest_bullish_ob_low": (smc_bull_ob[1].get("low") if smc_bull_ob else None),
        "smc_nearest_bearish_ob_dist": (smc_bear_ob[0] if smc_bear_ob else None),
        "smc_nearest_bearish_ob_high": (smc_bear_ob[1].get("high") if smc_bear_ob else None),
        "smc_nearest_bearish_ob_low": (smc_bear_ob[1].get("low") if smc_bear_ob else None),
        # DIAGNOSTIC (saturate ~always-true): use event_new / last_structure / swing dirs instead
        "smc_has_recent_bos": smc_recent("BOS"), "smc_has_recent_choch": smc_recent("CHoCH"),
        # Custom OB (Pine v11 audited: presence=active; state via bgColor alpha; DEMAND=bull/green, SUPPLY=bear/orange)
        "custom_ob_demand_active": bool(dem_active), "custom_ob_supply_active": bool(sup_active),
        "inside_demand_zone": bool(inside_demand), "inside_supply_zone": bool(inside_supply),
        "nearest_demand_dist": (nd[0] if nd else None), "nearest_supply_dist": (ns[0] if ns else None),
        "nearest_demand_high": (nd[1].get("high") if nd else None), "nearest_demand_low": (nd[1].get("low") if nd else None),
        "nearest_supply_high": (ns[1].get("high") if ns else None), "nearest_supply_low": (ns[1].get("low") if ns else None),
        "custom_ob_nearest_demand_state": nd_state, "custom_ob_nearest_supply_state": ns_state,
        "custom_ob_n_demand_zones": sum(1 for b in cob_boxes if is_dem(b)),
        "custom_ob_n_supply_zones": sum(1 for b in cob_boxes if is_sup(b)),
        "custom_ob_nearest_zone_type": ("DEMAND" if (nd and (not ns or nd[0] <= ns[0])) else ("SUPPLY" if ns else None)),
        "custom_ob_zone_source_confidence": "high",
        "custom_ob_mapping_method": "pine_v11: presence=active (violated/aged deleted, obshowbb=false); state via bgColor alpha (77 fresh/51 touched/25 mitig); x2 ignored (extend.right)",
        # RSI
        "rsi": rsi, "rsi_ma": rsi_ma,
        "rsi_above_ma": (rsi is not None and rsi_ma is not None and rsi > rsi_ma),
        "rsi_below_ma": (rsi is not None and rsi_ma is not None and rsi < rsi_ma),
        "rsi_cross_above_ma": None, "rsi_cross_below_ma": None,  # filled in post-pass
        # RSI divergences — SOURCE CONFIRMED in study_values (audit correction 2026-05-27)
        "rsi_div_bullish_raw": norm_num(rsi_v.get("Regular Bullish")),
        "rsi_div_bearish_raw": norm_num(rsi_v.get("Regular Bearish")),
        "rsi_div_bullish_label": norm_num(rsi_v.get("Regular Bullish Label")),
        "rsi_div_bearish_label": norm_num(rsi_v.get("Regular Bearish Label")),
        "rsi_div_bullish_event": rsi_v.get("Regular Bullish Label") is not None,
        "rsi_div_bearish_event": rsi_v.get("Regular Bearish Label") is not None,
        "rsi_divergence_confidence": "medium",
        # OHLCV-derived — filled in post-pass
        "atr14_sma_tr": None, "atr14_sma30_ratio": None, "atr14_wilder": None,
        "swing_high_10": None, "swing_low_10": None, "body_pct": None,
        "candle_range": None, "range_atr_ratio": None,
        "close_above_swing_high_10": None, "close_below_swing_low_10": None,
        "feature_quality": {
            "parse_errors": len(pe), "labels_capped": bool(labels_capped),
            "nas_max_x": nas_max_x, "nas_labels_n": len(nas_labels),
            "cob_boxes_n": len(cob_boxes), "ohlcv_short": len(obars) < 2,
            "sources_missing": [k for k, v in av.items() if not v],
        },
    }
    return row, this_nas_ids, this_smc_ids, pe


def flag(v):
    return None if v is None else int(round(v)) == 1


def post_pass(rows):
    """ATR (legacy SMA + Wilder), swing(10 prior), body/range, RSI cross — computed on the row series."""
    H = [r["high"] for r in rows]; L = [r["low"] for r in rows]; C = [r["close"] for r in rows]; O = [r["open"] for r in rows]
    n = len(rows)
    TR = [None] * n
    for i in range(n):
        if H[i] is None or L[i] is None:
            continue
        TR[i] = (H[i] - L[i]) if (i == 0 or C[i-1] is None) else max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1]))

    def sma(x, k, i):
        seg = x[i-k+1:i+1]
        if len(seg) < k or any(v is None for v in seg):
            return None
        return sum(seg) / k
    atr14 = [sma(TR, 14, i) for i in range(n)]
    # Wilder
    wil = [None] * n
    valid = [t for t in TR[:14] if t is not None]
    if len(valid) == 14:
        wil[13] = sum(TR[:14]) / 14
        for i in range(14, n):
            if TR[i] is not None and wil[i-1] is not None:
                wil[i] = (wil[i-1]*13 + TR[i]) / 14
    for i in range(n):
        r = rows[i]
        r["atr14_sma_tr"] = round(atr14[i], 6) if atr14[i] else None
        r["atr14_wilder"] = round(wil[i], 6) if wil[i] else None
        # ATR_MA30 = SMA over 30 of atr14 series (legacy)
        seg = atr14[i-29:i+1]
        ma30 = (sum(seg)/30) if (len(seg) == 30 and all(v is not None for v in seg)) else None
        r["atr14_sma30_ratio"] = round(atr14[i]/ma30, 6) if (atr14[i] and ma30) else None
        # swing of PRIOR 10 bars (breakout semantics)
        if i >= 10 and all(H[j] is not None for j in range(i-10, i)):
            sh = max(H[i-10:i]); sl = min(L[i-10:i])
            r["swing_high_10"] = sh; r["swing_low_10"] = sl
            r["close_above_swing_high_10"] = (C[i] is not None and C[i] > sh)
            r["close_below_swing_low_10"] = (C[i] is not None and C[i] < sl)
        if None not in (O[i], H[i], L[i], C[i]) and (H[i]-L[i]) > 0:
            r["body_pct"] = round(abs(C[i]-O[i])/(H[i]-L[i]), 4)
            r["candle_range"] = round(H[i]-L[i], 6)
            if atr14[i]:
                r["range_atr_ratio"] = round((H[i]-L[i])/atr14[i], 4)
        # RSI cross
        if i > 0:
            pr, pm = rows[i-1]["rsi"], rows[i-1]["rsi_ma"]
            cr, cm = r["rsi"], r["rsi_ma"]
            if None not in (pr, pm, cr, cm):
                r["rsi_cross_above_ma"] = (pr <= pm and cr > cm)
                r["rsi_cross_below_ma"] = (pr >= pm and cr < cm)


def main() -> int:
    ap = argparse.ArgumentParser(description="Slim feature extractor v2 (indicator fidelity layer)")
    ap.add_argument("--timeframe", default="4H")
    ap.add_argument("--start-date", default="2023-01-03")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text())
    ext_parent = Path(os.path.dirname(reg["_meta"]["external_root"]))
    entry = find_block(reg, args.timeframe, args.start_date)
    gz = ext_parent / entry["raw_gz_path"]
    if not gz.is_file():
        print(f"ERROR: RAW .gz not found: {gz}", file=sys.stderr)
        return 1
    out_dir = ext_parent / reg["_meta"]["external_root"].split(os.sep)[-1] / "slim_features" / "XAUUSD" / args.timeframe
    base = f"XAUUSD_{args.timeframe.lower()}_features_{entry['start_date']}_to_{entry['end_date']}"
    prov = {"raw_gz_path": entry["raw_gz_path"], "registry_entry": f"{entry['symbol']}_{entry['timeframe']}_{entry['start_date']}"}

    rows = []; total_pe = 0; error_bars = 0; prev_nas_ids = set(); prev_smc_ids = set()
    print(f"reading {gz}")
    for line in gzip.open(gz, "rt", encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            error_bars += 1; continue
        if rec.get("_error"):
            error_bars += 1; continue
        row, nas_ids, smc_ids, pe = extract_record(rec, prev_nas_ids, prev_smc_ids, prov)
        prev_nas_ids = nas_ids; prev_smc_ids = smc_ids
        rows.append(row); total_pe += len(pe)
    post_pass(rows)

    # validations
    n = len(rows); expected = entry["bars"]
    ts_list = [r["ts"] for r in rows]
    ts_sorted = all(ts_list[i] <= ts_list[i+1] for i in range(len(ts_list)-1))
    dup_ts = len(ts_list) - len(set(ts_list))
    nas_long_recent_2026 = sum(1 for r in rows if r["nas_label_long_recent"] and (r["ts"] or "").startswith("2026"))
    nas_long_event_2026 = sum(1 for r in rows if r["nas_label_long_event"] and (r["ts"] or "").startswith("2026"))
    nas_short_event_2026 = sum(1 for r in rows if r["nas_label_short_event"] and (r["ts"] or "").startswith("2026"))
    nas_study_long_total = sum(1 for r in rows if r["nas_signal_study_long"])
    cob_dem = sum(1 for r in rows if r["inside_demand_zone"]); cob_sup = sum(1 for r in rows if r["inside_supply_zone"])
    cob_both = sum(1 for r in rows if r["inside_demand_zone"] and r["inside_supply_zone"])
    from collections import Counter as _C
    bubble_active_n = sum(1 for r in rows if r["bubble_active"]); poc_n = sum(1 for r in rows if r["bubble_poc_current"])
    bub_buy_n = sum(1 for r in rows if r["bubble_buy_current"]); bub_sell_n = sum(1 for r in rows if r["bubble_sell_current"])
    bub_size_n = dict(_C(r["bubble_size_current"] for r in rows if r["bubble_size_current"]))
    # RSI divergence (source CONFIRMED in study_values)
    rsi_div_bull_raw = sum(1 for r in rows if r["rsi_div_bullish_raw"] is not None)
    rsi_div_bear_raw = sum(1 for r in rows if r["rsi_div_bearish_raw"] is not None)
    rsi_div_bull_label = sum(1 for r in rows if r["rsi_div_bullish_label"] is not None)
    rsi_div_bear_label = sum(1 for r in rows if r["rsi_div_bearish_label"] is not None)
    rsi_div_examples = [{"ts": r["ts"], "bull_label": r["rsi_div_bullish_label"], "bear_label": r["rsi_div_bearish_label"], "rsi": r["rsi"]}
                        for r in rows if (r["rsi_div_bullish_label"] is not None or r["rsi_div_bearish_label"] is not None)][:5]
    # SMC discrimination
    smc_event_new_n = sum(1 for r in rows if r["smc_structure_event_new"])
    smc_recent_bos = sum(1 for r in rows if r["smc_has_recent_bos"]); smc_recent_choch = sum(1 for r in rows if r["smc_has_recent_choch"])
    smc_evt_dir_n = dict(_C(r["smc_structure_event_direction"] for r in rows if r["smc_structure_event_new"] and r["smc_structure_event_direction"]))
    smc_evt_kind_n = dict(_C(r["smc_structure_event_kind"] for r in rows if r["smc_structure_event_new"] and r["smc_structure_event_kind"]))
    smc_eqh_n = sum(1 for r in rows if r["smc_recent_eqh"]); smc_eql_n = sum(1 for r in rows if r["smc_recent_eql"])
    smc_bull_ob_n = sum(1 for r in rows if r["smc_nearest_bullish_ob_dist"] is not None)
    smc_bear_ob_n = sum(1 for r in rows if r["smc_nearest_bearish_ob_dist"] is not None)
    cob_dem_active = sum(1 for r in rows if r["custom_ob_demand_active"]); cob_sup_active = sum(1 for r in rows if r["custom_ob_supply_active"])
    cob_dem_state_n = dict(_C(r["custom_ob_nearest_demand_state"] for r in rows if r["custom_ob_nearest_demand_state"]))
    cob_sup_state_n = dict(_C(r["custom_ob_nearest_supply_state"] for r in rows if r["custom_ob_nearest_supply_state"]))

    # NAS examples (5 events in 2026)
    examples = []
    prev_ids = set()
    for r in rows:
        if r["nas_label_long_event"] and (r["ts"] or "").startswith("2026") and len(examples) < 5:
            examples.append({"ts": r["ts"], "event_type": r["nas_label_event_type"],
                             "event_price": r["nas_label_event_price"], "recent_long_bars": r["nas_label_recent_long_bars"],
                             "nas_max_x": r["feature_quality"]["nas_max_x"], "ohlc": [r["open"], r["high"], r["low"], r["close"]]})

    report = {
        "strategy_layer": "canonical_feature_extraction", "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_raw_gz": entry["raw_gz_path"], "registry_entry": prov["registry_entry"],
        "rows_extracted": n, "expected_bars": expected, "rows_match_registry": (n == expected),
        "error_bars_skipped": error_bars, "parse_errors_total": total_pe,
        "ts_range": [ts_list[0], ts_list[-1]] if rows else None, "ts_monotonic": ts_sorted, "duplicate_ts": dup_ts,
        "params": {"nas_recent_n": NAS_RECENT_N, "smc_recent_n": SMC_RECENT_N, "bubble_recent_bars": BUBBLE_RECENT_BARS,
                   "atr": "ATR14=SMA(TR,14); ATR_MA30=SMA(ATR14,30); ratio=ATR14/ATR_MA30 (legacy)"},
        "validation": {
            "nas_label_long_event_2026": nas_long_event_2026,
            "nas_label_short_event_2026": nas_short_event_2026,
            "nas_label_long_recent_2026_bars": nas_long_recent_2026,
            "nas_signal_study_long_total_block": nas_study_long_total,
            "custom_ob_inside_demand_bars": cob_dem, "custom_ob_inside_supply_bars": cob_sup,
            "custom_ob_inside_both_bars": cob_both,
            "rsi_div_bullish_raw_count": rsi_div_bull_raw, "rsi_div_bearish_raw_count": rsi_div_bear_raw,
            "rsi_div_bullish_label_count": rsi_div_bull_label, "rsi_div_bearish_label_count": rsi_div_bear_label,
            "rsi_div_examples": rsi_div_examples,
            "smc_structure_event_new_count": smc_event_new_n,
            "smc_has_recent_bos_count": smc_recent_bos, "smc_has_recent_choch_count": smc_recent_choch,
            "bubble_active_bars": bubble_active_n, "poc_current_bars": poc_n,
            "bubble_buy_bars": bub_buy_n, "bubble_sell_bars": bub_sell_n, "bubble_size_counts": bub_size_n,
            "smc_event_new_direction_counts": smc_evt_dir_n, "smc_event_new_kind_counts": smc_evt_kind_n,
            "smc_recent_eqh_bars": smc_eqh_n, "smc_recent_eql_bars": smc_eql_n,
            "smc_nearest_bull_ob_bars": smc_bull_ob_n, "smc_nearest_bear_ob_bars": smc_bear_ob_n,
            "custom_ob_demand_active_bars": cob_dem_active, "custom_ob_supply_active_bars": cob_sup_active,
            "custom_ob_demand_state_counts": cob_dem_state_n, "custom_ob_supply_state_counts": cob_sup_state_n,
            "nas_examples_2026": examples,
        },
        "field_classes": {
            "official_for_backtest": [
                "nas_label_long_recent", "nas_label_short_recent", "nas_label_recent_long_bars", "nas_label_recent_short_bars",
                "nas_label_long_event", "nas_label_short_event", "nas_label_event_type/price/id",
                "bubble_buy_current", "bubble_sell_current", "bubble_buy_recent", "bubble_sell_recent",
                "bubble_poc_current", "bubble_poc_recent", "bubble_active", "bubble_raw_plot_ids",
                "rsi", "rsi_ma", "rsi_above_ma", "rsi_below_ma", "rsi_cross_above_ma", "rsi_cross_below_ma",
                "smc_structure_event_new", "smc_structure_event_type", "smc_structure_event_direction", "smc_structure_event_kind",
                "smc_structure_event_price", "smc_last_structure_event", "smc_last_structure_bars_ago",
                "smc_last_swing_bos_direction", "smc_last_swing_choch_direction", "smc_recent_eqh", "smc_recent_eql",
                "smc_strong_high_price", "smc_strong_low_price", "smc_nearest_bullish_ob_*", "smc_nearest_bearish_ob_*",
                "custom_ob_demand_active", "custom_ob_supply_active", "inside_demand_zone", "inside_supply_zone",
                "nearest_demand_*", "nearest_supply_*", "custom_ob_nearest_demand_state", "custom_ob_nearest_supply_state",
                "custom_ob_n_demand_zones", "custom_ob_n_supply_zones", "custom_ob_nearest_zone_type",
                "atr14_sma_tr", "atr14_sma30_ratio", "swing_high_10", "swing_low_10", "body_pct", "candle_range",
                "range_atr_ratio", "close_above_swing_high_10", "close_below_swing_low_10", "open/high/low/close/volume",
            ],
            "low_confidence": [
                "bubble_size_current", "bubble_size_rank", "bubble_large/medium/small_current (size MEDIUM, validate visual)",
                "rsi_div_bullish_event", "rsi_div_bearish_event (MEDIUM; validate visual before backtest use)",
            ],
            "diagnostic_only": [
                "nas_signal_study_long/short/bottom/top", "nas_dist_ema_atr", "nas_rsi",
                "smc_has_recent_bos", "smc_has_recent_choch (saturate)", "atr14_wilder", "bubble_activations_window",
                "rsi_div_bullish_raw", "rsi_div_bearish_raw", "rsi_div_bullish_label", "rsi_div_bearish_label",
            ],
            "do_not_use": ["bubble_event_price (no y in RAW activation)"],
            "deprecated": ["demand_zone_active/supply_zone_active (x2-based; removed -> use custom_ob_*_active presence)"],
        },
        "deprecated_diagnostic_fields": [
            "nas_signal_study_long/short/bottom/top (study_values; proven inadequate)",
            "smc_has_recent_bos/choch (saturate ~always-true)",
            "demand_zone_active/supply_zone_active (x2 not reliable as 'active to current bar')",
        ],
        "medium_confidence_fields": ["rsi_div_* (source confirmed in study_values; validate vs visual before operational use)"],
        "unavailable": ["bubble buy/sell split (plot titles generic 'Shapes'; no color exposed)"],
    }

    print(f"rows={n} expected={expected} match={n==expected} | dup_ts={dup_ts} monotonic={ts_sorted}")
    print(f"NAS 2026: long_events={nas_long_event_2026} short_events={nas_short_event_2026} | study_long_total(block)={nas_study_long_total}")
    print(f"CustomOB: inside_demand={cob_dem} inside_supply={cob_sup} both={cob_both}")
    print(f"RSI div: bull_raw={rsi_div_bull_raw} bear_raw={rsi_div_bear_raw} bull_label={rsi_div_bull_label} bear_label={rsi_div_bear_label}")
    print(f"SMC: event_new={smc_event_new_n} | has_recent_bos={smc_recent_bos} choch={smc_recent_choch} (diagnostic) | bubbles active={bubble_active_n} poc={poc_n}")
    if args.dry_run:
        print("[dry-run] not writing")
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{base}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    (out_dir / f"{base}.report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_dir}/{base}.jsonl + .report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
