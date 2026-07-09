#!/usr/bin/env python3
"""SANITY_PROBE — null episódico do teste D1-D3 (auditoria do MEDIDOR, pós-leitura do READER).
Leitura congelada do READER (ver report): conjunto marcado pela assinatura RASO-NO-ALTO
(D2 ratio<=0.40 & pos384>=0.70 — descrição da leitura, não gate) = {B4,C1,C2,C4,C5}; C6 borderline.
Null: hipergeométrico exato — P de um rótulo aleatório 10/10 colocar TODOS os marcados no grupo
negativo. Nada de decisão aqui; só P para o report."""
import math
def hyper_all_neg(k):  # P(todos os k marcados caírem nos 10 negativos de 20)
    return math.comb(10, k)/math.comb(20, k)
for k, tag in ((5, "conjunto core {B4,C1,C2,C4,C5}"), (6, "core + C6 borderline")):
    print(f"P(null) k={k} ({tag}): {hyper_all_neg(k):.4f}")
