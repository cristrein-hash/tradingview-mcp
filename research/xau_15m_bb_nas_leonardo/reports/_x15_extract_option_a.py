#!/usr/bin/env python3
# SANITY_PROBE - display do xau_15m_option_a_result.json (ja salvo; sem analise nova)
import json
from pathlib import Path
d=json.load(open(Path(__file__).resolve().parent/"xau_15m_option_a_result.json"))
print("n_universe:",d["n_universe"],"| risk_atr_median:",d["risk_atr_median"],"| timeouts:",d["timeouts"])
print("universe:",d["universe_panel"])
print("filter:",d["filter"])
print("kept:",d["kept_panel"])
print("per_year:",{k:{kk:v[kk] for kk in ('n','WR','sumR','maxDD_R','streak')} for k,v in d["kept_per_year"].items()})
