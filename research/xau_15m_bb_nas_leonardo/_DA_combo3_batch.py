#!/usr/bin/env python3
"""combo3 family: batch-run candidate KEEP filters through filter_harness and tabulate.
Reproducible: shells out to filter_harness.py (single source of truth for metrics)."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
HARNESS = str(HERE/"filter_harness.py")

CANDS = [
    # --- singles (sanity / component selection) ---
    "r['h1_eff']>=0.12",
    "(r.get('nas_short_w24') or 0)<2",
    "(r.get('regime_age_h') or 0)>=10",
    "(r.get('dist_demand_atr') or 0)<=2.0",
    "(r.get('nas_short_leg') or 0)<5",
    # --- 3-feature combos: chop + top-distribution + extension/context ---
    "r['h1_eff']>=0.12 and (r.get('nas_short_w24') or 0)<2 and (r.get('dist_demand_atr') or 0)<=2.5",
    "r['h1_eff']>=0.12 and (r.get('nas_short_w24') or 0)<2 and (r.get('regime_age_h') or 0)>=8",
    "r['h1_eff']>=0.13 and (r.get('nas_short_leg') or 0)<5 and (r.get('regime_age_h') or 0)>=8",
    "r['h1_eff']>=0.12 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<70",
    "r['h1_eff']>=0.10 and (r.get('nas_short_w24') or 0)<3 and (r.get('dist_demand_atr') or 0)<=3.0",
    "r['h1_eff']>=0.12 and (r.get('dist_demand_atr') or 0)<=2.5 and (r.get('regime_age_h') or 0)>=8",
    "r['h1_eff']>=0.12 and (r.get('nas_short_w24') or 0)<2 and (r.get('atr_regime') or 1)<2.5",
    "r['h1_eff']>=0.13 and (r.get('nas_short_w24') or 0)<2 and (r.get('disp4_atr') or 0)<3.5",
    "r['h1_eff']>=0.12 and (r.get('nas_short_leg') or 0)<5 and (r.get('dist_demand_atr') or 0)<=2.5",
    "r['h1_eff']>=0.10 and (r.get('nas_short_w24') or 0)<2 and (r.get('regime_age_h') or 0)>=6",
    "r['h1_eff']>=0.14 and (r.get('nas_short_w24') or 0)<2 and (r.get('rsi') or 0)<70",
    "r['h1_eff']>=0.12 and (r.get('h4_eff') or 1)>=0.10 and (r.get('nas_short_w24') or 0)<2",
    "r['h1_eff']>=0.12 and (r.get('nas_short_w24') or 0)<2 and (r.get('dist_supply_atr') or 99)<5",
    "r['h1_eff']>=0.13 and (r.get('dist_demand_atr') or 0)<=2.5 and (r.get('rsi') or 0)<70",
    "r['h1_eff']>=0.10 and (r.get('nas_short_leg') or 0)<5 and (r.get('dist_demand_atr') or 0)<=2.5",
]

def run(expr):
    out = subprocess.check_output([sys.executable, HARNESS, expr], text=True)
    j = json.loads(out)
    f = j["FILTERED"]
    return f

print(f"{'expr':70s} {'n':>4} {'wr':>5} {'dWR':>5} {'sumr':>6} {'dSumR':>6} {'dd':>6} {'dDD':>5} {'lc':>3} {'wl':>3} {'bwl':>3} {'stk':>3}")
rows=[]
for e in CANDS:
    f = run(e)
    rows.append((e,f))
    print(f"{e[:70]:70s} {f['n']:>4} {f['wr']:>5} {f['dWR']:>5} {f['sumr']:>6} {f['dSumR']:>6} {f['dd']:>6} {f['dDD']:>5} {f['losers_cut']:>3} {f['winners_lost']:>3} {f['big_winners_lost']:>3} {f['streak']:>3}")
