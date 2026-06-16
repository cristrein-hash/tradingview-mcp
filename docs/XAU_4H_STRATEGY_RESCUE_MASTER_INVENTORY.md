# XAU 4H — Inventário Mestre de Resgate de Estratégias (2026-06-16, read-only)

**Natureza:** inventário/resgate/classificação/leitura crítica. **Nenhum backtest, implementação, promoção, limpeza ou alteração de produção.** Fontes: catalog.json, BOOTSTRAP canônico, XAU_LEGACY_KNOWLEDGE_INDEX, XAU_STRATEGY_REEVALUATION_PLAN, XAU_4H_LONG_CONTINUATION_IDEA_REVIEW, UNTRACKED_ARTIFACTS_INVENTORY, candidates/, research/revalidation/, L1 module + reports, memory.

## 1. Executive summary
A única estratégia **operacional** é a **L1 EMA21 CONTINUATION** (refinada, ponta a ponta). Todas as demais XAU 4H são research/legacy/rejeitadas. **Regra-mãe:** não confiar em nome; verificar gates reais; separar **governança** (humano aprovou rodar) de **evidência** (edge provado); in-sample ≠ validação; visual ≠ edge estatístico; RAW = fonte de verdade; mismatch scanner/runtime invalida números; daily/HTF exige SHIFT1; feature futura = contaminado. **Recomendação de reanálise:** P0 = **Caminho B (bottom-catcher, ortogonal à L1)** com gate manifest; a **L1** segue operacional acumulando forward + pendente RAW OOS honesto. Demand Breakout, Reversal Capitulation, L5 supertrend e regime_B_v3-live = **DO_NOT_REOPEN** sem hipótese/SHIFT1 novos.

## 2. Estado atual da L1 refinada (ACTIVE_OPERATIONAL_CURRENT)
- **Gates reais (scanner.py = runtime, mesmos gates):** regime D-1 BULL (**regime_l1_v4**, SHIFT1) + close>EMA21>SMA50 + slopes + BOS + zona Custom OB v11 + body≥0.35 + F5 vol≤1.0 → **stack v1 anti-extensão** (ret5≤1.42%, ext_ema≤2.95ATR, zone_w≥0.6ATR, dist_zone≤1.81ATR) → **NAS SHIFT1≥1.31** (causal, via `data_get_study_values_at_bar`, alinhado por timestamp) → RSI exhaustion gate `rsi_vs_ma≤−9.35`. **Exit:** SL estrutural `max(zona_OB_low, swing6_low)−0.1ATR`, **target +3R**.
- **Live:** runtime avalia o **bar fechado** (study-values por timestamp), chart auto-managed, scheduler ativo, Telegram só candidate-notification, broker inativo. Commit `f599ba8`.
- **Evidência:** **NOT_VALIDATED_OOS** — in-sample 2020-2026 (31 op / 17 TARGET / +40.0R / PF 4.08); aprovado pelo Cris **sem OOS, risco assumido**. Ganho parcialmente mecânico (SL apertado→alvo perto). vol_entry_z removido; regime_B_v3 fora do live.
- **Pendente:** RAW OOS honesto; acumular candidatos forward reais (regime atual BEAR → no_candidate, correto).

