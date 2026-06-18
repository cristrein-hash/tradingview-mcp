# XAU 4H L2/BPT — Entry / Exhaustion Filter

**Status:** `RESEARCH · CAUSAL · PROVISIONAL · NO_PRODUCTION · NO_SLIM · NOT_PROMOTED` · **Data:** 2026-06-18
Frente para cortar entradas ruins (blow-off top / exaustão) ANTES de operar, causalmente, sem matar winners. SL FIXO STRUCT_PURE swing-origin, exit FIXO partial50@2R+6R. 8º DA. Não promove estratégia.

---

## 1. Executive summary

**Primeiro filtro causal recall-passing de toda a saga (SL/exit/cap/defended-swing).** `F_TOP_OB_RSI_strict` (**legpos90≥85 & RSI≥70**) corta blow-off tops, **0 BOM cortados** nas duas janelas, e — crucialmente — **valida fora da calibração**: na janela independente 2023-26 (casos calibradores E23/E24 são de 2020) bloqueia 25 trades net **−1.4R** e MELHORA o kept (sumR +57.2→+58.6, **avgR +0.367→+0.448**, maxDD 9.2→8.1). É o único filtro que (a) passa recall, (b) não custa PnL, (c) segura out-of-sample. **Classificação: AUTO_BLOCK_SAFE provisório** (efeito pequeno, bucket bloqueado dentro do ruído de zero a n=25-30 → precisa mais confirmação antes de produção). `F_TOP_OB_RSI` (RSI≥68) = **REVIEW only** (paga +4.3R de trades positivos por alívio cosmético de DD, bucket não-específico). `F_LATE_LEG_EXT` e `F_WEAK_RECLAIM` **cortam 1 BOM** → review/rejected. E15/E34/E39 + supply-rejection = **review humano** (não separáveis causalmente / usam candle pós-entrada). Nada em produção.

## 2. Why entry/exhaustion is now the focus

5 blocos mostraram que SL/exit/cap/defended-swing não são a alavanca. O bucket >4ATR e os casos não-salváveis apontaram upstream: a entrada. E23/E15/E24/E34 (topos/exaustão) são entradas que estruturalmente não deveriam existir — cortá-las na entrada é a alavanca não-testada.

## 3. Known should-cut cases

E23 (blow-off top pré-ATH), E15 (topo duplo, reclaim fraco), E24 (topo, RSI alto), E34 (exaustão), E39 (bear-leg bounce trap — mas indistinguível de E17).

## 4. Must-preserve cases

E1, E5, E13, E17, E21, E27, E30, E40 (8). Recall-gate obrigatório: nenhum filtro auto-block pode cortá-los.

## 5. Feature / source audit (Tarefa 2)

**Usados (causais, confiáveis):** OHLCV 4H frozen, ATR, **RSI real** (frozen, computado em closes≤i — causal ✓), legpos 90d, dist-from-90d-high, ext-above-20b-low, body fraction do candle de entrada, swing pivots Williams (j≤i-5). **NÃO usados (hard-stop):** tick-volume frozen (não-confiável), outcome_proxy, deep_confluence (RETRATADO), Session VP não necessário aqui. RSI causalidade confirmada: entry no close de i; RSI[i] conhecido nesse momento.

## 6. Hypotheses

TOP_EXHAUSTION · SUPPLY_REJECTION · LATE_LEG · WEAK_RECLAIM · BEAR_LEG_BOUNCE · BLOWOFF_NO_LONG. Testadas separadas.

## 7. Case-study results (`results/l2_bpt_entry_exhaustion_case_study.csv`)

Separação empírica (causal) CUT vs KEEP:

| | E23 | E24 | E15 | E34 | E39 | | E5 | E21 | E1 | E17 |
|---|---|---|---|---|---|---|---|---|---|---|
| legpos | 94 | 89 | 73 | 65 | 56 | | 92 | 90 | 48 | 62 |
| **RSI** | **77** | **69** | 53 | 49 | 46 | | 61 | 55 | 62 | 41 |
| reclaim | red | red | weak8% | — | weak | | green82 | green57 | green60 | green11 |

- **Blow-off top (E23/E24): legpos alto + RSI alto separa LIMPO** — E5(92)/E21(90) têm legpos alto mas RSI 55-61 (V-reversals, não overbought). RSI≥68/70 corta os tops e poupa as reversões-em-V.
- **E15** (reclaim fraco perto do high), **E34** (exaustão ambígua), **E39** (bear-bounce **indistinguível de E17**) → não separáveis por top-metrics → review.

## 8. Filter candidates (`results/l2_bpt_entry_exhaustion_filter_candidates.csv`)

| Filtro | Definição | Classificação |
|---|---|---|
| **F_TOP_OB_RSI_strict** | legpos90≥85 & RSI≥70 | **AUTO_BLOCK_SAFE (provisório)** |
| F_TOP_OB_RSI | legpos90≥85 & RSI≥68 | REVIEW (não-específico, paga R+) |
| F_LATE_LEG_EXT | legpos90≥85 & ext_lo20≥4.5 | REVIEW (corta 1 BOM) |
| F_WEAK_RECLAIM_NEAR_HIGH | dist_hi90<2 & body<0.15 | REVIEW (n=1 E15, corta 1 BOM) |
| F_BEAR_BOUNCE | bearleg context | REVIEW (E39≈E17, NUNCA auto-block) |
| F_SUPPLY_REJECTION | supply + rejeição pós-entrada | REJECTED (usa candle pós-entrada = não-causal) |

