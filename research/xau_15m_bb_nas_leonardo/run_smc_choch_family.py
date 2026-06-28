#!/usr/bin/env python3
"""Driver SMC-CHoCH family (engine de fluxo XAU 15M LONG BOTTOM, BASE=SUBSTRATO #4 N448).
Roda uma bateria de combos via score_flow.apply/panel (import direto, mesma lógica do scorer)
e tabula os campos do gate. Saída materializada/reproduzível.
Gate de retorno: null_p<0.02 AND runners_cut<=0.15*losers_cut AND avgR_after>base AND all_years_pos AND losers_cut>=8.
Uso: python3 run_smc_choch_family.py
"""
import json, sys
from pathlib import Path
import importlib.util
HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("score_flow", HERE/"score_flow.py")
sf = importlib.util.module_from_spec(spec)
# Avoid running main(): only import functions/data
import random, statistics
src = (HERE/"score_flow.py").read_text()
# exec module body but guard main
g = {"__file__": str(HERE/"score_flow.py")}
exec(compile(src.replace("if __name__==\"__main__\": main()", ""), "score_flow.py", "exec"), g)
RECS = g["RECS"]; apply = g["apply"]; panel = g["panel"]
BASE = panel(RECS)

def score(combo):
    kept = apply(combo, RECS); k = panel(kept)
    if not k: return None
    dl = BASE["losers"]-k["losers"]; dr = BASE["runners"]-k["runners"]; ncut = BASE["N"]-k["N"]
    rng = random.Random(20260628); avs=[]
    for _ in range(500):
        idx = set(rng.sample(range(len(RECS)), ncut)) if 0<ncut<len(RECS) else set()
        kk=[RECS[i] for i in range(len(RECS)) if i not in idx]; pp=panel(kk)
        if pp: avs.append(pp["avgR"])
    p_avg = round(sum(1 for x in avs if x>=k["avgR"])/len(avs),3) if avs else 1.0
    yrs = list(k["yr"].values())
    pas = (p_avg<0.02 and dr<=dl*0.15 and k["avgR"]>=BASE["avgR"] and all(v>=0 for v in yrs) and dl>=8)
    return {"combo":combo,"N":k["N"],"avgR":k["avgR"],"DD":k["DD"],"yr":k["yr"],
            "losers_cut":dl,"runners_cut":dr,"null_p":p_avg,"all_years_pos":all(v>=0 for v in yrs),
            "PASS":pas}

COMBOS = [
    # CHoCH single
    [{"feat":"choch_any_rec","dir":"eq1"}],
    [{"feat":"choch_any_rec","dir":"eq0"}],
    [{"feat":"h4n_choch_up_rec","dir":"eq1"}],
    [{"feat":"h1n_choch_up_rec","dir":"eq1"}],
    # CHoCH + demand flow (surgical loser cuts around CHoCH context)
    [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"dist_demand_atr","dir":"lo","q":0.33}],
    [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"clean_sky_atr","dir":"hi","q":0.33}],
    [{"feat":"choch_any_rec","dir":"eq1"},{"feat":"n_supply_overhead","dir":"lo","q":0.33}],
    # Demand-flow only (new axes) — cut losers far from demand / no reclaim
    [{"feat":"demand_reclaim","dir":"eq1"}],
    [{"feat":"in_demand","dir":"eq1"}],
    [{"feat":"htf_demand_any","dir":"eq1"}],
    [{"feat":"dist_demand_atr","dir":"lo","q":0.25}],
    [{"feat":"dist_demand_atr","dir":"lo","q":0.33}],
    [{"feat":"htf_demand_confluence","dir":"hi","q":0.33}],
    [{"feat":"n_demand_near","dir":"hi","q":0.33}],
    [{"feat":"h4n_dist_demand_atr","dir":"lo","q":0.33}],
    [{"feat":"h1n_dist_demand_atr","dir":"lo","q":0.33}],
    # NAS flow
    [{"feat":"nas_any_rec","dir":"eq1"}],
    [{"feat":"nas_long_16","dir":"hi","q":0.33}],
    [{"feat":"h4n_nas_long_rec","dir":"hi","q":0.33}],
    [{"feat":"h1n_nas_long_rec","dir":"hi","q":0.33}],
    # Bubbles flow
    [{"feat":"sell_minus_buy","dir":"hi","q":0.33}],
    [{"feat":"sell_minus_buy","dir":"lo","q":0.33}],
    [{"feat":"buy_bub_w","dir":"hi","q":0.33}],
    [{"feat":"sell_bub_w","dir":"hi","q":0.33}],
    # demand + nas / demand + choch combos
    [{"feat":"htf_demand_any","dir":"eq1"},{"feat":"choch_any_rec","dir":"eq1"}],
    [{"feat":"dist_demand_atr","dir":"lo","q":0.33},{"feat":"choch_any_rec","dir":"eq1"}],
    [{"feat":"in_demand","dir":"eq1"},{"feat":"dist_demand_atr","dir":"lo","q":0.33}],
]

def main():
    BASE_avgR = BASE["avgR"]
    print(f"BASE avgR={BASE_avgR} DD={BASE['DD']} losers={BASE['losers']} runners={BASE['runners']}")
    rows=[]
    for c in COMBOS:
        r=score(c)
        if r: rows.append(r)
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    print("=== PASSES ===")
    for r in rows:
        if r["PASS"]: print(json.dumps(r, ensure_ascii=False))

if __name__=="__main__": main()
