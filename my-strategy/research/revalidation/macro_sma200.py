#!/usr/bin/env python3
"""
LENS sma200 — classic Faber-style long SMA macro trend lens.

Idea (from scratch, no old machinery):
  Compute a simple moving average (SMA) of the daily close over a long window.
  For each day i (CAUSAL, close-only: only bars <= i, own close allowed):
    - BULL  if close[i] > SMA[i]  AND  SMA rising  (SMA[i] > SMA[i-slope_win])
    - BEAR  if close[i] < SMA[i]  AND  SMA falling (SMA[i] < SMA[i-slope_win])
    - RANGE otherwise (price/slope disagree, or not enough history)

Grid (closed, <=6 configs): SMA in {150,200,250} x slope_win in {20,40} days.
No hysteresis variant added (grid already fills the 6-config budget).
No metrics vs GT computed here.
"""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "raw_1d_ohlc.jsonl")
OUT_DIR = os.path.join(BASE, "results")
OUT = os.path.join(OUT_DIR, "macro_sma200_labels.json")

# Closed grid (max 6 configs)
SMA_LENS = [150, 200, 250]
SLOPE_WINS = [20, 40]


def load_closes(path):
    closes = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            bar = json.loads(line)
            closes.append(float(bar["c"]))
    return closes


def sma_causal(closes, i, n):
    """SMA over the last n closes up to and including day i (causal).
    Returns None if fewer than n bars available."""
    if i - n + 1 < 0:
        return None
    window = closes[i - n + 1: i + 1]
    return sum(window) / n


def label_config(closes, sma_len, slope_win):
    N = len(closes)
    # Precompute causal SMA series (None where insufficient history)
    sma = [sma_causal(closes, i, sma_len) for i in range(N)]
    labels = []
    for i in range(N):
        s_now = sma[i]
        s_prev = sma[i - slope_win] if i - slope_win >= 0 else None
        if s_now is None or s_prev is None:
            labels.append("RANGE")
            continue
        c = closes[i]
        rising = s_now > s_prev
        falling = s_now < s_prev
        if c > s_now and rising:
            labels.append("BULL")
        elif c < s_now and falling:
            labels.append("BEAR")
        else:
            labels.append("RANGE")
    return labels


def main():
    closes = load_closes(RAW)
    N = len(closes)
    assert N == 2982, f"expected 2982 bars, got {N}"

    configs = []
    cid = 0
    for sma_len in SMA_LENS:
        for slope_win in SLOPE_WINS:
            cid += 1
            labels = label_config(closes, sma_len, slope_win)
            assert len(labels) == N, f"label length mismatch: {len(labels)}"
            assert all(x in ("BULL", "BEAR", "RANGE") for x in labels)
            configs.append({
                "id": f"c{cid}",
                "params": f"sma{sma_len}_slope{slope_win}",
                "labels": labels,
            })

    assert len(configs) <= 6, f"too many configs: {len(configs)}"

    out = {"lens": "sma200", "configs": configs}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f)

    # Console summary only (no GT metrics)
    for cfg in configs:
        labs = cfg["labels"]
        b = labs.count("BULL")
        r = labs.count("RANGE")
        be = labs.count("BEAR")
        print(f"{cfg['id']} {cfg['params']}: BULL={b} BEAR={be} RANGE={r} "
              f"last={labs[-1]}")
    print(f"Wrote {OUT} with {len(configs)} configs, {N} labels each.")


if __name__ == "__main__":
    main()
