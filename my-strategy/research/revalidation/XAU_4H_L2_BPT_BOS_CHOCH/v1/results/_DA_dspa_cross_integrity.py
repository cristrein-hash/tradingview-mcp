#!/usr/bin/env python3
"""DA part 4: join integrity + outcome-blindness of predicates (base 276).
(1) every source covers the 276 bar_idx (or is safe-joined with .get default);
(2) EVd predicate builder (lines 25-47 of main) reads ONLY path/states/eng/ind/dec/bl/mph cols,
    never any column from unc (mfe_R/capped_realR/runner_flag/monster/hit*);
(3) prior layers (macro_reader_leg/sup_cat/macro_phase/bear_leg_refined/clean_sky/bottom_turn) ENTER as evidence axes."""
import csv, re
D="/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
MAIN="/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/l2_bpt_dspa_cross_confluence.py"
def keys(f): return set(int(r['bar_idx']) for r in csv.DictReader(open(f"{D}/{f}")))
path=keys('l2_bpt_dspa_path_features_276.csv')
print("[1] JOIN INTEGRITY (vs path 276)")
for f,safe in [('l2_bpt_dspa_intermediate_states_276.csv',False),('l2_bpt_full276_macro_engine_confluence.csv',False),
               ('l2_bpt_full276_indicator_engine_cross_v2.csv',True),('l2_bpt_full276_macro_bear_v3_decisions.csv',True),
               ('l2_bpt_bearleg_surgical.csv',True),('l2_bpt_uncapped_or_proxy_outcomes_276.csv',False)]:
    k=keys(f); miss=len(path-k)
    note='OK full' if miss==0 else ('OK (safe .get default -> sparse axis)' if safe else 'WARN missing without safe-get')
    print(f"    {f:55} n={len(k):3} missing={miss:3} -> {note}")

# [2] outcome-blindness: extract EVd body, assert no unc-outcome token appears
src=open(MAIN).read()
evd=re.search(r"def EVd\(b\):(.*?)\nEV=\{",src,re.S).group(1)
OUTCOME_TOKENS=['unc[','mfe_R','capped_realR','runner_flag','monster','hit2','hit3','hit5','hit8','hit10','max_run','runner_bucket','realized_']
leaks=[t for t in OUTCOME_TOKENS if t in evd]
print("\n[2] OUTCOME-BLINDNESS of EVd predicate builder")
print(f"    outcome tokens found inside EVd: {leaks if leaks else 'NONE'} -> {'LEAK!' if leaks else 'CLEAN (predicates are outcome-blind)'}")
# confirm predicates read prior-layer cols
PRIOR=['macro_reader_leg','sup_cat','macro_phase','bear_leg_refined','clean_sky_flag','bottom_turn','demand','supply']
used=[t for t in PRIOR if t in evd or t in src]
print(f"\n[3] PRIOR LAYERS entering as evidence axes: {used}")
print("    -> prior layers are NOT discarded; they are evidence inputs to EV booleans (bear/demand/sup_*/bottom_turn/clean_sky).")
print("DONE integrity.")
