# MACRO STRUCTURAL READING ENGINE — DESIGN SPEC

**2026-06-21.** **Design apenas. Não executar.** Engine **strategy-agnostic**: lê a estrutura macro/
contextual do mercado por episódio/bar e produz uma **leitura auditável**, consumível depois por
estratégias LONG e SHORT. Nasce da conclusão de que o problema não é `has_overhead` nem `dist_supply`,
mas uma **falha conceitual de leitura de CONJUNTO** — features singulares lêem fatias; o contexto vive
na confluência multi-fator multi-timeframe. Calibração inicial: L2/BPT XAU 4H (62 trades de ensino).

## 0. O que este engine É e NÃO É
- **É:** uma camada de PERCEPÇÃO de estrutura macro (reusável). Output = estado de contexto + reason codes + confiança.
- **NÃO é:** um qualificador de trades L2/BPT, nem AGG_v2, nem uma regra. O L2/BPT (e futuras estratégias) **consomem** a leitura; não são a leitura.

## 1. Contrato anti-ilusão (inseparável de "incluir tudo")
1. **Incluir todas as features por ASPECTO estrutural** (fraqueza isolada ≠ inútil — lição capit+rsi). Só MORTAS excluídas.
2. **NÃO busca combinatória cega.** Confluência = concordância de aspectos legível como mercado, não combo estatístico. O roster estrutura a busca; nada de jogar 122 features num fit.
3. **Os 62 (A26/B18/C18) são ENSINO/CALIBRAÇÃO, NÃO fit target.** Proibido tunar aos IDs.
4. **Princípio validado depois em 276 + OOS** antes de qualquer uso. Os 62 ensinam a leitura; o 276/OOS prova-a.
5. **Confluência só conta com interpretação de mercado.** Sem isso = fishing → rejeitado.
6. **Nenhum especialista é caixa-preta.** Cada output: provenance + reason codes + features citadas (factor+value), como na Fase 2A.
7. **Multiplicidade controlada** na validação futura (shuffle-null por confluência, held-out temporal).
8. **Causalidade absoluta:** só features conhecíveis no close do bar i; externas com shift D-1; SVP com prev-closed-session; sem outcome/futuro.

## 2. Roster de especialistas (leitores de ASPECTOS, não votadores)
| # | Especialista | Lê (inclui as "fracas") | Distingue |
|---|---|---|---|
| 1 | **Supply Structure** | **sup_cat/pol_cat (1ª classe)** + dist_supply 4H/D1 + overhead/blocks/broken/rejected/fresh | CLEAN_SKY/no-overhead-bullish ≠ supply_colada_bearish |
| 2 | **Demand Structure** | Custom OB: demand age/width/origin/touched/retest + dist_demand 4H/D1 | demanda defendida real ≠ base frágil |
| 3 | **Volumetry/Acceptance** | SVP POC/VAH/VAL + below_VAL + rel_volume + va_width + distribution_flag (⚠ prev-closed-session) | aceitação acima de valor ≠ rejeição/distribuição |
| 4 | **Multi-TF Alignment** | 4H + 1D + **semanal** (slopes, RSI, breaks h4/d/w, demand/supply D1/W) | bull-run maior ≠ bounce local |
| 5 | **Macro Regime** | regime_B_v3 COMPLETO (cascade/vol/combined/stage/atr_expansion/distribution/stall/sharp_drop/dist_alarm/macro_broken) + l1_v4 | macro_broken/distribution/cascade/stall/recovery |
| 6 | **Momentum/Exhaustion** | trend_30/90 + slope + rsi/rsi_1d + rise20 + bear_div + **legpos×momentum** | high-legpos saudável ≠ late_top exhaustion |
| 7 | **Capitulation/Climax** | drop20 + rsi_min + sweet_spot + bubbles_sell + capit+rsi | bottoming/climax ≠ faca caindo |
| 8 | **Fuel/Convexity** | room-to-supply + CLEAN_SKY + dist_d1_supply + va_width + target obstruction | (tier diagnóstico — SEM sizing policy) |
| 9 | **Risk/Structural SL** | sl_atr + sl_type + demand base + structural invalidation | entrada ruim ≠ entrada boa com SL curto (T34) |

