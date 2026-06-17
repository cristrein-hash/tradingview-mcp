#!/usr/bin/env python3
"""XAU_4H_BREAKOUT_D1A x L2/BPT — entry test (RAW-only).

Tests the user's thesis: BREAKOUT/D1a = validation; the value entry is the RETURN to the
broken polarity level (Cris Pattern #1: "rompimento -> retorno a polaridade de topo, mesma
altura CHoCH/BOS, SL abaixo do fundo estrutural"), NOT the breakout candle.

SOURCE = RAW replay .gz ONLY (audited extractor in-memory; NO slim file read).
Reused canonical (NOT new) thresholds from L2 v2 / SMC Unified pre-reg (decided w/ Cris 2026-06-06/07):
  retest tolerance 0.15*ATR · reclaim buffer 0.1*ATR · body>=0.5 · R floor 0.3*ATR / ceiling 1.5*ATR.
Polaridade P = swing_high_10[i] (the broken level). Entry compared: IMMEDIATE (next-open, tight SL)
vs L2_TOUCH (limit at P) vs L2_RECLAIM (green reclaim above P). Targets grid {2,3,4}R (pre-registered
comparison, NOT optimization). No-overlap for independence; TRAIN<2023 / HOLDOUT>=2023.

NOT validation. Gross R. No MCP/plot/Telegram/production. py_compile required.
"""
import json
import bisect
import statistics
from datetime import datetime, timezone
from pathlib import Path

import run_mechanical_rebuild_v1 as eng
import build_entry_anatomy as ba

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
EMA1D = HERE / "generated" / "xau_1d_ema_features.jsonl"

N_RETEST = 24          # bars to wait for the return to polarity
MAX_HOLD = 24          # time-stop from entry
RETEST_TOL = 0.15      # *ATR  (L2 canonical)
RECLAIM_BUF = 0.10     # *ATR  (L2 canonical)
BODY_MIN = 0.5
R_FLOOR = 0.3          # *ATR  (SMC Unified)
R_CEIL = 1.5           # *ATR  (SMC Unified) -> abort if exceeded
STOP_ATR_TIGHT = 0.5
TARGETS = [2.0, 3.0, 4.0]


