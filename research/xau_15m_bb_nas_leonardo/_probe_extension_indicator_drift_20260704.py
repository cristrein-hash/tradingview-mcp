#!/usr/bin/env python3
"""Diagnóstico do HARD STOP da extensão 2026-07-04: quais indicadores reportaram payload
em quais trechos do bloco coletado (drift vs baseline do 8º bloco)."""
import json
from pathlib import Path
F = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl")
names = {}
first_seen = {}; last_seen = {}
tot = 0
for i, l in enumerate(open(F)):
    r = json.loads(l); tot += 1
    seen = set()
    for fam in ("pine_boxes", "pine_labels", "pine_lines", "pine_shapes_bubbles", "study_values"):
        for st in (r.get(fam) or []):
            nm = st.get("name"); seen.add(nm)
    for nm in seen:
        names[nm] = names.get(nm, 0) + 1
        first_seen.setdefault(nm, i); last_seen[nm] = i
print(f"registros: {tot}")
for nm, c in sorted(names.items(), key=lambda kv: -kv[1]):
    print(f"  {nm!r:<50} em {c}/{tot} registros (primeiro idx {first_seen[nm]}, último {last_seen[nm]})")
missing = [x for x in ("Custom OB Detector v11 — Alert", "Smart Money Concepts [LuxAlgo]",
                       "NAS TOP BOTTOM DETECTOR") if x not in names]
print("\nAUSENTES do payload (presentes no chart_get_state pré-coleta):", missing)
