#!/usr/bin/env python3
"""Combo search wrapper around filter_harness.py for XAU 15M LONG scalp filter.
Runs a list of KEEP_EXPR through the harness and prints a compact one-line summary
per candidate. Single source of truth for metrics = filter_harness.py.
"""
import subprocess, json, sys, os

HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "filter_harness.py")

CANDIDATES = [
    "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=3",
    "r['h1_eff']>=0.15 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<71",
    "r['h1_eff']>=0.15 and r['buy_bub_L_w24']<=3 and r['dist_ema_atr']<=4",
    "r['h1_eff']>=0.16",
    "r['h1_eff']>=0.17",
    "r['h1_eff']>=0.15 and (r.get('room_above_atr') or 99)>=1",
    "r['h1_eff']>=0.15 and (r.get('rsi') or 0)<71",
    "r['h1_eff']>=0.15 and (r.get('nas_short_w24') or 0)<2",
    "r['h1_eff']>=0.15 and (r.get('rsi') or 0)<72 and r['buy_bub_L_w24']<=3",
    "r['h1_eff']>=0.15 and (r.get('h1_pos') or 0)<0.95",
    "r['h1_eff']>=0.15 and (r.get('nas_short_w24') or 0)<2 and r['buy_bub_L_w24']<=4",
]

def run(expr):
    out = subprocess.run([sys.executable, HARNESS, expr], capture_output=True, text=True)
    d = json.loads(out.stdout)
    f = d["FILTERED"]
    return (f"WR={f['wr']} dWR={f['dWR']} dDD={f['dDD']} dSumR={f['dSumR']} "
            f"n={f['n']} lc={f['losers_cut']} wl={f['winners_lost']} bwl={f['big_winners_lost']} "
            f"streak={f['streak']} | {expr}")

if __name__ == "__main__":
    exprs = [sys.argv[1]] if len(sys.argv) > 1 else CANDIDATES
    for e in exprs:
        print(run(e))
