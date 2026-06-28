#!/usr/bin/env python3
"""Reproducible runner: scores a list of named NAS-family combos via score_flow.py
and prints a compact one-line summary per combo. Source of truth = score_flow.py.
Usage: python3 run_nas_combos.py"""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
SCORER = str(HERE / "score_flow.py")

# (label, combo)
COMBOS = [
    ("nas_any_rec eq0", [{"feat": "nas_any_rec", "dir": "eq0"}]),
    ("nas_long_16 eq0", [{"feat": "nas_long_16", "dir": "eq0"}]),
    ("sell_minus_buy lo q0.25", [{"feat": "sell_minus_buy", "dir": "lo", "q": 0.25}]),
    ("sell_bub_w lo q0.25", [{"feat": "sell_bub_w", "dir": "lo", "q": 0.25}]),
    ("buy_bub_w hi q0.25", [{"feat": "buy_bub_w", "dir": "hi", "q": 0.25}]),
    ("dist_demand_atr lo q0.25", [{"feat": "dist_demand_atr", "dir": "lo", "q": 0.25}]),
    ("h4n_dist_demand_atr lo q0.25", [{"feat": "h4n_dist_demand_atr", "dir": "lo", "q": 0.25}]),
    ("htf_demand_any eq1", [{"feat": "htf_demand_any", "dir": "eq1"}]),
    ("htf_demand_confluence eq1", [{"feat": "htf_demand_confluence", "dir": "eq1"}]),
    ("choch_any_rec eq1", [{"feat": "choch_any_rec", "dir": "eq1"}]),
    ("h1n_choch_up_rec eq1", [{"feat": "h1n_choch_up_rec", "dir": "eq1"}]),
    ("h4n_choch_up_rec eq1", [{"feat": "h4n_choch_up_rec", "dir": "eq1"}]),
    # combos: NAS-absence + 2nd flow axis
    ("nas_any_rec=0 + sell_minus_buy lo", [{"feat": "nas_any_rec", "dir": "eq0"}, {"feat": "sell_minus_buy", "dir": "lo", "q": 0.25}]),
    ("nas_any_rec=0 + dist_demand lo", [{"feat": "nas_any_rec", "dir": "eq0"}, {"feat": "dist_demand_atr", "dir": "lo", "q": 0.25}]),
    ("nas_any_rec=0 + htf_demand=1", [{"feat": "nas_any_rec", "dir": "eq0"}, {"feat": "htf_demand_any", "dir": "eq1"}]),
    ("nas_long_16=0 + sell_minus_buy lo", [{"feat": "nas_long_16", "dir": "eq0"}, {"feat": "sell_minus_buy", "dir": "lo", "q": 0.25}]),
]


def run(combo):
    out = subprocess.run([sys.executable, SCORER, json.dumps(combo)],
                         capture_output=True, text=True)
    return json.loads(out.stdout)


def main():
    rows = []
    for label, combo in COMBOS:
        d = run(combo)
        if "after" not in d:
            print(f"{label:42s} ERROR {d}")
            continue
        a = d["after"]
        passed = d["verdict_hint"] == "PASS"
        rows.append((label, combo, d))
        print(f"{label:42s} losL={d['losers_cut']:3d} runL={d['runners_cut']:2d} "
              f"efic={d['efic_losL_per_runL']:4} avgR={a['avgR']:+.3f} DD={a['DD']:6} "
              f"nullp={d['null_p_avgR_random_ge']:.3f} yrpos={d['all_years_pos']} "
              f"yr={a['yr']} -> {d['verdict_hint']}")
    print("\n=== PASS combos ===")
    for label, combo, d in rows:
        if d["verdict_hint"] == "PASS":
            print(label, json.dumps(combo))


if __name__ == "__main__":
    main()
