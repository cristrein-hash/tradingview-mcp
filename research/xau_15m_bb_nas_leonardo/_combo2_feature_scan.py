#!/usr/bin/env python3
"""Scan feature presence/distribution in filter_dataset.jsonl for combo2 family research.
Reports, per feature: non-None count, and quartiles, to pick thresholds before AND-combos."""
import json
from pathlib import Path
HERE = Path(__file__).parent
ROWS = [json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines()]
keys = set()
for r in ROWS:
    keys.update(r.keys())
import statistics
num_feats = ["buy_bub_w_leg","sell_bub_w_leg","buy_bub_L_leg","buy_bub_w_w24","sell_bub_w_w24","buy_bub_L_w24",
 "nas_short_leg","nas_long_leg","nas_short_w24","nas_long_w24","dist_ema_atr","leg_ext_atr","room_above_atr",
 "rsi","h1_pos","h1_dist","disp4_atr","dist_supply_atr","vpnode_dist_atr","macro_retr","path_eff",
 "h1_eff","h4_eff","atr_regime","h4_pos","dist_demand_atr","regime_age_h","buy_sell_ratio4","flow_accel",
 "bars_to_base","bars_since_lowest","vol_low_vs_med"]
print("FEATURE n_nonNone  min  q25  med  q75  max")
for k in num_feats:
    vals = [r.get(k) for r in ROWS if r.get(k) is not None]
    if not vals:
        print(f"{k}: ALL NONE"); continue
    vals_s = sorted(vals)
    def q(p): return round(vals_s[min(len(vals_s)-1,int(p*len(vals_s)))],3)
    print(f"{k}: {len(vals)}  {round(min(vals),3)}  {q(.25)}  {q(.5)}  {q(.75)}  {round(max(vals),3)}")
bool_feats=["in_demand","demand_fresh","macro_bull","macro_bear","is_ny_overlap","is_deadzone","vol_climax","absorption","smc_bos","killzone"]
print("\nBOOL/CAT feature value counts:")
for k in bool_feats:
    from collections import Counter
    c=Counter(repr(r.get(k)) for r in ROWS)
    print(f"{k}: {dict(c)}")
