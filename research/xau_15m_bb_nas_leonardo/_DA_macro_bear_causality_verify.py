#!/usr/bin/env python3
"""DA: verify macro_bear in filter_dataset is AS-OF (no repaint): for each candidate, recompute
macro_at(tc) directly from macro_regime_4h.json using bisect_right(t_end, tc)-1 and confirm it
matches the stored macro_bear/macro_bull. Also confirm the chosen 4H bar's t_end <= tc strictly
(only CLOSED 4H bars) and that the entry tc falls AFTER that bar closed. 2026-06-27."""
import json, bisect
from pathlib import Path
HERE = Path(__file__).parent
MR = json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]
MEND = [b["t_end"] for b in MR]

def macro_at(t):
    k = bisect.bisect_right(MEND, t) - 1
    return (MR[k]["macro"] if k >= 0 else "WARMUP"), k

rows = [json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines()]
mism = 0; closed_ok = 0; total = 0
worst_lag = 1e18; min_lag = 1e18
for r in rows:
    tc = r["t"]
    m, k = macro_at(tc)
    stored = "BEAR" if r["macro_bear"]==1 else ("BULL" if r["macro_bull"]==1 else "NEUTRAL")
    if m != stored:
        mism += 1
        if mism <= 5: print(f"  MISMATCH tc={tc} recomputed={m} stored={stored}")
    total += 1
    if k >= 0:
        bar_end = MR[k]["t_end"]
        if bar_end <= tc:
            closed_ok += 1
            min_lag = min(min_lag, tc - bar_end)   # how far after 4H close is the entry
        else:
            print(f"  LEAK: bar t_end={bar_end} > tc={tc}")
print(f"\nrows={total} | macro recompute mismatches={mism} | closed-bar-only(t_end<=tc)={closed_ok}")
print(f"min lag tc-bar_end = {min_lag}s ({min_lag/60:.1f} min) -> if >=0, entry consumes only a CLOSED 4H bar")
# show the bisect_right boundary semantics: a candidate whose tc == some t_end uses that bar (just closed) — still causal
print("\nNote: bisect_right(MEND,tc)-1 selects the LAST bar with t_end <= tc, i.e. the most recent CLOSED 4H bar.")
print("The in-progress 4H bar (t_end > tc) is never selected -> no repaint of the label using future 4H data.")
