# XAU 4H L2/BPT v2.2 — Demand/Supply Distance-Quality Model

**Status:** `DIAGNOSTIC · HYPOTHESIS_ONLY · NOT_STRATEGY · NOT_VALIDATION` · **Data:** 2026-06-17
**RAW gz read-only · sem backtest/PnL/filtro/veto/plotagem/MCP/produção/SLIM.** Recall-first. Substitui presença binária por distância+qualidade.

---

## 1. Executive summary

Modelo causal de **distância + qualidade** demand/supply (Custom OB v11 as-of-bar) para os 2965 candidatos da PRUNED_BASE_V2. Discriminadores BOM↔NAO (event-level, **small-n 17/6 — hypotheses-only**):
- **Mais limpo:** `supply_dist_from_polarity_atr` **BOM 2.48 vs NAO 1.08** e `dist_4h_supply_low_atr` **BOM 1.93 vs NAO 0.78** → **NAO entra com a polaridade colada no supply (compra contra o teto); BOM tem espaço acima**.
- Demanda **abaixo existe em ambos** (17/17 e 6/6) — presença não separa; mas `DEMAND_SUPPORTING_RETEST` é mais comum em BOM (9/17 vs 2/6) e `demand_origin_of_leg` 8/17 vs 2/6.
- `quality_score_exploratory`: BOM 1.0 vs NAO 0.0 (composto direcional).
- **Crítico (proteção):** os BOM frágeis (GT13B/GT17A/GT24) têm **q=0 e supply perigoso** (FRESH_DANGEROUS / NEAR_REJECTING / BLOCKS_TARGET). Logo **nenhuma regra de qualidade-de-supply pode virar veto** — mataria winners.

## 2. Why binary demand/supply failed

`a6d8e3a` (UNTRUSTED) usou presença binária + tolerância 0.5ATR → `at_D1_demand=0/17` (artefato) e "supply domina ambos". A pergunta certa é **distância+qualidade+relação com polaridade**, não "tem/não tem". Reconciliação: `XAU_4H_L2_BPT_MACRO_CONTEXT_VISUAL_RECONCILIATION_AUDIT.md`.

## 3. Base and source confirmation

PRUNED_BASE_V2 = **2965 candidatos** (39 candidatos-BOM em 17 eventos, 14 candidatos-NAO em 6 eventos, 2912 UNKNOWN). Fonte: Custom OB Detector v11 `pine_boxes` (4H 240m gz + 1D gz), **as-of-bar (causal)**, zero SLIM. 77/2965 sem alinhamento 4H OB (bordas/gap, flagged).

## 4. Feature definitions

Por candidato (`results/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv`): distâncias demand/supply (top/mid/low em ATR), larguras, `touched_on_retest` (preço entrou na zona em ≤12 bars), `origin_of_leg` (topo da demand ≤1.5ATR da polaridade), `below_polarity`, supply `broken/rejected_before_entry`, `blocks_target_{2,3,4}ATR`, D1 demand/supply distance, relação com polaridade, `quality_score_exploratory`.
**UNAVAILABLE (não inventado):** `age_bars`/freshness (x1/x2 são ordinais, não temporais), `demand_below_stop` e R-targets exatos (v2.2 não tem SL → uso **targets ATR-proxy**, rotulados).

## 5. Demand 4H model

Demanda abaixo presente em **17/17 BOM, 6/6 NAO** (não separa). Distância ao topo da demand: BOM med 2.51 vs NAO 2.71 ATR (similar). Diferença qualitativa: `DEMAND_SUPPORTING_RETEST` BOM **9/17** vs NAO **2/6**; `origin_of_leg` BOM 8/17 vs NAO 2/6. → demanda **tocada/defendida no retest** e **origem da perna** lean BOM (fraco, small-n).

## 6. Supply 4H model

**Onde está o sinal.** `dist_4h_supply_low_atr` BOM **1.93** vs NAO **0.78**. Categorias: BOM = CLEAN_SKY(5)+SUPPLY_FAR_ENOUGH(5)=**10/17 favorável**; NAO = SUPPLY_NEAR_AND_REJECTING(3/6) dominante. `supply_broken_before_entry` = **0/17 e 0/6** (boxes mitigados saem da lista ativa → feature nula, inútil aqui). `blocks_target_2ATR` BOM 9/17 vs NAO 5/6 (NAO mais bloqueado).

## 7. D1 context model (contexto amplo, não veto)

`dist_d1_demand_atr` BOM 2.38 vs NAO 1.31; `dist_d1_supply_atr` BOM 1.18 vs NAO 2.16 (noisy, small-n). D1 = **contexto amplo** — demanda 1D existe abaixo de todos (~2 ATR); não usar como entry gate.

## 8. Polarity/BOS relation

**`supply_dist_from_polarity_atr` BOM 2.48 vs NAO 1.08** = o separador mais limpo: a polaridade do NAO está logo abaixo de supply (aceitação difícil); a do BOM tem espaço. `POLARITY_UNDER_SUPPLY_PRESSURE` é **NAO-exclusivo** (2/6 vs 0/17). ⚠️ `RECLAIM_REJECTED_BELOW_SUPPLY` aparece alto em BOM (9/17) — provável **artefato** do heurístico de "rejection" capturando o wick do reclaim atravessando o supply; **superficial, a refinar** (não usar).

## 9. BOM vs NAO comparison

