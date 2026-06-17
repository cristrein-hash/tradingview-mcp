#!/usr/bin/env python3
"""XAU_4H_BREAKOUT_D1A — Entry Anatomy substrate builder (Phase 1). RAW-ONLY.

SOURCE = RAW replay .gz ONLY (pine_boxes/pine_labels/pine_shapes_bubbles/study_values/ohlcv).
NO slim_features file is ever read (feedback_never_use_slim_features). The canonical indicator
interpretation is reused IN MEMORY by importing the AUDITED extractor (extract_replay_features)
and applying extract_record/post_pass to RAW records — the extractor's job is exactly "turn RAW
into features"; here its output is never persisted as slim.

For each breakout validation event (close>swing10[i-1] + bullish + body>=0.5 + rsi>ma), cross the
full structural+volumetric context (SMC / Custom OB / NAS / Bubbles / RSI+div / volume, from RAW)
with the FORWARD path (retrace-to-demand, MFE/MAE, current-rules outcome). MEASUREMENT-FIRST.
"""
import gzip
import json
import bisect
import sys
from datetime import datetime, timezone
from pathlib import Path

import run_mechanical_rebuild_v1 as eng

HERE = Path(__file__).resolve().parent
ROOT = next(d for d in HERE.parents if (d / "scripts").is_dir())
sys.path.insert(0, str(ROOT / "scripts"))
import extract_replay_features as cx  # AUDITED canonical interpreter (applied to RAW in-memory)

RESULTS = HERE / "results"
EMA1D = HERE / "generated" / "xau_1d_ema_features.jsonl"
RAW_DIR = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H")
RAW_BLOCKS = [
    ("XAUUSD_240m_replay_2016-05-25_to_2020-01-01.jsonl.gz", "2016-05-25"),
    ("XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz", "2020-01-01"),
    ("XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz", "2023-01-03"),
]
FWD = 24
WARMUP = 200
STOP_ATR_MULT = 0.5
TARGET_R = 4.0
MAX_HOLD = 24

CTX_FIELDS = [
    "inside_demand_zone", "inside_supply_zone", "nearest_demand_dist", "nearest_demand_low",
    "nearest_demand_high", "nearest_supply_dist", "nearest_supply_low", "nearest_supply_high",
    "custom_ob_nearest_zone_type", "custom_ob_nearest_demand_state", "custom_ob_nearest_supply_state",
    "custom_ob_n_demand_zones", "custom_ob_n_supply_zones",
    "smc_last_structure_event", "smc_last_structure_bars_ago", "smc_last_swing_bos_direction",
    "smc_last_swing_choch_direction", "smc_strong_low_price", "smc_strong_high_price",
    "smc_nearest_bullish_ob_dist", "smc_nearest_bullish_ob_low", "smc_recent_eqh", "smc_recent_eql",
    "smc_structure_event_new", "smc_structure_event_type", "smc_structure_event_direction",
    "nas_dist_ema_atr", "nas_label_long_recent", "nas_label_short_recent",
    "nas_label_recent_long_bars", "nas_label_recent_short_bars", "nas_rsi",
    "bubble_buy_current", "bubble_sell_current", "bubble_large_current", "bubble_size_current",
    "bubble_poc_current", "bubble_active", "bubble_buy_recent", "bubble_sell_recent",
    "rsi", "rsi_ma", "rsi_above_ma", "rsi_div_bullish_event", "rsi_div_bearish_event",
    "body_pct", "candle_range", "volume",
]


