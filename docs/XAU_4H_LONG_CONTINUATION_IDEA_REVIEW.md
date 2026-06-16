# XAU 4H LONG — CONTINUATION — Inventário neutro de ideias (2026-06-16, read-only)

**Natureza:** revisão/inventário. **Nenhum backtest rodado, nenhum código alterado, produção não tocada.** Devil's Advocate executado sobre as classificações de risco (read-only) e incorporado.
**Fontes:** STRATEGY.md/MANIFEST.md da L1, scanner.py, runtime_xau.py, run_l1_cycle.py, regime_l1_v4.py, research/revalidation rebuild_v1/v2/v3, catalog.json, XAU_LEGACY_KNOWLEDGE_INDEX, XAU_STRATEGY_REEVALUATION_PLAN, BOOTSTRAP canônico, memory.

## 1. Executive summary
A família CONTINUATION tem **uma única coisa viva**: a **L1 · EMA21 CONTINUATION**, que está **human-approved para rodar (discricionária, human-in-the-loop)** — **mas o edge NÃO está validado out-of-sample.** Todos os números existentes são reconstruções **in-sample** marcadas `NOT_VALIDATION`; o headline +32.6R (KEEP-19) é **artefato** (Cris rotulou winners olhando o chart) e o veredito registrado é `NEEDS_CAUSAL_FILTER_BEFORE_ANY_CLAIM` / `mechanizable_now=false`. **Separar sempre dois eixos: `governance_status` (humano autorizou rodar) ≠ `evidence_status` (edge provado).** A L1 é governance=APPROVED, evidence=NÃO validado.

Três descobertas estruturais que o inventário obriga a registrar:
1. **Regime "split-brain":** o `scanner.py` (autoridade da base-rule, gerou os números in-sample) gateia em **regime_B_v3**; o `runtime_xau.py` (caminho LIVE do scheduler) gateia em **regime_l1_v4**. São classificadores **diferentes** → os números in-sample **não correspondem ao gate que roda ao vivo**, e o regime declarado morto (`regime_B_v3`, "IRRECUPERÁVEL") **continua wired no scanner**.
2. **Drift doc↔código:** STRATEGY.md cita `regime_B_v3` na base-rule e diz ao mesmo tempo "GATE automático" e "FLAG, não gate"; MANIFEST.md ainda anuncia o leg `vol_entry_z>=1.993` (removido do scanner **e** derivado de matriz comprovadamente bugada).
3. **Reconciliação nunca fechou:** n=11 (histórico) vs 16 (re-run) vs 38 (rebuild); v1 `CANNOT_RECONCILE_NO_ORIGINAL_TRADES`, v2 `FAILED_RECONSTRUCTION`. Só v3 "reconcilia" — e por agregado, sobre o subconjunto humano KEEP-19 (≈16), não por contagem.

**Recomendação:** **não estudar nova continuação ainda.** A próxima ação correta para CONTINUATION é **consertar a fundação da L1** (unificar a fonte de regime, sincronizar docs, e preparar um gate manifest + RAW out-of-sample) — não abrir L2/L3. Deixar a L1 acumular candidatos forward reais (regime atual BEAR → 0 até agora).

## 2. Estado atual da L1 aprovada (gates REAIS, verificados no código)
- **Identidade:** XAU 4H LONG — CONTINUATION / L1 · EMA21 CONTINUATION · PEPPERSTONE:XAUUSD · 4H · LONG · group XAU_240.
- **governance_status:** `USER_APPROVED_FINAL`, `HUMAN_DISCRETIONARY` (scanner gera candidato; entrada é decisão humana). **evidence_status:** `PROMISING_BUT_NEEDS_MORE_DATA` — **edge não validado OOS**.
- **Base-rule (scanner.py, autoridade):** regime D-1 BULL (**regime_B_v3** `v3_state`, SHIFT1) + `close>EMA21>SMA50` + slopes>0 + BOS causal + toque zona Custom OB v11 + `body_pct≥0.35` + F5 `vol_ratio_med50≤1.0`; stop estrutural longo (R_CEIL removido); exit V_stair_A (BE@+2R→+20R, time_stop 60).
- **Gate de exaustão (scanner.py):** `round(rsi_vs_ma,2) ≤ −9.35` → `blocked_exhaustion` (automático; leg de volume removido). `operational = passed and not exhaustion_gate`.
- **Caminho LIVE (run_l1_cycle.py → runtime_xau.py):** regime D-1 = **regime_l1_v4** (≠ scanner!); confirma regime+RSI gate; **a regra-base estrutural completa (EMA/SMA/BOS/OB/F5) NÃO é confirmada ao vivo** — o runtime marca `needs_base_confirmation` (NÃO operacional, sem Telegram) quando passa regime+RSI mas falta a base estrutural. **Limitação central: a L1 ao vivo ainda não consegue emitir um `operational_candidate` real** porque a base-rule não está no snapshot live.
- **Estado atual:** regime BEAR → todos os ciclos `no_candidate`. 0 candidatos operacionais forward.

