#!/usr/bin/env python3
"""XAU_4H_BREAKOUT_D1A — Mechanical Rebuild Round 1 (V0/V1/V5/V7 + optional V2-V4/V6).

READ-ONLY w.r.t. RAW + production. Reconstructs the 4H series from RAW 4H replay,
reads RSI/RSI_MA from the captured TV study_values, computes regime indicators from
OHLC, joins D1a via the CAUSAL rule (daily.close_time <= 4H bar_open), runs the
legacy outcome engine, and emits trades + metrics + a trade-level SHIFT audit.

NO threshold optimization, NO new filters, NO stop/target changes, NO plotting,
NO MCP, NO Telegram, NO broker, NO RAW mutation. Deterministic. Gross R.

Predicates (frozen, per gate_manifest):
  T1 close > max(high[i-10:i])      T2 close>open      T3 body_pct>=0.5      T4 rsi>rsi_ma
  R1 ADX(14)>=20   R2 close>EMA200   R3 EMA50>EMA200   R4 EMA50[i]>EMA50[i-5]   R5 atr14_wilder>SMA(atr14_wilder,20)
  D1a close_1D>EMA200_1D AND EMA50_1D>EMA200_1D, daily by close_time<=bar_open (CAUSAL).
Outcome: entry next-bar-open; SL low-0.5*atr14_wilder; target +4R; BE@+1R (applies j+1);
  time stop 24 bars; stop-first intrabar; no-overlap; sanity 0<risk<=5*atr.
"""
import gzip
import json
import bisect
import argparse
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = HERE / "generated"
RESULTS = HERE / "results"
EMA1D = GEN / "xau_1d_ema_features.jsonl"
RAW_4H_DIR = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/")
RAW_4H_BLOCKS = [
    "XAUUSD_240m_replay_2016-05-25_to_2020-01-01.jsonl.gz",
    "XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",
    "XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz",
]
WARMUP = 200
MAX_HOLD = 24
TARGET_R = 4.0
STOP_ATR_MULT = 0.5
SANITY_ATR_MULT = 5.0
SWING_LB = 10
ADX_MIN = 20.0
SLOPE_LB = 5
ATR_MA_PERIOD = 20

# Variant -> set of required regime/D1a gate keys (trigger T1-T4 always required)
VARIANTS = {
    "V0": set(),
    "V1": {"adx"},
    "V2": {"close_ema200", "ema_stack"},
    "V3": {"atr_exp"},
    "V4": {"slope"},
    "V5": {"adx", "close_ema200", "ema_stack", "slope", "atr_exp"},
    "V6": {"d1a"},
    "V7": {"adx", "close_ema200", "ema_stack", "slope", "atr_exp", "d1a"},
}


def reconstruct_4h():
    """Union ohlcv windows (dedup by time, keep-last) + per-bar RSI/RSI_MA from study_values."""
    bars = {}
    rsi_map = {}  # ohlcv[-1].time -> (rsi, rsi_ma) captured at that bar's close
    for blk in RAW_4H_BLOCKS:
        p = RAW_4H_DIR / blk
        if not p.exists():
            raise SystemExit(f"HARD STOP: RAW 4H block missing: {p}")
        with gzip.open(p, "rt") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                oh = rec.get("ohlcv") or []
                for b in oh:
                    t = b.get("time")
                    if t is None or b.get("close") is None:
                        continue
                    bars[t] = b
                # RSI from study_values at the current (closing) bar = ohlcv[-1]
                if oh:
                    cur_t = oh[-1].get("time")
                    for s in (rec.get("study_values") or []):
                        if isinstance(s, dict) and s.get("name") == "Relative Strength Index":
                            v = s.get("values") or {}
                            try:
                                rsi = float(v.get("RSI"))
                                rsi_ma = float(v.get("RSI-based MA"))
                                rsi_map[cur_t] = (rsi, rsi_ma)
                            except (TypeError, ValueError):
                                pass
    series = sorted(bars.values(), key=lambda b: b["time"])
    return series, rsi_map