def extract_raw_rows():
    """Stream RAW .gz blocks, interpret each record via the audited extractor (in memory)."""
    rows = []
    for fname, start in RAW_BLOCKS:
        gz = RAW_DIR / fname
        prov = {"raw_gz_path": f"raw_replay/XAUUSD/4H/{fname}", "registry_entry": f"XAUUSD_4H_{start}"}
        prev_nas_ids, prev_smc_ids = set(), set()
        block = []
        with gzip.open(gz, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("_error"):
                    continue
                row, nas_ids, smc_ids, _pe = cx.extract_record(rec, prev_nas_ids, prev_smc_ids, prov)
                prev_nas_ids, prev_smc_ids = nas_ids, smc_ids
                block.append(row)
        rows.extend(block)
    # dedup by bar_close_time (keep last), sort, then post_pass for ATR/swing continuity
    by_t = {}
    for r in rows:
        t = r.get("bar_close_time")
        if t is not None and r.get("close") is not None:
            by_t[t] = r
    rows = [by_t[t] for t in sorted(by_t)]
    cx.post_pass(rows)            # fills atr14_wilder / swing_high_10 / body_pct / close_above_swing_high_10
    return rows


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    S = extract_raw_rows()
    n = len(S)
    O = [r["open"] for r in S]; H = [r["high"] for r in S]; L = [r["low"] for r in S]; C = [r["close"] for r in S]
    Tc = [r["bar_close_time"] for r in S]
    ema50 = eng.ema(C, 50); ema200 = eng.ema(C, 200)
    adx = eng.adx_wilder(H, L, C, 14)
    atr_ma = eng.sma_series([r.get("atr14_wilder") for r in S], 20)

    daily = [json.loads(l) for l in EMA1D.read_text().splitlines() if l.strip()]
    daily.sort(key=lambda d: d["close_time"])
    d_close = [d["close_time"] for d in daily]

    def d1a_at(bar_open):
        i = bisect.bisect_right(d_close, bar_open) - 1
        return daily[i] if i >= 0 else None

    def regime_year(t):
        y = datetime.fromtimestamp(t, tz=timezone.utc).year
        return {2016: "pre_covid", 2017: "pre_covid", 2018: "pre_covid", 2019: "bull_pre_covid",
                2020: "covid_rally", 2021: "chop_post_covid", 2022: "chop_inflation_bear",
                2023: "chop_macro"}.get(y, "bull_recent")

    events = []
    for i in range(WARMUP, n - 1):
        r = S[i]
        if not (r.get("close_above_swing_high_10") and C[i] > O[i]
                and (r.get("body_pct") or 0) >= 0.5 and r.get("rsi_above_ma")):
            continue
        atr = r.get("atr14_wilder")
        if not atr or atr <= 0:
            continue
        entry = O[i + 1]
        stop = L[i] - STOP_ATR_MULT * atr
        risk = entry - stop
        if risk <= 0 or risk > 5 * atr:
            continue
        target = entry + TARGET_R * risk
        be = False; exit_idx = exit_price = exit_reason = None
        end = min(i + 1 + MAX_HOLD, n)
        for j in range(i + 1, end):
            cur_stop = entry if be else stop
            if L[j] <= cur_stop:
                exit_idx, exit_price, exit_reason = j, cur_stop, ("stop_be" if be else "stop"); break
            if H[j] >= target:
                exit_idx, exit_price, exit_reason = j, target, "target"; break
            if not be and H[j] >= entry + risk:
                be = True
        if exit_idx is None:
            last = min(i + 1 + MAX_HOLD - 1, n - 1)
            exit_idx, exit_price, exit_reason = last, C[last], "time_limit"
        close_R = (exit_price - entry) / risk

        w_end = min(i + 1 + FWD, n)
        fwd_high = max(H[i + 1:w_end]) if w_end > i + 1 else H[i]
        fwd_low = min(L[i + 1:w_end]) if w_end > i + 1 else L[i]
        bars_to_high = next((k - (i + 1) for k in range(i + 1, w_end) if H[k] == fwd_high), None)
        bars_to_low = next((k - (i + 1) for k in range(i + 1, w_end) if L[k] == fwd_low), None)
        mfe_R = (fwd_high - entry) / risk
        mae_R = (fwd_low - entry) / risk

        nd_low = r.get("nearest_demand_low"); nd_high = r.get("nearest_demand_high")
        dist_to_demand_atr = ((C[i] - nd_low) / atr) if (nd_low is not None) else None
        retraced = touch_k = run_after = None
        # ALT ENTRY (the user's thesis): pending long fills on retrace TOUCH of the nearest demand
        # zone top; structural SL = demand_low - 0.5ATR; same +4R/BE@1R/time-stop engine FROM touch.
        # alt_close_R is the REAL outcome of the retrace-entry (DA-required; not the excursion proxy).
        alt = {"filled": False, "entry": None, "stop": None, "risk": None,
               "close_R": None, "exit_reason": None, "touch_bar": None}
        if nd_high is not None and nd_low is not None:
            for k in range(i + 1, w_end):
                if L[k] <= nd_high:
                    retraced = True; touch_k = k - (i + 1)
                    run_after = (max(H[k:w_end]) - nd_high) / atr if w_end > k else 0.0
                    a_entry = nd_high
                    a_stop = nd_low - STOP_ATR_MULT * atr
                    a_risk = a_entry - a_stop
                    if a_risk > 0:
                        a_target = a_entry + TARGET_R * a_risk
                        be2 = False; a_xidx = a_xprice = a_xreason = None
                        a_end = min(k + MAX_HOLD, n)
                        for j in range(k, a_end):
                            cs = a_entry if be2 else a_stop
                            if L[j] <= cs:
                                a_xidx, a_xprice, a_xreason = j, cs, ("stop_be" if be2 else "stop"); break
                            if H[j] >= a_target:
                                a_xidx, a_xprice, a_xreason = j, a_target, "target"; break
                            if not be2 and H[j] >= a_entry + a_risk:
                                be2 = True
                        if a_xidx is None:
                            last2 = min(k + MAX_HOLD - 1, n - 1)
                            a_xidx, a_xprice, a_xreason = last2, C[last2], "time_limit"
                        alt = {"filled": True, "entry": round(a_entry, 4), "stop": round(a_stop, 4),
                               "risk": round(a_risk, 4), "close_R": round((a_xprice - a_entry) / a_risk, 4),
                               "exit_reason": a_xreason, "touch_bar": touch_k}
                    break
            if retraced is None:
                retraced = False
        ema_stack = (ema50[i] is not None and ema200[i] is not None and ema50[i] > ema200[i])
        d = d1a_at(Tc[i] - 14400)
        events.append({
            "event_ts": datetime.fromtimestamp(Tc[i], tz=timezone.utc).isoformat(),
            "bar_close_time": Tc[i], "regime_year": regime_year(Tc[i]),
            "ev_open": O[i], "ev_high": H[i], "ev_low": L[i], "ev_close": C[i], "atr14": round(atr, 4),
            "ema50_gt_ema200": bool(ema_stack), "close_gt_ema200": bool(ema200[i] is not None and C[i] > ema200[i]),
            "ema50_slope_pos": bool(i >= 5 and ema50[i - 5] is not None and ema50[i] > ema50[i - 5]),
            "adx14": round(adx[i], 2) if adx[i] is not None else None,
            "adx_ge_20": bool(adx[i] is not None and adx[i] >= 20),
            "atr_expanding": bool(atr_ma[i] is not None and atr > atr_ma[i]),
            "d1a_pass": bool(d["d1a_pass"]) if d else None,
            "d1_close_gt_ema200": bool(d["close_gt_ema200"]) if d else None,
            "d1_ema50_gt_ema200": bool(d["ema50_gt_ema200"]) if d else None,
            "dist_to_demand_atr": round(dist_to_demand_atr, 3) if dist_to_demand_atr is not None else None,
            "retraced_to_demand": retraced, "bars_to_demand_touch": touch_k,
            "run_after_demand_atr": round(run_after, 3) if run_after is not None else None,
            "mfe_R": round(mfe_R, 3), "mae_R": round(mae_R, 3),
            "bars_to_fwd_high": bars_to_high, "bars_to_fwd_low": bars_to_low,
            "fwd_high": fwd_high, "fwd_low": fwd_low,
            "entry_price": round(entry, 4), "stop_price": round(stop, 4), "target_price": round(target, 4),
            "risk": round(risk, 4), "close_R": round(close_R, 4), "exit_reason": exit_reason,
            "winner": close_R > 0, "be_moved": be,
            "alt_demand_entry": alt,
            "bar_index": i,
            "ctx": {f: r.get(f) for f in CTX_FIELDS},
        })

    # no-overlap flag (greedy by current-rules window) for independence-safe mining
    last_end = -1
    for e in events:
        if e["bar_index"] > last_end:
            e["no_overlap"] = True
            last_end = e["bar_index"] + FWD
        else:
            e["no_overlap"] = False

    out = RESULTS / "entry_anatomy.jsonl"
    with open(out, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

    nov = [e for e in events if e["no_overlap"]]
    nwin = sum(1 for e in events if e["winner"])
    def rate(pred, pool=None):
        sub = [e for e in (pool if pool is not None else events) if pred(e)]
        w = sum(1 for e in sub if e["winner"])
        return {"n": len(sub), "win_rate": round(w / len(sub), 3) if sub else None,
                "sumR": round(sum(e["close_R"] for e in sub), 1)}
    # ALT demand-entry outcome (the real retrace-entry measurement; DA-required)
    filled = [e for e in events if e["alt_demand_entry"]["filled"]]
    fwin = sum(1 for e in filled if e["alt_demand_entry"]["close_R"] > 0)
    alt_sumR = round(sum(e["alt_demand_entry"]["close_R"] for e in filled), 1)
    # paired: for retraced events, current-rules R (≈stop) vs alt demand-entry R
    paired_cur = round(sum(e["close_R"] for e in filled), 1)
    agg = {
        "source": "RAW replay .gz ONLY (audited extractor in-memory; no slim file read)",
        "bars": n, "events": len(events), "no_overlap_events": len(nov),
        "winners": nwin, "win_rate": round(nwin / len(events), 3) if events else None,
        "sumR": round(sum(e["close_R"] for e in events), 1),
        "no_overlap_headline": {"n": len(nov), "win_rate": round(sum(1 for e in nov if e["winner"]) / len(nov), 3) if nov else None,
                                "sumR": round(sum(e["close_R"] for e in nov), 1)},
        "ALT_demand_entry": {
            "_note": "real outcome of retrace-to-demand entry (fill@demand_high, SL=demand_low-0.5ATR, +4R/BE/time). DA-required; supersedes run_after proxy.",
            "filled": len(filled), "of_events": len(events),
            "win_rate": round(fwin / len(filled), 3) if filled else None, "sumR": alt_sumR,
            "vs_current_on_same_events": {"current_sumR": paired_cur, "alt_sumR": alt_sumR,
                                          "delta_R": round(alt_sumR - paired_cur, 1)},
            "no_overlap": {"filled": sum(1 for e in nov if e["alt_demand_entry"]["filled"]),
                           "win_rate": round(sum(1 for e in nov if e["alt_demand_entry"]["filled"] and e["alt_demand_entry"]["close_R"] > 0) / max(1, sum(1 for e in nov if e["alt_demand_entry"]["filled"])), 3),
                           "sumR": round(sum(e["alt_demand_entry"]["close_R"] for e in nov if e["alt_demand_entry"]["filled"]), 1)}},
        "by_inside_supply": {"yes": rate(lambda e: e["ctx"].get("inside_supply_zone")),
                             "no": rate(lambda e: not e["ctx"].get("inside_supply_zone"))},
        "by_nas_short_recent": {"yes": rate(lambda e: e["ctx"].get("nas_label_short_recent")),
                                "no": rate(lambda e: not e["ctx"].get("nas_label_short_recent"))},
        "by_retraced_to_demand": {"yes": rate(lambda e: e["retraced_to_demand"]),
                                  "no": rate(lambda e: e["retraced_to_demand"] is False)},
        "by_d1a": {"pass": rate(lambda e: e["d1a_pass"]), "fail": rate(lambda e: e["d1a_pass"] is False)},
        "by_ema_stack": {"yes": rate(lambda e: e["ema50_gt_ema200"]), "no": rate(lambda e: not e["ema50_gt_ema200"])},
        "by_dist_to_demand": {
            "near_<=1atr": rate(lambda e: e["dist_to_demand_atr"] is not None and e["dist_to_demand_atr"] <= 1.0),
            "mid_1to3": rate(lambda e: e["dist_to_demand_atr"] is not None and 1.0 < e["dist_to_demand_atr"] <= 3.0),
            "ext_>3atr": rate(lambda e: e["dist_to_demand_atr"] is not None and e["dist_to_demand_atr"] > 3.0)},
        "by_nearest_zone_type": {"DEMAND": rate(lambda e: e["ctx"].get("custom_ob_nearest_zone_type") == "DEMAND"),
                                 "SUPPLY": rate(lambda e: e["ctx"].get("custom_ob_nearest_zone_type") == "SUPPLY")},
        "by_bubble": {"sell_bubble": rate(lambda e: e["ctx"].get("bubble_sell_current")),
                      "large_buy": rate(lambda e: e["ctx"].get("bubble_large_current") and e["ctx"].get("bubble_buy_current"))},
        "out": str(out),
    }
    (RESULTS / "entry_anatomy_orientation.json").write_text(json.dumps(agg, indent=2))
    print(json.dumps(agg, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
