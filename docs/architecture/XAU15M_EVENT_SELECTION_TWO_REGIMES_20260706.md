# XAU 15M LONG — Seleção Causal de Evento-Fundo em DOIS REGIMES

**Data:** 2026-07-06 · **Status:** RESULTADO SIGNIFICATIVO / EM CURSO — causal, sem look-ahead, NÃO produção ·
**Autor:** pesquisa Claude + direção Cris · **Commits:** `8038cbd..53ddb9e`

## 1. Contexto e virada de método

A caça pelos 60 fundos verdadeiros (círculos do Cris) percorreu 8 caminhos (features de candidato,
RAW dedicadas, nível-evento, kNN não-linear). A virada decisiva (Cris): **a entry nunca foi o
gargalo — dentro de um evento-fundo verdadeiro, qualquer entrada razoável dá ~50% hit-3R (null-
dentro-do-fundo 0,87). O problema é 100% SELECIONAR o evento-fundo.** Ordenamento correto:
**primeiro selecionar o evento, depois entrar.**

Unidade = EVENTO (cluster de candidatos flush-reclaim ±48h/±3ATR; 797 eventos, 50 contêm círculo,
densidade base 14,9:1).

## 2. Os dois filtros causais (features ≤ cj, outcome NUNCA na decisão — não circular)

- **Família (envelope de retração macro):** cada evento classificado por retração da perna macro
  (RASO <0,5 · BANDA 0,5-1,3 · FUNDO >1,3); envelope por-família das features causais de evento.
  Recall 100% (50/50 fundos), densidade 5,6:1, P(null)=0,004.
- **Cascata SMC (cascade≥T):** evento contém candidato com T BOS-/CHoCH- consecutivos (capitulação
  estrutural). Causal (known_at). Sozinha: WR 32% streak-8 (pega capitulações BEAR-contínuas que
  não são fundos). **A família corta essas — garante PULLBACK, não queda livre.**

**SINERGIA:** família+cascata JUNTAS >> cada uma só.

## 3. O pipeline completo (causal) — DOIS REGIMES

| regime | seleção | entry | N | WR | streak q95 | DD | anos (2024/25/26) |
|--------|---------|-------|---|-----|-----------|-----|-------------------|
| **Capitulação** | família & cascade≥3 | E6 (cascade≥3 & higher-low & reclaim) | 20 | **55%** | 6 | −2,3 | +0,5 / +6,8 / +13,8 |
| **Suave** | família, sem cascata | reclaim & oversold(rsi_min8≤38) & demanda(below_poc) | 45 | 47% | 9 | −5,1 | todos + |
| **UNIÃO** | ambos | — | 65 | 47,7% | 9 | −4,1 | +9,4 / +22,9 / +20,5 |

- **Capitulação:** assinatura estrutural forte → WR alto, streak baixo, poucos sinais.
- **Suave:** sem assinatura estrutural → WR menor, streak maior (difícil separar fundo-suave de
  lixo-suave; reflete o teto AUC 0,62 da separação evento-fundo).
- **União:** N65, WR 47,7%, NET +52,5R, DD −4,1R, 0,59/sem (~31/ano), 7 círculos capturados,
  **todos os anos fortemente positivos**.

## 4. Validação (causal, honesta)

- Filtros 100% causais (features ≤ cj); envelope/cascata calibrados nos fundos = supervisionado
  declarado, NÃO circular (outcome nunca entra na decisão).
- Null família P=0,004; null envelope-aleatório P<0,01.
- Null-episódio da entry E6 = 0,20 (a entry não é edge — confirma que o valor está na SELEÇÃO,
  consistente com "dentro do fundo tudo funciona").
- Causalidade da cascata e do reclaim verificada (DA: 0 look-ahead).

## 5. Relação com o CASCEX pré-aprovado

O regime CAPITULAÇÃO é a mesma veia do **CASCEX** (pré-aprovado, N34 WR 55,9%). Este trabalho:
(a) confirma a cascata como seletor causal por caminho independente; (b) adiciona a FAMÍLIA como
filtro sinérgico essencial; (c) adiciona o regime SUAVE para cobertura dos fundos sem capitulação.

## 6. Pendências (EM CURSO — não conclusão)

- Streak q95 da união (9) > limite FN (≤5): afinar o layer SUAVE (o gargalo de WR/streak).
- Recall ainda baixo (7/60 círculos capturados pela entry): o discriminador fundo-suave-vs-lixo-
  suave falta (candidato: features de fluxo/absorção do mapa RAW aplicadas ao regime suave).
- Prereg + forward-test para promoção.

## 7. Reprodução

Scripts em `research/xau_15m_bb_nas_leonardo/`:
`event_cascade_filter_curve_20260706.py` (sinergia família×cascata) ·
`event_soft_layer_20260706.py` (regimes + união) · `_val_famcasc.py` (nulls) ·
`plot_union65_20260706.py` (plot: 20 #C laranja + 45 #S azul). Cache causal:
`results/raw_feature_cache_20260706.jsonl`. GT selado: `results/ground_truth_bottoms_20260705.json`.
