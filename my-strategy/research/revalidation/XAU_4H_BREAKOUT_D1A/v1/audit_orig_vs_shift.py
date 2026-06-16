#!/usr/bin/env python3
"""ORIG-vs-SHIFT alignment audit for XAU_4H_BREAKOUT_D1A (D1a).

Proves empirically that the production-style daily selector (open_time < bar_time)
LEAKS the same-session forming daily for intraday 4H bars in a backtest, while the
CAUSAL selector (daily.close_time <= bar_open) never uses a forming daily.

READ-ONLY: streams RAW 4H replay .gz to collect real 4H bar OPEN times; loads the
derived EMA1D dataset. No backtest, no trades, no RAW mutation.

  SUSPECT/ORIG  : latest daily with daily.open_time  < bar_open   (prod-style t<bar_time)
  CAUSAL/SHIFT  : latest daily with daily.close_time <= bar_open   (fully closed before bar)
  LEAK          : ORIG selects a daily whose close_time > bar_open  (still forming)
"""
import gzip
import json
import bisect
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = HERE / "generated"
EMA = GEN / "xau_1d_ema_features.jsonl"
OUT = GEN / "orig_vs_shift_audit.json"
RAW_4H_DIR = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/")
RAW_4H_BLOCKS = [
    "XAUUSD_240m_replay_2016-05-25_to_2020-01-01.jsonl.gz",
    "XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",
    "XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz",
]
BAR_4H_SEC = 4 * 3600


def collect_4h_open_times():
    times = set()
    for blk in RAW_4H_BLOCKS:
        p = RAW_4H_DIR / blk
        if not p.exists():
            continue
        with gzip.open(p, "rt") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                for b in (rec.get("ohlcv") or []):
                    t = b.get("time")
                    if t is not None:
                        times.add(int(t))
    return sorted(times)


def load_daily():
    rows = [json.loads(l) for l in EMA.read_text().splitlines() if l.strip()]
    rows.sort(key=lambda r: r["open_time"])
    return rows


