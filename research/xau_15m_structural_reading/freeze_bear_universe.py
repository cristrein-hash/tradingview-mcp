#!/usr/bin/env python3
"""FASE 3A — CONGELAR O UNIVERSO BEAR (prereg do composite; NÃO computa nenhum composite).
Extrai da base causal live-fireable os candidatos macro==BEAR (166→78 esperado), grava os IDs (t)
+ counts + sha, ANTES de qualquer teste. Nenhuma métrica de composite é calculada aqui."""
import csv, json, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
LEDGER = HERE/"results/skip_family_discovery_ledger.csv"
rows = list(csv.DictReader(open(LEDGER)))
bear = sorted(int(r["t"]) for r in rows if r["macro"] == "BEAR")
losers = sum(1 for r in rows if r["macro"] == "BEAR" and r["out"] == "0")
sha = hashlib.sha256(json.dumps(bear).encode()).hexdigest()[:16]
out = {"universe": "BEAR-only, base causal live-fireable (macro v5 == regime_csv 166/166, DA verificado)",
       "n": len(bear), "losers": losers, "winners": len(bear)-losers,
       "ids_t": bear, "ids_sha16": sha, "frozen_at": "2026-07-09 pre-test",
       "note": "IDs congelados ANTES do teste; nenhum composite computado neste script"}
(HERE/"results/bear_universe_frozen.json").write_text(json.dumps(out, indent=2))
print(f"BEAR universe frozen: n={len(bear)} ({losers}L/{len(bear)-losers}W) sha16={sha}")
