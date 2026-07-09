#!/usr/bin/env python3
"""SANITY_PROBE — null episódico dos Medidores A/B (auditoria pós-leitura).
Medidor A: separação PERFEITA 12 fundos vs 3 INVALIDO pela medida contínua pré-registada
dist_prior_episode_bottom_atr (fundos ≤ −8,7; INVALIDO ≥ −4,7). Null exato: P de os 3 INVALIDO
ocuparem os 3 ranks mais rasos sob rótulos aleatórios = 1/C(15,3).
Medidor B: sem separação a auditar (leitura = estéril; declarado)."""
import math
print(f"Medidor A — P(null) separação perfeita 12v3: {1/math.comb(15,3):.4f} (1/{math.comb(15,3)})")
print("Medidor B — OB: sem separação observada (BULL inside 11/26 vs C 2/6; dists sobrepostos) => sem null aplicável")
