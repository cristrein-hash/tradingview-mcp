#!/usr/bin/env python3
"""XAU 4H LONG L2/BPT BOS-CHoCH — mechanical CENSUS 2019-2026 (RAW-only).

RECONSTRUCTION CENSUS / MECHANICAL BASELINE / HYPOTHESES-ONLY (NOT final validation).
Source = RAW replay .gz ONLY (audited extractor in-memory via build_entry_anatomy; NO slim).
Causal SMC state machine: pivots Williams 5/5 SHIFT5 -> protected_LH -> CHoCH (close>protected_LH
+0.2ATR, bearish ctx) -> polaridade fixed -> retest (low<=polaridade+0.15ATR) -> reclaim (green,
body>=0.5, close>polaridade+0.1ATR) -> entry at reclaim close -> structural SL (recent confirmed PL
below entry -0.1ATR, R-bound floor 0.3 / ceiling 1.5 ATR abort) -> targets {2,3,4}R, stop-first,
time-stop 24. One entry per CHoCH episode (dedup). Overlays = TAGS only (no hard filter).

NO threshold optimization, NO human adjustment, NO MCP/plot/Telegram/production. py_compile required.
"""
import json
import sys
import statistics
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
# build_entry_anatomy (RAW-only loader, audited extractor in-memory) lives in the breakout v1 dir
sys.path.insert(0, str(HERE.parent.parent / "XAU_4H_BREAKOUT_D1A" / "v1"))
import build_entry_anatomy as ba  # noqa: E402
RESULTS = HERE / "results"
K = 5                 # Williams 5/5 pivot, SHIFT5
N_RETEST = 24         # bars to wait for retest+reclaim after CHoCH
MAX_HOLD = 24
B_CHOCH = 0.2         # *ATR
TOL_RETEST = 0.15     # *ATR
BUF_RECLAIM = 0.1     # *ATR
BODY_MIN = 0.5
R_FLOOR = 0.3         # *ATR
R_CEIL = 1.5          # *ATR
TARGETS = [2.0, 3.0, 4.0]
TAGS = ["inside_demand_zone", "inside_supply_zone", "nearest_supply_dist",
        "nas_label_long_recent", "nas_label_short_recent",
        "bubble_buy_current", "bubble_sell_current", "bubble_large_current",
        "rsi", "rsi_div_bearish_event"]


def compute_pivots(H, L, k=K):
    n = len(H); ph = [False] * n; pl = [False] * n
    for j in range(k, n - k):
        if H[j] > max(H[j - k:j]) and H[j] > max(H[j + 1:j + k + 1]):
            ph[j] = True
        if L[j] < min(L[j - k:j]) and L[j] < min(L[j + 1:j + k + 1]):
            pl[j] = True
    return ph, pl


