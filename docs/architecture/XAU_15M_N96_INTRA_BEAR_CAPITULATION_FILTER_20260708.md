# XAU 15M LONG · N96 · Intra-BEAR Capitulation Filter

> 🚨 **CONTAMINATION NOTICE (2026-07-09):** as métricas de BASE neste doc (N96, +112→+125R) derivam da base com **event-selection lookahead** (INVALIDADA; ver `XAU_15M_N83_SL_EXIT_FINAL_DA.md`) = resultados históricos contaminados. **O FILTRO em si sobreviveu:** re-validado causal **out-of-population** na base reparada live-fireable (corta 22=22L/0W; P exato 0,0016; episódico 0,0047; 14/14 losers novos) — status `VALIDATED_CAUSAL_RISK_CONTROL` no canon `XAU_15M_MARKUP_DEMAND_CURRENT_STATUS_CANON.md`.

**Cris 2026-07-08.** Registo correto do achado, substituindo o veredito prematuro anterior.

## Status
- `USER_APPROVED_NOT_PRODUCTION`
- `VALIDATED_BY_CRIS_AS_CAUSAL_LOGIC`
- `DA_VERDICT = PROFITABLE_BUT_FRAGILE`
- `NOT_PRODUCTION` · `NO_RUNTIME` · `NO_TELEGRAM` · `NO_AUTO_TRADING`

## 1. Contexto N96
Motor de entrada XAU 15M LONG "N96" — 96 entradas (pullbacks markup/demanda, alvo fixo 3:1), 52 winners / 44 losers, hit-3R 54,2%, +112R (R = 3·W − L). Janela 2025-08-01 → 2026-07-02. Reproduz byte via `research/xau_15m_bb_nas_leonardo/entry_engine_master_20260707.py` + `agent_ctx_kit.py`. Objetivo desta rodada: **filtrar losers estruturais sem cortar winners, RAW-native**.

## 2. Erro anterior corrigido (por que d09ad3b foi parcialmente retratado)
O commit `d09ad3b` continha 2 documentos com **veredito prematuro/incorreto `NO_CLEAN_FILTER`** (audit + DA), induzido de uma análise de **eixo único global** (features HTF numa logística LOO sobre os 96, sem leitura estrutural). Esse veredito estava errado: não era "não existe filtro", era "cruzamento sem contexto estrutural é estéril".
- **Removidos do estado atual (revert cirúrgico, opção 1 do Cris):**
  - `docs/architecture/XAU_15M_N96_RAW_MTF_LOSER_FILTER_AUDIT_20260704.md`
  - `docs/architecture/XAU_15M_N96_RAW_MTF_LOSER_FILTER_DA_20260704.md`
- **Preservados como VÁLIDOS** (não apagar): o extractor RAW 30M/1H `build_30m1h_primitives.py`, as primitives `htf_primitives/XAUUSD_{30m,60m}_*.primitives.json` (RAW 30M/1H nativo, autorizado pelo Cris), e a análise de eixo-único `n96_loser_*.py` + results (superseded, mas correta como histórico). **Sem reescrita de histórico.**

## 3. Tese estrutural do Cris (provada com dados)
**Indicadores só discriminam DEPOIS da leitura estrutural (regime macro + perna específica).** O mesmo indicador **inverte de sinal por regime** → a média global cancela e parece estéril.
- Prova direta (mesma feature `preço vs EMA-1D`): **+78R FORA do bear** (32W/18L, sobretudo winners) mas **−13R DENTRO do bear** (0W/13L). O regime é a chave, não o indicador isolado.
- Em regime BEAR: **comprar LONG só em fundo de capitulação; o repique raso dentro do bear deve ser cortado.**

## 4. Regra causal testada
1. **Regime por entry = detector v5 CANÓNICO hour-causal** (`engine_substrate4_v5_hourcausal.py`, `regime_hourcausal(cjt)`: override 1H no último bar fechado ≤ t + camada estável do dia D-1; ZERO look-ahead). Carregado verbatim, sem reinventar.
2. **DENTRO do regime BEAR-causal:** `SKIP se 1D_px_vs_ema >= 0` — preço de entrada no/acima da EMA 1D (último bar 1D fechado, normalizado por ATR) = **repique raso, não capitulação**. KEEP se bem abaixo da EMA 1D = capitulação funda.
3. **Fora do BEAR (BULL/RANGE): sem filtro.** Lógica bear-específica por construção (prior estrutural RTSE). Testar em BULL/RANGE é irrelevante.