## 3–4. Tabela mestre por família
| Família · variante | Path/source | Dir/Style | Gates reais (resumo) | Evidência | Status | Riscos | Próxima ação |
|---|---|---|---|---|---|---|---|
| **L1 EMA21 CONTINUATION** | `xau_4h_long/continuation/L1_EMA21_CONTINUATION/` | LONG · continuation pullback | regime_l1_v4 BULL + EMA21>SMA50 + BOS + OB + F5 + stack v1 + NAS SHIFT1≥1.31 + RSI gate; SL estrutural; +3R | in-sample (NOT_VALIDATION); aprovado risco-assumido | **ACTIVE_OPERATIONAL_CURRENT** | in-sample; exit-defined; sem OOS | rodar + acumular forward; **NEEDS_RAW_BACKTEST** OOS |
| Continuation EMA21_A+F5 rebuild_v1/v2/v3 | `research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/` | LONG · continuation | EMA21_A + F5; v3 base-rule + SL (R_CEIL off) | v1 MISMATCH · v2 FAILED_RECONSTRUCTION · v3 in-sample/artefato (KEEP-19 rótulo humano) | **SUPERSEDED_BY_L1 / KEEP_REFERENCE** | reconciliação nunca fechou (11/16/38) | só referência (absorvido na L1) |
| Caminho A L1 v1 F4+F5 | memory + candidates | LONG · continuation | EMA21_A + sell≤7 + vol≤1.0 (F4 inerte) | in-sample escasso (n=11); reconc. 11/16/38 nunca fechou | **SUPERSEDED_BY_L1 / KEEP_REFERENCE** (veredito 2026-06-16, deep dive `docs/XAU_4H_CAMINHO_A_L1_F4_F5_DEEP_DIVE.md` / 5a3aae9) | n pequeno; não reabrir s/ hipótese nova | precursor da L1 (absorvido) |
| **XAUUSD_4H_BREAKOUT_CONTINUATION** | catalog + `research/revalidation/XAUUSD_4H_BREAKOUT_CONTINUATION/v1` | LONG · **breakout** decisivo (≠ pullback) | breakout decisivo (legacy) | catalog diz ACTIVE_CANDIDATE (enganoso); **não deployado**; recheck:931 neutralizado | **CONTAMINATED_LEGACY / KEEP_REFERENCE** | rótulo enganoso; recheck/Telegram legacy | corrigir rótulo no catalog (bloco futuro); não reabrir sem hipótese |
| **Caminho B LONG (bottom catcher)** | `candidates/xau_4h_caminho_b_long/` (+reentry) | LONG · **reversal/bottom-catch** | 4 agents convergentes + anti_demand + rsi≤30 + Dead Hours + Sweet Spot + V_stair (+filtro composto v1.6) | OFICIAL em memory (WL±20% ok, WF 3/3); **não migrado** ao novo core | **REVALIDATION_CANDIDATE / NEEDS_GATE_MANIFEST** | validado em slim antes; precisa RAW + checklist | **P0** reanálise: gate manifest → RAW OOS |
| **Caminho A reversal v1_4g_rws_a6 / a6_a7** | `candidates/xau_4h_reversal_v1_4g_rws_a6[_a7]/` | LONG · **reversal** | NAS + RWS + A6/A7 anti-RSI-bear-div; exit stop−1ATR/target+2.7ATR | OFICIAL ATUAL (memory) do Caminho A LONG; in-sample | **REVALIDATION_CANDIDATE** | reversal (≠ continuation); lookahead-audit pendente | **P1** RAW OOS + SHIFT1 audit |
| Caminho A — A1 BALANCE | memory | LONG · reversal/natural-bull | bsw∈(0,30] + bubble_buy + exit stair | in-sample | **KEEP_REFERENCE** | derivado da família com look-ahead | referência |
| **Caminho A — A1' SUPERTREND (L5)** | memory | LONG · continuation-em-supertrend | supertrend ativo + features daily | **INVALIDADO** (look-ahead 88%→46%) | **REJECTED_DO_NOT_REOPEN** | features daily do MESMO dia (não SHIFT1) | só com SHIFT1 limpo |
| **XAU_4H_DEMAND_BREAKOUT** | catalog + `research/revalidation/XAU_4H_DEMAND_BREAKOUT/v2` | LONG · zone breakout | OB demand + breakout | REJECTED (visual: comprava em zona que agia como venda) | **REJECTED_DO_NOT_REOPEN** | data-only insuficiente | só com hipótese auction nova |
| **XAU_4H_REVERSAL_CAPITULATION** | catalog + `research/revalidation/XAU_4H_REVERSAL_CAPITULATION/v2` | LONG · reversal capitulação | NAS+RSI1D<50+ATR>1.3 | REJECTED (PF 0.47 RAW; slim inflava) | **REJECTED_DO_NOT_REOPEN** | slim enganoso | só com hipótese nova |
| **XAU_4H_REVERSAL_DISCRETIONARY (SWEEP)** | catalog | LONG · liquidity-sweep reversal | NAS + sweep/reentry + CHoCH/BOS | RESEARCH, discricionário, n pequeno | **KEEP_REFERENCE / P2** | discricionário (não mecanizado) | mecanizar sweep+reentry; n |
| XAUUSD_INTRADAY_BB_CONFLUENCE | catalog + `research/revalidation/XAUUSD_INTRADAY_BB_CONFLUENCE/v1` | LONG · 15M zone-rejection | BB + confluência | RESEARCH, NOT_DEPLOYED, forward parado ~04-30 | **KEEP_FOR_REVALIDATION / P2** | 15M (não 4H) | revalidar RAW 15M |
| L2 / BPT / Reason Atlas | safety pack `~/Desktop/.../L2_REBOOT_SAFETY_PACK_2026-06-09` | LONG · macro-location | macro D1, at_d1_demand, NAS ordering, acceptance | RESEARCH_CORE | **KEEP_REFERENCE / P2** | separação é post-entry (gestão), não filtro entrada | eixos ortogonais + coleta |
| regime_B_v3 (v1/v2/v3) | `candidates/regime_classifier_v3/` | (regime, não estratégia) | cascade+breaks+vol_score+MACRO_BROKEN | histórico estático recuperável; v1 B gerador perdido | **KEEP_REFERENCE (histórico) / DO_NOT_REOPEN (live)** | não forward-computável; bias 10.68% sem SHIFT1 | só backtest histórico; nunca live |
| (ref) XAU 1H AUCTION LAB / 1H DECISIVE_BODY60 / 1H REJECTION | `research/revalidation/XAUUSD_1H_*` + catalog | 1H · vários | — | RESEARCH/REJECTED | **KEEP_REFERENCE (não-4H)** | fora do escopo 4H atual | não reavaliar agora |

