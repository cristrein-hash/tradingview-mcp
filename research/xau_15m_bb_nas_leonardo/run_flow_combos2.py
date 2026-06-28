#!/usr/bin/env python3
"""Runner round 2: pares/triplas OB-demanda + CHoCH + NAS. Reprodutível.
Uso: python3 run_flow_combos2.py"""
import json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).parent
SCORER=str(HERE/"score_flow.py")

COMBOS=[
    ("choch_any eq1 + dist_dem lo",      [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"dist_demand_atr","dir":"lo","q":0.33}]),
    ("h1n_choch eq1 + dist_dem lo",      [{"feat":"h1n_choch_up_rec","dir":"eq1"},{"feat":"dist_demand_atr","dir":"lo","q":0.33}]),
    ("choch_any eq1 + h4n_dist lo",      [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.33}]),
    ("dist_dem lo + h4n_dist lo",        [{"feat":"dist_demand_atr","dir":"lo","q":0.25},{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.25}]),
    ("dist_dem lo + nas_long lo",        [{"feat":"dist_demand_atr","dir":"lo","q":0.25},{"feat":"nas_long_16","dir":"lo","q":0.25}]),
    ("h4n_dist lo + nas_long lo",        [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.25},{"feat":"nas_long_16","dir":"lo","q":0.25}]),
    ("choch_any eq1 + nas_long lo",      [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"nas_long_16","dir":"lo","q":0.33}]),
    ("dist_dem lo + n_demand hi",        [{"feat":"dist_demand_atr","dir":"lo","q":0.25},{"feat":"n_demand_near","dir":"hi","q":0.33}]),
    ("h4n_dist lo + choch_any eq1",      [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.25},{"feat":"choch_any_rec","dir":"eq1"}]),
    ("dist_dem lo q33",                  [{"feat":"dist_demand_atr","dir":"lo","q":0.33}]),
    ("h4n_dist lo q33",                  [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.33}]),
    ("dist_dem lo + sell_minus_buy hi",  [{"feat":"dist_demand_atr","dir":"lo","q":0.25},{"feat":"sell_minus_buy","dir":"hi","q":0.33}]),
    ("dist_dem lo q20",                  [{"feat":"dist_demand_atr","dir":"lo","q":0.2}]),
    ("h4n_dist lo q20",                  [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.2}]),
    ("choch_any eq1 + h4n_dist lo q25",  [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.25}]),
]

def run(combo):
    r=subprocess.run([sys.executable,SCORER,json.dumps(combo)],capture_output=True,text=True)
    return json.loads(r.stdout)

def main():
    print(f"{'label':34} {'avgR':>6} {'DD':>6} {'N':>4} {'losC':>5} {'runC':>5} {'efic':>5} {'nullp':>6} {'yrpos':>5} {'hint':>5}  yr")
    out=[]
    for label,combo in COMBOS:
        o=run(combo)
        if "error" in o:
            print(f"{label:34} EMPTY"); continue
        a=o["after"]
        passed=(o["null_p_avgR_random_ge"]<0.02 and o["runners_cut"]<=0.15*o["losers_cut"]
                and a["avgR"]>o["base"]["avgR"] and o["all_years_pos"] and o["losers_cut"]>=8)
        print(f"{label:34} {a['avgR']:>6.3f} {a['DD']:>6.1f} {a['N']:>4} {o['losers_cut']:>5} {o['runners_cut']:>5} "
              f"{o['efic_losL_per_runL']:>5} {o['null_p_avgR_random_ge']:>6} {str(o['all_years_pos']):>5} "
              f"{o['verdict_hint']:>5}  {a['yr']}  {'<<PASS' if passed else ''}")
        if passed: out.append((label,o))
    print("\nPASSING:",[l for l,_ in out])

if __name__=="__main__": main()
