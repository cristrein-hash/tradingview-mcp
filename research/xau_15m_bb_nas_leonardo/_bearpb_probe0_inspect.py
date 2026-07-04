#!/usr/bin/env python3
"""BEAR-PULLBACK · PROBE 0 — inspeção de estrutura dos arquivos de entrada (read-only)."""
import json, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
TR = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
print("n trades:", len(TR))
for t in TR:
    print(t.get("id"), t.get("n"), t.get("utc"), t.get("regime"), t.get("plan_outcome"), t.get("plan_R"))
