#!/usr/bin/env python3
"""combo3: temporal robustness (by_year/by_block) for the top finalists + big-winner audit."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
HARNESS = str(HERE/"filter_harness.py")
ROWS = [json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines()]

def dedup(cands):
    byblk = {}
    for c in cands: byblk.setdefault(c["block"], []).append(c)
    taken = []
    for blk, cs in byblk.items():
        cs.sort(key=lambda x: x["cj"]); busy = -10**9
        for c in cs:
            if c["cj"] <= busy: continue
            busy = c["exi"]; taken.append(c)
    taken.sort(key=lambda x: x["t"]); return taken

# audit which big winners (R>=3) survive a filter
def keepfn(expr):
    return lambda r: eval(expr, {}, {"r": r})

FINALISTS = [
    "r['h1_eff']>=0.15 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<71",
    "r['h1_eff']>=0.15 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<70",
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<71",
    "r['h1_eff']>=0.14 and (r.get('rsi') or 0)<70 and (r.get('atr_regime') or 1)<2.0",
]

BASE = dedup(ROWS)
BIG = [c for c in BASE if c["R"] >= 3]
print("BIG winners in base (R>=3):", [(c["block"], round(c["R"],1)) for c in BIG])

for e in FINALISTS:
    print("\n#### ", e)
    out = subprocess.check_output([sys.executable, HARNESS, e, "--by"], text=True)
    j = json.loads(out)
    print("  by_year:", j.get("by_year"))
    print("  by_block:", j.get("by_block"))
    # which big winners survive
    fn = keepfn(e)
    kept = dedup([c for c in ROWS if fn(c)])
    kept_ids = {(c["block"], c["low_t"]) for c in kept}
    surv = [(c["block"], round(c["R"],1)) for c in BIG if (c["block"], c["low_t"]) in kept_ids]
    print("  BIG survivors:", surv)
