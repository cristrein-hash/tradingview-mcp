# ENTRY-QUALITY SPECIALIST — RELATÓRIO DIAGNÓSTICO (hipótese REFUTADA)

**2026-06-22.** Diagnóstico/calibração. 62 = ensino. Sem outcome. Engine/decisions/produção intocados.
Testa a hipótese: "a LOCALIZAÇÃO da entrada (pullback-a-demanda vs perseguição-de-topo/range) separa
A (bull bom) de B (bear/late-top ruim)". **CONCLUSÃO: REFUTADA.**

## Exploração de features (medianas A vs B)
| feature | medA (bull-bom) | medB (bear-ruim) |
|---|---|---|
| dist_4h_demand_low_atr | 2.86 | 2.45 (B até mais perto) |
| reclaim_dist_from_demand_atr | 2.17 | 1.36 |
| dist_VAL_atr | 0.71 | 0.92 |
| dist_POC_atr | 0.41 | 0.57 |
| demand_category | SUPPORTING_RETEST 14/26 | SUPPORTING_RETEST 15/18 |
| below_VAL | 23 False / 3 True | 16 False / 2 True |

**Quase idênticas.** A e B entram à mesma distância de demanda, com a mesma categoria de demanda defendida, na mesma posição vs valor.

## Classificação + separação
- entry_family por set: **A = 11 GOOD / 3 NEUTRAL / 12 RISK · B = 10 GOOD / 8 RISK · C = 11 GOOD / 7 RISK.**
- A 'GOOD/NEUTRAL': 14/26 · B 'RISK': 8/18 → **não separa** (ambos ~50/50).
- Combinação macro_v1=BULL AND entry≠RISK: A mantidos 11/26, B mantidos 8/18 → **corta A e mantém B** (pior).
- Anchor check: preserve(GOOD/NEUTRAL) **7/14**, block(RISK) **0/1**.

## Conclusão: entry-location NÃO é o separador
Os bad-entries (B) são **estruturalmente indistinguíveis** dos good-entries (A) por localização: ambos são
**pullback a demanda defendida perto de valor** — que é literalmente o que a estratégia L2/BPT faz. A diferença
NÃO é ONDE se entra; é em QUE LEG a entrada está (bull que continua vs bear/late-stage que reverte).

**Isto CONFIRMA a direção leg-state** (não entry-quality) — exatamente o que o Cris previu e o que a lógica de
Auction Theory exige: o trap e a continuação são feitos idênticos no ponto de entrada; o que difere é o
contexto de leg/liquidez. A localização da entrada está esgotada como eixo.

## Próximo passo
Antes de qualquer spec de leg-state: **verificar a proveniência causal do `smc_bos`/`smc_choch` e dos pivots
(risco de repaint)** — limpar a sujeira de BOS/CHoCH primeiro, para o spec nascer sabendo o que é causal.