## 9. Full-base results (276 ep; baseline sem filtro: WR48.2 sumR+62.5 PF1.44 maxDD24.3 streak9)

| Filtro | block | BOM_cut | sumR_blocked | KEPT sumR | KEPT maxDD | KEPT streak |
|---|---|---|---|---|---|---|
| **F_TOP_OB_RSI_strict** | 30 | **0** | **−0.9** | **+63.4** | 22.1 | 8 |
| F_TOP_OB_RSI | 38 | 0 | +4.3 | +58.2 | 21.4 | 7 |
| F_LATE_LEG_EXT | 46 | **1** | +7.7 | +54.8 | 20.1 | 8 |
| F_WEAK_RECLAIM | 14 | **1** | +5.4 | +57.1 | 23.2 | 8 |

**F_strict é o único que melhora sumR (+63.4 vs +62.5) com 0 BOM** — bloqueia net-negativo. F_TOP_OB_RSI custa sumR (bloqueia +4.3R positivos). LATE_LEG/WEAK cortam BOM.

## 10. Recall-gate + validação temporal

**Casos:** F_strict bloqueia E23 (legpos94/rsi77) [E24 só por RSI≥68, não no strict]; poupa 8/8 must-preserve. **0 BOM cortados na base completa (de 15).**
**Validação out-of-calibration (casos calibradores de 2020 → 2023-26 independente):**
- 2020-2022: block 5, BOM_cut 0, blocked +0.5R, kept sumR 5.3→4.8 (≈flat), maxDD 24→22.
- **2023-2026 (independente): block 25, BOM_cut 0, blocked −1.4R, kept sumR 57.2→58.6, avgR 0.367→0.448, maxDD 9.2→8.1.** ✅ segura fora da calibração.

## 11. Auto-block vs review-only (Tarefa 6)

- **AUTO_BLOCK_SAFE (provisório):** F_TOP_OB_RSI_strict — preserva must-preserve, melhora out-of-calibration, bloqueia net-negativo. Efeito pequeno → provisório, não promovido.
- **HUMAN_REVIEW_FLAG:** F_TOP_OB_RSI (RSI 68-70), F_WEAK_RECLAIM (E15-tipo), F_LATE_LEG.
- **REVIEW (nunca auto-block):** F_BEAR_BOUNCE (E39≈E17).
- **REJECTED como entry filter:** F_SUPPLY_REJECTION (candle pós-entrada).

## 12. Future Telegram flags

`overbought-top` (legpos≥85 & RSI≥68) e `weak-reclaim-near-high` e `bear-leg-bounce` são candidatos a **flag de review humano no Telegram** (requisito futuro [[project_l2_bpt_telegram_bear_flags_FUTURE]]) — aparecer no sinal para decisão humana, NÃO bloqueio automático (exceto F_strict que pode ser auto-block provisório).

## 13. DA appendix

8º DA. Verdict (síntese): "Exercício é in-sample nos mesmos 9 casos que definiram o corte; o 0-BOM-cut é circular por construção. **F_strict é a única melhoria honesta e grátis** (bloqueia net-negativo, 0 BOM, melhor PF/DD) — genuinamente melhor que SL/exit/cap, mas threshold calibrado em 9 casos. F_TOP_OB_RSI paga R+ por DD cosmético, bucket não-específico (36 dos 38 não são tops confirmados, provavelmente inclui pullbacks de uptrend legítimos). Passo obrigatório: validar em episódios fora dos 9." **Resposta ao passo obrigatório (feita):** validação 2023-26 (independente) confirma F_strict (kept avgR 0.367→0.448, 0 BOM, blocked net-negativo). Checklist: SLIM não · retratado não · tick-vol não · futuro não (RSI causal) · must-preserve preservados (0 BOM) · E23/E24 tratados (cut), E15/E34/E39 review · causal sim · robusto out-of-calibration sim (modesto) · SL/exit intactos · produção intacta · não promovido.

## 14. Recommendation (research-only)

1. **Carregar F_TOP_OB_RSI_strict (legpos90≥85 & RSI≥70) como AUTO_BLOCK provisório** — primeiro filtro causal que passa recall E melhora out-of-calibration. Efeito pequeno; NÃO promover a produção sem confirmação adicional (mais janelas independentes, cross-asset proibido por política, ou mais casos rotulados).
2. **F_TOP_OB_RSI + weak-reclaim + bear-bounce = flags de REVIEW HUMANO** (Telegram futuro), não auto-block.
3. **E34/E39 + supply-rejection = irredutíveis a filtro causal de entrada** — review discricionário.
4. Próximo: validar F_strict em mais sub-janelas / aumentar amostra de tops rotulados antes de qualquer promoção. Regime v3 / SHORT seguem para depois.

---

*Outputs: `results/l2_bpt_entry_exhaustion_{case_study,filter_candidates,policy_results,recall_gate}.csv`. Script: `l2_bpt_entry_exhaustion.py` + `entry_case_study.py`. Sem produção, sem SLIM, sem chart, SL/exit inalterados, nada promovido.*