def sim(entry_idx, entry, stop, target, H, L, C, n):
    risk = entry - stop
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
    S = ba.extract_raw_rows()
    # 2019+ only
    def yr_of(t): return datetime.fromtimestamp(t, tz=timezone.utc).year
    S = [r for r in S if r.get("bar_close_time") and yr_of(r["bar_close_time"]) >= 2019]
    n = len(S)
    O = [r["open"] for r in S]; H = [r["high"] for r in S]; L = [r["low"] for r in S]; C = [r["close"] for r in S]
    Tc = [r["bar_close_time"] for r in S]
    ATR = [r.get("atr14_wilder") for r in S]
    ph, pl = compute_pivots(H, L)

    confH = []  # (idx, price) confirmed pivot highs in time order
    confL = []
    funnel = {"choch": 0, "bos": 0, "episodes_with_retest": 0, "episodes_with_reclaim": 0,
              "entries": 0, "no_retest": 0, "no_reclaim": 0, "R_ceiling_abort": 0,
              "invalidation_before_entry": 0, "no_struct_low": 0}
    trades = []

    state = "S0"; polaridade = None; choch_bar = None
    retest_done = False; choch_ph_ref = None

    for i in range(2 * K, n - 1):
        # confirm pivot at j=i-K (SHIFT5)
        j = i - K
        if ph[j]:
            confH.append((j, H[j]))
        if pl[j]:
            confL.append((j, L[j]))
        atr = ATR[i]
        if not atr or atr <= 0:
            continue

        if state == "S0":
            # protected_LH: most recent confirmed PH before the most recent confirmed PL, bearish ctx
            if not confL or not confH:
                continue
            last_pl_idx, last_pl_px = confL[-1]
            # bearish context: lower-low vs prior PL, else lower-high vs prior PH
            bearish = False
            if len(confL) >= 2 and last_pl_px < confL[-2][1]:
                bearish = True
            elif len(confH) >= 2 and confH[-1][1] < confH[-2][1]:
                bearish = True
            if not bearish:
                continue
            prior_PH = [p for p in confH if p[0] < last_pl_idx]
            if not prior_PH:
                continue
            protected_LH = prior_PH[-1][1]
            if C[i] > protected_LH + B_CHOCH * atr:
                funnel["choch"] += 1
                state = "S1"; polaridade = protected_LH; choch_bar = i
                retest_done = False; choch_ph_ref = confH[-1][1] if confH else None
                got_retest = got_reclaim = False
                episode_atr = atr
                # leg-origin structural low: most recent confirmed PL below polaridade (for invalidation only)
                below_o = [p for p in confL if p[1] < protected_LH]
                struct_low_origin = below_o[-1][1] if below_o else last_pl_px
            continue

        # state == "S1"
        # BOS tag: close breaks a confirmed PH formed after CHoCH (counted only; not entry path in v1)
        ph_after = [p[1] for p in confH if p[0] > choch_bar]
        if ph_after and C[i] > min(ph_after) + B_CHOCH * atr:
            funnel["bos"] += 1
        # (1) retest detection FIRST (so a deep-wick retest bar is not pre-killed by invalidation)
        if not retest_done and L[i] <= polaridade + TOL_RETEST * episode_atr:
            retest_done = True
            if not got_retest:
                funnel["episodes_with_retest"] += 1; got_retest = True
        # (2) reclaim -> entry. SL = RETEST SWING LOW (lowest low choch_bar+1..i) - 0.1ATR
        #     (manifest §1.9 "low recente" term; NOT the deep leg-origin PL -> R-viable)
        if retest_done and C[i] > O[i] and (H[i] - L[i]) > 0 and (abs(C[i] - O[i]) / (H[i] - L[i])) >= BODY_MIN \
           and C[i] > polaridade + BUF_RECLAIM * episode_atr:
            if not got_reclaim:
                funnel["episodes_with_reclaim"] += 1; got_reclaim = True
            entry = C[i]
            retest_low = min(L[choch_bar + 1:i + 1]) if i > choch_bar else L[i]
            sl = retest_low - 0.1 * episode_atr
            risk = entry - sl
            if risk <= 0:
                funnel["no_struct_low"] += 1; state = "S0"; continue
            if risk < R_FLOOR * episode_atr:
                sl = entry - R_FLOOR * episode_atr; risk = R_FLOOR * episode_atr
            if risk > R_CEIL * episode_atr:
                funnel["R_ceiling_abort"] += 1; state = "S0"; continue
            r = S[i]
            tr = {"entry_ts": datetime.fromtimestamp(Tc[i], tz=timezone.utc).isoformat(),
                  "year": yr_of(Tc[i]), "entry": round(entry, 4), "stop": round(sl, 4),
                  "risk_atr": round(risk / episode_atr, 3), "polaridade": round(polaridade, 4),
                  "choch_to_entry_bars": i - choch_bar,
                  "tags": {t: r.get(t) for t in TAGS}, "at_D1_demand": "tag_pending"}
            for t in TARGETS:
                res = sim(i + 1, entry, sl, entry + t * risk, H, L, C, n)
                tr[f"R{int(t)}"] = {"R": round(res[0], 4), "exit": res[1]}
            funnel["entries"] += 1
            trades.append(tr)
            state = "S0"; continue
        # (3) invalidation: only a real structural break of the leg-origin low (after retest/reclaim chance)
        if C[i] < struct_low_origin:
            funnel["invalidation_before_entry"] += 1
            state = "S0"; continue
        # (4) timeout
        if i - choch_bar > N_RETEST:
            if not got_retest:
                funnel["no_retest"] += 1
            elif not got_reclaim:
                funnel["no_reclaim"] += 1
            state = "S0"; continue

    # chronological ids
    for cid, t in enumerate(trades, 1):
        t["id"] = cid

    def block(rs):
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
        return {"n": len(rs), "WR": round(w / len(rs), 3), "sumR": round(sum(rs), 1),
                "avgR": round(sum(rs) / len(rs), 3), "medianR": round(statistics.median(rs), 3),
                "PF": pf, "maxDD_R": round(mdd, 1), "losing_streak": int(mstreak)}

    def exits(rs_exits):
        return {r: rs_exits.count(r) for r in ("target", "stop", "time_limit")}

    metrics = {}
    for t in TARGETS:
        tk = f"R{int(t)}"
        rs = [tr[tk]["R"] for tr in trades]
        ex = [tr[tk]["exit"] for tr in trades]
        m = block(rs); m["exits"] = exits(ex)
        m["yearly"] = {}
        by = {}
        for tr in trades:
            by.setdefault(tr["year"], []).append(tr[tk]["R"])
        m["yearly"] = {str(y): {"n": len(v), "sumR": round(sum(v), 1),
                                "WR": round(sum(1 for x in v if x > 0) / len(v), 3)} for y, v in sorted(by.items())}
        metrics[tk] = m

    # tag breakdown @R3
    def tag_rate(pred):
        rs = [tr["R3"]["R"] for tr in trades if pred(tr)]
        return block(rs)
    tagm = {
        "inside_supply": tag_rate(lambda t: t["tags"].get("inside_supply_zone")),
        "not_inside_supply": tag_rate(lambda t: not t["tags"].get("inside_supply_zone")),
        "inside_demand": tag_rate(lambda t: t["tags"].get("inside_demand_zone")),
        "nas_short_recent": tag_rate(lambda t: t["tags"].get("nas_label_short_recent")),
        "nas_long_recent": tag_rate(lambda t: t["tags"].get("nas_label_long_recent")),
        "bubble_large_buy": tag_rate(lambda t: t["tags"].get("bubble_large_current") and t["tags"].get("bubble_buy_current")),
        "rsi_div_bearish": tag_rate(lambda t: t["tags"].get("rsi_div_bearish_event")),
    }

    summary = {
        "round": "L2/BPT BOS-CHoCH mechanical census 2019-2026",
        "status": "RECONSTRUCTION_CENSUS / MECHANICAL_BASELINE / HYPOTHESES_ONLY (NOT final validation)",
        "source": "RAW replay .gz ONLY (audited extractor in-memory; NO slim)",
        "bars_2019plus": n, "date_range": [datetime.fromtimestamp(Tc[0], tz=timezone.utc).isoformat(),
                                           datetime.fromtimestamp(Tc[-1], tz=timezone.utc).isoformat()],
        "funnel": funnel,
        "metrics": metrics,
        "tag_breakdown_R3": tagm,
        "gross": True, "costs": False,
    }
    (RESULTS / "l2_bpt_census_summary.json").write_text(json.dumps(summary, indent=2))
    with open(RESULTS / "l2_bpt_census_trades.jsonl", "w") as f:
        for t in trades:
            f.write(json.dumps(t) + "\n")
    with open(RESULTS / "l2_bpt_census_plot_ready.csv", "w") as f:
        f.write("id,entry_ts,entry_price,stop_price,target_price_R3,close_R3,result_class,color_hint\n")
        for t in trades:
            R = t["R3"]["R"]; tgt = round(t["entry"] + 3 * (t["entry"] - t["stop"]), 4)
            f.write(f'{t["id"]},{t["entry_ts"]},{t["entry"]},{t["stop"]},{tgt},{R},'
                    f'{"winner" if R>0 else "loser"},{"#1a8917" if R>0 else "#cc0000"}\n')
    # review queue (mechanical classification, no human adjustment of metric)
    with open(RESULTS / "l2_bpt_census_review_queue.csv", "w") as f:
        f.write("id,entry_ts,close_R3,exit_R3,risk_atr,class,needs_visual\n")
        for t in trades:
            R = t["R3"]["R"]; ex = t["R3"]["exit"]
            if R >= 2: cls = "mechanical_winner"
            elif R > 0: cls = "mechanical_small_win"
            elif ex == "stop": cls = "mechanical_loser_coherent"
            else: cls = "mechanical_loser_incoherent"
            nv = "yes" if cls in ("mechanical_loser_incoherent", "mechanical_small_win") else "no"
            f.write(f'{t["id"]},{t["entry_ts"]},{R},{ex},{t["risk_atr"]},{cls},{nv}\n')

    print(json.dumps({"funnel": funnel, "metrics": metrics, "tag_breakdown_R3": tagm,
                      "bars": n, "date_range": summary["date_range"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
