#!/usr/bin/env python3
"""SANITY_PROBE — extract reprodutível (display) dos JSONs salvos do base repair (sem análise nova)."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
u=json.load(open(HERE/"xau_15m_live_fireable_universe_result.json"))
g=json.load(open(HERE/"xau_15m_live_fireable_source_guard_result.json"))
f=json.load(open(HERE/"xau_15m_live_fireable_n83_filter_result.json"))
r=json.load(open(HERE/"xau_15m_live_fireable_n83_robustness_result.json"))
print("UNIVERSE:",{k:u[k] for k in ("n_live_fireable","matched_n96","extra","WR_resolved_pct","sumR_3R_model","regime_coverage")})
print("sanity_1d max_diff:",u["sanity_1d_vs_cut_csv"]["max_abs_diff"])
print("GUARD:",g["verdict"],"| lower-low pós-entry:",g["pct_lower_low_after_entry"],"%")
print("FILTER: skip",f["n_skipped"],f["skip_by_outcome"],"| kept",f["kept_panel"])
print("ROBUST: negQ",r["neg_quarters"],"| null_bear_cuts:",r["null_random_bear_cuts"]["P_cut22_zero_winners"])