def ema(values, period):
    a = 2.0 / (period + 1)
    out = [None] * len(values)
    if not values:
        return out
    prev = values[0]
    out[0] = prev
    for i in range(1, len(values)):
        prev = a * values[i] + (1 - a) * prev
        out[i] = prev
    return out


def atr_wilder(H, L, C, n=14):
    """Wilder ATR matching extract_replay_features post_pass (seed SMA14, then recursive)."""
    N = len(C)
    TR = [None] * N
    for i in range(N):
        TR[i] = (H[i] - L[i]) if i == 0 else max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))
    out = [None] * N
    if N < n:
        return out
    seed = sum(TR[:n]) / n
    out[n - 1] = seed
    for i in range(n, N):
        out[i] = (out[i - 1] * (n - 1) + TR[i]) / n
    return out


def adx_wilder(H, L, C, n=14):
    """Standard Wilder ADX(n): TR/+DM/-DM Wilder-smoothed -> DI± -> DX -> Wilder-smooth(DX)."""
    N = len(C)
    if N < 2 * n:
        return [None] * N
    TR = [0.0] * N
    pDM = [0.0] * N
    mDM = [0.0] * N
    for i in range(1, N):
        up = H[i] - H[i - 1]
        dn = L[i - 1] - L[i]
        pDM[i] = up if (up > dn and up > 0) else 0.0
        mDM[i] = dn if (dn > up and dn > 0) else 0.0
        TR[i] = max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))
    # Wilder smoothing seeded at index n (sum of 1..n)
    atr = [None] * N
    spDM = [None] * N
    smDM = [None] * N
    atr[n] = sum(TR[1:n + 1])
    spDM[n] = sum(pDM[1:n + 1])
    smDM[n] = sum(mDM[1:n + 1])
    for i in range(n + 1, N):
        atr[i] = atr[i - 1] - atr[i - 1] / n + TR[i]
        spDM[i] = spDM[i - 1] - spDM[i - 1] / n + pDM[i]
        smDM[i] = smDM[i - 1] - smDM[i - 1] / n + mDM[i]
    dx = [None] * N
    for i in range(n, N):
        if atr[i] and atr[i] != 0:
            pdi = 100 * spDM[i] / atr[i]
            mdi = 100 * smDM[i] / atr[i]
            s = pdi + mdi
            dx[i] = 100 * abs(pdi - mdi) / s if s else 0.0
    adx = [None] * N
    first = 2 * n
    if first < N:
        vals = [dx[i] for i in range(n, first) if dx[i] is not None]
        if len(vals) >= n:
            adx[first - 1] = sum(vals[-n:]) / n
            for i in range(first, N):
                if dx[i] is not None and adx[i - 1] is not None:
                    adx[i] = (adx[i - 1] * (n - 1) + dx[i]) / n
    return adx


def sma_series(x, k):
    out = [None] * len(x)
    for i in range(len(x)):
        seg = x[i - k + 1:i + 1]
        if len(seg) == k and all(v is not None for v in seg):
            out[i] = sum(seg) / k
    return out


def load_daily():
    rows = [json.loads(l) for l in EMA1D.read_text().splitlines() if l.strip()]
    rows.sort(key=lambda r: r["close_time"])
    return rows


def regime_of_year(y):
    return {2016: "pre_covid", 2017: "pre_covid", 2018: "pre_covid", 2019: "bull_pre_covid",
            2020: "covid_rally", 2021: "chop_post_covid", 2022: "chop_inflation_bear",
            2023: "chop_macro"}.get(y, "bull_recent")


