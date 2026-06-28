#!/usr/bin/env python3
"""Round 4 FINAL: tentar reconciliar null_p<0.02 com preservacao de runners.
Estrategia: corte de losers via eq0 (ausencia de flow ruim) e cortes amplos suaves repetidos.
Imprime tambem o teto de runc permitido (0.15*losC) p/ auditar. Reprodutível.
Uso: python3 run_flow_combos4.py"""
import json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).parent
SCORER=str(HERE/"score_flow.py")

COMBOS=[
    # CHoCH variations trying to preserve runners
    ("choch_any eq0 (drop CHoCH)",       [{"feat":"choch_any_rec","dir":"eq0"}]),
    ("h4n_choch eq0",                    [{"feat":"h4n_choch_up_rec","dir":"eq0"}]),
    ("nas_any eq0",                      [{"feat":"nas_any_rec","dir":"eq0"}]),
    # demand absence as loser marker
    ("htf_demand_any eq0",               [{"feat":"htf_demand_any","dir":"eq0"}]),
    ("in_demand eq0",                    [{"feat":"in_demand","dir":"eq0"}]),
    ("demand_reclaim eq0",               [{"feat":"demand_reclaim","dir":"eq0"}]),
    # the strongest null_p combos re-checked w/ runc ceiling
    ("choch_any eq1 + h4n_dist lo q33",  [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.33}]),
    ("choch_any eq1 + nas_long lo q33",  [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"nas_long_16","dir":"lo","q":0.33}]),
    # broad combined demand-proximity triple (more loser cut, watch runners)
    ("h4n_dist lo q25 + dist_dem lo q25 + nas_long lo q25",
        [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.25},{"feat":"dist_demand_atr","dir":"lo","q":0.25},{"feat":"nas_long_16","dir":"lo","q":0.25}]),
    ("h4n_dist lo q20 + nas_long lo q20 + dist_dem lo q20",
        [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.2},{"feat":"nas_long_16","dir":"lo","q":0.2},{"feat":"dist_demand_atr","dir":"lo","q":0.2}]),
]

def run(combo):
    r=subprocess.run([sys.executable,SCORER,json.dumps(combo)],capture_output=True,text=True)
    return json.loads(r.stdout)

def main():
    print(f"{'label':52} {'avgR':>6} {'N':>4} {'losC':>5} {'runC':>5} {'ceil':>5} {'nullp':>6} {'yrpos':>5}  yr")
    out=[]
    for label,combo in COMBOS:
        o=run(combo)
        if "error" in o:
            print(f"{label:52} EMPTY"); continue
        a=o["after"]; ceil=round(0.15*o["losers_cut"],1)
        passed=(o["null_p_avgR_random_ge"]<0.02 and o["runners_cut"]<=ceil
                and a["avgR"]>o["base"]["avgR"] and o["all_years_pos"] and o["losers_cut"]>=8)
        print(f"{label:52} {a['avgR']:>6.3f} {a['N']:>4} {o['losers_cut']:>5} {o['runners_cut']:>5} "
              f"{ceil:>5} {o['null_p_avgR_random_ge']:>6} {str(o['all_years_pos']):>5}  {a['yr']}  {'<<PASS' if passed else ''}")
        if passed: out.append((label,o))
    print("\nPASSING:",[l for l,_ in out])

if __name__=="__main__": main()