## 5. Resultado histórico
- **Corta 13 trades — 13 losers, 0 winners.** Impacto **+13R** (v5 hour-causal; 112 → 125). Todos thresholds 0…−12 dão +R (+6 a +13).
- **Robustez por detector: +4R a +13R** (hour-causal +13 · day-causal +11 · v2-sem-override +4). O *sinal* (0 winners cortados) é robusto em TODAS as variantes; só a magnitude varia. **Citar como faixa +4…+13R.**
- **Feature-search null dentro do BEAR: P=0.005** (paga a busca de ~75 features × 2 direções × 7 tamanhos). Within-bear random-subset null: P=0.001. Joint 3-regime null: P=0.007.
- **Stale-free:** 0 dos 13 cortados na cauda HTF stale (todos < 2026-05-24).
- **Não é skip-all-BEAR disfarçado:** skip-all-BEAR = −27R; skip-Fev-Mai/2026 = −23R; skip-2026 = −42R (todas negativas). Clustering PASS (13 losers em 9 semanas ISO / 8 meses).
- hit-3R do que fica: 0,542 → 0,627.

### Os 13 cortados
| # | data | família | 1D_px_vs_ema | resultado |
|---|---|---|---|---|
| 24 | 2025-10-22 | MGMT | 1,39 | LOSER |
| 25 | 2025-10-24 | C | 4,53 | LOSER |
| 55 | 2026-01-29 | C | 14,99 | LOSER |
| 56 | 2026-02-04 | C | 3,53 | LOSER |
| 57 | 2026-02-10 | C | 7,85 | LOSER |
| 58 | 2026-02-10 | C | 9,48 | LOSER |
| 59 | 2026-02-11 | C | 7,83 | LOSER |
| 66 | 2026-03-04 | D | 5,18 | LOSER |
| 67 | 2026-03-11 | D | 12,21 | LOSER |
| 79 | 2026-04-15 | C | 6,78 | LOSER |
| 83 | 2026-05-06 | C | 1,76 | LOSER |
| 84 | 2026-05-07 | C | 3,10 | LOSER |
| 85 | 2026-05-13 | C | 0,62 | LOSER |

(`results/n96_intra_bear_cut_list.json`.) 2025: 2 cortes (+2R) · 2026: 11 cortes (+11R).

## 6. DA dedicado (PROFITABLE_BUT_FRAGILE)
Verificou tudo do RAW antes de atacar. **A causalidade PASS** (1D_px_vs_ema recomputado do RAW = último bar 1D fechado; regime hour-causal). **C:** sinal robusto (0 winners cortados em toda variante), magnitude frágil (+4…+13). **D:** não é cluster (9 semanas). **E:** lucro confirmado 0W/13L. **F:** o gate de regime faz trabalho real (mesma feature +78R fora / −13R dentro). **Multiplicidade:** 1D_px_vs_ema nem é a célula de máx-separação (1D_ema_trend é mais forte, AUC 0,098) → escolheram a feature teórica, não a mais forte.

## 7. Caveats obrigatórios
- **N pequeno**; 11 dos 13 cortes num único bear (2026); out-of-2026 = 2 trades.
- `PROFITABLE_BUT_FRAGILE`; **magnitude +4…+13R** conforme detector — nunca citar +13 solto.
- **NOT_PRODUCTION**; precisa **forward / live review** como árbitro final.
- **Daily RAW/HTF congela em 2026-05-24 → extensão pendente** para uso futuro/live (o filtro não dispara live até a daily retomar). Não contamina o histórico.
- Não alterar `strategy_rules`; não Telegram; não runtime; não usar como SHORT; não confundir com o filtro global (morto); válido **apenas dentro de regime BEAR**.

## 8. Próximos passos
- Estender daily RAW/HTF pós-2026-05-24 (bloco `RAW_15M_EXTENSION_PLAN`) para viabilizar forward/live.
- Forward nas ops live do Cris.
- Rodada **RANGE / distribuição-de-range** com RAW/MTF completo (mesmo método estrutural-primeiro): losers RANGE causais = #5,6,7,8 (R) + #27,31,48,60,68,69.

## Artefactos (research/xau_15m_bb_nas_leonardo/)
`n96_mtf_kit.py` · `n96_exhaustive_mtf_discrimination.py` · `n96_confluence_reading.py` · `n96_causal_regime_recross.py` · `n96_within_bear_depth_filter.py` · `n96_within_bear_hardening.py` · `results/n96_causal_regime.json` · `results/n96_intra_bear_cut_list.json`. Detector canónico: `engine_substrate4_v5_hourcausal.py`. Régua de regime: `regime_turnstate_engine/ground_truth/cris_regime_boxes.csv`.
