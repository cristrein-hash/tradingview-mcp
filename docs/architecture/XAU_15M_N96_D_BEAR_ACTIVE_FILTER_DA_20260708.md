# XAU 15M LONG · N96 · D (Bear-Active) Round · Devil's Advocate

**2026-07-08.** Checagem adversarial da rodada D-bear-active. Read-only. Números reproduzidos de `n96_d_bear_active_filter_analysis.py` + scratchpad (da_search/da_null/da_raw).

## Veredito: `NO_ADDITIONAL_GATE_INTRABEAR_SUFFICES` — ganho, mas o raciocínio da rodada estava em parte errado e escondia um confound maior.

## Evidência por ataque
**A/F — Causalidade & Source: PASS.** Features do kit RAW-native causal (`bars_upto` exclui barra HTF corrente; zones born_t; bubbles known_at). Sem SVP/Fractal-MTF/resample. Spot-check RAW byte-level: #94 1D_px_vs_ema=(4189,98−4611,41)/7,847=−53,7 (CSV −53,704); #93 −51,4; #92 −27,3; #89 −20,9 — exatos de `htf_primitives/htf_1D`.

**B — "todo corte é profit-negativo" = FALSO (imprecisão da rodada).** Só se testaram q0,4/0,5/0,6 em eixos únicos (esses são −6…−14R). Busca exaustiva single+pair acha cortes **+R limpos in-sample**: `rangewidth≤6,62`→{77,86,87,92}=**+4R/0W**; par `demand_room≤0,568 & 1D_ema_trend≥−7,47`→{80,86,87,89,93,94}=**+6R/0W**. **O motivo real de falhar = MULTIPLICIDADE:** mining-null (baralha DEEP outcomes, repete a busca) dá ≥+6R em **39,7%** das vezes (P=0,40). Os cortes limpos são winner's-curse.

**C — Runner preservation: corte largo é catastrófico.** `rangewidth≤q0,6` corta 14=7L mas destrói 7 winners de capitulação {26,71,73,74,75,76,82}=−21R. Base 2:1 winners no pool ⇒ cortes largos sangram R.

**D — "faca quieta vs capitulação violenta" = real univariado mas frágil.** Null de permutação intra-DEEP (5000): `rangewidth` AUC 0,781 **P=0,028**; `demand_room_4h` 0,777 **P=0,030**; `rotational_smc` 0,750 **P=0,046** — sobrevivem individualmente. MAS `bub_sell_ml` (o "sell-climax absorbido" que destaquei) AUC 0,699 **P=0,103 FALHA**. Sob ~15 features, P~0,03 é Bonferroni-borderline. Direccionalmente real, fraco/correlacionado demais para gate.

**E — mis-bucket #49,50,27 não distorce.** O pool DEEP exige REG=BEAR → causal-BULL #49,50 (px +16/+23) e RANGE #27 ficam FORA do pool. Labels de subfamília são decorativos (#86,89,92,93,94 marcados "capitulacao_valida" mas perderam). **#77 no "8 deep losers" é família MGMT, não D** → só 7/8 são D. A faca NÃO é estritamente inseparável: `demand_room_4h≤0,21` isola {89,93,94} (sem demanda por baixo = free-fall) — mas ver caveat.

**G — negativo é GANHO, não preguiçoso.** Estrutural-primeiro + busca completa (single+pair, 84-feat+auction+bubbles+SMC) + mining-null + objetivo-lucro.

## Caveat central (não divulgado pela rodada)
**O cluster deep-knife é um confound stale-HTF / episódio único.** `htf_1D` acaba **2026-05-24**, `htf_4H` **2026-06-09**; entries #88-96 leem uma **EMA 1D congelada (4611,41 de 24-mai)**. 4 dos 8 deep-losers (#89,92,93,94) são Jun/2026, num único declínio ~3-sem (5-22 jun; #93/#94 mesmo dia), e a "profundidade" extrema (px −20 a −54) está **amplificada por uma EMA de um mês atrás durante uma queda**. O corte `demand_room_4h` que "isola" #89,93,94 apoia-se em zonas 4H que pararam de atualizar em 9-jun. Reforça "sem gate" mas devia ter sido divulgado.

## Bottom line
- **Confirmado:** intra-BEAR (SKIP se BEAR & 1D_px_vs_ema≥0) = 13L/0W = +13R limpo, corta D #66,67. Camada correta.
- **Nenhum gate D adicional sobrevive multiplicidade honesta** (melhor minerado +6R → P=0,40).
- **A faca NÃO é estritamente inseparável** (rangewidth/demand_room/rotational univariado P 0,03-0,05) **mas a separação é frágil demais** (N=8 losers, features correlacionadas, multiplicidade, concentração stale Jun/2026) para virar gate.
- **Residual defensável = REVIEW-LAYER FRACO só** (flag, nunca auto-skip): dip fundo QUIETO + range estreito + sem demanda-4H = risco de faca. Confundido pelo gap de cobertura.
- **Recomendação:** estender `htf_1D`/`htf_4H` pós-2026-05-24/06-09 e re-correr antes de qualquer confiança — 4/8 deep-losers montam em referência HTF congelada.
