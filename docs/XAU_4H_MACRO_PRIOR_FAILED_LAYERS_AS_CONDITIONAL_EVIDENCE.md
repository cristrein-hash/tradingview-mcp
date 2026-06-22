# TRAVA METODOLÓGICA — PRIOR FAILED LAYERS AS CONDITIONAL EVIDENCE

**2026-06-22. OBRIGATÓRIA.** O spec do Leg-State & Liquidity-Structure Specialist (e qualquer engine futuro)
**DEVE incorporar esta seção.** Registro a pedido do Cris.

## A regra
**Nenhuma feature/camada anterior é descartada só porque falhou ISOLADAMENTE.** Muitas leituras ricas só
precisavam do contexto estrutural certo (lição capit+rsi: cada uma fraca sozinha, decisivas juntas). Falha
como *regra primária* ≠ inutilidade como *evidência condicional*.

## A tese correta (não "substituir tudo por leg-state")
**Leg-state é o BACKBONE estrutural primário; as camadas anteriores viram EVIDÊNCIA CONDICIONAL de
suporte/conflito DENTRO da leg-state.** O leg-state diz "em que leg estou"; as camadas antigas dizem
"o que isto significa NESTA leg".

## Cruzamento interpretável (NÃO busca combinatória cega)
- bull-leg + high legpos + CLEAN_SKY → continuação boa.
- bear-leg + pullback-to-demand → TRAP (a mesma entrada que é boa em bull).
- bull-leg + supply próxima QUEBRADA → markup.
- bear-leg + supply próxima/rejeição → bearish.
- entry-quality só importa DEPOIS de saber a leg.
- fuel só importa DEPOIS de separar no-overhead-bullish de supply_colada.
- risk_sl é eixo SEPARADO (SL curto ≠ entrada ruim — T34).

## Catálogo (auditável: `results/l2_bpt_prior_layers_conditional_evidence.csv`)
Taxonomia de status: **ALIVE** (viva) · **DEAD** (morta de verdade) · **FORBIDDEN** (proibida por
causalidade/proveniência) · **WEAK_ISOLATED** (fraca isolada → condicional) · **SECOND_LAYER** (2ª camada
de validação) · **RETEST_UNDER_LEGSTATE** (exige novo teste sob leg-state) · **CONTEXT_ONLY** (regime-bound).

| Camada | Por que falhou como primária | Papel sob leg-state | Status |
|---|---|---|---|
| **SMC BOS/CHoCH + pivots** | (causais, verificados) SMC esparso ~41% | **BACKBONE: pivots HH/HL vs LH/LL + SMC como shift** | ALIVE |
| **Macro Reading Engine v1 (9 esp.)** | bloqueio fraco (B 5/18) | **leitor de contexto bull/regime primário** (manter) | ALIVE |
| **sup_cat / pol_cat** | descartado em favor de dist_supply cru | **input de 1ª classe (Supply specialist)** | ALIVE |
| **SVP / volumetria** | (causal verificado) | input de confluência (aceitação/distribuição) | ALIVE |
| **has-overhead-aware** | exigia broken_before (raro); pior sozinho | gate dentro do Supply specialist | ALIVE (nec.-não-suf.) |
| **risk_sl / T34** | não é separador de leg | **eixo SEPARADO** (SL curto ≠ entrada ruim) | ALIVE |
| **regime_B_v3 (30 campos)** | só 2 testados | Macro Regime specialist (cascade/vol/stall/sharp_drop/dist_alarm/distribution/macro_broken/breaks, D-1, comportamento-não-nome) | ALIVE/RETEST |
| **regime_l1_v4** | não testado isolado | Macro Regime input (D-1) | ALIVE/RETEST |
| **entry-quality (dist_demand/POC-VAL/reclaim)** | entradas estruturalmente idênticas | **2ª camada condicional** (bull-leg: near-demand=bom; bear-leg: near-demand=trap) | SECOND_LAYER |
| **dist_supply / dist_demand** | monótono falha (mesmo valor = bull ou bear) | condicional a leg-state + has_overhead + sup_cat | RETEST_UNDER_LEGSTATE |
| **legpos 30/60/90** | alto penaliza bull-run (falso) | condicional a momentum + leg-state | RETEST_UNDER_LEGSTATE |
| **Regime/Context/Fuel v0/v1** | dist_supply artefato; univariado | features secundárias condicionais | RETEST_UNDER_LEGSTATE |
| **capit+rsi** | refutada OOS bear (regime-bound) | Capitulation input **APENAS no regime de fundo/turn** | CONTEXT_ONLY |
| **Stage A context labels** | não separa A/B | feature/evidência (não label-verdade) | WEAK_ISOLATED |
| **Confluence v2 macro override / late-top** | over-bloqueou A; não corrigiu B | **GUARD-RAIL**: macro_broken só p/ 3 casos; NUNCA usar legpos p/ late-top | DEAD-as-rule / lição viva |
| **macro_leg_direction/phase** | REFERENCE_ONLY (não computado) | substituído por leg-state via pivots | DEAD/FORBIDDEN |
| **hour_utc** | session-time, overfit | — | FORBIDDEN |
| **demand_age_bars** | UNAVAILABLE | — | DEAD |

## Procedimento obrigatório no próximo spec
O Leg-State spec deve declarar explicitamente, para cada camada: **viva / morta / fraca-isolada /
2ª-camada / proibida / exige-retest-sob-leg-state** — e como entra (suporte, conflito, sanity, fallback,
feature secundária). Sem busca combinatória cega; cruzamento sempre interpretável (Auction Theory).