def sim_from(entry_idx, entry, stop, target, H, L, C, n):
    risk = entry - stop
    if risk <= 0:
        return None
    be = False  # no BE in this clean L2/immediate comparison
    end = min(entry_idx + MAX_HOLD, n)
    for j in range(entry_idx, end):
        if L[j] <= stop:
            return (stop - entry) / risk, "stop"
        if H[j] >= target:
            return (target - entry) / risk, "target"
    last = min(entry_idx + MAX_HOLD - 1, n - 1)
    return (C[last] - entry) / risk, "time_limit"


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    S = ba.extract_raw_rows()                       # RAW-only, audited interp in-memory
    n = len(S)
    O = [r["open"] for r in S]; H = [r["high"] for r in S]; L = [r["low"] for r in S]; C = [r["close"] for r in S]
    Tc = [r["bar_close_time"] for r in S]
    ema50 = eng.ema(C, 50); ema200 = eng.ema(C, 200)
    atr_ma = eng.sma_series([r.get("atr14_wilder") for r in S], 20)
    daily = [json.loads(l) for l in EMA1D.read_text().splitlines() if l.strip()]
    daily.sort(key=lambda d: d["close_time"]); d_close = [d["close_time"] for d in daily]

    def d1a_at(bo):
        i = bisect.bisect_right(d_close, bo) - 1
        return daily[i] if i >= 0 else None

    def yr(t):
        return datetime.fromtimestamp(t, tz=timezone.utc).year

    events = []
    last_end = -1
    for i in range(200, n - 1):
        r = S[i]
        atr = r.get("atr14_wilder")
        if not atr or atr <= 0:
            continue
        # T8 = trigger(T1-T4) + EMA stack + D1a
        if not (r.get("close_above_swing_high_10") and C[i] > O[i] and (r.get("body_pct") or 0) >= 0.5 and r.get("rsi_above_ma")):
            continue
        es = (ema50[i] is not None and ema200[i] is not None and ema50[i] > ema200[i] and C[i] > ema200[i])
        if not es:
            continue
        d = d1a_at(Tc[i] - 14400)
        if not (d and d["d1a_pass"]):
            continue
        P = r.get("swing_high_10")                  # polaridade = broken level (Pattern #1)
        if P is None:
            continue
        no_overlap = i > last_end
        if no_overlap:
            last_end = i + N_RETEST

        ev = {"i": i, "ts": datetime.fromtimestamp(Tc[i], tz=timezone.utc).isoformat(), "year": yr(Tc[i]),
              "no_overlap": no_overlap, "atr": atr, "polaridade": P,
              "ctx": {k: r.get(k) for k in ("inside_supply_zone", "nearest_supply_dist",
                      "custom_ob_nearest_demand_state", "nas_label_short_recent")},
              "atr_expanding": bool(atr_ma[i] is not None and atr > atr_ma[i])}

        # IMMEDIATE entry (baseline)
        entry_im = O[i + 1]; stop_im = L[i] - STOP_ATR_TIGHT * atr
        ev["immediate"] = {}
        for tr in TARGETS:
            res = sim_from(i + 1, entry_im, stop_im, entry_im + tr * (entry_im - stop_im), H, L, C, n)
            ev["immediate"][f"R{int(tr)}"] = {"R": round(res[0], 4), "exit": res[1]} if res else None

        # L2 retest of polaridade within N_RETEST
        touch_k = None
        for k in range(i + 1, min(i + 1 + N_RETEST, n)):
            if L[k] <= P + RETEST_TOL * atr:
                touch_k = k; break
        ev["retested"] = touch_k is not None

        # CAUSAL structural SL = pre-breakout consolidation base (swing_low_10[i]) - 0.1ATR.
        # Known at the EVENT bar (before any fill) -> no look-ahead (DA Q4 fix). NO artificial
        # R-floor (DA fix #2): risk is whatever the structure gives; abort if > R_CEIL*ATR.
        sl_struct = r.get("swing_low_10")

        # L2_TOUCH: limit fill at P; structural SL = consolidation base
        ev["l2_touch"] = {"filled": False}
        if touch_k is not None and sl_struct is not None:
            entry_t = P
            stop_t = sl_struct - 0.1 * atr
            risk_t = entry_t - stop_t
            if risk_t <= 0:
                ev["l2_touch"] = {"filled": False, "abort": "nonpos_risk"}
            elif risk_t > R_CEIL * atr:
                ev["l2_touch"] = {"filled": False, "abort": "R_ceiling"}
            else:
                ev["l2_touch"] = {"filled": True, "entry": round(entry_t, 4), "stop": round(stop_t, 4),
                                  "risk_atr": round(risk_t / atr, 3)}
                for tr in TARGETS:
                    res = sim_from(touch_k, entry_t, stop_t, entry_t + tr * risk_t, H, L, C, n)
                    ev["l2_touch"][f"R{int(tr)}"] = {"R": round(res[0], 4), "exit": res[1]} if res else None

        # L2_RECLAIM: green reclaim above P after touch; structural SL = consolidation base
        ev["l2_reclaim"] = {"filled": False}
        if touch_k is not None and sl_struct is not None:
            rec_m = None
            for m in range(touch_k, min(i + 1 + N_RETEST, n)):
                if C[m] > O[m] and ((H[m] - L[m]) > 0) and (abs(C[m] - O[m]) / (H[m] - L[m])) >= BODY_MIN and C[m] > P + RECLAIM_BUF * atr:
                    rec_m = m; break
            if rec_m is not None and rec_m + 1 < n:
                entry_r = C[rec_m]
                stop_r = sl_struct - 0.1 * atr
                risk_r = entry_r - stop_r
                if 0 < risk_r:
                    if risk_r > R_CEIL * atr:
                        ev["l2_reclaim"] = {"filled": False, "abort": "R_ceiling"}
                    else:
                        ev["l2_reclaim"] = {"filled": True, "entry": round(entry_r, 4), "stop": round(stop_r, 4),
                                            "risk_atr": round(risk_r / atr, 3), "reclaim_bars_after_touch": rec_m - touch_k}
                        for tr in TARGETS:
                            res = sim_from(rec_m, entry_r, stop_r, entry_r + tr * risk_r, H, L, C, n)
                            ev["l2_reclaim"][f"R{int(tr)}"] = {"R": round(res[0], 4), "exit": res[1]} if res else None
        # L2 with a REALISTIC fixed structural buffer SL = P - 1.0*ATR (causal; DA fix #2 "raise to ~1ATR").
        # Entry at touch (P) -> risk = 1ATR; entry at reclaim (close>P) -> risk > 1ATR.
        for et_name, fill_idx, fill_px in (("l2_touch_fix1", touch_k, P),
                                           ("l2_reclaim_fix1", None, None)):
            ev[et_name] = {"filled": False}
        if touch_k is not None:
            stop_f = P - 1.0 * atr
            # touch fixed
            risk_f = P - stop_f
            if risk_f > 0:
                ev["l2_touch_fix1"] = {"filled": True, "entry": round(P, 4), "stop": round(stop_f, 4), "risk_atr": 1.0}
                for tr in TARGETS:
                    res = sim_from(touch_k, P, stop_f, P + tr * risk_f, H, L, C, n)
                    ev["l2_touch_fix1"][f"R{int(tr)}"] = {"R": round(res[0], 4), "exit": res[1]} if res else None
            # reclaim fixed
            rec_m2 = None
            for m in range(touch_k, min(i + 1 + N_RETEST, n)):
                if C[m] > O[m] and ((H[m] - L[m]) > 0) and (abs(C[m] - O[m]) / (H[m] - L[m])) >= BODY_MIN and C[m] > P + RECLAIM_BUF * atr:
                    rec_m2 = m; break
            if rec_m2 is not None:
                entry_rf = C[rec_m2]; risk_rf = entry_rf - stop_f
                if risk_rf > 0 and risk_rf <= R_CEIL * atr:
                    ev["l2_reclaim_fix1"] = {"filled": True, "entry": round(entry_rf, 4), "stop": round(stop_f, 4),
                                             "risk_atr": round(risk_rf / atr, 3)}
                    for tr in TARGETS:
                        res = sim_from(rec_m2, entry_rf, stop_f, entry_rf + tr * risk_rf, H, L, C, n)
                        ev["l2_reclaim_fix1"][f"R{int(tr)}"] = {"R": round(res[0], 4), "exit": res[1]} if res else None
                else:
                    ev["l2_reclaim_fix1"] = {"filled": False, "abort": "R_ceiling"}
        events.append(ev)

    # ---- aggregate (no-overlap; FASE 1) ----
    nov = [e for e in events if e["no_overlap"]]
    def agg(entry_type, target_key, pool, gate=None):
        rows = []
        for e in pool:
            blk = e.get(entry_type, {})
            if entry_type != "immediate" and not blk.get("filled"):
                continue
            if gate and not gate(e):
                continue
            cell = blk.get(target_key)
            if cell:
                rows.append(cell["R"])
        if not rows:
            return {"n": 0}
        w = sum(1 for x in rows if x > 0)
        wins = [x for x in rows if x > 0]; losses = [x for x in rows if x <= 0]
        pf = round(sum(wins) / abs(sum(losses)), 3) if losses and sum(losses) != 0 else None
        return {"n": len(rows), "WR": round(w / len(rows), 3), "sumR": round(sum(rows), 1),
                "avgR": round(sum(rows) / len(rows), 3), "PF": pf}

    summary = {
        "source": "RAW replay .gz ONLY (audited extractor in-memory; NO slim file)",
        "thesis": "breakout=validation; entry on return to polaridade=swing_high_10 (Cris Pattern #1)",
        "canonical_reused": {"retest_tol_atr": RETEST_TOL, "reclaim_buf_atr": RECLAIM_BUF,
                             "body_min": BODY_MIN, "R_floor_atr": R_FLOOR, "R_ceil_atr": R_CEIL,
                             "_note": "L2 v2 / SMC Unified pre-reg values (decided w/ Cris), NOT new"},
        "bars": n, "T8_events": len(events), "no_overlap_events": len(nov),
        "retested_rate": round(sum(1 for e in nov if e["retested"]) / len(nov), 3) if nov else None,
        "FASE1_pre_registered": {},
        "FASE2_creative": {},
    }
    # FASE 1: immediate vs l2_touch vs l2_reclaim, targets 2/3/4, no-overlap + train/holdout
    for et in ("immediate", "l2_touch", "l2_reclaim", "l2_touch_fix1", "l2_reclaim_fix1"):
        summary["FASE1_pre_registered"][et] = {}
        for tr in TARGETS:
            tk = f"R{int(tr)}"
            summary["FASE1_pre_registered"][et][tk] = {
                "all": agg(et, tk, nov),
                "TRAIN": agg(et, tk, [e for e in nov if e["year"] < 2023]),
                "HOLDOUT": agg(et, tk, [e for e in nov if e["year"] >= 2023]),
            }
    # FASE 2: creative causal gates on l2_reclaim @ R3 (HYPOTHESIS_ONLY)
    gates = {
        "base_l2_reclaim_R3": None,
        "+atr_expanding": lambda e: e["atr_expanding"],
        "+not_inside_supply": lambda e: not e["ctx"].get("inside_supply_zone"),
        "+fresh_demand": lambda e: e["ctx"].get("custom_ob_nearest_demand_state") == "fresh",
        "+not_nas_short_recent": lambda e: not e["ctx"].get("nas_label_short_recent"),
        "+atr_exp&not_supply": lambda e: e["atr_expanding"] and not e["ctx"].get("inside_supply_zone"),
    }
    for name, g in gates.items():
        summary["FASE2_creative"][name] = {"status": "HYPOTHESIS_ONLY/CAUSAL/NEEDS_PREREG/NEEDS_VISUAL/NEEDS_OOS",
                                           "all": agg("l2_reclaim", "R3", nov, g),
                                           "HOLDOUT": agg("l2_reclaim", "R3", [e for e in nov if e["year"] >= 2023], g)}
    # runaways lost vs top-losers avoided (immediate R4 as reference)
    runaway_lost = sum(1 for e in nov if not e["retested"] and (e["immediate"].get("R4") or {}).get("R", 0) > 0)
    toploss_avoided = sum(1 for e in nov if not e["retested"] and (e["immediate"].get("R4") or {}).get("R", 0) <= 0)
    summary["runaway_vs_toploss"] = {
        "_note": "events that NEVER retested polaridade (no L2 fill): how many were immediate-R4 winners (runaways lost) vs losers (top-losses avoided)",
        "never_retested": sum(1 for e in nov if not e["retested"]),
        "runaways_lost(immediate_R4_win)": runaway_lost,
        "toploss_avoided(immediate_R4_loss)": toploss_avoided}

    (RESULTS / "l2_bpt_breakout_test_summary.json").write_text(json.dumps(summary, indent=2))
    # trades.jsonl + plot_ready: the REALISTIC viable variant = l2_touch_fix1 @ R4 (SL = P-1ATR causal)
    VOUT, VTK = "l2_touch_fix1", "R4"
    with open(RESULTS / "l2_bpt_breakout_trades.jsonl", "w") as f:
        cid = 0
        for e in events:
            blk = e.get(VOUT, {})
            if not blk.get("filled") or not blk.get(VTK):
                continue
            cid += 1
            f.write(json.dumps({"chronological_id": cid, "variant": f"{VOUT}_{VTK}", "entry_ts": e["ts"],
                                "entry_price": blk["entry"], "stop_price": blk["stop"],
                                "target_price": round(blk["entry"] + 4 * (blk["entry"] - blk["stop"]), 4),
                                "close_R": blk[VTK]["R"], "exit_reason": blk[VTK]["exit"],
                                "result_class": "winner" if blk[VTK]["R"] > 0 else "loser",
                                "polaridade": e["polaridade"], "no_overlap": e["no_overlap"]}) + "\n")
    with open(RESULTS / "l2_bpt_breakout_plot_ready.csv", "w") as f:
        f.write("chronological_id,variant,entry_ts,entry_price,stop_price,target_price,close_R,result_class,color_hint\n")
        cid = 0
        for e in events:
            blk = e.get(VOUT, {})
            if not blk.get("filled") or not blk.get(VTK):
                continue
            cid += 1
            R = blk[VTK]["R"]
            f.write(f'{cid},{VOUT}_{VTK},{e["ts"]},{blk["entry"]},{blk["stop"]},'
                    f'{round(blk["entry"]+4*(blk["entry"]-blk["stop"]),4)},{R},'
                    f'{"winner" if R>0 else "loser"},{"#1a8917" if R>0 else "#cc0000"}\n')

    print(json.dumps({k: summary[k] for k in ("bars", "T8_events", "no_overlap_events", "retested_rate",
                                              "FASE1_pre_registered", "FASE2_creative", "runaway_vs_toploss")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
