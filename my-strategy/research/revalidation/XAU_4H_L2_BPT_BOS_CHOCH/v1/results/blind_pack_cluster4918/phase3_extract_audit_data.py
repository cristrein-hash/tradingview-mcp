#!/usr/bin/env python3
"""
Phase-3 audit data extractor (read-only).
Pulls (a) uncapped outcomes per episode and (b) real price path ~10-40 bars
after entry, to compare the FROZEN reader dossier vs reality.

SANITY_PROBE: not a single-axis static test — per-episode comparison of a frozen
multi-factor reading against realized outcome + price path. Diagnostic of reading
QUALITY, NOT a gate/hit-rate for promotion.

Verified at: 2026-06-23
"""
import csv, json, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", ".."))  # .../v1/results -> .../v1
V1 = os.path.abspath(os.path.join(BASE, "..", ".."))     # blind_pack -> results -> v1
OUTCOMES = os.path.join(V1, "results", "l2_bpt_uncapped_or_proxy_outcomes_276.csv")
JSONL = os.path.join(V1, "repro_recovery", "raw_features_2020_2026.jsonl")

EPISODES = [1661, 4918, 5701, 6887, 7426, 8878, 8923, 8940, 4926]


def load_outcomes():
    tg = set(EPISODES)
    with open(OUTCOMES) as f:
        r = csv.DictReader(f)
        return {int(row["bar_idx"]): row for row in r if int(row["bar_idx"]) in tg}


def load_bars():
    bars = []
    with open(JSONL) as f:
        for line in f:
            line = line.strip()
            if line:
                bars.append(json.loads(line))
    return bars


def main():
    outcomes = load_outcomes()
    bars = load_bars()
    print(f"# total bars in jsonl: {len(bars)}")
    print()

    for bi in EPISODES:
        o = outcomes.get(bi)
        print("=" * 70)
        print(f"EPISODE bar_idx={bi}")
        if o:
            print(f"  outcome: dt={o['datetime']} mfe_R={o['mfe_R']} mae_R={o['mae_R']} "
                  f"mae_before_mfe={o['mae_before_mfe']} capped_realR={o['capped_realR']} "
                  f"exit={o['capped_exitype']} bucket={o['runner_bucket']} "
                  f"hit5={o['hit5']} hit10={o['hit10']} risk_atr={o['risk_atr']} "
                  f"time_to_2R={o['time_to_2R']} stop_before_2R={o['stop_before_2R']}")
        else:
            print("  outcome: NOT FOUND")
        # entry bar = bars[bi]; show entry + next 40 bars OHLC
        if bi < len(bars):
            entry = bars[bi]
            ec = entry.get("close")
            print(f"  entry bar OHLC: o={entry.get('open')} h={entry.get('high')} "
                  f"l={entry.get('low')} c={entry.get('close')} ts={entry.get('ts_epoch')}")
            # path stats over next N bars
            for N in (10, 20, 40):
                seg = bars[bi+1: bi+1+N]
                if not seg:
                    continue
                hh = max(b["high"] for b in seg)
                ll = min(b["low"] for b in seg)
                lastc = seg[-1]["close"]
                print(f"  next {N:>2} bars: maxHigh={hh:.2f} minLow={ll:.2f} "
                      f"lastClose={lastc:.2f} "
                      f"(vs entryClose {ec:.2f}: upMove={hh-ec:+.2f} dnMove={ll-ec:+.2f})")
            # detailed first 16 bars
            print("  first 16 post-entry bars (idx,o,h,l,c):")
            for k, b in enumerate(bars[bi+1: bi+1+16], start=1):
                print(f"    +{k:>2} o={b['open']:.2f} h={b['high']:.2f} "
                      f"l={b['low']:.2f} c={b['close']:.2f}")
        else:
            print("  bar index out of range")
        print()


if __name__ == "__main__":
    main()
