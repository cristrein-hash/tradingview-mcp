# RTSE_SCHEMA_V0 — Schema de Estado Causal por Barra

**Status:** PLANNING. Documentação only. Define o estado multi-eixo + as 2 travas de integridade (n-adequacy; confidence não-fitada).

---

## 1. Princípio (correção do Cris aceita)
Regime **não é etiqueta única**; é leitura em CAMADAS. `bull/range/bear` sozinho esconde: macrobull+bear-leg local, macrobear+bottoming, range-superior+markup-local, pullback contra-tendência, sweep em continuação, bear-trap em estrutura viva. Por isso eixos separados, cada um independentemente validável.

## 2. Estado por barra (causal, as-of close, SHIFT1, daily=D-1)
```
{
  "structural_regime":  "BULL | RANGE | BEAR | MIXED | UNKNOWN",
  "local_leg_state":    "UP_LEG | DOWN_LEG | SIDEWAYS | EXHAUSTION | RECLAIM | DISTRIBUTION",
  "turn_state":         "NONE | EARLY_POTENTIAL_BOTTOM | MATURING_BOTTOM | CONFIRMED_BOTTOM |
                         EARLY_POTENTIAL_TOP | MATURING_TOP | CONFIRMED_TOP | FAILED_TURN",
  "counter_pullback":   "NONE | BEAR_DIP_IN_MACRO_BULL | BULL_BOUNCE_IN_MACRO_BEAR | RANGE_FADE | LIQUIDITY_SWEEP",
  "transition_phase":   "NO_TRANSITION | COMPRESSION | FLUSH | RECLAIM | ACCEPTANCE | MARKUP | FAILURE",
  "strength":           0.0-1.0,        // bottom/top-power relativo — calibração, NUNCA gate
  "confidence":         0.0-1.0,        // agregado NÃO-fitado (ver §4)
  "confidence_components": { ... },     // reportados separados (transparência)
  "latency_since_candidate_pivot_bars": int|null,   // barras desde o pivô CAUSALMENTE detectável (não o M8)
  "expected_latency_bucket": "EARLY | MID | LATE",
  "false_positive_budget": "LOW | MED | HIGH",
  "risk_of_whipsaw":   "LOW | MED | HIGH",
  "profile_routes":     { ... },        // ver RTSE (§5 canon) — NUNCA route global
  "provenance":         { ... }         // RTSE_SOURCE_MAP_V0 §5
}
```

### Domínios e cálculo causal (resumo; detalhe em build na fase 2/3)
- `structural_regime` ← regime v5 stable-daily (D-1) + override intraday; `MIXED` quando stable-daily e intraday discordam; `UNKNOWN` quando dado insuficiente.
- `local_leg_state` ← leg atual em TF de trabalho (perna up/down, lateralização, exaustão de perna, reclaim, distribuição) — só a partir de features provadas (§3 nascimento faseado).
- `turn_state` ← gradação de maturidade (early→maturing→confirmed→failed). `EARLY` = candidato fraco (alta FP, baixa latência); `CONFIRMED` = baixa FP, alta latência. **Nunca dispara numa barra que ainda faz novo low/high in-bar.**
- `counter_pullback` ← o 2º eixo de perda nomeado pelo Cris (dip-em-bull / bounce-em-bear / range-fade / sweep).
- `transition_phase` ← fase da transição (compressão→flush→reclaim→aceitação→markup→falha).

## 3. ⛔ Nascimento FASEADO dos eixos (endurecimento aceito #3)
Os sub-estados **nascem ancorados só nas features causalmente-provadas** (regime v5, swept, h1_pos, bottom-power, HTF). Valores interpretativos/SMC (`DISTRIBUTION`, `ACCEPTANCE`, `MARKUP`, `EXHAUSTION`) ficam **inertes/placeholder até passarem null individualmente**. Ordem:
1. **V0 provado:** structural_regime, turn_state(early/maturing/confirmed via swept+bottom-power+reclaim), counter_pullback(dip/bounce/sweep), strength, confidence, latency.
2. **V1 (só após null por valor):** local_leg_state interpretativos, transition_phase interpretativas.
Rótulo que não passou null = não entra em validação de promoção (continua RESEARCH_ONLY).

## 4. ⛔ Guarda de n-adequacy (endurecimento aceito #1)
- Universo de validação ≈ **414 reversões M8 / 3 anos**. O produto cartesiano dos eixos (~milhares de células) é não-validável (fatia-fina = violação PRINCIPAL_3).
- **Regra dura: validamos cada EIXO independentemente** (null/jackknife por eixo). NUNCA o produto cartesiano.
- `route` (e qualquer decisão) é uma **FUNÇÃO** dos eixos (composição de regras causais), **não um lookup** sobre a combinação.
- Qualquer corte/combinação proposta com **n<30 por célula** = anedótico (sem claim direcional); n<10 = bloqueado. Reportar n por célula sempre (`feedback_full_panel_always`).

## 5. ⛔ Confidence NÃO-fitada (endurecimento aceito #2)
- `confidence_components` (technical_structure, multi_tf_alignment, exhaustion, acceptance, external_factor_alignment, data_quality) são **reportados separados** = transparência.
- O **agregado** `confidence` é ou:
  - (a) combinação **defensável e não-tunada** — ex.: *contagem de eixos ortogonais alinhados* ou *mínimo dos componentes críticos*; **nunca** soma de pesos escolhidos a dedo; OU
  - (b) **calibrado forward** contra hit-rate real (mesmo espírito do theory-scoreboard do EF) — peso aprendido pela realidade, não pelo autor.
- Proibido: soma ponderada ajustada à mão que "parece científica". Isso é fit disfarçado.

## 6. `strength` ≠ gate
`strength` (bottom/top-power) é **calibração relativa** para o consumidor ponderar — **nunca** um threshold de entrada do próprio RTSE. (Seleção-de-fundo morreu; §canon não-objetivo #1.)

## 7. Latência: definição honesta
`latency_since_candidate_pivot_bars` = barras desde o pivô **causalmente detectável** que o detector travou — **NÃO** barras desde o pivô verdadeiro M8 (isso exigiria o futuro). A distância real ao M8 é medida só na VALIDAÇÃO (régua), nunca exposta como feature/estado.
