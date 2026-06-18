# XAU 4H L2/BPT — Entry Selection / Timing: PRÉ-REGISTRO

**Status:** `PRE-REGISTERED · NOT_STARTED · AWAITING_APPROVAL` · **Data:** 2026-06-18
Bloco de retrabalho de ENTRADA. Pré-registrado ANTES de qualquer medição. Sem plotagem. Não medir até autorização.

---

## 0. Estado herdado (fixo neste bloco)
1. **SL = SL_CONTEXT_DEMAND** (demanda 4H, repaint-auditado) — operating point aprovado. Não mexer.
2. **Exit = partial50@2R+6R** — fixo. Não mexer.
3. **BOS/CHoCH NÃO é a fonte de edge** (teste de atribuição) — NÃO refinar o trigger BOS.
4. **Baseline real = LONG ALEATÓRIO CASADO POR LEGPOS.** F_STRICT = 1º exemplo positivo (remove entrada ruim, não cria edge sozinho).

## 1. REGRA DURA (inviolável)
> **Qualquer entrada nova só importa se BATER o long-random-matched-by-legpos. Senão é só drift.**
Toda hipótese é medida como **delta vs baseline legpos-random** (mesma composição de legpos bucket, entradas aleatórias, mesma mecânica SL_CONTEXT_DEMAND + partial50), com bootstrap. Delta dentro do ruído (P<~0.9) ou Bonferroni-fail = REJEITADA (não "ganhou dinheiro" ≠ edge).

## 2. As 3 hipóteses (só 3, sem grid)

### H1 — DEMAND_BACKED_ENTRY
Entrar só quando há **demanda 4H próxima/defendida** (a mesma zona que ancora o SL): `dist_4h_demand_low_atr ≤ θ` (θ a fixar, ex. ≤2-3ATR) E `demand_4h_touched_on_retest=1`. Hipótese: entrada demand-backed bate o legpos-random (a demanda defendida — não o BOS — é o que dá o edge + SL tight, como E17).

### H2 — RECLAIM_TIMING
Dentro de um cluster (múltiplos reclaims na mesma perna), escolher **o reclaim certo** — evitar prematuros (E25/E26) e pegar o real (E27). Regra causal a definir (ex.: o reclaim após o pullback mais profundo / após toque de demanda / 1º reclaim que segura acima da polaridade por K barras). Hipótese: timing-de-reclaim bate (a) o 1º-sinal atual e (b) o legpos-random.

### H3 — NO_TRADE / TOP / LATE FILTER
Aplicar **F_STRICT (legpos≥85 & RSI≥70)** + sinais late/top como CORTE. Hipótese: o conjunto MANTIDO (pós-corte) bate o legpos-random (i.e., a remoção seleciona melhor-que-drift). NB: F_STRICT já mostrou remoção near-breakeven em R — o teste aqui é se o KEPT supera o baseline legpos-casado.

## 3. Metodologia (obrigatória)
- **Baseline:** long-random-matched-by-legpos (recomputar a composição legpos do subset de cada hipótese; amostrar random com a mesma distribuição de legpos).
- **Mecânica fixa:** SL_CONTEXT_DEMAND + partial50@2R+6R + custo 0.10R.
- **Classificação por TIPO DE SAÍDA** (target/partial/runner/stop/time), NUNCA R-sign.
- **Recall-gate:** não matar must-preserve (E1,E5,E13,E17,E21,E27,E30,E40) sem justificativa.
- **Bootstrap 5000:** delta_avgR/sumR/DD vs baseline, CI 5/50/95, P(delta>0); **Bonferroni ×3**.
- **Split temporal** 2020-22 / 2023-26.
- **RAW audit** dos campos (demanda já auditada causal; reclaim-timing precisa de def causal sem lookahead).
- **Sem plotagem** neste bloco.

## 4. Não fazer
Não refinar BOS · não mexer SL/exit · não SLIM · não outcome-future · não declarar edge sem bater o legpos-random + bootstrap + Bonferroni · não plotar · não produção · não promover.

## 5. Outputs previstos (quando autorizado)
`results/l2_bpt_entry_sel_{baseline_legpos_random,H1_demand,H2_timing,H3_filter,bootstrap}.csv` + doc `XAU_4H_L2_BPT_ENTRY_SELECTION_TIMING_RESEARCH.md` + DA obrigatório.

---

*Pré-registro. NÃO medir/plotar sem autorização explícita do Cris. Foundation: [[XAU_4H_L2_BPT_ENTRY_ATTRIBUTION_BOS_NOT_EDGE]].*
