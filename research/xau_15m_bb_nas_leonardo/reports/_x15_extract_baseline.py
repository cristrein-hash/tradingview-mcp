#!/usr/bin/env python3
"""Extract reprodutível (display) dos JSONs salvos das fases 5-7 (sem análise nova)."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
b=json.load(open(HERE/"xau_15m_n83_sl_exit_baseline_result.json"))
print("N96:",b["N96"]); print("N83:",b["N83"])
print("per_year:",{k:{'n':v['n'],'WR':v['WR'],'sumR':v['sumR']} for k,v in b["per_year_n83"].items()})
print("per_regime:",{k:{'n':v['n'],'WR':v['WR'],'sumR':v['sumR']} for k,v in b["per_regime_n83"].items()})
for f in ("xau_15m_n83_sl_review_result.json","xau_15m_n83_exit_review_result.json"):
    d=json.load(open(HERE/f)); print("\n==",f)
    for name,p in d["alts"].items():
        print(f"{name:<30} n={p['n']} WR={p['WR']} sumR={p['sumR']} PF={p['PF']} DD={p['maxDD_R']} stk={p['streak']}")