Cada especialista emite evidência estruturada {aspect, features citadas (factor+value), reading, reason_codes, confidence, caveat, causal} — cego a outcome/decisão (Fase 2A style). Não decide trade.

## 3. Modelo de confluência (não soma cega de votos)
Os especialistas **inter-relacionam-se**: a leitura final é o **estado de mercado coerente** que satisfaz required-supports e não viola fatal-conflicts. Estados de saída (cada um = required_supports · fatal_conflicts · reason_codes · tf_agreement · confidence/tier · anchors · failure_modes):

| Estado | required (esboço) | fatal_conflict |
|---|---|---|
| MACRO_BULL_RUN_CONTINUATION | regime bull + TF-align(4H/1D/1W) + (CLEAN_SKY ∨ markup) + momentum forte | macro_broken / distribution |
| BULL_PULLBACK_CONTINUATION | regime bull + demanda defendida + pullback + momentum não-negativo | bear-leg / supply_colada |
| RANGE_MACRO_BULL_RECLAIM | macro bull + range + reclaim aceito + acceptance(SVP) | rejeição sob supply |
| BOTTOM_REVERSAL_VALID | capitulation/climax + reclaim + demanda + momentum a virar | faca caindo sem reclaim |
| CAPITULATION_RECLAIM_VALID | drop forte + climax(bubbles/vol) + reclaim | continuação de baixa |
| NO_OVERHEAD_MARKUP | CLEAN_SKY/has_overhead=0 + momentum + breaks bull | momentum fraco |
| BEAR_BOUNCE_RISK | macro bear/range + bounce sob overhead + momentum fraco | (bloquear LONG) |
| CORRECTIVE_BEAR_LEG | bear-leg corretiva + sob supply + reclaim frágil | (bloquear) |
| LATE_TOP_EXHAUSTION | legpos90 alto + momentum a enfraquecer + rsi alto + distribution_flag | (bloquear) |
| SUPPLY_COLADA_REJECTION | SUPPLY_NEAR_AND_REJECTING/FRESH + momentum fraco | (bloquear) |
| MID_RANGE_NOISE | sem tese estrutural / baixa convicção | — |
| UNKNOWN_CONFLICT | especialistas em conflito irreconciliável | — |

Família BULL (consumível como contexto-favorável-LONG) vs RISK (bloquear/rebaixar) vs NEUTRO. Para SHORT futuro: o mesmo engine, lendo o espelho (RISK-LONG ≈ favorável-SHORT).

## 4. Ensino com os 62 SEM overfit (§5 do bloco)
- **Anchors qualitativas a preservar (família BULL):** T34/T35, T37, S20, S24-S27, S29-S32, T39, T41, S35-S38.
- **Bloquear/rebaixar (família RISK):** T40, S40-like.
- **Casos especiais (eixos não-regime):** T34=risk_sl (SL curto, entrada boa); T36=lógica certa/winner curto aceitável; S39=bom winner menor convexidade; S19=SKIP correto bear+fuel fraco; T27/S14/T40=timing/anchor.
- **EXPLÍCITO:** anchors = sanity/teaching, **NÃO fit target**. Qualquer regra derivada tem que ser interpretável E depois testada em 276 + OOS. Acertar os 62 não é sucesso; sucesso é o princípio generalizar.

## 5. Plano de validação futura (sem executar agora)
1. Aplicar engine aos 276 (não só 62). 2. Comparar leitura vs matriz/decisões antigas. 3. OOS (2013-2016 + futuro). 4. LONG agora, SHORT depois (espelho). 5. Medir lucro/PF/DD/frequência/convexidade do qualificador que CONSOME a leitura. 6. Avaliar se a leitura macro melhora qualificadores DIFERENTES (não só L2/BPT) — teste de strategy-agnosticismo. Multiplicidade controlada (shuffle-null/held-out).

## 6. Próximos passos
(a) Resolver a causalidade do SVP (prev-closed-session vs as-of-bar) — provenance check dedicado. (b) Implementar os 9 especialistas como leitores de evidência sobre os 62 (ensino). (c) Confluência → estados. (d) Anchor check + interpretação. (e) SÓ DEPOIS: 276 + OOS. Cada etapa = bloco diagnóstico próprio, sem promoção.
