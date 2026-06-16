# Rebuild v3 — XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5
2026-06-15 · RECONSTRUÇÃO. NÃO valida, NÃO promove, NÃO popula registry.

## Mudança vs v2 (decisão Cris)
- **NÃO mudar o stop** (mantido o estrutural; largo = respiro/RxR para winners).
- **Removido o R_CEIL 1.5ATR abort** — era ele que abortava 35/38 e matava os KEEP no v2 (não o cooldown). Esse era o conserto real.
- Classes VISUAIS do Cris aplicadas: KEEP(19)/BLOCK_TOP(17)/BLOCK_STOP(#5)/REVIEW(#31).

## Resultado
- KEEP(19): **+32.6R, WR 57.9%, avgR 1.72, DD 1.3R** → ~ documentado (n=16/+31.74R) → **base rule + SL RECONSTRUÍDOS FIELMENTE**.
- BLOCK_TOP(17): −15.6R, WR 5.9% → losers reais (classificação visual do Cris empiricamente correta).
- FULL 38: +14.9R, WR 31.6% (base sem filtro = fraca). #5 −1.1R, #31 −1.1R.

## Devil's Advocate — NEEDS_CAUSAL_FILTER_BEFORE_ANY_CLAIM
- **KEEP +32.6R é ARTEFATO IN-SAMPLE**: Cris rotulou KEEP/BLOCK olhando o chart com o resultado visível (hindsight). DD colapsar 7.9→1.3R é o tell de seleção por outcome. NÃO é edge.
- **FULL-38 +14.9R/avgR0.39** = a única expectância de uma regra causal hoje = fraca, frágil a slippage.
- **Composto objetivo NÃO reproduz o BLOCK_TOP visual** (8/17, erra 6 KEEP winners) → o julgamento visual codifica info que as features não capturam → **NÃO mecanizável agora**.
- Sem leak temporal novo (NAS first-appearance, swing 5/5, regime D-1, R por forward bars OK). O risco é seleção/hindsight + n pequeno (KEEP n=19, Wilson largo).

## Landing honesto
- A reconstrução do **base rule + SL está FIEL** (o conserto era remover o R_CEIL, como o Cris intuiu).
- O **filtro de losers (BLOCK_TOP) é VISUAL/discricionário**, não codável pelo composto simples — consistente com a decisão do Cris ("composto/REVIEW, não 1 filtro").
- Para CLAIM de edge / automação: precisa de filtro causal que reproduza o BLOCK_TOP, OU operar L1 como **discricionário humano-in-the-loop** (alinha com a filosofia do projeto: decisão visual humana, não automação).