## 3. Inventário das famílias/variantes CONTINUATION
1. **L1 EMA21 CONTINUATION (operacional).** Ver §2.
2. **rebuild_v1 (EMA21_A+F5).** n=3 trades, sumR −0.3R, `reconciliation=MISMATCH`, `CANNOT_RECONCILE_NO_ORIGINAL_TRADES`. Reconstrução infiel.
3. **rebuild_v2 (EMA21_A+F5).** `FAILED_RECONSTRUCTION`, trade_count=3, dedup K=6 bars = ASSUMPTION não validada; separou candidate-gen de trade-select (38 candidatos pre-cooldown).
4. **rebuild_v3 (EMA21_A+F5).** FULL-38 +14.9R/WR31.6%/avgR+0.39/`big*W=0`; KEEP-19 +32.6R = **artefato in-sample** (rótulo humano); BLOCK_TOP-17 −15.6R; `R_CEIL 1.5ATR removido` (o conserto). `DA_verdict=NEEDS_CAUSAL_FILTER`, `mechanizable_now=false`. **É a base de onde a L1 foi destilada.**
5. **Caminho A L1 v1 F4+F5** (EMA21_A + sell≤7 + vol≤1.0; memory): 11 trades, 6W/5L, +35.2R, look-ahead clean, direção 4/4 anos. **Linhagem precursora direta da L1.**
6. **XAUUSD_4H_BREAKOUT_CONTINUATION** (catalog): `validation_status=ACTIVE_CANDIDATE`, `deployment=None`. Archetype `DECISIVE_BREAKOUT_CONTINUATION` — **breakout decisivo, NÃO pullback-continuation como a L1** (sub-arquétipo diferente). É o breakout legacy **neutralizado** (recheck:931 sem SETUP_VALIDO). **Rótulo ACTIVE_CANDIDATE é enganoso** — não está deployado e não é a continuação da L1.
7. **Leg de exaustão `vol_entry_z>=1.993`** — morto sob F5 **e** derivado de matriz bugada (35/38 divergentes; #11 matriz=1.993 vs RAW=−0.93).
8. **regime_B_v3 como gate macro** — declarado IRRECUPERÁVEL/morto por regime_l1_v4.py, **mas ainda wired no scanner.py**; bias residual ~10.68% (`NEEDS_SHIFT1_AUDIT` nunca feito).
9. **Camadas continuation futuras** (memory "5 layers + 8 padrões"): L2 breakout+polaridade, L3 failure swing, L4 second entry pós-cap, L5 supertrend. **Propostas, não construídas.** L5 supertrend = linhagem A1' **INVALIDADA por look-ahead** (88%→46%).
10. **Threads de Caminho A reversão** (A1/A1'/BALANCE; packet a6/a6_a7) — **são REVERSAL/bottom-catcher, NÃO continuation** (a6/a6_a7 = REVERSAL_LONG). Fora do escopo continuation; cross-ref ao plano de reavaliação. A1' SUPERTREND invalidado por look-ahead.

## 4. Tabela
| Nome | Fonte | Gates reais | Status | Reutilizável? | Risco | Próxima ação |
|---|---|---|---|---|---|---|
| L1 EMA21 CONTINUATION | scanner.py/runtime/STRATEGY | regime BULL D-1 + EMA21>SMA50 + slopes + BOS + OB + body≥.35 + F5 ≤1.0; RSI gate ≤−9.35; V_stair_A | **ACTIVE_OPERATIONAL** (gov) / **NEEDS_RAW_BACKTEST** (evidence) | sim (é a viva) | regime split-brain; base-rule não-live; in-sample | unificar regime + base-rule live + RAW OOS |
| rebuild_v1 | research | EMA21_A+F5 (gates v1) | SUPERSEDED_BY_L1 / KEEP_REFERENCE | provenance | reconciliação falhou (n=3) | nenhuma |
| rebuild_v2 | research | idem v1 + dedup K=6 | SUPERSEDED_BY_L1 / KEEP_REFERENCE | provenance | FAILED_RECONSTRUCTION; K assumption | nenhuma |
| rebuild_v3 | research | base-rule + SL, R_CEIL off | KEEP_REFERENCE (CONTAMINATED como edge) | provenance da L1 | KEEP-19 artefato in-sample; mechanizable=false | só referência |
| Caminho A L1 v1 F4+F5 | memory/candidates | EMA21_A + sell≤7 + vol≤1.0 | SUPERSEDED_BY_L1 / KEEP_REFERENCE | sim (precursor) | n=11 escasso | absorvido na L1 |
| XAUUSD_4H_BREAKOUT_CONTINUATION | catalog | breakout decisivo (≠ pullback) | CONTAMINATED_LEGACY / KEEP_REFERENCE | não (sub-arquétipo distinto) | rótulo ACTIVE_CANDIDATE enganoso; recheck neutralizado | corrigir rótulo no catalog (bloco futuro) |
| vol_entry_z≥1.993 leg | STRATEGY audit | spike de volume | REJECTED_DO_NOT_REOPEN | não | dado bugado + morto sob F5 | nunca reabrir |
| regime_B_v3 (gate macro) | scanner.py | cascade/breaks legacy | CONTAMINATED_LEGACY (mas LIVE no scanner) | não como autoridade | bias 10.68%, sem SHIFT1; split-brain | migrar scanner→regime_l1_v4 (re-derivar números) |
| L2/L3/L4 continuation futuras | memory | (a definir) | REVALIDATION_CANDIDATE / NEEDS_GATE_MANIFEST | sim (ideias) | hipótese sem dados | só após L1 consolidada |
| L5 supertrend | memory/Caminho A | supertrend ativo | REJECTED_DO_NOT_REOPEN (sem SHIFT1) | não (como estava) | look-ahead 88%→46% | só com SHIFT1 limpo |
| Caminho A reversão (a6/a7, A1/BALANCE) | candidates/memory | reversal/bottom | KEEP_REFERENCE (fora de continuation) | em outra família | A1' look-ahead | ver plano de reavaliação (P0 Caminho B) |

## 5. O que foi absorvido pela L1
A linhagem **Caminho A L1 v1 F4+F5** (EMA21_A + sell≤7 + vol≤1.0) + a reconstrução **rebuild_v3** (base-rule EMA21>SMA50 + slopes + BOS + OB + body≥0.35 + F5 vol≤1.0; **remoção do R_CEIL 1.5ATR** = o conserto real; exit V_stair_A) → destilados na L1. O **gate de exaustão RSI-only ≤−9.35** substituiu o leg de volume bugado.

## 6. O que continua útil para futuras camadas
- Conceito de **continuação calma (sem clímax de volume)** via F5 — robusto e ortogonal a reversão.
- **V_stair_A** como exit em degraus (capturar runner sem perder breakeven).
- Ideias de camadas L2/L3/L4 (breakout+polaridade, failure swing, second-entry) como **REVALIDATION_CANDIDATE** futuras — só após L1 ter base-rule live + dados forward.
- A separação **continuation (L1) ⟂ reversal/bottom (Caminho B)** sustenta o objetivo de múltiplas estratégias ortogonais.

## 7. Legacy contaminado
- **regime_B_v3** como autoridade (bias 10.68%, sem SHIFT1, declarado morto mas wired no scanner).
- **vol_entry_z≥1.993** (matriz bugada + morto sob F5).
- **XAUUSD_4H_BREAKOUT_CONTINUATION** legacy/recheck:931 (neutralizado; rótulo de catalog enganoso).
- Números **slim/in-sample** narrados como performance; **KEEP-19 +32.6R** é o exemplo a NÃO repetir.
- strategy_rules / catalog deployment / recheck / Telegram antigos.

## 8. O que NÃO deve ser reaberto
vol_entry_z leg · regime_B_v3 como autoridade · L5 supertrend sem SHIFT1 · breakout legacy via recheck/Telegram · qualquer promoção baseada em KEEP-19/in-sample · slim como validação.

## 9. Gaps antes de qualquer backtest
1. **Unificar a fonte de regime** (scanner usa B_v3, runtime usa L1_v4) — decidir L1_v4 em ambos e **re-derivar** todos os números (os atuais não correspondem ao gate live). **Antes disso, nenhum número da L1 é comparável ao que roda.**
2. **Confirmar base-rule ao vivo** (runtime hoje não confirma EMA/SMA/BOS/OB/F5 → nunca emite operational_candidate). Sem isso não há candidato forward para medir.
3. **Gate manifest + RAW out-of-sample** (TRAIN/VAL/TEST; SHIFT1 audit do regime; OB zone label real, hoje ASSUMPTION; dedup K validado).
4. **Reconciliação real** com a série original (nunca fechou: 11/16/38).
5. Aplicar o **checklist de 15 problemas** (a L1 hoje passa quase nenhum gate de promoção: 1 ativo, 1 direção, 1 regime, ~4 anos, n=38, sem walk-forward, sem cross-asset).

## 10. Recomendação
- **Próxima continuação a estudar: NENHUMA nova ainda.** Abrir L2/L3 agora seria empilhar hipótese sobre uma fundação inconsistente (regime split-brain + base-rule não-live + in-sample).
- **Confirmar que a L1 deve rodar mais / ser consertada antes:** SIM. A L1 deve (a) ter a fonte de regime unificada, (b) ganhar confirmação de base-rule live, (c) acumular candidatos forward reais (depende de regime BULL voltar), (d) então um RAW OOS honesto. Só depois faz sentido nova camada continuation.
- **Não promover, não automatizar, não enviar Telegram além do candidate notification atual.**

## 11. Próximo bloco recomendado
**Bloco de fundação da L1 (toca runtime → exige Pre-Change Discipline + autorização explícita):** decidir e **unificar a fonte de regime** (scanner.py + runtime_xau.py ambos em `regime_l1_v4`), sincronizar STRATEGY.md/MANIFEST.md com o código real (remover citação regime_B_v3, remover leg vol_entry_z, resolver "gate vs flag"), e **planejar** (sem rodar) o gate manifest + RAW OOS da L1. Alternativa de menor risco/sem tocar runtime: começar só pela **sincronização documental** (corrigir STRATEGY/MANIFEST/catalog), deixando a unificação de regime para um bloco com autorização.

---
### Apêndice — caveats obrigatórios (Devil's Advocate)
1. **Edge NÃO validado.** Tudo in-sample (`NOT_VALIDATION`); +32.6R (KEEP-19) é artefato de rótulo humano; `mechanizable_now=false`; `NEEDS_CAUSAL_FILTER`. O filtro causal objetivo testado (`nas_short20≥2 AND ext≥3`) **falhou** (erra winners #9/#17/#18/#34/#36). Status = aprovado-para-rodar, discricionário.
2. **Regime contraditório, o morto está vivo.** scanner=regime_B_v3 (declarado IRRECUPERÁVEL, bias 10.68%, sem SHIFT1) vs runtime=regime_l1_v4. Os números in-sample foram gerados sob B_v3; o live roda L1_v4 → **não correspondem**.
3. **Drift doc/código + herança de dado bugado.** STRATEGY "gate" vs "flag"; MANIFEST anuncia leg `vol_entry_z` removido e derivado de matriz bugada; reconciliação nunca fechou.
- **Não exagerar:** o gate "corta 0 winners / preserva monumentais" é **seleção in-sample** (threshold −9.35 tunado sobre os mesmos n=38, flagando 4); os "monumentais" #36 +9.5R / #38 +6.53R **não são ≥20R** — é relabeling local, não captura de cauda.

_Read-only. Nenhum backtest, nenhum código, produção não tocada._
