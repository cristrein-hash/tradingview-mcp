# XAU 15M LONG — Leitura Estrutural TOTAL (re-estudo dos 22 prints #1-#96)

**Data:** 2026-07-07 · Pedido do Cris: "faça leitura estrutural TOTAL reestudando os prints". Ground-truth: 96 trades com outcome (32/32 alinhados). Preços reais do ouro Ago/2025→Jul/2026.

## As 4 FASES do ciclo macro (a leitura que separa)

Re-estudando os prints, cada trade cai numa de 4 fases macro. Winner/loser NÃO é forma da perna nem proximidade de demanda (ambos win e lose colam a demandas) — é a **POSIÇÃO NO CICLO**:

### FASE A — MARKUP ATIVO (uptrend limpo fazendo higher-highs) → WINNERS
Pullback dentro de tendência que ainda estende. Ago-Set (escada PLT/DM), Nov, Dez, fim-Mar/Abr, Jul.
Ex.: #1R, #11-14, #28-30, #44R-45, #71R-75R, #95R-96.

### FASE B — INICIAÇÃO DE PERNA / REVERSAL BOTTOM GENUÍNO (flush a demanda válida + CHoCH-up, começa nova perna) → WINNERS (mesmo intra-bear)
O 1º reclaim depois de um FLUSH fundo a uma demanda válida, INICIANDO a subida. Distinto do topo.
Ex.: **#82R** (fundo Mai, flush + reclaim), #61R-63 (fundo Fev), #26R (fundo Out-Nov), #95R.

### FASE C — DISTRIBUIÇÃO DE TOPO (markup exausto; overlapping/choppy nos máximos, EQH, CHoCH-down a formar) → LOSERS
Compra TARDIA depois da perna já ter corrido, a perseguir para dentro da exaustão. NÃO inicia, distribui.
Ex.: **#21,#23,#24,#25** (topo Out ~4380), **#31** (topo Nov), **#55** (topo spike Jan 5060), **#56,#57,#59,#60** (chop pós-topo Fev), **#65,#67** (topo Mar), **#79,#83,#84,#85** (topo Mai ~4700).

### FASE D — BEAR DOWNTREND ATIVO (lower-highs/lower-lows, BOS-down) → LOSERS
Comprar contra estrutura descendente. Ex.: **#66,#68,#69** (Mar, "perna bear clara antecede"), **#86,#87R,#89R,#92,#93R,#94** (Mai-Jun), #49,#50 (falsos fundos em polaridade-topo).

## O separador REAL (do re-estudo)

**#82R (winner) vs #83,#84,#85 (losers) — todos intra-bear, todos em demanda:**
- #82R = **INICIAÇÃO** (Fase B): flush fundo → 1ª recuperação off a demanda → CHoCH-up → começa perna nova.
- #83,#84,#85 = **CONTINUAÇÃO-em-EXAUSTÃO** (Fase C): a perna já correu de #82R, agora distribui no topo; comprar aqui = perseguir.

→ **O discriminador não é bear-vs-bull nem perto-de-demanda. É: INICIAÇÃO-de-perna (Fase B, off flush a demanda com CHoCH-up) vs CONTINUAÇÃO-em-exaustão (Fase C) vs BEAR-ativo (Fase D).** Winner = Fase A (markup ativo) ∪ Fase B (iniciação genuína). Loser = Fase C (distribuição-topo) ∪ Fase D (bear-ativo).

Isto reconecta ao trabalho original swept-runner/RWS: o fundo genuíno = SWEEP/flush a demanda + reclaim (iniciação). Os topos-exaustão = sem flush fresco, só chase.

## Verificações honestas (o que NÃO separa)
- Proximidade a demanda causal (born<entry): NÃO separa — WIN med 0,05 vs LOSE 0,04; quase toda entrada cola a demanda. (`check_bear_demand_thesis_20260707.py`)
- Fase-descriptors isolados (failed_high, choch_down, overlap_top, dist_major_low): NÃO separam — #82 (winner) ≡ #83/#85 (losers) nesses eixos. (`read_exhaustion_phase_20260707.py`)
- Bear-detection por EMA/lower-high: inconsistente com a leitura macro do Cris (#55,#65,#67,#79,#84 saem "não-bear").

## Implicação para o engine
O alvo NÃO é "cortar bear" nem "exigir demanda" (ambos falham). É **distinguir INICIAÇÃO-de-perna (Fase B) + MARKUP-ativo (Fase A) de CONTINUAÇÃO-exaustão (Fase C) + BEAR-ativo (Fase D)** — um classificador de FASE do ciclo, multi-fatorial, sequencial, causal. A ser construído e verificado (lookahead-audit + null + poison + por-ano) antes de qualquer número chegar ao Cris.
