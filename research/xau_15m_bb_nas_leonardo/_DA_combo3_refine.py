#!/usr/bin/env python3
"""combo3 refine: tune around the leader h1_eff + nas_short_w24 + rsi (and variants)."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
HARNESS = str(HERE/"filter_harness.py")

CANDS = [
    # leader and neighbors
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<70",
    "r['h1_eff']>=0.15 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<70",
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<69",
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<71",
    "r['h1_eff']>=0.13 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<70",
    "r['h1_eff']>=0.16 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<70",
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<1 and (r.get('rsi') or 0)<70",
    # swap rsi for dist_demand (both top/extension flavored)
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('dist_demand_atr') or 0)<=2.5",
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('dist_demand_atr') or 0)<=3.0",
    # add atr_regime cap (avoid volatile blowoff)
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('atr_regime') or 1)<2.0",
    # 4th flavor: h1_eff + rsi + atr_regime (drop nas)
    "r['h1_eff']>=0.14 and (r.get('rsi') or 0)<70 and (r.get('atr_regime') or 1)<2.0",
    # h1_eff stronger + rsi only mild + nas
    "r['h1_eff']>=0.15 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<71",
    # nas_short_leg variant
    "r['h1_eff']>=0.14 and (r.get('nas_short_leg') or 0)<4 and (r.get('rsi') or 0)<70",
    # disp4 instead of rsi
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('disp4_atr') or 0)<3.5",
]

def run(expr):
    out = subprocess.check_output([sys.executable, HARNESS, expr], text=True)
    return json.loads(out)["FILTERED"]

print(f"{'expr':74s} {'n':>4} {'wr':>5} {'dWR':>5} {'sumr':>6} {'dSumR':>6} {'dd':>6} {'dDD':>5} {'lc':>3} {'wl':>3} {'bwl':>3} {'stk':>3}")
for e in CANDS:
    f = run(e)
    print(f"{e[:74]:74s} {f['n']:>4} {f['wr']:>5} {f['dWR']:>5} {f['sumr']:>6} {f['dSumR']:>6} {f['dd']:>6} {f['dDD']:>5} {f['losers_cut']:>3} {f['winners_lost']:>3} {f['big_winners_lost']:>3} {f['streak']:>3}")
