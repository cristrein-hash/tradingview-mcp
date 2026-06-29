# RTSE_CANON_V0 — Regime & Turn-State Engine · Cânone

**Status:** PLANNING / aguardando construção. Documento canônico (igual papel do EXTERNAL_FACTORS_V2_DESIGN). **Nenhum código escrito.**
**Decisão-mãe:** memória `project_regime_turnstate_engine.md`. Síntese de 2 reflexões (Plan agent + correções do Cris) + 4 endurecimentos aprovados (2026-06-30).
**Companheiros:** `RTSE_SOURCE_MAP_V0` · `RTSE_SCHEMA_V0` · `RTSE_VALIDATION_PROTOCOL_V0` · `RTSE_EXTERNAL_FACTORS_BRIDGE_V0` · `RTSE_PHASE_PLAN_V0`.

---

## 1. Objetivo
Serviço causal transversal de **leitura de estado e transição** de mercado (regime + turn-state + pullback contrário), com saída **probabilística, auditável e perfilável por estratégia**. Padroniza a leitura de regime que hoje está duplicada/enterrada nos entries (regime v5 15M, regime gate 4H, h1_eff, swept). Abastece toda estratégia (XAU 15M LONG aprovada, 4H L1/L2, SHORT XAU futuro, outros ativos depois) via API as-of, sem acoplamento.

**Tese central (Cris):** quase todo SL/BE vem de UM ponto — entrada no contexto errado de regime/pullback. O lever não é catar fundo; é **VELOCIDADE de percepção anti-look-ahead** de (a) viradas de macro-regime e (b) pullbacks contrários intra-regime (bear-leg/range em macrobull e o inverso). Ganho realista = **mover a distribuição** (mais dips validados, menos topos-em-range) sob **orçamento de falso-positivo fixo**.

## 2. Não-objetivos (travas duras — violar = voltar às paredes históricas)
1. **NÃO é detector de fundo/topo.** Selecionar qual low vira fundo forte tem parede ~6% (E2/E3/E4, rabbit-hole audit). RTSE roteia *contexto*, não cata o pivô. `strength` é calibração relativa, **nunca gate de entrada**.
2. **NÃO é sinal de entrada nem auto-trader.** Não emite R, size, nem exit. Roteia; a estratégia decide. Live só após sign-off (Fase 7).
3. **NÃO é estratégia.**
4. **NÃO é gate global.** `route` é SEMPRE por-profile (ver §5). Um mesmo estado é BLOCK p/ L1, REVIEW p/ L2-capitulação, EARLY p/ scalp, SHORT_CONTEXT p/ short futuro.
5. **NÃO vence a lei latência↔FP.** Detector perfeito é rejeitado por design. A entrega é a *curva*, não a eliminação do erro de transição.
6. **NÃO é asset-agnostic como premissa.** Arquitetura portável, **validação XAU-first**. Cross-asset é proibido como gate de validação (cânone). Especificidade-por-ativo > generalização.
7. **NÃO usa OOS / cross-asset como validação.** Validação mora DENTRO dos dados (forward/null/jackknife/por-regime/por-ano).

## 3. ⛔ TRAVA ANTI-ORACLE (a mais importante — Cris)
> **"Se virar oracle, morreu."**

- RTSE **nunca explica um loser pós-fato.** "O regime estava ruim" depois do trade = **hindsight, PROIBIDO**.
- Só emite estado causal **forward**, com info ≤ close da barra.
- Não é o módulo que "resolve o trading system". Função = melhorar leitura, padronizar regime, medir velocidade de virada, reduzir duplicação, deixar estratégias escolherem tolerância. **Não** é: achar fundo, provar entrada, substituir estratégia, bloquear tudo, virar oráculo, explicar todo loser.
- Anti-oracle = `PRINCIPAL_3_anti_myopia` aplicado a este módulo: multi-fatorial + trajetória, **nunca snapshot de eixo único**, nunca narrativa pós-fato.

## 4. Paredes conhecidas (e como o design as respeita)
| Parede | Evidência | Respeito no design |
|---|---|---|
| Seleção de fundo (~6%) | E2/E3/E4, rabbit-hole, macro-bottom refutado | RTSE roteia contexto, não seleciona pivô; `strength`=calibração não-gate |
| Latência↔FP é LEI | — | é a curva-entrega, não inimigo; todo output traz latência+FP budget |
| Look-ahead (bug nº1) | lookahead_audit shift1 | SHIFT1/close-only/as-of/D-1; red-team gate TODA fase |
| Over-fit do próprio M8 | — | M8 = régua, NUNCA feature; params espelhados do v5 (não fitados); sensitivity M6/M10/M12 |
| Beta disfarçado de sinal | L2/EF | por-regime + por-ano + jackknife-episódio expõe; EF entra low-weight (nível estático=null) |
| Explosão combinatória (n insuficiente) | PRINCIPAL_3 fatia-fina | **valida cada EIXO, NUNCA o produto cartesiano**; guarda de n-adequacy (`RTSE_SCHEMA_V0`) |
| Confidence fitada | overfit escondido | componentes reportados; agregado **não-tunado** ou forward-calibrado, nunca soma de pesos a dedo |
| Rótulos interpretativos (SMC) | entry-wall | sub-estados nascem das features causalmente-provadas; interpretativos só após passar null |
| Oracle/hindsight | — | §3 trava dura |

## 5. Inputs PERMITIDOS / PROIBIDOS (detalhe em `RTSE_SOURCE_MAP_V0`)
**Permitidos:** RAW OHLCV · campos RAW da fonte (pine_boxes/labels/study_values RAW) · features já RAW-traced e validadas (regime v5, swept_prior_low, h1_pos, bottom-power) · snapshot do External Factors (quando existir, só como prior modulador de confiança).
**Proibidos:** outcome futuro · `true_reversals`/labels M8 como FEATURE · capped realR · endpoint humano · SLIM/proxy não-validado · features interpretativas sem RAW/source-trace · pivot futuro · zona hindsight · resultado do trade.

## 6. Posição no Trading System (separação que dá escala sem contaminar)
- **External Factors** = contexto exógeno (macro).
- **RTSE** = contexto técnico/estrutural causal.
- **Strategies** = exploração específica do contexto (cada uma com seu profile).
- **Reader** = interpretação profunda em casos complexos.
- **Production** = só consome após validação + sign-off.

## 7. Cânone de validação (resumo; detalhe em `RTSE_VALIDATION_PROTOCOL_V0`)
Métrica primária = **latência até detectar `true_reversals_M8` a FP fixo** (curva precisão/recall/latência mediana+p90, por-regime/ano/bloco). Tem que **bater em Pareto** baselines triviais (v5-puro, MA-cross lagged, swing-break, RSI causal, null). **Se só empatar com v5 → vale como consolidação arquitetural, NÃO como edge novo** (declarar na cara, não inflar). Promoção: ≥12/15 checklist; default `recorded_context` até sign-off.