def build_features(series, rsi_map):
    n = len(series)
    O = [b["open"] for b in series]
    H = [b["high"] for b in series]
    L = [b["low"] for b in series]
    C = [b["close"] for b in series]
    T = [b["time"] for b in series]
    ema50 = ema(C, 50)
    ema200 = ema(C, 200)
    atrw = atr_wilder(H, L, C, 14)
    atr_ma = sma_series(atrw, ATR_MA_PERIOD)
    adx = adx_wilder(H, L, C, 14)
    feats = []
    rsi_cov = 0
    for i in range(n):
        swing = max(H[i - SWING_LB:i]) if i >= SWING_LB else None
        rng = H[i] - L[i]
        body_pct = abs(C[i] - O[i]) / rng if rng > 0 else 0.0
        rsi, rsi_ma = rsi_map.get(T[i], (None, None))
        if rsi is not None:
            rsi_cov += 1
        feats.append({
            "i": i, "time": T[i], "open": O[i], "high": H[i], "low": L[i], "close": C[i],
            "swing10": swing, "body_pct": body_pct, "rsi": rsi, "rsi_ma": rsi_ma,
            "ema50": ema50[i], "ema200": ema200[i], "atrw": atrw[i], "atr_ma": atr_ma[i],
            "adx": adx[i], "ema50_5ago": ema50[i - SLOPE_LB] if i >= SLOPE_LB else None,
        })
    return feats, rsi_cov


def gate_flags(f):
    """Return (trigger_ok, dict of regime gate bools) or None if a required field is missing."""
    if f["swing10"] is None or f["rsi"] is None or f["rsi_ma"] is None:
        return None
    t1 = f["close"] > f["swing10"]
    t2 = f["close"] > f["open"]
    t3 = f["body_pct"] >= 0.5
    t4 = f["rsi"] > f["rsi_ma"]
    trigger = t1 and t2 and t3 and t4
    if None in (f["ema50"], f["ema200"], f["atrw"], f["atr_ma"], f["adx"], f["ema50_5ago"]):
        regime = None
    else:
        regime = {
            "adx": f["adx"] >= ADX_MIN,
            "close_ema200": f["close"] > f["ema200"],
            "ema_stack": f["ema50"] > f["ema200"],
            "slope": f["ema50"] > f["ema50_5ago"],
            "atr_exp": f["atrw"] > f["atr_ma"],
        }
    return trigger, regime, {"t1": t1, "t2": t2, "t3": t3, "t4": t4}


def causal_daily(daily, d_close, bar_open):
    idx = bisect.bisect_right(d_close, bar_open) - 1
    return daily[idx] if idx >= 0 else None


def simulate(feats, sig_i):
    """Run one trade from signal bar sig_i. Returns dict or None (skip)."""
    n = len(feats)
    if sig_i + 1 >= n:
        return None
    f = feats[sig_i]
    atr = f["atrw"]
    if atr is None or atr <= 0:
        return None
    entry = feats[sig_i + 1]["open"]
    stop = f["low"] - STOP_ATR_MULT * atr
    risk = entry - stop
    if risk <= 0 or risk > SANITY_ATR_MULT * atr:
        return None
    target = entry + TARGET_R * risk
    be = False
    entry_idx = sig_i + 1
    end = min(entry_idx + MAX_HOLD, n)
    exit_idx = exit_price = exit_reason = None
    for j in range(entry_idx, end):
        fj = feats[j]
        cur_stop = entry if be else stop
        if fj["low"] <= cur_stop:
            exit_idx, exit_price = j, cur_stop
            exit_reason = "stop_be" if be else "stop"
            break
        if fj["high"] >= target:
            exit_idx, exit_price, exit_reason = j, target, "target"
            break
        if not be and fj["high"] >= entry + risk:
            be = True
    if exit_idx is None:
        last = min(entry_idx + MAX_HOLD - 1, n - 1)
        exit_idx, exit_price, exit_reason = last, feats[last]["close"], "time_limit"
    close_R = (exit_price - entry) / risk
    return {"sig_i": sig_i, "entry_idx": entry_idx, "exit_idx": exit_idx,
            "entry": entry, "stop": stop, "target": target, "exit_price": exit_price,
            "risk": risk, "close_R": close_R, "exit_reason": exit_reason, "be_moved": be}


