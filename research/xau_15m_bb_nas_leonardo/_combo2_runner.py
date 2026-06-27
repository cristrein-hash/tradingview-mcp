#!/usr/bin/env python3
"""combo2 family: run a batch of KEEP-expressions through filter_harness and print a compact table.
Saved (not inline) per repo discipline. Single source of truth for metrics = filter_harness.py.
Usage: python3 _combo2_runner.py   (edit EXPRS list below)"""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
HARNESS = HERE / "filter_harness.py"

EXPRS = [
    # range/chop AND extended
    "r['h1_eff']>=0.15 and r['leg_ext_atr']<=6",
    "r['h1_eff']>=0.15 and r['rsi']<=72",
    "r['h1_eff']>=0.15 and r['dist_ema_atr']<=4",
    "r['h1_eff']>=0.2 and r['leg_ext_atr']<=6",
    "r['h1_eff']>=0.15 and r['leg_ext_atr']<=5.5",
    # extended AND extended (clean sky + leg)
    "r['leg_ext_atr']<=6 and r['rsi']<=72",
    "r['leg_ext_atr']<=6 and r['dist_ema_atr']<=4",
    "r['leg_ext_atr']<=6 and r['room_above_atr']>=0.2",
    # bubble distribution AND extended
    "r['buy_bub_L_w24']<=2 and r['leg_ext_atr']<=6",
    "r['nas_short_w24']<=2 and r['h1_eff']>=0.15",
    "r['buy_bub_L_w24']<=2 and r['h1_eff']>=0.15",
    # range AND bubble
    "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=2",
    # chop + rsi top
    "r['h1_eff']>=0.15 and r['rsi']<=75",
    # leg + clean sky combined
    "r['leg_ext_atr']<=6 and r['room_above_atr']>=0.15",
]

def run(expr):
    out = subprocess.run([sys.executable, str(HARNESS), expr],
                         capture_output=True, text=True)
    try:
        d = json.loads(out.stdout)["FILTERED"]
    except Exception:
        return None
    return d

if __name__ == "__main__":
    extra = sys.argv[1:]
    exprs = extra if extra else EXPRS
    print(f"{'n':>4} {'wr':>5} {'sumr':>6} {'dd':>6} {'stk':>3} {'wlost':>5} {'bwlost':>6} {'lcut':>4} {'dWR':>5} {'dSumR':>6} {'dDD':>5}  expr")
    for e in exprs:
        d = run(e)
        if d is None:
            print(f"ERR  {e}"); continue
        print(f"{d['n']:>4} {d['wr']:>5} {d['sumr']:>6} {d['dd']:>6} {d['streak']:>3} "
              f"{d['winners_lost']:>5} {d['big_winners_lost']:>6} {d['losers_cut']:>4} "
              f"{d['dWR']:>5} {d['dSumR']:>6} {d['dDD']:>5}  {e}")
