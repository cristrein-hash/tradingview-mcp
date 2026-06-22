# BEAR-LEG BLOCK — KNOWLEDGE STATE (real / quantificável / positivo)

**2026-06-22.** Consolidação do trabalho de bloqueio de compras em bear-leg/range nos 62 (ensino).
Documentação apenas — sem análise nova, sem chart/MCP (risco de look-ahead), sem 276/OOS, sem produção.
Base para persistir o que vale antes de adicionar a regra CORRECTIVE.

## 1. O que é REAL, QUANTIFICÁVEL e POSITIVO (a guardar)
- **Gate de bloqueio bear-markdown/range FUNCIONA** (commit 2315325): preserva **23/26 A** (winners) e
  bloqueia bear/range losers — **T9, T11, T15, T42** (B) + 7 C. Quantificável e positivo.
- **Carve-out bottom/turn (oversold rsi_min≤32 + reclaim≥0.4 + demanda)** recupera fundos genuínos (S15).
  Corrigiu o sinal errado anterior (drop20). Funciona para o fundo-a-virar.
- **Backbone D1/weekly** dá a leg macro limpa (preserva bull-run; resolve o confound de escala do 4H).
- **Taxonomia corrigida pelo Cris** (`results/l2_bpt_bear_leg_taxonomy_cris_corrected.csv`) — ground truth visual
  dos trades contestados, separando o que é blocável do que é aberto/irredutível.

## 2. Taxonomia corrigida (ground truth visual do Cris)
| status | trades | significado |
|---|---|---|
| JÁ_BLOQUEADO ✓ (B) | T9, T11, T15, T42 | bear/range losers do set B — gate pega |
| JÁ_BLOQUEADO ✓ (C) | T19, S19 | set C (não B): T19 d1_leg=MACRO_BULL_LEG/REVIEW, S19=BLOCK_acceptable_skip — gate pega na mesma |
| CORRECTIVE_LATER | T12, T25, T26, S28 | corrective pullback — adicionar regra (baixo risco) **PRÓXIMO** |
| MICRO_STRUCTURE_OPEN | T17, T20 | range-bull entrada em micro-TOPO — REAL visual, sinal causal NÃO capturado |
| PRESERVAR (contraste) | S12 (no set); T21, T22 fora-dos-62 | range-bull micro-FUNDO/breakout bom; só S12 está no working-set — T21/T22 nomeados pelo Cris mas NÃO nos 62 |
| CLASSIFIER_ERROR / HINDSIGHT | T23 | meu D1 errou (BULL→bear); mas "bear" pode ser forward-looking (regime era TRANSITION à entrada) |
| IRREDUTÍVEL | T32, S11 | late-top esticado genuíno / em acumulação — aceitar |
| FORA_DOS_62_GAP | S40 (e S11-ish; T21/T22) | fatal-skip BLOCK / contraste fora do working-set A/B/C |

## 3. Limites honestos (a realidade estrutural impõe)
- **micro-topo vs micro-fundo (T17/T20 vs T21/T22/S12) é REAL visualmente, mas NÃO causalmente capturado.**
  Minha métrica de posição-no-range CONTRADISSE a leitura do Cris (T22/S12 = 0.96/0.99 "topo" por mim, mas
  micro-fundo/breakout bons por ele). O sinal verdadeiro é micro-estrutura de liquidez (reclaim-de-micro-fundo
  vs varredura-de-micro-topo), não posição-no-range. **Risco de ser parcialmente irredutível** (breakout-bom e
  micro-topo-ruim são idênticos à entrada — disfarce de liquidez).
  - **Misfire residual a anotar:** o carve-out bottom/turn v2 atualmente PRESERVA T17 (oversold 23.3 + reclaim 1.07
    + demanda defendida) — falso-positivo vs veredicto do Cris (BLOCK micro-topo). A regra CORRECTIVE/micro-estrutura
    futura precisa reverter este caso sem matar fundos genuínos (S15).
- **T23 "bear" pode usar hindsight:** à entrada (2022-03-24) o regime era TRANSITION, não bear; o markdown veio
  depois. Bloqueá-lo exige um sinal de bear **disponível à entrada**, não o markdown posterior.
- **Gap de working-set:** fatal-skips marcados BLOCK (S40, e similares) caíram fora dos 62 (A/B/C). Precisam de
  um set "must-stay-blocked" separado.

## 4. AUTO-CORREÇÃO (importante)
Eu **sobre-declarei "auction-irredutível"** num bloco anterior (chamei T17/T20/T23/T32 todos irredutíveis). O
review visual do Cris mostrou que **só T32 é genuinamente irredutível**; T17/T20 são um problema de
**feature-em-falta** (micro-estrutura), não irredutibilidade provada; T23 foi **erro do meu classificador D1**.
A "incapacidade dos agentes" não provou irredutibilidade — provou que o conjunto de features era insuficiente
(faltava micro-estrutura). Lição: não chamar "irredutível" antes de exaurir as features causais plausíveis.

## 5. Próximo passo (aprovado pelo Cris, depois desta consolidação)
**Adicionar regra CORRECTIVE** → recupera T12, T25, T26, S28 (baixo risco). Depois, em aberto: investigar a
micro-estrutura de liquidez (T17/T20) com humildade, e o sinal de bear-as-of-entry (T23). T32/S11 = aceitar.
Tudo nos 62; sem 276/OOS; sem chart/MCP.
