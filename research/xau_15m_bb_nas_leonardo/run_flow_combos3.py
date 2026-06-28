#!/usr/bin/env python3
"""Round 3: alvo = null_p<0.02 E runc<=0.15*losC (preserva runners) E todos anos>=0 E losC>=8.
Estrategia: cortes que removem losers concentrados sem matar runners. Reprodutível.
Uso: python3 run_flow_combos3.py"""
import json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).parent
SCORER=str(HERE/"score_flow.py")

COMBOS=[
    # gentle dist_demand variants (preserve runners) - sweep q
    ("dist_dem lo q15",                  [{"feat":"dist_demand_atr","dir":"lo","q":0.15}]),
    ("h4n_dist lo q15",                  [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.15}]),
    ("dist_dem lo q12",                  [{"feat":"dist_demand_atr","dir":"lo","q":0.12}]),
    ("h4n_dist lo q12",                  [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.12}]),
    # pair the two best runner-preserving cuts
    ("dist_dem lo q20 + h4n_dist lo q20",[{"feat":"dist_demand_atr","dir":"lo","q":0.2},{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.2}]),
    ("dist_dem lo q15 + nas_long lo q15",[{"feat":"dist_demand_atr","dir":"lo","q":0.15},{"feat":"nas_long_16","dir":"lo","q":0.15}]),
    ("h4n_dist lo q20 + nas_long lo q20",[{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.2},{"feat":"nas_long_16","dir":"lo","q":0.2}]),
    ("h4n_dist lo q20 + dist_dem lo q20",[{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.2},{"feat":"dist_demand_atr","dir":"lo","q":0.2}]),
    # n_supply_overhead lo (less resistance) - correlated w pos but test
    ("n_supply lo q25",                  [{"feat":"n_supply_overhead","dir":"lo","q":0.25}]),
    ("clean_sky hi q25",                 [{"feat":"clean_sky_atr","dir":"hi","q":0.25}]),
    # demand proximity + light flow
    ("h4n_dist lo q25 + sell_minus_buy lo",[{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.25},{"feat":"sell_minus_buy","dir":"lo","q":0.33}]),
    ("h4n_dist lo q25 + buy_bub hi",     [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.25},{"feat":"buy_bub_w","dir":"hi","q":0.33}]),
    # demand_reclaim/in_demand keep + dist
    ("dist_dem lo q20 + in_demand eq1",  [{"feat":"dist_demand_atr","dir":"lo","q":0.2},{"feat":"in_demand","dir":"eq1"}]),
    # nas_long lo gentler
    ("nas_long lo q15",                  [{"feat":"nas_long_16","dir":"lo","q":0.15}]),
    ("nas_long lo q33",                  [{"feat":"nas_long_16","dir":"lo","q":0.33}]),
]

def run(combo):
    r=subprocess.run([sys.executable,SCORER,json.dumps(combo)],capture_output=True,text=True)
    return json.loads(r.stdout)

def main():
    print(f"{'label':38} {'avgR':>6} {'DD':>6} {'N':>4} {'losC':>5} {'runC':>5} {'efic':>5} {'nullp':>6} {'yrpos':>5} {'hint':>5}  yr")
    out=[]
    for label,combo in COMBOS:
        o=run(combo)
        if "error" in o:
            print(f"{label:38} EMPTY"); continue
        a=o["after"]
        passed=(o["null_p_avgR_random_ge"]<0.02 and o["runners_cut"]<=0.15*o["losers_cut"]
                and a["avgR"]>o["base"]["avgR"] and o["all_years_pos"] and o["losers_cut"]>=8)
        print(f"{label:38} {a['avgR']:>6.3f} {a['DD']:>6.1f} {a['N']:>4} {o['losers_cut']:>5} {o['runners_cut']:>5} "
              f"{o['efic_losL_per_runL']:>5} {o['null_p_avgR_random_ge']:>6} {str(o['all_years_pos']):>5} "
              f"{o['verdict_hint']:>5}  {a['yr']}  {'<<PASS' if passed else ''}")
        if passed: out.append((label,o))
    print("\nPASSING:",[l for l,_ in out])

if __name__=="__main__": main()
