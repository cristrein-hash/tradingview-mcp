#!/usr/bin/env python3
"""backtest_xau_4h_breakout_continuation_v1.py — canonical real-R revalidation.

Reads ONLY:
  my-strategy/research/revalidation/XAUUSD_4H_BREAKOUT_CONTINUATION/v1/config.json
  + canonical 4H slim via build_crosstf_dataset.

Single official config (S_full_trend_htf, frozen). No sweep, no reconciliation
against trade-level legacy (CSV is aggregate-only). Produces trades.jsonl +
report.json + summary.md inside the v1 dir.

Strategy spec sources:
  my-strategy/research/experimental/xauusd_4h_long_breakout_continuation_regime_filtered.md
  my-strategy/pine_alerts/01_xauusd_4h_breakout_continuation.pine
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT_FILE = Path(__file__).resolve()
sys.path.insert(0, str(ROOT_FILE.parent))
from build_crosstf_dataset import (  # noqa: E402
    repo_root,
    load_tf,
    dedup_keep_last,
    add_close_epochs,
    iso,
)

ROOT = repo_root()
LAB = (
    ROOT
    / "my-strategy"
    / "research"
    / "revalidation"
    / "XAUUSD_4H_BREAKOUT_CONTINUATION"
    / "v1"
)
CONFIG_PATH = LAB / "config.json"
REGISTRY = ROOT / "docs" / "data" / "dataset_registry.json"


# ---------------------------------------------------------------------------
# Indicator computation (Python pure, no numpy required)
# ---------------------------------------------------------------------------


def ema_series(values, period):
    """Standard EMA, alpha = 2/(period+1). None-tolerant."""
    out = [None] * len(values)
    alpha = 2.0 / (period + 1)
    cur = None
    for i, v in enumerate(values):
        if v is None:
            continue
        if cur is None:
            cur = float(v)
        else:
            cur = alpha * float(v) + (1.0 - alpha) * cur
        out[i] = cur
    return out


def sma_series(values, period):
    """Rolling simple moving average over `period` non-null values."""
    out = [None] * len(values)
    buf = []
    for i, v in enumerate(values):
        if v is None:
            buf = []
            continue
        buf.append(float(v))
        if len(buf) > period:
            buf.pop(0)
        if len(buf) == period:
            out[i] = sum(buf) / period
    return out


def adx_wilder(highs, lows, closes, period=14):
    """Wilder's ADX(period). Returns list aligned to input length."""
    n = len(closes)
    tr = [None] * n
    dm_p = [None] * n
    dm_m = [None] * n
    for i in range(1, n):
        h, l = float(highs[i]), float(lows[i])
        pc = float(closes[i - 1])
        ph, pl = float(highs[i - 1]), float(lows[i - 1])
        tr[i] = max(h - l, abs(h - pc), abs(l - pc))
        up = h - ph
        dn = pl - l
        dm_p[i] = up if (up > dn and up > 0) else 0.0
        dm_m[i] = dn if (dn > up and dn > 0) else 0.0

    # Wilder-smoothed TR / DM
    s_tr = None
    s_dmp = None
    s_dmm = None
    di_p = [None] * n
    di_m = [None] * n
    dx = [None] * n
    for i in range(1, n):
        if tr[i] is None:
            continue
        if s_tr is None and i >= period:
            window_start = i - period + 1
            if all(tr[j] is not None for j in range(window_start, i + 1)):
                s_tr = sum(tr[window_start : i + 1])
                s_dmp = sum(dm_p[window_start : i + 1])
                s_dmm = sum(dm_m[window_start : i + 1])
        elif s_tr is not None:
            s_tr = s_tr - s_tr / period + tr[i]
            s_dmp = s_dmp - s_dmp / period + dm_p[i]
            s_dmm = s_dmm - s_dmm / period + dm_m[i]
        if s_tr is not None and s_tr > 0:
            di_p[i] = 100.0 * s_dmp / s_tr
            di_m[i] = 100.0 * s_dmm / s_tr
            denom = di_p[i] + di_m[i]
            if denom > 0:
                dx[i] = 100.0 * abs(di_p[i] - di_m[i]) / denom

    # ADX = Wilder smoothing of DX over `period`
    adx = [None] * n
    first_dx = next((i for i in range(n) if dx[i] is not None), None)
    if first_dx is not None:
        seed_end = first_dx + period - 1
        if seed_end < n and all(dx[j] is not None for j in range(first_dx, seed_end + 1)):
            cur = sum(dx[first_dx : seed_end + 1]) / period
            adx[seed_end] = cur
            for i in range(seed_end + 1, n):
                if dx[i] is None:
                    continue
                cur = (cur * (period - 1) + dx[i]) / period
                adx[i] = cur
    return adx


