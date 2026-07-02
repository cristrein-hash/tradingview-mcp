# XAU 15M LONG — REGIME DETECTOR RE-ADAPTATION · READ-ONLY AUDIT (2026-07-02)

**Modo executado:** read-only / audit-first — zero backtest, zero chart/TradingView/MCP-visual, zero produção/runtime/Telegram/daemons/RAW/strategy-rules/monitor tocados, zero plot gerado (plotting-canon skill aplicado como REGRA — nenhuma plotagem nesta fase).
**Fontes:** git (HEAD==origin ✓, tree limpo) · project authority (04/02/10 lidos integralmente no contexto principal; 00/01/03/05/07 extraídos por subagent Explore real) · Supabase memory via MCP read-only (queries 15M/regime/swept) · memory cards locais lidos integralmente (regime_detector, swept_runner, loser_filters, 8atr_stack) · PLOTTING_CANON_MASTER + skills/plotting-canon (autoridade desta sessão) · inventário completo de `research/xau_15m_bb_nas_leonardo/` (466 .py, 33 .csv) + revalidation + runtime cross-check por subagent Explore real.

## 1. Executive verdict

**Estado do XAU 15M LONG: LIMPO, APROVADO E BEM-DEFINIDO — pronto para re-adaptação de regime.** A estratégia principal (swept-runner base #4) é `USER_APPROVED_NOT_PRODUCTION` com stack 100% causal, zero contaminação SLIM (guard mecânico + grep confirmam), RAW mapping único e sancionado, e **pendência única para OFICIAL_FN = slippage/custos**. O detector de regime v5 MTF é o canônico ("o melhor que temos", Cris 2026-06-28). Conflitos encontrados são documentais (docs stale), não estruturais.

## 2. Estado real da estratégia (do status master L55 + cards + artefatos)

**`XAU 15M LONG · swept-runner (+ #4, 8ATR, regime-v5)` = USER_APPROVED_NOT_PRODUCTION** (aprovada Cris 2026-06-28; status master já aponta "NEXT review block: 15M regime re-adaptation" — este bloco).

**Stack final 100% causal (gates reais, em ordem):** fractal-low k3 confirmada (entry close cj=p+3) → KNIFEKILL_v2 → **regime v5 hour-causal ≠BEAR** → HTF 4H&1D up → `swept_prior_low==1` → `h1_pos≥0,44` → `pos_recent20≥q0,25` → `rsi_cj≥q0,2`. SL = flush(min low p..cj −0,1ATR). Exit = let-run (trail swing-low pós+1R, HMAX480, cap20R).
**Métricas (2024-26):** N435 · WR47,6% · +291,5R · avgR0,670 · DD−11,0 · r/DD26,58 · streak−8/+6 · por-ano 39,7/213,6/38,3 (todos +).
**Validação interna feita:** swept null p=0 · h1_pos null p=0,018 · jackknife-por-EPISÓDIO robusto (nenhum bloco carrega; sem OOS por cânone) · hour-causal sem look-ahead.

## 3. Classificação por componente

| Componente | Classificação | Nota |
|---|---|---|
| Swept-runner base #4 (stack acima) | **approved** (USER_APPROVED_NOT_PRODUCTION) | pendência única OFICIAL_FN: slippage/custos |
| Regime detector **v5 MTF** (`engine_regime15m_v5.py`) | **active/canônico** | estável diária v2 + override 1H dd%≥6%; balanceada 87,7%, BEAR onset 0,3-0,5d |
| Regime v1/v3/v4 (`engine_regime15m*.py`) | **superseded** | retidos como histórico; v4 descartado (fragmentou RANGE) |
| Loser-filter #1 (`h1_pos≥0,44`) | **approved** (parte do stack) | frente "filtrar losers" concluída: 0/27 combos micro robustos; parede confirmada |
| CHoCH-up-HTF (N84 avgR1,19 DD−3,5 null p=0,003) | **active** (sub-estratégia separada validada como ideia) | "poucas balas alta assertividade"; pendente exit próprio/sizing se desenvolver |
| 8ATR / 5ATR A2 stack (+h1_eff+macro≠BEAR, N181 WR65,2% +75,6) | **dormant** (PRÉ-aprovado, não oficial) | scalp sem convexidade; número realista +44-75R/2anos uma-posição |
| Bottom-power engine · transversal monforte · managed-agents engine | **dormant** | eixos futuros declarados |
| Engine 2 (entrada MON+FORTE) · Engine 7 (confluência fundo) · Engine 8 (direção-por-regime) · short-mirror · macro-bottom · window-cleaning · T2/T3 range | **superseded/refutados** | paredes conhecidas — NÃO re-escavar |
| `XAUUSD_INTRADAY_BB_CONFLUENCE` (lab 2026-06-01) | **needs_revalidation** (RESEARCH no master) | linhagem SEPARADA e mais antiga; não confundir com swept-runner |
| `manual_trade_table.csv` (PDFs Leonardo, 15W+4L curados) | **calibração apenas** | README: NUNCA base rate/expectancy |
| Contaminação SLIM | **NENHUMA** | `_source_guard.py` proíbe mecanicamente slim/raw_features/repro_recovery etc.; grep limpo; nuance declarada: Custom OB v11 = proxy BigBeluga por linhagem Pine (em MANIFEST_PROVENANCE, documentado, não oculto) |

## 4. Mapa técnico

- **RAW/source (fonte única):** `/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M` (gz, 8 blocos, ~47k bars, **2024-05 → 2026-02**) → `build_causal_primitives.py` (único leitor do RAW) → `primitives/*.primitives.json` (9,7M) + `bubbles/*.jsonl` (known_at-filtered) + `htf_primitives/` (4H/1D nativos). Todos os engines leem SÓ primitives/bubbles/htf + jsonls gerados. 6/6 referências a /Volumes apontam ao path sancionado.
- **Detector v5:** inputs = primitives (15M→1H+diário) + `regime_zones_cris.json` (6 zonas ground-truth do Cris via MCP). Config P=48h/mom24h/dd6%/Krec5. Output `regime15m_v5_result.json` (30-jun, artefato mais recente). Uso causal = hour-causal (override no último 1H fechado ≤t + estável D-1).
- **Artefatos aprovados:** `sweptsempre_window.csv` (309) · `sweptsempre_bull.csv` (257) · `swept_keep_window.csv` (440) · `substrate4_window.csv` (128) · `strategy_trades.csv` (410) · `strategy_chosen_trades.csv` (181) · `strategy_5atr_*.csv` (257/212/171) · engines `engine_substrate4_v5_hourcausal.py` (base final), `engine_jackknife_episodes.py`, `engine16_swept_null.py`, `engine21/22` (loser map/validate).
- **Base aprovada = swept-sempre N896** (⊆ keep-swept, verificado `verify_swept_subset.py`); keep-em-cluster (N1284) foi a pré-aprovada líder antes do swept-sempre virar A base — ambas registradas, sem ambiguidade de qual vale (swept-sempre, Cris 2026-06-28).
- **Outputs vivos / runtime:** **NENHUM runtime 15M existe** (sem daemon/monitor/cron/LaunchAgent; `run_xau_15m_pullback_ohlcv.py` = coletor histórico offline). Consistente com re-audit de produção.
- **Scripts canônicos de plot 15M** (reconciliados R1/R2 nesta data): `plot_strategy_canonical`, `plot_chosen_canonical`, `plot_5atr_*` (width 10 pós-R1), `plot_candidates_canonical`, `plot_reversals_canonical`; one-shots/exceções banner-marcados. Toda plotagem futura via `skills/plotting-canon`.
- **Nota de data:** `plot_*.py` com mtime 02-jul = patches R1/R2 desta sessão (commits `d645b17`/`4270180`), não re-execuções.

## 5. Conflitos identificados (memória × docs)

1. **00_PROJECT_OVERVIEW e 05_SYSTEM_ARCHITECTURE estão STALE vs 04_STATUS_MASTER:** não citam 15M (nenhum status/timeframe canônico/dataset), mas o 04 (2026-07-02) tem a entrada aprovada. **Proposta:** reconciliar 00/05 num batch doc futuro (não bloqueia este bloco; 04 é o canônico de status).
2. **07_INCIDENTS Incident 6 CONTRADIZ o plotting canon:** manda usar "stopLevel/profitLevel = absolute price levels" — wording pré-bug-de-ticks (2026-06-11), hoje **ERRADO** (canon = TICKS offsets). Risco real de reintroduzir o bug seguindo o 07. **Proposta:** corrigir a linha no 07 com ponteiro ao PLOTTING_CANON_MASTER (requer autorização, doc de autoridade).
3. **Detector v5 × marcação BEAR do Cris (jan-2026):** o detector estende regime até ~mar-2026 (lê bounce fev-mar +6% como RANGE/BULL — causalmente correto, não-shortar-repique), enquanto a zona BEAR do Cris começa no topo (29-jan, marcação macro). Concordância BEAR 0,75 por isso. Registrado nos cards como divergência de natureza (macro vs causal), calibração n=6. **É o coração da "re-adaptação de regime"** — decidir se/como tratar (aceitar como está · re-calibrar override · camada extra), decisão do Cris.
4. **Cobertura RAW termina 2026-02:** ~4-5 meses sem RAW 15M (mar→jun-2026, incl. o BEAR 2026 inteiro do Cris). Qualquer re-adaptação/validação sobre 2026 recente exigirá **coleta Replay nova** (safe_backtest_window, bloco próprio autorizado).
5. Supabase memory × cards locais: **consistentes** (espelho fiel; sem conflito).

## 6. Riscos de plotagem (mapeados, mitigados)

Scripts 15M reconciliados (R1: widths 10 nos reusáveis, draw_clear gated; R2: one-shots banner-marcados). Gramática de cor 15M tem os 2 modos oficiais (outcome/direction) — declarar por plot. Nenhum plot será gerado fora do `skills/plotting-canon`. Sem risco aberto.

## 7. O que "re-adaptação de regime" tem de decidir (próximos passos PROPOSTOS — decisão do Cris)

A. **Resolver a divergência v5 × BEAR-jan-2026** (conflito #3): aceitar leitura causal do v5 · re-calibrar override BEAR · ou camada macro adicional. (Passo 9 do protocolo 03: split-por-regime + thresholds vizinhos.)
B. **Estender RAW 15M** (mar→jun-2026) via coleta Replay autorizada — pré-requisito para re-adaptar com o BEAR-2026 completo e re-validar o corte de regime.
C. **Slippage/custos** — a pendência única do OFICIAL_FN da estratégia aprovada (independe de A/B; pode rodar sobre a base atual).
D. **Alinhamento com RTSE** — o v5 é candidato natural a implementação-referência do Regime & Turn-State Engine (módulo transversal, SPEC_EM_PLANEJAMENTO); decidir se a re-adaptação acontece dentro do RTSE ou na linha atual.
E. (Menor) Reconciliar docs 00/05/07 (conflitos #1/#2).

Nenhum destes foi iniciado — bloco atual é audit-only. Ordem/escolha = Cris.

## 8. Critérios de aceitação (cumpridos)

- [x] Estado real mapeado (estratégia, detector, artefatos, RAW, runtime) · [x] conflitos memória/docs identificados (5) · [x] RAW/source mapping preliminar (§4, fonte única sancionada) · [x] plotting canon aplicado como regra, zero plot · [x] próximos passos propostos sem auto-decisão · [x] zero backtest/produção/chart/RAW-write · [x] commit local, sem push sem autorização.