## 5. Seção especial — TODAS as continuations
| Continuation | Precursora da L1? | Absorvida? | Superseded? | Algo único? | L2/L3 futura? | Aprendizado | Reabrir? |
|---|---|---|---|---|---|---|---|
| **L1 EMA21 CONTINUATION (atual)** | — (é a viva) | — | — | a config refinada (anti-ext + NAS SHIFT1 + SL estrutural) | base p/ L2/L3 | discriminador real está em features de entrada/estrutura, NÃO no regime puro | **operacional; reanálise OOS** |
| rebuild_v1/v2/v3 (EMA21_A+F5) | SIM | SIM (na L1) | SIM | nada além da L1 | não | reconstrução exige stop/trigger fiel; R_CEIL era o conserto | arquivar referência |
| Caminho A L1 v1 F4+F5 | SIM (linhagem) | SIM | SIM | nada único | não | EMA21_A + sell≤7 + vol≤1.0 = semente | referência |
| XAUUSD_4H_BREAKOUT_CONTINUATION | NÃO (é **breakout**, não pullback) | NÃO | parcial (legacy) | sub-arquétipo breakout decisivo (distinto) | **possível L2 breakout** (com gate manifest novo, SHIFT1, sem recheck) | breakout ≠ pullback-continuation; rótulo de catalog engana | KEEP_REFERENCE; reabrir só como L2 nova |
| A1' SUPERTREND (L5 supertrend) | NÃO | NÃO | — | continuation em supertrend | só com SHIFT1 limpo | look-ahead via close diário do mesmo dia | **DO_NOT_REOPEN** sem SHIFT1 |
| (futuras) L2 breakout+polaridade / L3 failure-swing / L4 second-entry | — | — | — | ideias do "5 layers" (memory) | **SIM** (REVALIDATION_CANDIDATE) | só após L1 consolidada + dados forward | NEEDS_GATE_MANIFEST |

**Próximo teste correto p/ continuation:** (a) **L1**: RAW OOS honesto (sub-janela/cross-asset), revalidar sob exit real, antes de qualquer promoção a edge-provado; (b) **L2 breakout** (distinta da L1 pullback) só com gate manifest novo + SHIFT1, sem reusar recheck:931.

