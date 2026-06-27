#!/usr/bin/env python3
"""combo3: LOO on the atr_regime variant (h1_eff + rsi + atr_regime)."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
HARNESS = str(HERE/"filter_harness.py")
LOO = {
    "FULL":            "r['h1_eff']>=0.14 and (r.get('rsi') or 0)<70 and (r.get('atr_regime') or 1)<2.0",
    "drop h1_eff":     "(r.get('rsi') or 0)<70 and (r.get('atr_regime') or 1)<2.0",
    "drop rsi":        "r['h1_eff']>=0.14 and (r.get('atr_regime') or 1)<2.0",
    "drop atr_regime": "r['h1_eff']>=0.14 and (r.get('rsi') or 0)<70",
}
def run(expr):
    return json.loads(subprocess.check_output([sys.executable, HARNESS, expr], text=True))["FILTERED"]
print(f"{'variant':16s} {'n':>4} {'wr':>5} {'dWR':>5} {'sumr':>6} {'dSumR':>6} {'dd':>6} {'dDD':>5} {'lc':>3} {'bwl':>3}")
for k, e in LOO.items():
    f = run(e)
    print(f"{k:16s} {f['n']:>4} {f['wr']:>5} {f['dWR']:>5} {f['sumr']:>6} {f['dSumR']:>6} {f['dd']:>6} {f['dDD']:>5} {f['losers_cut']:>3} {f['big_winners_lost']:>3}")
