#!/usr/bin/env python3
"""Runner OB-demanda family: passa combos JSON ao score_flow.py e imprime linha compacta.
Reprodutível: edite COMBOS abaixo. Uso: python3 run_flow_combos.py"""
import json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).parent
SCORER=str(HERE/"score_flow.py")

COMBOS=[
    # label, combo
    ("nas_long_16 lo",     [{"feat":"nas_long_16","dir":"lo","q":0.25}]),
    ("in_demand eq1",      [{"feat":"in_demand","dir":"eq1"}]),
    ("htf_demand_any eq1", [{"feat":"htf_demand_any","dir":"eq1"}]),
    ("dist_demand_atr lo", [{"feat":"dist_demand_atr","dir":"lo","q":0.25}]),
    ("dist_demand_atr hi", [{"feat":"dist_demand_atr","dir":"hi","q":0.25}]),
    ("demand_reclaim eq1", [{"feat":"demand_reclaim","dir":"eq1"}]),
    ("n_demand_near hi",   [{"feat":"n_demand_near","dir":"hi","q":0.25}]),
    ("h4n_in_demand eq1",  [{"feat":"h4n_in_demand","dir":"eq1"}]),
    ("h1n_in_demand eq1",  [{"feat":"h1n_in_demand","dir":"eq1"}]),
    ("htf_demand_conf hi", [{"feat":"htf_demand_confluence","dir":"hi","q":0.25}]),
    ("h4n_dist_demand lo", [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.25}]),
    ("h1n_dist_demand lo", [{"feat":"h1n_dist_demand_atr","dir":"lo","q":0.25}]),
    ("choch_any_rec eq1",  [{"feat":"choch_any_rec","dir":"eq1"}]),
    ("h4n_choch_up eq1",   [{"feat":"h4n_choch_up_rec","dir":"eq1"}]),
    ("h1n_choch_up eq1",   [{"feat":"h1n_choch_up_rec","dir":"eq1"}]),
    ("sell_minus_buy hi",  [{"feat":"sell_minus_buy","dir":"hi","q":0.25}]),
    ("sell_bub_w hi",      [{"feat":"sell_bub_w","dir":"hi","q":0.25}]),
    ("buy_bub_w lo",       [{"feat":"buy_bub_w","dir":"lo","q":0.25}]),
    ("nas_any_rec eq1",    [{"feat":"nas_any_rec","dir":"eq1"}]),
]

def run(combo):
    r=subprocess.run([sys.executable,SCORER,json.dumps(combo)],capture_output=True,text=True)
    return json.loads(r.stdout)

def main():
    print(f"{'label':28} {'avgR':>6} {'DD':>6} {'losC':>5} {'runC':>5} {'efic':>5} {'nullp':>6} {'yrpos':>5} {'hint':>5}  yr")
    out=[]
    for label,combo in COMBOS:
        o=run(combo)
        if "error" in o:
            print(f"{label:28} EMPTY"); continue
        a=o["after"]
        passed=(o["null_p_avgR_random_ge"]<0.02 and o["runners_cut"]<=0.15*o["losers_cut"]
                and a["avgR"]>o["base"]["avgR"] and o["all_years_pos"] and o["losers_cut"]>=8)
        print(f"{label:28} {a['avgR']:>6.3f} {a['DD']:>6.1f} {o['losers_cut']:>5} {o['runners_cut']:>5} "
              f"{o['efic_losL_per_runL']:>5} {o['null_p_avgR_random_ge']:>6} {str(o['all_years_pos']):>5} "
              f"{o['verdict_hint']:>5}  {a['yr']}  {'<<PASS' if passed else ''}")
        if passed: out.append((label,o))
    print("\nPASSING:",[l for l,_ in out])

if __name__=="__main__": main()
