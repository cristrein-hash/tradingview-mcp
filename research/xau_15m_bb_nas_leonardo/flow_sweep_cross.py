#!/usr/bin/env python3
"""Cross-family flow sweep wrapper around score_flow.py — reproducible runner.
Runs a list of combos through score_flow.py and prints a compact one-line summary
per combo plus PASS/FAIL against the cross-flow gate:
  null_p < 0.02 AND runners_cut <= 0.15*losers_cut AND avgR_after > base AND all_years_pos AND losers_cut >= 8.
Usage: python3 flow_sweep_cross.py            # runs the built-in catalog
       python3 flow_sweep_cross.py '<json combo>'  # runs one ad-hoc combo
"""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
SCORE = HERE / "score_flow.py"
BASE_AVGR = 0.629

def run(combo):
    out = subprocess.run([sys.executable, str(SCORE), json.dumps(combo)],
                         capture_output=True, text=True)
    try:
        return json.loads(out.stdout)
    except Exception:
        return {"error": out.stdout + out.stderr}

def gate(o):
    if "after" not in o:
        return False
    a = o["after"]; dl = o["losers_cut"]; dr = o["runners_cut"]
    return (o["null_p_avgR_random_ge"] < 0.02 and dr <= 0.15 * dl
            and a["avgR"] > BASE_AVGR and o["all_years_pos"] and dl >= 8)

def line(label, combo):
    o = run(combo)
    if "after" not in o:
        print(f"{label:42s} ERR {o.get('error','')[:60]}"); return None
    a = o["after"]
    pf = "PASS" if gate(o) else "----"
    print(f"{label:42s} N{a['N']:>3} avgR{a['avgR']:+.3f} DD{a['DD']:>6} "
          f"losC{o['losers_cut']:>3} runC{o['runners_cut']:>2} "
          f"efic{o['efic_losL_per_runL']:>5} p{o['null_p_avgR_random_ge']:.3f} "
          f"yr{a['yr']} {pf}")
    return o if gate(o) else None

# Built-in catalog: cross-family 2-3 leg combos (1 NAS-ish + 1 bubble + 1 demand/CHoCH)
CATALOG = [
    ("nasANY + sell_bub_hi",        [{"feat":"nas_any_rec","dir":"eq1"},{"feat":"sell_bub_w","dir":"hi","q":0.33}]),
    ("buybub_lo + choch_any",       [{"feat":"buy_bub_w","dir":"lo","q":0.33},{"feat":"choch_any_rec","dir":"eq1"}]),
    ("sellbub_hi + in_demand",      [{"feat":"sell_bub_w","dir":"hi","q":0.33},{"feat":"in_demand","dir":"eq1"}]),
    ("h4choch + sellbub_hi",        [{"feat":"h4n_choch_up_rec","dir":"eq1"},{"feat":"sell_bub_w","dir":"hi","q":0.33}]),
]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        line("adhoc", json.loads(sys.argv[1]))
    else:
        passers = []
        for lab, c in CATALOG:
            o = line(lab, c)
            if o: passers.append((lab, c, o))
        print(f"\n{len(passers)} passer(s)")