# ---------------------------------------------------------------------------
# Regime by entry year (per methodology table)
# ---------------------------------------------------------------------------


def regime_for(iso_str):
    try:
        y = int(iso_str[:4])
    except Exception:
        return "unknown"
    if y <= 2018:
        return "pre_covid"
    if y == 2019:
        return "bull_pre_covid"
    if y == 2020:
        return "covid_rally"
    if y == 2021:
        return "chop_post_covid"
    if y == 2022:
        return "chop_inflation_bear"
    if y == 2023:
        return "chop_macro"
    return "bull_recent"  # 2024-2026


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute everything but do not write outputs.")
    args = ap.parse_args()

    print(f"Reading config: {CONFIG_PATH.relative_to(ROOT)}")
    cfg = json.loads(CONFIG_PATH.read_text())
    assert cfg["strategy_id"] == "XAUUSD_4H_BREAKOUT_CONTINUATION"
    assert cfg["base_tf"] == "4H"
    assert cfg["direction"] == "long"

    sig = cfg["signal"]
    stop_cfg = cfg["stop"]
    spec = cfg["strategy_specific"]
    primary_r = cfg["targets"]["primary_r"]
    max_hold = cfg["time_limit_bars"]
    warmup = spec["warmup_bars"]

    print(f"Loading 4H canonical slim via registry...")
    reg = json.loads(REGISTRY.read_text())
    ext_root = Path(reg["_meta"]["external_root"])  # /Volumes/.../TradingData
    ext_parent = ext_root.parent  # /Volumes/...
    raw, reg_entries, _raw_paths = load_tf(reg, ext_parent, "4H")
    h4, _, _ = dedup_keep_last(raw)
    add_close_epochs(h4, "4H")
    n_bars = len(h4)
    print(f"  loaded {n_bars} bars  range {iso(h4[0]['bar_close_time'])} → {iso(h4[-1]['bar_close_time'])}")

    closes = [float(b["close"]) for b in h4]
    opens = [float(b["open"]) for b in h4]
    highs = [float(b["high"]) for b in h4]
    lows = [float(b["low"]) for b in h4]
    atrs = [
        float(b["atr14_wilder"]) if b.get("atr14_wilder") is not None else None
        for b in h4
    ]
    bodies = [
        float(b["body_pct"]) if b.get("body_pct") is not None else None
        for b in h4
    ]
    close_above_swing = [bool(b.get("close_above_swing_high_10")) for b in h4]
    rsi_above_ma = [bool(b.get("rsi_above_ma")) for b in h4]

    print("Computing EMA50, EMA200, ATR_MA20, ADX14...")
    ema50 = ema_series(closes, sig["filter_ema_fast"])
    ema200 = ema_series(closes, sig["filter_ema_slow"])
    atr_ma20 = sma_series(atrs, sig["filter_atr_ma_period"])
    adx14 = adx_wilder(highs, lows, closes, sig["filter_adx_min"] if False else 14)
    print("  ✓ computed")

    slope_lb = sig["filter_ema_slope_lookback"]
    adx_min = sig["filter_adx_min"]
    body_min = sig["trigger_body_pct_min"]
    stop_atr_mult = stop_cfg["stop_atr_mult"]
    sanity_atr_mult = stop_cfg["sanity_risk_max_atr_mult"]

    print("Scanning signals...")
    signals = []
    for i in range(warmup, n_bars):
        # Triggers
        if not close_above_swing[i]:
            continue
        if closes[i] <= opens[i]:
            continue
        if bodies[i] is None or bodies[i] < body_min:
            continue
        if not rsi_above_ma[i]:
            continue
        # Filters
        if adx14[i] is None or adx14[i] < adx_min:
            continue
        if ema200[i] is None or closes[i] <= ema200[i]:
            continue
        if ema50[i] is None or ema50[i] <= ema200[i]:
            continue
        if i < slope_lb or ema50[i - slope_lb] is None or ema50[i] <= ema50[i - slope_lb]:
            continue
        if atrs[i] is None or atr_ma20[i] is None or atrs[i] <= atr_ma20[i]:
            continue
        signals.append(i)
    print(f"  signals: {len(signals)}")

    print("Simulating trades (stop-first intrabar, BE at +1R, max_hold=24, no-overlap)...")
    trades = []
    last_exit_bar = -1
    for sb in signals:
        ei = sb + 1
        if ei >= n_bars:
            break
        if sb <= last_exit_bar:
            continue  # no overlap
        entry = opens[ei]
        atr = atrs[sb]
        stop = lows[sb] - stop_atr_mult * atr
        risk = entry - stop
        if risk <= 0 or risk > sanity_atr_mult * atr:
            continue
        target = entry + primary_r * risk
        be_threshold = entry + 1.0 * risk
        end_idx = min(ei + max_hold - 1, n_bars - 1)
        stop_actual = stop
        be_moved = False
        exit_reason = None
        exit_bar = None
        exit_price = None
        R = None
        for j in range(ei, end_idx + 1):
            # Stop-first: use current stop_actual (may have been moved at end of prior bar)
            if lows[j] <= stop_actual:
                R = round((stop_actual - entry) / risk, 4)
                exit_reason = "stop_be" if be_moved else "stop"
                exit_bar = j
                exit_price = stop_actual
                break
            if highs[j] >= target:
                R = float(primary_r)
                exit_reason = "target"
                exit_bar = j
                exit_price = target
                break
            # BE move: only at end of bar (after stop+target checks), so next bar uses moved stop
            if not be_moved and highs[j] >= be_threshold:
                stop_actual = entry
                be_moved = True
        else:
            # Time limit
            j = end_idx
            R = round((closes[j] - entry) / risk, 4)
            exit_reason = "time_limit"
            exit_bar = j
            exit_price = closes[j]
        # MFE / MAE over [ei..exit_bar]
        mfe_r = max((highs[k] - entry) / risk for k in range(ei, exit_bar + 1))
        mae_r = min((lows[k] - entry) / risk for k in range(ei, exit_bar + 1))
        right_censored = (
            exit_reason == "time_limit" and exit_bar == ei + max_hold - 1
        )
        sig_iso = iso(h4[sb]["bar_close_time"])
        trade = {
            "strategy_id": "XAUUSD_4H_BREAKOUT_CONTINUATION",
            "config_id": spec["filter_set_id"],
            "stop_variant": stop_cfg["primary"],
            "direction": "LONG",
            "signal_bar": sb,
            "signal_iso": sig_iso,
            "entry_bar": ei,
            "entry_iso": iso(h4[ei]["bar_close_time"]),
            "exit_bar": exit_bar,
            "exit_iso": iso(h4[exit_bar]["bar_close_time"]),
            "entry_price": round(entry, 4),
            "stop_price": round(stop, 4),
            "target_price_primary": round(target, 4),
            "exit_price": round(exit_price, 4),
            "atr14": round(atr, 4),
            "risk": round(risk, 4),
            "R_multiple": R,
            "MFE_R": round(mfe_r, 4),
            "MAE_R": round(mae_r, 4),
            "exit_reason": exit_reason,
            "be_moved": be_moved,
            "right_censored": right_censored,
            "regime": regime_for(sig_iso),
            "registry_entry": h4[sb].get("registry_entry"),
        }
        trades.append(trade)
        last_exit_bar = exit_bar

    print(f"  trades: {len(trades)}")

    # Aggregate
    n = len(trades)
    Rs = [t["R_multiple"] for t in trades]
    win = sum(1 for r in Rs if r > 0)
    avg_R = sum(Rs) / n if n else 0.0
    total_R = sum(Rs)
    wins = [r for r in Rs if r > 0]
    losses = [r for r in Rs if r < 0]
    pf = (sum(wins) / abs(sum(losses))) if losses else (None if not wins else float("inf"))
    exit_mix = {}
    for t in trades:
        exit_mix[t["exit_reason"]] = exit_mix.get(t["exit_reason"], 0) + 1
    by_regime = {}
    for t in trades:
        r = t["regime"]
        if r not in by_regime:
            by_regime[r] = {"n": 0, "R": 0.0, "win": 0}
        by_regime[r]["n"] += 1
        by_regime[r]["R"] += t["R_multiple"]
        if t["R_multiple"] > 0:
            by_regime[r]["win"] += 1
    for r in by_regime:
        d = by_regime[r]
        d["avg_R"] = round(d["R"] / d["n"], 4)
        d["win_rate"] = round(d["win"] / d["n"], 4)
        d["R"] = round(d["R"], 4)

    report = {
        "strategy_id": "XAUUSD_4H_BREAKOUT_CONTINUATION",
        "version": "v1",
        "config_id": spec["filter_set_id"],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "method": "replay_real_rt_canonical_slim",
        "data_source": str(ext_root),
        "h4_bars_loaded": n_bars,
        "first_bar_iso": iso(h4[0]["bar_close_time"]),
        "last_bar_iso": iso(h4[-1]["bar_close_time"]),
        "warmup_bars": warmup,
        "signals_count": len(signals),
        "trades_count": n,
        "win_rate": round(win / n, 4) if n else 0.0,
        "avg_R": round(avg_R, 4),
        "total_R": round(total_R, 4),
        "pf": round(pf, 4) if isinstance(pf, float) and pf != float("inf") else (None if pf is None else "inf"),
        "exit_reasons": exit_mix,
        "be_moved_count": sum(1 for t in trades if t["be_moved"]),
        "right_censored_count": sum(1 for t in trades if t["right_censored"]),
        "by_regime": by_regime,
        "legacy_aggregate_comparison": {
            "legacy_n": 234,
            "legacy_pf": 1.64,
            "legacy_win_rate": 0.286,
            "legacy_total_net_r": 64.57,
            "note": "Aggregate-vs-aggregate informational comparison only — legacy lacks trade-level dump.",
        },
        "primary_r": primary_r,
        "max_hold_bars": max_hold,
    }

    if args.dry_run:
        print("\n[dry-run] skipping writes")
        print(json.dumps(report, indent=2, default=str))
        return 0

    out_trades = LAB / "trades.jsonl"
    out_report = LAB / "report.json"
    out_summary = LAB / "summary.md"

    with open(out_trades, "w", encoding="utf-8") as fh:
        for t in trades:
            fh.write(json.dumps(t) + "\n")
    print(f"  wrote {out_trades.relative_to(ROOT)}")

    with open(out_report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(f"  wrote {out_report.relative_to(ROOT)}")

    with open(out_summary, "w", encoding="utf-8") as fh:
        fh.write(render_summary(report))
    print(f"  wrote {out_summary.relative_to(ROOT)}")

    print("\nDONE.")
    return 0


def render_summary(r):
    lines = []
    lines.append(f"# XAUUSD 4H BREAKOUT_CONTINUATION v1 — Revalidation Summary\n")
    lines.append(f"- Generated: {r['generated_at']}")
    lines.append(f"- git: {r['git_commit'][:12]}")
    lines.append(
        f"- Data: canonical 4H slim · {r['h4_bars_loaded']} bars · "
        f"{r['first_bar_iso'][:10]} → {r['last_bar_iso'][:10]}"
    )
    lines.append(f"- Method: {r['method']}")
    lines.append(f"- Config: {r['config_id']}")
    lines.append(f"- Primary target: {r['primary_r']}R · max_hold: {r['max_hold_bars']} bars")
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| signals | {r['signals_count']} |")
    lines.append(f"| trades | {r['trades_count']} |")
    lines.append(f"| win_rate | {r['win_rate']:.4f} |")
    lines.append(f"| avg_R | {r['avg_R']:+.4f} |")
    lines.append(f"| total_R | {r['total_R']:+.4f} |")
    lines.append(f"| PF | {r['pf']} |")
    lines.append(f"| BE moves | {r['be_moved_count']} |")
    lines.append(f"| right-censored | {r['right_censored_count']} |")
    lines.append("")
    lines.append("## Exit reasons")
    lines.append("")
    for k, v in r["exit_reasons"].items():
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## By regime")
    lines.append("")
    lines.append("| regime | n | win_rate | avg_R | total_R |")
    lines.append("|---|---:|---:|---:|---:|")
    for rg, d in r["by_regime"].items():
        lines.append(
            f"| {rg} | {d['n']} | {d['win_rate']:.4f} | "
            f"{d['avg_R']:+.4f} | {d['R']:+.4f} |"
        )
    lines.append("")
    lines.append("## Legacy aggregate comparison (informational)")
    lines.append("")
    lc = r["legacy_aggregate_comparison"]
    lines.append(
        f"- legacy: n={lc['legacy_n']}, pf={lc['legacy_pf']}, "
        f"win={lc['legacy_win_rate']}, total_net_r={lc['legacy_total_net_r']}"
    )
    lines.append(
        f"- canonical v1: n={r['trades_count']}, pf={r['pf']}, "
        f"win={r['win_rate']:.4f}, total_R={r['total_R']:+.4f}"
    )
    lines.append(f"- _note_: {lc['note']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