def main():
    daily = load_daily()
    d_open = [r["open_time"] for r in daily]
    d_close = [r["close_time"] for r in daily]
    # for CAUSAL we need daily sorted by close_time (it is monotonic with open_time here)
    bars = collect_4h_open_times()

    def orig_idx(bar_open):
        # latest daily with open_time < bar_open
        i = bisect.bisect_left(d_open, bar_open) - 1
        return i if i >= 0 else None

    def causal_idx(bar_open):
        # latest daily with close_time <= bar_open
        i = bisect.bisect_right(d_close, bar_open) - 1
        return i if i >= 0 else None

    total = 0
    orig_leak = 0          # ORIG picked a daily still forming at bar_open (close_time > bar_open)
    same_picked = 0        # ORIG and CAUSAL picked the same daily
    diff_d1a = 0           # d1a_pass differs between ORIG and CAUSAL selection
    diff_close_gt = 0
    diff_ema_gt = 0
    orig_none = causal_none = 0
    leak_examples = []
    for bo in bars:
        oi = orig_idx(bo)
        ci = causal_idx(bo)
        total += 1
        if oi is None:
            orig_none += 1
        if ci is None:
            causal_none += 1
        if oi is not None:
            # leak if the ORIG-selected daily has not closed yet at bar_open
            if d_close[oi] > bo:
                orig_leak += 1
        if oi is not None and ci is not None:
            if oi == ci:
                same_picked += 1
            else:
                ro, rc = daily[oi], daily[ci]
                if ro["d1a_pass"] != rc["d1a_pass"]:
                    diff_d1a += 1
                if ro["close_gt_ema200"] != rc["close_gt_ema200"]:
                    diff_close_gt += 1
                if ro["ema50_gt_ema200"] != rc["ema50_gt_ema200"]:
                    diff_ema_gt += 1
                if len(leak_examples) < 8 and d_close[oi] > bo:
                    bdt = datetime.fromtimestamp(bo, tz=timezone.utc)
                    leak_examples.append({
                        "bar_4h_open": bdt.isoformat(),
                        "orig_picked_date": ro["date"], "orig_closes": datetime.fromtimestamp(d_close[oi], tz=timezone.utc).isoformat(),
                        "orig_still_forming_at_bar": True,
                        "causal_picked_date": rc["date"],
                        "orig_d1a": ro["d1a_pass"], "causal_d1a": rc["d1a_pass"],
                    })

    # Edge cases at fixed hours on a normal week + weekend + dataset bounds
    def pick_bar_on(date_str, hour):
        target = int(datetime(*map(int, date_str.split("-")), hour, tzinfo=timezone.utc).timestamp())
        # nearest actual 4H bar with that open
        i = bisect.bisect_left(bars, target)
        for j in (i, i - 1, i + 1):
            if 0 <= j < len(bars) and datetime.fromtimestamp(bars[j], tz=timezone.utc).hour == hour and \
               datetime.fromtimestamp(bars[j], tz=timezone.utc).strftime("%Y-%m-%d") == date_str:
                return bars[j]
        return None

    edge = []
    # Actual 4H grid for the contiguous 240m blocks = 02/06/10/14/18/22 UTC.
    # Mon 2024-05-13 (after weekend) across the day + Tue 2024-05-14 spot checks.
    edge_specs = [
        ("2024-05-13", 2), ("2024-05-13", 6), ("2024-05-13", 10),
        ("2024-05-13", 14), ("2024-05-13", 18), ("2024-05-13", 22),
        ("2024-05-14", 2),  # Tue 02:00
    ]
    for ds, hr in edge_specs:
        bo = pick_bar_on(ds, hr)
        if bo is None:
            edge.append({"req": f"{ds} {hr:02d}:00", "found": False})
            continue
        oi, ci = orig_idx(bo), causal_idx(bo)
        bdt = datetime.fromtimestamp(bo, tz=timezone.utc)
        edge.append({
            "bar_4h_open": bdt.isoformat() + f" ({bdt.strftime('%a')})",
            "orig_daily": daily[oi]["date"] if oi is not None else None,
            "orig_closes": datetime.fromtimestamp(d_close[oi], tz=timezone.utc).isoformat() if oi is not None else None,
            "orig_leak": (oi is not None and d_close[oi] > bo),
            "causal_daily": daily[ci]["date"] if ci is not None else None,
            "causal_d1a": daily[ci]["d1a_pass"] if ci is not None else None,
        })
    # dataset bounds
    for label, bo in [("first_4h_bar", bars[0]), ("last_4h_bar", bars[-1])]:
        oi, ci = orig_idx(bo), causal_idx(bo)
        bdt = datetime.fromtimestamp(bo, tz=timezone.utc)
        edge.append({"edge": label, "bar_4h_open": bdt.isoformat(),
                     "orig_daily": daily[oi]["date"] if oi is not None else None,
                     "causal_daily": daily[ci]["date"] if ci is not None else None,
                     "causal_none": ci is None})

    summary = {
        "total_4h_bars": total,
        "4h_range": [datetime.fromtimestamp(bars[0], tz=timezone.utc).isoformat(),
                     datetime.fromtimestamp(bars[-1], tz=timezone.utc).isoformat()],
        "orig_leak_count": orig_leak,
        "orig_leak_pct": round(100 * orig_leak / total, 2) if total else None,
        "same_daily_picked": same_picked,
        "differ_selection": total - same_picked - max(orig_none, causal_none),
        "d1a_pass_divergences": diff_d1a,
        "close_gt_ema200_divergences": diff_close_gt,
        "ema50_gt_ema200_divergences": diff_ema_gt,
        "orig_none": orig_none, "causal_none": causal_none,
        "leak_examples": leak_examples,
        "edge_cases": edge,
    }
    OUT.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