def metrics(trades):
    if not trades:
        return {"n": 0}
    Rs = [t["close_R"] for t in trades]
    wins = [r for r in Rs if r > 0]
    losses = [r for r in Rs if r <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else None
    # max DD on cumulative R
    cum = 0.0
    peak = 0.0
    mdd = 0.0
    streak = mstreak = 0
    for r in Rs:
        cum += r
        peak = max(peak, cum)
        mdd = min(mdd, cum - peak)
        if r <= 0:
            streak += 1
            mstreak = max(mstreak, streak)
        else:
            streak = 0
    by_year = {}
    for t in trades:
        y = datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).year
        by_year.setdefault(y, []).append(t["close_R"])
    yb = {str(y): {"n": len(v), "sumR": round(sum(v), 2), "wr": round(sum(1 for r in v if r > 0) / len(v), 3)}
          for y, v in sorted(by_year.items())}
    er = {}
    for t in trades:
        er[t["exit_reason"]] = er.get(t["exit_reason"], 0) + 1
    return {
        "n": len(trades), "targets": er.get("target", 0), "stops": er.get("stop", 0),
        "stop_be": er.get("stop_be", 0), "time_limit": er.get("time_limit", 0),
        "sumR": round(sum(Rs), 2), "avgR": round(sum(Rs) / len(Rs), 4),
        "PF": round(pf, 3) if pf else None, "WR": round(sum(1 for r in Rs if r > 0) / len(Rs), 3),
        "maxDD_R": round(mdd, 2), "max_losing_streak": mstreak,
        "first_year": min(by_year), "last_year": max(by_year),
        "yearly": yb, "gross": True,
    }


def run_variant(vid, feats, daily, d_close):
    req = VARIANTS[vid]
    needs_d1a = "d1a" in req
    regime_keys = req - {"d1a"}
    trades = []
    shift = {"with_d1a": needs_d1a, "total_d1a_eval": 0, "same_day_selected": 0,
             "close_time_gt_bar_open": 0, "missing_daily": 0, "examples": []}
    last_exit_idx = -1
    n = len(feats)
    for i in range(WARMUP, n - 1):
        if i <= last_exit_idx:
            continue
        gf = gate_flags(feats[i])
        if gf is None:
            continue
        trigger, regime, tflags = gf
        if not trigger:
            continue
        if regime_keys:
            if regime is None or not all(regime.get(k) for k in regime_keys):
                continue
        d1a_info = None
        if needs_d1a:
            bar_open = feats[i]["time"]
            drow = causal_daily(daily, d_close, bar_open)
            shift["total_d1a_eval"] += 1
            if drow is None:
                shift["missing_daily"] += 1
                continue
            if drow["close_time"] > bar_open:
                shift["close_time_gt_bar_open"] += 1
            bdate = datetime.fromtimestamp(bar_open, tz=timezone.utc).strftime("%Y-%m-%d")
            if drow["date"] == bdate and drow["close_time"] > bar_open:
                shift["same_day_selected"] += 1
                if len(shift["examples"]) < 5:
                    shift["examples"].append({"bar_open": bdate, "daily": drow["date"]})
            d1a_info = drow
            if not drow["d1a_pass"]:
                continue  # D1a gate blocks
        sim = simulate(feats, i)
        if sim is None:
            continue
        sim["entry_ts"] = feats[sim["entry_idx"]]["time"]
        sim["exit_ts"] = feats[sim["exit_idx"]]["time"]
        sim["variant_id"] = vid
        sim["regime_flags"] = regime if regime else {}
        sim["trigger_flags"] = tflags
        sim["d1a"] = ({"d1_daily_ts": d1a_info["date"], "d1_daily_close_time": d1a_info["close_time"],
                       "close_gt_ema200": d1a_info["close_gt_ema200"],
                       "ema50_gt_ema200": d1a_info["ema50_gt_ema200"], "d1a_pass": d1a_info["d1a_pass"]}
                      if d1a_info else None)
        trades.append(sim)
        last_exit_idx = sim["exit_idx"]
    # chronological ids (ordered by entry_ts; already in order)
    for cid, t in enumerate(trades, 1):
        t["chronological_id"] = cid
        t["regime_year"] = regime_of_year(datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).year)
    m = metrics(trades)
    return trades, m, shift


