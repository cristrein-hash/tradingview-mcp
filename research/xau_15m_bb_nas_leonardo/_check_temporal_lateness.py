#!/usr/bin/env python3
"""SANITY PROBE (materializada, 2026-07-03): lateness TEMPORAL da base #4 — gap apontado pelo DA.
Resultado: cj − p = 3 barras para TODOS os 435 (por construção: fractal k3 confirmada, entry close
em p+3). ⇒ Não existe variação temporal de 'entrada tardia' — a dimensão real da sensação do Cris
é a ALTURA do bounce de 3 barras (= risk_atr, mediana ~2,1 ATR; identidade lateness=risk_atr−0,1),
um CUSTO ESTRUTURAL DO GATILHO, não um erro por-trade filtrável. Lever = redesenho da geometria de
confirmação (família 5ATR/8ATR explora exatamente isso), não filtro sobre o gatilho atual.
Requer: base4_maturation_features.json (gerado por analysis_base4_maturation_read.py).
"""
import json
import statistics as st
from collections import Counter
from pathlib import Path

T = json.load(open(Path(__file__).parent / "base4_maturation_features.json"))
d = Counter(t["cj"] - t["p"] for t in T)
print("distribuição cj−p (barras):", dict(sorted(d.items())))
W = [t for t in T if t["win"]]; L = [t for t in T if not t["win"]]
print("mediana W:", st.median(t["cj"] - t["p"] for t in W), "| L:", st.median(t["cj"] - t["p"] for t in L))
assert all(t["cj"] - t["p"] == 3 for t in T), "construção mudou — rever leitura"
print("CONFIRMADO: confirmação fixa em 3 barras — 'lateness' é altura ($) do bounce, não tempo.")
