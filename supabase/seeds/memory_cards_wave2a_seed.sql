-- ============================================================================
-- SUPABASE MEMORY — CARDS WAVE 2A · seed:memory_cards_wave2a · gerado por scripts/memory/generate_wave2a_seed.py
-- ============================================================================
-- Plano: docs/architecture/SUPABASE_MEMORY_WAVE2_PLAN.md
-- 50 memory cards criticos/atuais -> memory_items (1 card = 1 row).
-- body = frontmatter description do card (resumo curado); conteudo integral
--   permanece no card local (source_ref). Zero RAW, zero edge detalhado, zero secrets.
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV). MCP permanece read-only.
-- IDEMPOTENTE: md5-uuid deterministico + ON CONFLICT (id) DO NOTHING.
-- Copiar SEMPRE do ficheiro/raw (nunca de render de chat — corrompe aspas).
-- ROLLBACK (comentado no fim): delete por batch tag.
-- ============================================================================

begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_cards_wave2a:PRINCIPAL_1_claude_behavior.md')::uuid,
  'product', 'internal', 'feedback',
  'PRINCIPAL_1_claude_behavior',
  '⭐ PRINCIPAL #1 — Karpathy''s Rules + protocolos permanentes de comportamento, comunicação, cadência. Sintetiza 12 feedbacks individuais. LER NO INÍCIO DE TODA SESSÃO.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/PRINCIPAL_1_claude_behavior.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:PRINCIPAL_2_engineering_discipline.md')::uuid,
  'product', 'internal', 'feedback',
  'PRINCIPAL_2_engineering_discipline',
  '⭐ PRINCIPAL #2 — Disciplina técnica + rigor estatístico + lições engineering. Sintetiza 23 feedbacks individuais. LER NO INÍCIO DE TODA SESSÃO.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/PRINCIPAL_2_engineering_discipline.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:PRINCIPAL_3_anti_myopia.md')::uuid,
  'product', 'internal', 'feedback',
  'PRINCIPAL_3_anti_myopia',
  'PRINCIPAL #3 — protocolo anti-miopia (sintese permanente). Conteudo integral no card local.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/PRINCIPAL_3_anti_myopia.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_never_use_slim_features.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_never_use_slim_features',
  'PROIBIÇÃO PERMANENTE — nunca usar slim_features para nada neste projeto; sempre RAW pine_boxes/pine_labels/study_values',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_never_use_slim_features.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_no_oos_no_crossasset_validation.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_no_oos_no_crossasset_validation',
  'TRAVA DURA PERMANENTE — NUNCA recomendar OOS / held-out / cross-asset (EUR/USOUSD) / bear-2013-2016 como gate de validação ou promoção; Cris matou isso 3+ vezes; validação mora DENTRO dos 276',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_no_oos_no_crossasset_validation.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_validate_before_presenting.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_validate_before_presenting',
  'NUNCA apresentar resultado parcial/não-validado que cria expectativa; auditar o PRÓPRIO processo (bugs de scoring/causalidade) ANTES de mostrar qualquer número. E não fazer screenshots/visualizações próprias — Cris faz.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_validate_before_presenting.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_never_capture_screenshot_unless_requested.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_never_capture_screenshot_unless_requested',
  'NUNCA capturar screenshot via capture_screenshot/MCP a não ser que Cris peça explicitamente; ele vê o chart direto no TradingView Desktop',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_never_capture_screenshot_unless_requested.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_full_panel_always.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_full_panel_always',
  'Cris exige PAINEL COMPLETO de métricas em todo report de backtest/amostra daqui em diante — incluir STREAK (perdas/ganhos consecutivos), que eu havia omitido.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_full_panel_always.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_devils_advocate_fulltime.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_devils_advocate_fulltime',
  '🚨 REGRA PERMANENTE 2026-06-04 — agente Devil''s Advocate full-time + sequential-thinking + skills carregados para evitar análises superficiais durante research Caminho B (e qualquer estratégia)',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_devils_advocate_fulltime.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_close_only_causal_universal.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_close_only_causal_universal',
  '🚨 REGRA PERMANENTE 2026-06-06 — CLOSE-ONLY-CAUSAL UNIVERSAL: toda feature em qualquer backtest XAU/EUR/USOUSD usa APENAS dados do bar fechado i + bars anteriores. Entry no close do bar i. Indicadores que podem repintar (SMC, Bubbles, OB) → SHIFT1 (consultar bar i-1) por default. Look-ahead estruturalmente anulado se aplicado consistentemente.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_close_only_causal_universal.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_engine_objetivo_lucro_nao_winrate.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_engine_objetivo_lucro_nao_winrate',
  'O engine L2/BPT (e a suite) existe para LUCRO em prop firm, não para n baixo / ultra-winrate; equilíbrio winrate × R:R × frequência',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_engine_objetivo_lucro_nao_winrate.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_operational_viability_streak.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_operational_viability_streak',
  'Critério de 1ª classe p/ L2/BPT range (Cris 2026-07-01): VIABILIDADE PSICOLÓGICA/OPERACIONAL (streak de losses, WR, consistência mensal p/ saque em prop) — NÃO só expectancy. 13 losses:1-2 wins é matematicamente positivo mas inexecutável por humano.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_operational_viability_streak.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_episode_unit_of_analysis_canon.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_episode_unit_of_analysis_canon',
  'VIRADA ARQUITETURAL PERMANENTE — a unidade de análise é o EPISÓDIO de mercado que produziu o trade, não trade→feature→decisão; o leitor (LLM) julga holisticamente, o medidor (código) nunca julga',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_episode_unit_of_analysis_canon.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_calibration_vs_validation_45_groups.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_calibration_vs_validation_45_groups',
  '🚨 REGRA METODOLÓGICA PERMANENTE 2026-06-07 — Os 45 grupos visualmente classificados (BOM/RUIM/AMBI) são SET DE CALIBRAÇÃO, NÃO validação de edge. Usar para descobrir predicados, separar visualmente, eliminar métricas que não discriminam. NUNCA usar para provar edge, lockar thresholds finais, ratificar estratégia ou concluir winrate/drawdown. Aplicar em todas frentes futuras.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_calibration_vs_validation_45_groups.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_no_superficial_hasty_reading.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_no_superficial_hasty_reading',
  'Funcionamento superficial/apressado é a causa-raiz dos erros mais graves do projeto. Carregar SEMPRE os caveats; tratar leads como hipóteses; respostas curtas e leigas.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_no_superficial_hasty_reading.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_no_auto_recommend_next_lane.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_no_auto_recommend_next_lane',
  'NÃO empurrar próximo-passo preferido ao fim de relatórios. Caminho B NÃO deve ser recomendado como ''próximo bloco'' — Cris decide quando. Ficar na pista de investigação atual até nova ordem.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_no_auto_recommend_next_lane.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_pause_daemon_and_cron.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_pause_daemon_and_cron',
  'Sistema XAU 4H roda em modo híbrido daemon+cron — pausar apenas o daemon NÃO basta; o cron triggara execuções que tocam o chart. Sempre pausar AMBOS antes de plotar/visual review.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_pause_daemon_and_cron.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_canonical_trade_plotting.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_canonical_trade_plotting',
  'Ao plotar trades no TradingView, usar SEMPRE long_position canônico + label, nunca só labels de texto',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_canonical_trade_plotting.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_nas_long_short_never_top_bottom.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_nas_long_short_never_top_bottom',
  'REGRA PERMANENTE — leitura operacional do NAS é SEMPRE LONG/SHORT (pine_labels via first-appearance), NUNCA TOP/BOTTOM nem NAS_*_SIGNAL numérico',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_nas_long_short_never_top_bottom.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_bubbles_polarity_rule.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_bubbles_polarity_rule',
  'BUBBLES polarity is CONTEXT-DEPENDENT — Auction Theory (bubble_sell at bottom) applies to true reversal at lows, bubble_buy applies to pullback-in-uptrend continuation. Empirically validated 2026-06-03.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_bubbles_polarity_rule.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_indicators_raw_first.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_indicators_raw_first',
  'TODO indicador (NAS/SMC/bubbles/RSI/SVP/OB) vem do RAW replay ORIGINAL, nunca de derivado (raw_features_2020_2026/repro_recovery/frozen/slim/packet); auditar RAW antes de declarar indicador ausente/stale',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_indicators_raw_first.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_never_declare_blocked_without_provenance_search.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_never_declare_blocked_without_provenance_search',
  'PROIBIDO declarar uma métrica/fonte ''ausente/BLOCKED/não-serializada/não-reconstruível'' sem ANTES: (1) buscar no repo+memória uma extração já existente/validada, (2) verificar o layout real do campo, (3) checar contra prints/chart. Refazer extração já feita = falha grave.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_never_declare_blocked_without_provenance_search.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_macro_engine_methodological_canon.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_macro_engine_methodological_canon',
  'TRAVA PERMANENTE — a frente L2/BPT Macro Structural Reading Engine não é busca de filtros/gates sobre realR capado/teaching-set agregado; é leitura estrutural convergente trade-a-trade com prioridades causais ordenadas',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_macro_engine_methodological_canon.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_prior_layers_conditional_evidence.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_prior_layers_conditional_evidence',
  'TRAVA permanente — nunca descartar specs/features anteriores por falharem isoladamente; viram evidência condicional sob novo contexto estrutural',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_prior_layers_conditional_evidence.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:reference_backtest_methodology_checklist.md')::uuid,
  'product', 'internal', 'reference',
  'reference_backtest_methodology_checklist',
  '🔬 Checklist canônico de 15 problemas metodológicos insidiosos em backtests (além de look-ahead). Aplicar SISTEMATICAMENTE em todo backtest antes de promover candidato. Cada item tem mecanismo + método de detecção empírica. Criado 2026-06-06 após sessão autônoma identificar outlier dominance/concentração temporal/time-of-day/correlação como herdados em B v1.5 SHIFT1.',
  array['seed:memory_cards_wave2a','wave:2A','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_backtest_methodology_checklist.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:reference_loops_cron_governance.md')::uuid,
  'product', 'internal', 'reference',
  'reference_loops_cron_governance',
  'Política de uso de /loop + cron (features nativas reais do Claude Code) no projeto — só tarefas determinísticas não-produção; loop-de-research autónomo PROIBIDO (fábrica de ilusões).',
  array['seed:memory_cards_wave2a','wave:2A','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_loops_cron_governance.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_regras_operacionais_2026_06_06.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_regras_operacionais_2026_06_06',
  '🚨 REGRAS OPERACIONAIS PERMANENTES 2026-06-06 — 19 regras inviáveis para execução autônoma multi-dias (escopo de arquivos, não interferência em sistemas externos, anti-overwork, anti-buraco-lógico, devil''s advocate full-time, leitura de prints, multi-strategy cross-refinement, regimes, SHORT bonus). Autorizadas por Cris.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_regras_operacionais_2026_06_06.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_safe_backtest_window_executes.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_safe_backtest_window_executes',
  'safe_backtest_window.sh NÃO tem modo validar-apenas — rodar com TF válido + datas válidas abre uma maintenance window REAL e executa o collector. Como validar com segurança.',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_safe_backtest_window_executes.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_backtest_chart_isolation.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_backtest_chart_isolation',
  'Antes de rodar backtest via replay MCP, DESATIVAR os 2 LaunchAgents claude-intraday-monitor e claude-monitor — eles trocam o chart no meio do run',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_backtest_chart_isolation.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:feedback_use_plan_agent_for_architecture.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_use_plan_agent_for_architecture',
  'Forçar uso do Plan subagent ANTES de escrever código quando mudança toca arquitetura, prompt operacional, pipeline ou módulo de strategy',
  array['seed:memory_cards_wave2a','wave:2A','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_use_plan_agent_for_architecture.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_l2_bpt_structural_regime_level_engine.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_structural_regime_level_engine',
  '✅ OK FINAL Cris 2026-07-02 — USER_APPROVED_NOT_PRODUCTION (escopo B integral+caveats, VISUAL_REVIEW_COMPLETED_BY_USER): V2 zona-pura N17 WR53% +36,2R avgR+2,13 DD−4,1 streak3 (BULL6/RANGE10/BEAR1). BEAR canónico=phase48 (n=1, NÃO coração estatístico); RANGE=beta/concentrado/overfit-risk; ''RANGE+BEAR coração''=linguagem CALIBRADA. Causal-limpo (DA Q1 PASS). Registada em 04_STRATEGY_STATUS_MASTER §4.4 + Confirmation Sheet; PUSHED origin/main e90e971. NOT_PRODUCTION (sem runtime/exec).',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_structural_regime_level_engine.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_l2_bpt_base_approved.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_base_approved',
  'BASE APROVADA L2/BPT (Cris 2026-06-25): entrada → SL_CONTEXT → let-run → skip(conv≤1 ∪ bear_leg_refined). 214 trades, WR 35.5%, +79.2R, maxDD 27.6, 0 runners cortados. Objetivo agora: WR 50% sem perder nenhum winner/monumental.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_base_approved.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_l2_bpt_sl_exit_approved.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_sl_exit_approved',
  'APROVADO DEFINITIVO (Cris 2026-06-25) — SL estrutural = SL_CONTEXT (demanda 4H defendida) + EXIT = let-run. NÃO se discute mais; régua oficial da estratégia L2/BPT.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_sl_exit_approved.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_xau_15m_swept_runner_signal.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_swept_runner_signal',
  'XAU 15M — swept_prior_low (sweep de liquidez, CAUSAL) é o diferenciador da entrada-runner dentro de clusters. KEEP-swept-em-cluster valida (null p=0): DD -51→-23, r/DD 8,6→18,3. 1º lever positivo na base-janela.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_swept_runner_signal.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_xau_15m_loser_filters.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_loser_filters',
  'XAU 15M LONG BOTTOM — frente de filtrar losers sobre a base APROVADA swept-sempre (N896). Filtro #1 VALIDADO = h1_pos>=0,44 (corta 224 quase-só-losers, avgR 0,354->0,446, null p=0,018). Mapa: reclaim_atr/up_closes/confirm_body separam mas cortá-los derruba sumR.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_loser_filters.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_xau_15m_8atr_stack_preapproved.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_8atr_stack_preapproved',
  'PRÉ-APROVADO (Cris 2026-06-27) — estratégia XAU 15M LONG "8ATR confirm + R2 + R_B lapidado". WR ~69-71%, scalp alto-acerto SEM convexidade. Números deployáveis (dedup) + caveats. NÃO é OFICIAL ainda.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_8atr_stack_preapproved.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_xau_15m_regime_detector_and_direction.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_regime_detector_and_direction',
  'XAU 15M — detector causal de regime (RANGE/BULL/BEAR) calibrado às zonas visuais do Cris + testes de direção-por-regime (Engine 7/8). Detector=causal/útil; direção=beta-overlay, short-bear=artefato 1-período.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_regime_detector_and_direction.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_regime_turnstate_engine.md')::uuid,
  'private', 'private', 'project',
  'project_regime_turnstate_engine',
  'DECISÃO (Cris 2026-06-29) — Regime & Turn-State Engine = MÓDULO transversal de 1ª classe (molde External Factors), não feature em entry/filtro. Tese central do projeto. Status=SPEC_EM_PLANEJAMENTO.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_regime_turnstate_engine.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_external_factors_v2_plan.md')::uuid,
  'private', 'private', 'project',
  'project_external_factors_v2_plan',
  'External Factors v2 — módulo macro NOVO (não reativa iMac cancelado). Two-tier (FRED-numérico-keyless backtestável vs LLM-realtime-contexto). Fase 0 FEITA. Agent SDK na Fase 3. Construção autônoma (FRED keyless, sem depender de keys do Cris).',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_external_factors_v2_plan.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_xau_4h_long_objetivo_final.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_long_objetivo_final',
  '🎯 OBJETIVO PERMANENTE 2026-06-06 — construir SUITE de estratégias XAU 4H LONG limpas (Wilson lower ≥45%, sumR positivo, monumentais ≥+20R capturados), múltiplas filosofias Auction Theory ortogonais, cobertura por regime, baseado em leitura de prints. 1 estratégia >50% NÃO interrompe busca. Após exaustar LONG, explorar SHORT espelho.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_long_objetivo_final.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_fundednext_constraints.md')::uuid,
  'private', 'private', 'project',
  'project_fundednext_constraints',
  'Operational constraints from FundedNext prop firm plan that govern XAU 4H REVERSAL_LONG V1.3+ strategy decisions',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_fundednext_constraints.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_xau_4h_reversal_v1_4g_rws_a6_a7.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_reversal_v1_4g_rws_a6_a7',
  'V1.4g-RWS-A6-A7 OFICIAL ATUAL XAU 4H REVERSAL_LONG — WR 67.2%, streak 4, DD 4.4R, 100% monumentais preservados, +A7 anti RSI bear div cluster',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_reversal_v1_4g_rws_a6_a7.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2a:project_xau_4h_caminho_b_long.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_caminho_b_long',
  'Caminho B LONG OFICIAL XAU 4H — bottom catcher / macro fundos. Convergent rule from 4 agents + anti_demand + rsi≤30. n=177, 28/30 monumentais ≥10R preservados, +254.5R, FN-compatible 0.2% sizing.',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_caminho_b_long.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2a:project_regime_classifier_v3_official.md')::uuid,
  'private', 'private', 'project',
  'project_regime_classifier_v3_official',
  'Regime Classifier B v3 OFICIAL — sistema-nível 3 estados (BULL/TRANSITION/BEAR) com Cascade+Vol+STALL+SHARP_DROP+DIST_ALARM+MACRO_BROKEN state machine',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_regime_classifier_v3_official.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2a:project_python_strategy_monitor.md')::uuid,
  'private', 'private', 'project',
  'project_python_strategy_monitor',
  '2026-05-21 — Caminho D Python adotado pra novas estratégias. monitor_xau_4h_strategies.py operacional com 3 estratégias (CAPITULATION + DISCR BASE + DISCR SWEEP) via daemon event-driven + cron 1x/hora',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_python_strategy_monitor.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2a:project_xau_l1_paused_2026_06_23.md')::uuid,
  'private', 'private', 'project',
  'project_xau_l1_paused_2026_06_23',
  'xau-l1-cycle LaunchAgent PAUSADO intencionalmente 2026-06-23 p/ sessão Reader Vivo (plotagem chart); NÃO religar sem autorização do Cris',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_l1_paused_2026_06_23.md',
  'paused'
),
(
  md5('seed:memory_cards_wave2a:user_role.md')::uuid,
  'private', 'private', 'user',
  'user_role',
  'Cristiano trabalha com parceiro Leonardo num projeto de trading que busca validação por proxy (não automação). Eu sou Professional Trading Assistant, não bot.',
  array['seed:memory_cards_wave2a','wave:2A','type:user'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/user_role.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:user_name_ris.md')::uuid,
  'private', 'private', 'user',
  'user_name_ris',
  'User prefers to be addressed as \"Cris\" (short for Cristiano)',
  array['seed:memory_cards_wave2a','wave:2A','type:user'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/user_name_ris.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:project_supabase_memory_full_migration.md')::uuid,
  'private', 'private', 'project',
  'project_supabase_memory_full_migration',
  'Bloco ativo 2026-07-02 — migração total da memória durável para Supabase DEV; XAU 15M/SHORT deferred até completar; MCP sempre read-only, escrita só Cris via SQL Editor',
  array['seed:memory_cards_wave2a','wave:2A','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_supabase_memory_full_migration.md',
  'active'
),
(
  md5('seed:memory_cards_wave2a:reference_gold_analysts_sources.md')::uuid,
  'private', 'private', 'reference',
  'reference_gold_analysts_sources',
  'Lista curada de fontes humanas de ALTA qualidade p/ análise de ouro (XAU)/metais — complemento humano (Tier-2 contexto, NUNCA sinal) do External Factors. Tiered por independência+rigor, com tag de viés.',
  array['seed:memory_cards_wave2a','wave:2A','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_gold_analysts_sources.md',
  'active'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- ROLLBACK (NAO EXECUTAR JUNTO — so em DEV, manual, sob autorizacao)
-- ============================================================================
-- begin;
-- delete from memory_items where 'seed:memory_cards_wave2a' = any(tags);
-- commit;
-- ============================================================================
