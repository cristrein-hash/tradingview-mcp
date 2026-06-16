#!/usr/bin/env python3
"""Build causal EMA50/EMA200 daily features for XAU_4H_BREAKOUT_D1A (D1a).

READ-ONLY w.r.t. RAW: streams the RAW 1D replay .gz, reconstructs the clean
daily OHLCV series (union of all snapshot ohlcv windows, dedup by `time`,
keep-last = finalized close), computes EMA50/EMA200 (alpha=2/(p+1), adjust=False
recursive seeded by close[0]) with warmup from 2012, and emits a derived dataset
under research/revalidation/.../v1/generated/.

D1a predicate (per gate_manifest §4): close_1D > EMA200_1D AND EMA50_1D > EMA200_1D.
NOT a backtest. No trades. No 4H join here (the alignment audit is separate).
NO RAW mutation. Output is clearly a derived research artifact.

Usage:
  python3 build_xau_1d_ema_features.py            # builds + validates + writes
"""
import gzip
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = HERE / "generated"
OUT = GEN / "xau_1d_ema_features.jsonl"
RAW_1D = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1D/"
              "XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz")
REF_DAILY = HERE.parent.parent.parent.parent / "core/regime_l1/xau_daily_l1v4.jsonl"
CALC_VERSION = "ema1d_v1_2026-06-16"


def reconstruct_daily(gz_path):
    """Union all snapshot ohlcv bars, dedup by `time` keeping last-seen (finalized)."""
    bars = {}  # time -> bar dict
    n_records = 0
    with gzip.open(gz_path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            n_records += 1
            for b in (rec.get("ohlcv") or []):
                t = b.get("time")
                if t is None or b.get("close") is None:
                    continue
                bars[t] = b  # keep last-seen (later snapshot = finalized close)
    series = sorted(bars.values(), key=lambda b: b["time"])
    return series, n_records


def ema(values, period):
    """Standard EMA, alpha=2/(period+1), adjust=False, seeded by values[0]."""
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


def build():
    series, n_records = reconstruct_daily(RAW_1D)
    closes = [b["close"] for b in series]
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    n = len(series)
    rows = []
    for i, b in enumerate(series):
        open_time = b["time"]                      # RAW bar.time = session OPEN (unix, UTC, 22:00)
        # Each gold daily candle is 24h: a candle opening 22:00 UTC on day D closes
        # 22:00 UTC on day D+1 and represents trading day D+1. close_time = open + 86400
        # (NOT next_open: next_open jumps the weekend for the Friday candle -> mislabel).
        close_time = open_time + 86400
        approx = (i + 1 >= n)                       # last bar: no successor to cross-check
        open_dt = datetime.fromtimestamp(open_time, tz=timezone.utc)
        close_dt = datetime.fromtimestamp(close_time, tz=timezone.utc)
        # session_date = calendar date of the CLOSE = trading day (matches production labeling).
        session_date = close_dt.strftime("%Y-%m-%d")
        e50, e200 = ema50[i], ema200[i]
        warmup_ready = i >= 200                     # EMA200 reliable after >=200 bars
        e50_gt = (e50 is not None and e200 is not None and e50 > e200)
        c_gt = (e200 is not None and b["close"] > e200)
        rows.append({
            "date": session_date,
            "ts": open_dt.isoformat(),
            "open_time": open_time,
            "close_time": close_time,
            "close_time_approx": approx,
            "open": b["open"], "high": b["high"], "low": b["low"], "close": b["close"],
            "volume": b.get("volume"),
            "ema50": round(e50, 6) if e50 is not None else None,
            "ema200": round(e200, 6) if e200 is not None else None,
            "ema50_gt_ema200": bool(e50_gt),
            "close_gt_ema200": bool(c_gt),
            "d1a_pass": bool(e50_gt and c_gt and warmup_ready),
            "warmup_ready": bool(warmup_ready),
            "source_raw_path": str(RAW_1D),
            "calculation_version": CALC_VERSION,
        })
    return rows, n_records


def validate_against_ref(rows):
    """Sanity: reconstructed close must match the production daily file on overlap."""
    if not REF_DAILY.exists():
        return {"ref_available": False}
    ref = {}
    for l in REF_DAILY.read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            ref[r["ts"]] = r["close"]
    by_date = {r["date"]: r for r in rows}
    overlap = 0
    w05 = w2 = w5 = 0  # within 0.5 / 2.0 / 5.0 USD
    worst = 0.0
    diffs = []
    examples = []
    for d, c in ref.items():
        if d in by_date:
            g = by_date[d]["close"]
            diff = abs(g - c)
            overlap += 1
            diffs.append(diff)
            worst = max(worst, diff)
            if diff <= 0.5:
                w05 += 1
            if diff <= 2.0:
                w2 += 1
            if diff <= 5.0:
                w5 += 1
            elif len(examples) < 5:
                examples.append({"date": d, "ref": c, "built": g, "diff": round(diff, 4)})
    diffs.sort()
    median = diffs[len(diffs) // 2] if diffs else None
    return {"ref_available": True, "overlap": overlap,
            "within_0.5": w05, "within_2.0": w2, "within_5.0": w5,
            "pct_within_2.0": round(100 * w2 / overlap, 1) if overlap else None,
            "median_diff": round(median, 4) if median is not None else None,
            "worst_diff": round(worst, 4),
            "note": "RAW replay vs MCP-derived production daily; small diffs = session/vintage, not labeling. RAW is source-of-truth (project_authority/02).",
            "examples_over_5": examples}


def main():
    GEN.mkdir(parents=True, exist_ok=True)
    rows, n_records = build()
    val = validate_against_ref(rows)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    first_warm = next((r["date"] for r in rows if r["warmup_ready"]), None)
    summary = {
        "output": str(OUT),
        "lines": len(rows),
        "sha256": sha,
        "raw_records_read": n_records,
        "date_range": [rows[0]["date"], rows[-1]["date"]] if rows else None,
        "first_warmup_ready_date": first_warm,
        "d1a_pass_count": sum(1 for r in rows if r["d1a_pass"]),
        "ref_validation": val,
        "calculation_version": CALC_VERSION,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