## 6. NÃO reabrir (sem hipótese/condição nova)
Demand Breakout (REJECTED, data-only) · Reversal Capitulation (PF 0.47 RAW) · A1' SUPERTREND/L5 (look-ahead) · regime_B_v3 como autoridade **live** · vol_entry_z (morto + matriz bugada) · breakout legacy via recheck:931/Telegram antigo.

## 7. Podem virar futuras camadas (REVALIDATION_CANDIDATE / NEEDS_GATE_MANIFEST)
Caminho B (bottom-catcher, ortogonal à L1) · Caminho A reversal a6_a7 · L2 breakout+polaridade · L3 failure-swing · L4 second-entry · SWEEP mecanizado · BB confluence (15M) · L2/BPT (macro-location).

## 8. Precisam de GATE MANIFEST antes de qualquer backtest
Caminho B (predicados RAW exatos, mapping bubble plot_id, SHIFT1, TRAIN/VAL/TEST, checklist ≥12/15, Wilson≥45%) · Caminho A a6_a7 (SHIFT1 audit de features daily) · qualquer L2/L3 nova.

## 9. Prioridades de reanálise
- **P0:** **Caminho B (bottom-catcher 4H)** — ortogonal à L1, gates documentados, packet versionado, RAW-validatable, clean no lookahead audit (B v1.5 SHIFT1). · **L1**: manter operacional + planejar RAW OOS (paralelo).
- **P1:** Caminho A reversal **a6_a7** (oficial reversal; SHIFT1 audit + RAW OOS).
- **P2:** SWEEP mecanizado · BB confluence (15M) · L2/BPT · L2 breakout (continuation-breakout, distinta da L1) · XAU 15M/30M.
- **KEEP_REFERENCE:** continuation precursors (rebuilds, A L1 v1) · A1 BALANCE · regime_B_v3 histórico · discretionary · 1H packets.
- **DO_NOT_REOPEN:** Demand Breakout · Reversal Capitulation · A1' SUPERTREND/L5 sem SHIFT1 · regime_B_v3 live · vol_entry_z.

## 10. Recomendações finais
1. **Próximo bloco de reanálise = Caminho B**: começar por **gate manifest** (pré-registro, sem backtest), depois RAW OOS — é o candidato de maior valor ortogonal à L1.
2. **L1**: não promover a "edge provado" sem RAW OOS; seguir operacional acumulando forward (Forward Outcome Layer Fase 1/2 já lê o event store).
3. **Corrigir rótulo enganoso** `XAUUSD_4H_BREAKOUT_CONTINUATION=ACTIVE_CANDIDATE` no catalog (bloco dedicado).
4. **Não reabrir** as rejeitadas sem hipótese auction nova; **regime_B_v3** só como histórico.
5. Aplicar os aprendizados da re-arquitetura (scanner=runtime, SHIFT1, anti in-sample, plotagem 100%, DA de mismatch) a TODA reanálise futura.

---
### Apêndice DA (auto-verificação)
- Alguma strategy classificada só pelo nome? **Não** — gates reais checados (catalog val_status + reports + memory).
- In-sample chamado de validação? **Não** — L1 e todos marcados in-sample/NOT_VALIDATION explicitamente.
- Legacy contaminado marcado como candidato sem caveat? **Não** — Demand/Capitulation/L5/regime_B_v3 com DO_NOT_REOPEN + razão.
- Alguma continuation importante fora? **Não** — L1, rebuilds, A L1 v1, breakout-continuation, L5, L2/L3 futuras cobertas.
- L1 descrita com a config refinada correta? **Sim** (stack v1 + NAS SHIFT1 + SL estrutural + 3R + scanner=runtime + study por timestamp).
- Caminho A vs B separados? **Sim** (A=reversal/a6_a7/A1; B=bottom-catcher).
- Demand/Capitulation reabertas sem hipótese? **Não** (DO_NOT_REOPEN).
- Algo operacional tocado? **Não** — read-only, só este doc.

_Nenhum backtest. Nenhum arquivo movido/deletado. Produção intacta. Sem MCP/chart/Telegram/broker._
