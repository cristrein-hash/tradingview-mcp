# MACRO STRUCTURAL FEATURE CENSUS — XAU 4H L2/BPT

**2026-06-21.** Censo auditável de TODAS as fontes úteis para um Macro Structural Reading Engine.
Princípio: **fraqueza isolada ≠ inutilidade** (lição capit+rsi). Nada podado por fraqueza individual;
só o MORTO (não-populado) é excluído. CSV: `results/l2_bpt_macro_structural_feature_census.csv` (122 features).

## Distribuição
- 122 features · 6 fontes · status: 3 MORTA · 2 SUSPEITA · 3 FORTE · 9 MODERADA · 34 FRACA · **63 NÃO-TESTADA** · 1 ARTEFATO · 4 PARCIAL_NULL · 2 categóricas-não-usadas-como-input.
- **63 NÃO-TESTADAS = o universo macro que nunca entrou em confluência** (regime_B_v3 quase todo, semanal, SVP, dist_POC/VAL, demand age/width/origin, etc.).

## A. Packet 84 fatores (78 citáveis, 17 famílias)
Inventariadas no CSV com família/timeframe/causalidade/status. Destaques de status:
- **MORTA (excluir):** `macro_leg_direction`, `macro_leg_phase` (REFERENCE_ONLY), `demand_age_bars` (UNAVAILABLE).
- **ARTEFATO (forbidden):** `hour_utc` (session-time, overfit na árvore regime_v1).
- **FORTE:** `has_4h_supply_overhead` (gate), `has_d1_supply` (no-supply-D1=ATH sinal), `nas_long_new_8b`.
- **SUSPEITA:** `dist_4h_supply_low_atr` (forte-isolada mas artefato sem overhead), `reclaim_dist_from_supply` (colinear).
- **FRACA (manter p/ confluência):** capit (drop20/rsi_min/sweet_spot), bubbles (11), legpos (condicional a momentum), rsi/rsi_1d, exhaustion, sl_atr (eixo risk_sl/T34), demanda 4H.

## B. Externas macro (causal via shift) — a riqueza ignorada
- **`regime_B_v3` — 30 campos, só 2 testados.** Vocabulário macro intocado: `cascade_score`, `vol_score`, `combined_score`, `stage_dir/stage_n`, `atr_expansion_ratio`, `distribution_flag`, `stall`, `sharp_drop`, `dist_alarm`, `macro_broken`, `h4/d/w_break_bear/bull`, ma_50/200. Causal via **shift D-1** (validado regime_v1: 0 join_issues).
- **`regime_l1_v4`** + `slope/rsi` 1D.
- **`xau_weekly_with_features` — 3º TIMEFRAME, nunca usado** (rsi/ma20/ma50/slope/atr semanais; prev-closed-week = causal).
- **`xau_daily_with_features`** (1D OHLC+indicadores).

## C. Volumetria
- **tick-volume (raw_features):** NÃO-CONFIÁVEL → não usar como volume macro.
- **Session VP nativo (`svp_bars.jsonl`):** CONFIÁVEL (volume REAL, 100% match fundos). POC/VAH/VAL + vol + below_VAL/dist_POC/dist_VAL/va_width/rel_volume.
- ⚠️ **Caveat causal:** VP da sessão usa volume da sessão inteira → bar 4H intra-sessão = look-ahead. **Solução obrigatória: previous-closed-session VP, OU provar as-of-bar.** Não assumir.

## D. Supply/Demand CATEGÓRICO — elevado a primeira classe (o achado central)
`demand_supply_quality.py` já deriva (causal, range i-12..i) categorias que **codificam a leitura que tentamos reinventar do zero com `dist_supply` cru — e falhámos**:
- **`sup_cat`:** CLEAN_SKY (=no_overhead_bullish) · SUPPLY_NEAR_BUT_BROKEN (=markup) · SUPPLY_FRESH_DANGEROUS / SUPPLY_NEAR_AND_REJECTING (=supply_colada_bearish) · SUPPLY_FAR_ENOUGH · SUPPLY_BLOCKS_TARGET · SUPPLY_PRESENT_NEUTRAL.
- **`pol_cat`:** RECLAIM_ACCEPTED_ABOVE_SUPPLY · RECLAIM_REJECTED_BELOW_SUPPLY · POLARITY_SUPPORTED_BY_DEMAND · POLARITY_UNDER_SUPPLY_PRESSURE · POLARITY_FLOATING_NO_BASE.
- **Conclusão:** abandonámos a leitura rica (categórica/gestalt) e ficámos com a fatia pobre (distância crua) — que falhou. O engine deve consumir `sup_cat`/`pol_cat` como input de primeira classe, não recomputar distância.