def main():
    ap = argparse.ArgumentParser(description="Mechanical rebuild round 1 (read-only).")
    ap.add_argument("--variants", default="V0,V1,V5,V7", help="comma list")
    args = ap.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    vids = [v.strip() for v in args.variants.split(",") if v.strip()]
    for v in vids:
        if v not in VARIANTS:
            raise SystemExit(f"unknown variant {v}")

    series, rsi_map = reconstruct_4h()
    feats, rsi_cov = build_features(series, rsi_map)
    daily = load_daily()
    d_close = [d["close_time"] for d in daily]

    all_trades = []
    summary = {"bars_4h": len(feats), "rsi_coverage": round(rsi_cov / len(feats), 4),
               "4h_range": [datetime.fromtimestamp(feats[0]["time"], tz=timezone.utc).isoformat(),
                            datetime.fromtimestamp(feats[-1]["time"], tz=timezone.utc).isoformat()],
               "daily_bars": len(daily), "warmup": WARMUP, "gross": True,
               "outcome": {"entry": "next_bar_open", "sl": "low-0.5*atr14_wilder", "target": "+4R",
                           "be": "+1R", "time_stop": MAX_HOLD, "intrabar": "stop_first"},
               "variants": {}, "shift_audit": {}}
    for v in vids:
        trades, m, shift = run_variant(v, feats, daily, d_close)
        summary["variants"][v] = m
        summary["shift_audit"][v] = shift
        all_trades.extend(trades)

    # outputs
    (RESULTS / "mechanical_rebuild_v1_summary.json").write_text(json.dumps(summary, indent=2))
    with open(RESULTS / "mechanical_rebuild_v1_trades.jsonl", "w") as f:
        for t in all_trades:
            d1a = t.get("d1a") or {}
            f.write(json.dumps({
                "chronological_id": t["chronological_id"], "variant_id": t["variant_id"],
                "entry_ts": datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).isoformat(),
                "entry_price": round(t["entry"], 4), "stop_price": round(t["stop"], 4),
                "target_price": round(t["target"], 4),
                "exit_ts": datetime.fromtimestamp(t["exit_ts"], tz=timezone.utc).isoformat(),
                "exit_price": round(t["exit_price"], 4), "close_R": round(t["close_R"], 4),
                "result_class": "winner" if t["close_R"] > 0 else "loser",
                "exit_reason": t["exit_reason"], "be_moved": t["be_moved"],
                "d1a_pass": d1a.get("d1a_pass"), "d1_daily_ts": d1a.get("d1_daily_ts"),
                "d1_daily_close_time": d1a.get("d1_daily_close_time"),
                "d1a_close_gt_ema200": d1a.get("close_gt_ema200"),
                "d1a_ema50_gt_ema200": d1a.get("ema50_gt_ema200"),
                "regime_flags": t["regime_flags"], "trigger_flags": t["trigger_flags"],
                "regime_year": t["regime_year"], "notes": ""}) + "\n")
    # plot-ready csv (canonical fields; NOT plotted)
    with open(RESULTS / "mechanical_rebuild_v1_plot_ready.csv", "w") as f:
        f.write("chronological_id,variant_id,entry_ts,entry_price,stop_price,target_price,"
                "exit_ts,exit_price,close_R,result_class,exit_reason,d1a_pass,color_hint\n")
        for t in all_trades:
            d1a = t.get("d1a") or {}
            color = "#1a8917" if t["close_R"] > 0 else "#cc0000"
            f.write(f'{t["chronological_id"]},{t["variant_id"]},'
                    f'{datetime.fromtimestamp(t["entry_ts"],tz=timezone.utc).isoformat()},'
                    f'{round(t["entry"],4)},{round(t["stop"],4)},{round(t["target"],4)},'
                    f'{datetime.fromtimestamp(t["exit_ts"],tz=timezone.utc).isoformat()},'
                    f'{round(t["exit_price"],4)},{round(t["close_R"],4)},'
                    f'{"winner" if t["close_R"]>0 else "loser"},{t["exit_reason"]},'
                    f'{d1a.get("d1a_pass")},{color}\n')
    (RESULTS / "mechanical_rebuild_v1_shift_audit.json").write_text(
        json.dumps(summary["shift_audit"], indent=2))

    print(json.dumps({"summary": {v: summary["variants"][v] for v in vids},
                      "shift_audit": summary["shift_audit"],
                      "rsi_coverage": summary["rsi_coverage"],
                      "bars_4h": summary["bars_4h"], "4h_range": summary["4h_range"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
