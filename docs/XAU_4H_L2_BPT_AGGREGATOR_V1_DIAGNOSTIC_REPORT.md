# AGGREGATOR v1 — RELATÓRIO DIAGNÓSTICO

**2026-06-19.** Escopo: XAU_4H_L2_BPT_BOS_CHOCH. **Diagnóstico/laboratório, NÃO promoção.** Rodou sobre a
população COMPLETA (276). Spec: `..._AGGREGATOR_V1_DIAGNOSTIC_SPEC.md`. Outcome só pós-hoc.

## Lógica v1 (resumo)
TAKE EXIGE âncora (`nas supportive` OU `demand_supply+risk_sl supportive`). Veto comum (DA/risk/exhaustion)
→ REBAIXA para REVIEW (não SKIP). SKIP só em falha fatal (late_top, exhaustion-hostile-sem-fundo,
no-demand+bad-risk, no-anchor em bear/late). capit+rsi = camada de refino que eleva REVIEW→TAKE só em
contexto permitido (bottom/demand/pullback/sweep). bubbles/bull_beta/volume/RSI-isolado NÃO podem dar TAKE.

## Resultados (de-capado, 276)
| bucket | n | /ano | exp/trade | PF | hit2R | maxDD | streak |
|---|---|---|---|---|---|---|---|
| **V1_TAKE** | 63 | 9.9 | **+0.959R** | 3.10 | 49% | −3.5 | 5 |
| V1_REVIEW | 41 | 6.5 | +0.414R | 1.71 | 29% | −7.7 | 6 |
| V1_SKIP | 172 | 27.1 | +0.235R | 1.44 | 26% | −19.5 | 15 |
| OLD_TAKE | 32 | 5.0 | +1.175R | 3.63 | 53% | −4.4 | 4 |
| V0_TAKE | 50 | 7.9 | +0.917R | 3.14 | 46% | −3.6 | 4 |

## Comparação
- **v1 > v0:** mais frequência (63 vs 50) + qualidade ligeiramente melhor (exp 0.959 vs 0.917, hit2 49% vs 46%, maxDD −3.5 vs −3.6). v1 corrigiu o veto-largo (veto→REVIEW) e ancorou em NAS/estrutura.
- **v1 vs OLD_TAKE:** v1 quase **dobra a frequência** (9.9 vs 5/ano) e **+60% de sumR** (60.4 vs 37.6R), ao custo de ~18% de expectancy/trade (0.959 vs 1.175) e PF (3.10 vs 3.63). DD melhor (−3.5 vs −4.4), streak +1 (5 vs 4). **É um trade-off throughput × seletividade** — para prop firm com PF ainda >3 e DD baixo, é atraente.
- **OLD_TAKE:** v1 manteve 21/32; rebaixou 11 (4 eram winners). **Novos TAKE: 42** (37 ex-REVIEW + 5 ex-SKIP), 18W/19stop (~49% — carregam via runners, mesma assimetria do TAKE).
- **REVIEW ficou útil** (não virou depósito): n=41, exp +0.41R/PF 1.71 — volume de conflito real para o humano.

## Regime-aware (TAKE por contexto)
bull_pullback_continuation 19 · demand_reclaim 17 · bottom_reversal_capitulation 14 · liquidity_sweep_reversal 11 · **bear_bounce só 2 · late_top 0**. → o TAKE concentra nos contextos permitidos; quase não vaza para bear/late. Coerente com a refutação OOS bear.

## Frequência operacional
TAKE ~9.9/ano · REVIEW ~6.5/ano · **TAKE+REVIEW ~16.4/ano** (~1.4/mês) = volume viável para prop-firm assistido por humano. Distribuição por ano relativamente estável (10-13 TAKE/ano 2020-2025; 2023 fraco com 5; 2026 parcial 1).

## Erros residuais (error_analysis)
- **DEMAND_SUPPLY_FALSE_POSITIVE: 25** — TAKE que stoparam com demanda "supportive" (zona não segurou) → maior alavanca p/ v2: qualidade da zona de demanda.
- **VETO_TOO_HARD: 40** — winners caídos em SKIP via fatal. **AMBÍGUO:** muitos são winners-sortudos em contexto adverso (late_top/bear) que a regra regime-aware corta de propósito; precisa inspeção visual p/ separar "corte correto" de "duro demais".
- NAS_OVERREQUIRED 5, GOOD_REVIEW_NOT_TAKE 3, OTHER 1 — baixos.

## Veredito
- **v1 melhora o v0** e oferece um perfil prop-firm interessante (≈2× frequência, +60% sumR, PF 3.1, DD −3.5R) — **mas NÃO supera o OLD_TAKE em qualidade por trade**; troca seletividade por throughput.
- **V2 recomendado (opcional):** (a) refinar qualidade da zona de demanda (cortar os 25 false-positives); (b) inspecionar visualmente os 40 fatal-skipped winners p/ calibrar se o fatal-SKIP está duro demais.
- **Pode ir para REVISÃO VISUAL:** sim — os 42 novos TAKE e os 40 fatal-skips são o material exato para o humano calibrar (liga com a política visual).
- **Está LONGE de promoção:** sim. Pesos/limiares v1 são escolhas de design não validadas OOS; capit+rsi segue CONTEXT_ONLY. Nada disto vira regra/Telegram/produção.

## Próximos passos
1. (humano) revisar visualmente os 42 novos TAKE + 40 fatal-skips. 2. (opcional) v2 com qualidade-de-demanda. 3. só MUITO depois, se algo convergir, considerar promoção via Hypothesis Registry + gate + autorização explícita.