`results/l2_bpt_v2_2_bom_nao_demand_supply_comparison.csv`. Respostas (small-n caveat):
1. BOM demand mais próxima? **Não** (similar ~2.5 ATR).
2. BOM demand de origem da perna? **Mais** (8/17 vs 2/6, fraco).
3. BOM toca/defende demand no retest? **Mais** (10/17 vs 3/6, fraco).
4. NAO supply mais próxima? **SIM** (0.78 vs 1.93 ATR) — sinal forte direcional.
5. NAO compra contra supply antes de aceitar? **SIM** (POLARITY_UNDER_SUPPLY_PRESSURE NAO-exclusivo).
6. BOM rompe/aceita supply antes? **Não detectável** (broken=0/0; boxes mitigados somem).
7. Supply perto é ruim sempre? **Não** — alguns BOM têm supply perto (GT01/GT24); depende de aceitação/contexto.
8. Demand abaixo ajuda ou é comum? **Comum** (não separa por presença).
9. D1 demand = suporte amplo? **Sim**, não entry context.
10. Relação demand/supply×polaridade separa melhor que presença? **SIM** — `supply_dist_from_polarity` é o melhor separador.

## 10. Fragile BOM protection

`results/l2_bpt_v2_2_fragile_bom_demand_supply_profile.csv`:
- **GT13B:** DEMAND_TOO_DEEP + SUPPLY_BLOCKS_TARGET, q=0.
- **GT17A:** DEMAND_SUPPORTING_RETEST + **SUPPLY_FRESH_DANGEROUS**, q=0.
- **GT24:** DEMAND_SUPPORTING_RETEST + **SUPPLY_NEAR_AND_REJECTING**, q=0.
- **GT23:** DEMAND_ORIGIN_OF_LEG + SUPPLY_BLOCKS_TARGET, q=1.

**Os frágeis parecem "ruins" pela qualidade de supply** (supply perto/bloqueando, q baixo). **Implicação dura:** vetar `SUPPLY_FRESH_DANGEROUS`, `SUPPLY_NEAR_AND_REJECTING` ou `SUPPLY_BLOCKS_TARGET` **mataria GT13B/GT17A/GT24/GT23**. → essas categorias **NUNCA viram veto**; no máximo visual_priority/human_review.

## 11. UNKNOWN ranking

`results/l2_bpt_v2_2_unknown_demand_supply_ranking.csv` (2912): BOM_LIKE_DEMAND_SUPPLY **1009** · NAO_LIKE_SUPPLY_PRESSURE **843** · CLEAN_BUT_UNPROVEN **494** · LOW_PRIORITY **489** · NEEDS_VISUAL **77**. ⚠️ ranking exploratório (categorias hypotheses-only, fragile-violations mostram que q baixo ≠ loser) — **nenhum promovido a trade**; serve para priorizar revisão visual.

## 12. Reason Atlas distance-quality v4

`results/l2_bpt_v2_2_reason_atlas_distance_quality_v4.csv` (16 reasons, side demand/supply/polarity). Roles: `POLARITY_UNDER_SUPPLY_PRESSURE` / `SUPPLY_NEAR_AND_REJECTING` → soft_warning (NAO-leaning, **não veto** — frágeis violam); `DEMAND_SUPPORTING_RETEST` / `CLEAN_SKY` / `SUPPLY_FAR_ENOUGH` → visual_priority/tag (BOM-leaning). Confidence **low** (BOM_ev=17, NAO_ev=6). Causal; age UNAVAILABLE.

## 13. What looks promising

- **Distância polaridade→supply** (BOM 2.48 vs NAO 1.08) e **dist supply** (1.93 vs 0.78): NAO compra contra o teto. Sinal estrutural coerente com o visual.
- `DEMAND_SUPPORTING_RETEST` / `origin_of_leg` lean BOM.
- Como **soft context / visual_priority**, não veto.

## 14. What is still superficial

- `rejected_before_entry` heurístico (conflita wick do reclaim com rejeição) — refazer.
- `supply_broken` = 0/0 (boxes mitigados somem) — feature morta como está.
- `origin_of_leg` = proxy (topo da demand ≤1.5ATR da polaridade), não a perna real do detector.
- `quality_score` é composto ad-hoc; frágeis com q=0 mostram que não prediz outcome.
- Tudo small-n (17/6) = calibração, não validação.

## 15. What must be visually reviewed

- Os 3 frágeis com supply perigoso (GT13B/GT17A/GT24): por que venceram apesar de supply perto?
- Os 843 UNKNOWN_NAO_LIKE_SUPPLY_PRESSURE vs os 1009 BOM_LIKE — amostra para o Cris confirmar no chart.
- A relação reclaim×supply (refinar rejection vs aceitação).

## 16. DA appendix

- SLIM? ❌. Diagnóstico UNTRUSTED como verdade? ❌ (citado só como referência refutada).
- Demand/supply por distância/qualidade, não binário? ✅.
- OB 4H analisado explicitamente? ✅ (distâncias, categorias).
- D1 como contexto amplo? ✅ (não gate).
- supply_overhead virou veto? ❌ — explicitado que mataria frágeis.
- Hard filter criado? ❌ — tudo HYPOTHESIS_ONLY/TAG_ONLY.
- Frágeis protegidos? ✅ §10 (e proíbem veto de supply-quality).
- UNKNOWN promovidos? ❌. Backtest/PnL/plotagem? ❌. Produção intacta? ✅. Caminho B? ❌.

**DA verdict: PASS — modelo distance-quality construído causalmente; melhor separador = distância polaridade→supply (NAO compra contra o teto, small-n); frágeis vencem APESAR de supply ruim → supply-quality não pode ser veto; nada promovido; produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv`, `_bom_nao_demand_supply_comparison.csv`, `_unknown_demand_supply_ranking.csv`, `_fragile_bom_demand_supply_profile.csv`, `reason_atlas_distance_quality_v4.csv`. Scripts: `demand_supply_quality.py` + análise (py_compile OK).*
