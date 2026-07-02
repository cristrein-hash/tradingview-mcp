-- ============================================================================
-- SUPABASE MEMORY — CARDS WAVE 2FINAL (fecho da migracao) · seed:memory_cards_wave2final
-- gerado por scripts/memory/generate_wave2final_seed.py (reconciliacao 229/229 embutida)
-- ============================================================================
-- Review: docs/architecture/SUPABASE_MEMORY_WAVE2FINAL_REVIEW_20260702.md
-- 30 cards restantes -> memory_items: Grupo A operacionais/config +
--   Grupo B legacy/no-metadata (revisao card a card; 'unknown_review' quando duvidoso).
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV). MCP permanece read-only.
--   Pos-Run, verificar no proprio SQL Editor:
--   SELECT count(*) FROM memory_items WHERE tags @> ARRAY['seed:memory_cards_wave2final'];  -- esperado 30
-- IDEMPOTENTE: md5-uuid deterministico + ON CONFLICT (id) DO NOTHING.
-- Copiar SEMPRE do ficheiro/raw (nunca de render de chat — corrompe aspas).
-- ============================================================================

begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_cards_wave2final:project_custom_ob_detector_v10.md')::uuid,
  'private', 'private', 'project',
  'project_custom_ob_detector_v10',
  'Pine Script construído 2026-05-18 que replica BigBeluga Smart Money Concepts (OB detection + state machine + lifecycle) com payload JSON enriquecido pro indicator_signals pipeline',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_custom_ob_detector_v10.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:project_monitor_targets_leak.md')::uuid,
  'private', 'private', 'project',
  'project_monitor_targets_leak',
  'alert-bridge/monitor_targets.json e monitor_targets_intraday.json estão tracked no git mas são modificados continuamente pelo intraday monitor. Backlog Task #14 desta sessão.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_monitor_targets_leak.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2final:project_pipeline_fase3.md')::uuid,
  'private', 'private', 'project',
  'project_pipeline_fase3',
  'Fase 3 do pipeline indicator_signals construída 2026-05-18 — enrich_indicator_outcomes.py (cron diário 03:00) + report_indicator_edge.py (manual/mensal) pro backtest D2R',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_pipeline_fase3.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2final:project_receiver_broker_prefix_normalization.md')::uuid,
  'private', 'private', 'project',
  'project_receiver_broker_prefix_normalization',
  'tv_webhook_receiver.py normaliza broker prefix defensivamente antes de gravar indicator_signals.jsonl',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_receiver_broker_prefix_normalization.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:project_replay_historical_base_multitf.md')::uuid,
  'private', 'private', 'project',
  'project_replay_historical_base_multitf',
  'Base histórica multi-TF XAU via TradingView Replay (15M/30M/1H) — progresso de coleta, layout de indicadores baseline, e armazenamento frio no HD externo',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_replay_historical_base_multitf.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:project_roadmap_post_xau_1h_v1.md')::uuid,
  'private', 'private', 'project',
  'project_roadmap_post_xau_1h_v1',
  'Roadmap declarada 2026-06-02 pelo operador após adoção da hipótese XAU_1H_DEMAND_RECLAIM_REENTRY_LONG v1.1. Próximas frentes em ordem: (1) revisão visual manual da v1.1 em curso, (2) refinar XAU 4H operacional, (3) construir intraday agressivo 15M+30M contextualizado por 1H+4H. Sistema em pausa mantida — não restaurar.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_roadmap_post_xau_1h_v1.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:project_smc_eur_audit_v3.md')::uuid,
  'private', 'private', 'project',
  'project_smc_eur_audit_v3',
  'V3d Leonardo OB em EURUSD 4H — descoberta forte (Sharpe combined +1.10, +172% R). V3d shadow logando em produção desde 2026-05-15.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_smc_eur_audit_v3.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:project_smc_xau_audit_v3.md')::uuid,
  'private', 'private', 'project',
  'project_smc_xau_audit_v3',
  'Audit Leonardo SMC vs mecânico no XAU 4H. V3c/V3d são COMPLEMENTARES (não substitutos). Decisão pendente sobre módulo paralelo.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_smc_xau_audit_v3.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:project_telegram_silencer_observacao.md')::uuid,
  'private', 'private', 'project',
  'project_telegram_silencer_observacao',
  '2026-05-15 — SETUP_EM_OBSERVACAO silenciado no Telegram. Critical_terms causava 51% false-positive em records OBSERVACAO. Routing V3.1.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_telegram_silencer_observacao.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:project_tf_15m_long_liberated.md')::uuid,
  'private', 'private', 'project',
  'project_tf_15m_long_liberated',
  '2026-05-15 — TF 15M LONG removido da regra \"rigor extra\". Tratamento igual TF 4H quando direção LONG + ativo whitelist. Baseado D2R Phase 2 n=208.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_tf_15m_long_liberated.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:project_tv_layouts_architecture.md')::uuid,
  'private', 'private', 'project',
  'project_tv_layouts_architecture',
  '5 layouts TradingView (4 split-2 + 1 single) aprovados 2026-05-17 — 1 layout por ativo, pareamento 4H+1H, stack canônico 7 indicators',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_tv_layouts_architecture.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:project_watchlist_focus_5_plus_usousd.md')::uuid,
  'private', 'private', 'project',
  'project_watchlist_focus_5_plus_usousd',
  '2026-05-18 — Watchlist reduzida a 6 ativos (XAUUSD, EURUSD, US500, ETHUSD, XAGUSD, USOUSD); BTCUSD+XPTUSD removidos pra otimizar dados+indicadores; USDJPY+GBPUSD já estavam fora',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_watchlist_focus_5_plus_usousd.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:project_external_factors_audit_roadmap.md')::uuid,
  'private', 'private', 'project',
  'project_external_factors_audit_roadmap',
  '2026-05-19 auditoria External Factors v1.2 + roadmap P0-P4; P0.1+P0.2 aplicados (commit e63967e); aguardar 30d antes de promover qualquer fator',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_external_factors_audit_roadmap.md',
  'superseded'
),
(
  md5('seed:memory_cards_wave2final:project_l2_bpt_sl_structural.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_sl_structural',
  'L2/BPT SL estrutural trade-a-trade (exit fixo partial50): swing-origin (=SL_STRUCTURE_LOW visual) recupera bad_SL 5→10/12 e melhora streak/2020-22, MAS 35% dos trades >4ATR (máx 15ATR) = inviável prop-firm sem cap; na base 276 não bate baseline em R (dentro do ruído); SL não é onde mora a edge.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_sl_structural.md',
  'superseded'
),
(
  md5('seed:memory_cards_wave2final:feedback_cadence.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_cadence',
  'O usuário trabalha por etapas, ativo por ativo, sem antecipação. Mesmo que eu tenha o panorama completo, devo entregar em camadas.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_cadence.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:feedback_memory_methodology.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_memory_methodology',
  'Protocolo obrigatório de salvamento de memória por sessão. Gatilhos, tipos, formato, checklist de fim-de-sessão.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_memory_methodology.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:feedback_partnership.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_partnership',
  'Como o usuário quer trabalhar comigo — assistente colaborativo, não ferramenta automatizadora. Evolução gradual, sem sobrecarga.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_partnership.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:feedback_session_persistence.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_session_persistence',
  'Ao final de cada sessão (ou quando algo essencial for resolvido), gravar em memória para garantir continuidade entre conversas.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_session_persistence.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:feedback_statistical_patience.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_statistical_patience',
  'Princípio metodológico fundamental: amostras pequenas são direcionais, não verediticais. Não desistir cedo de estratégias/módulos.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_statistical_patience.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:feedback_trades_in_chat.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_trades_in_chat',
  'Trades, listas de tópicos pendentes, listas operacionais — sempre entregar no chat em formato lista. Nunca remeter para arquivo MD.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_trades_in_chat.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:project_d2r_state.md')::uuid,
  'private', 'private', 'project',
  'project_d2r_state',
  'Estado do backfill D2R (R-multiple post-hoc evaluation). Phase 1+2 completas em 2026-05-13. Asset×direction matrix consolidada.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_d2r_state.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:project_execution_context.md')::uuid,
  'private', 'private', 'project',
  'project_execution_context',
  'Conta simulada $100k USD; nenhum trade real executado. Todos "trades" são alertas/sinais. Sistema em fase de implementação e testes.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_execution_context.md',
  'active'
),
(
  md5('seed:memory_cards_wave2final:project_external_factors.md')::uuid,
  'private', 'private', 'project',
  'project_external_factors',
  'Sistema de enriquecimento macro/calendar/rates/funding em modo passive logging. Infra OK, receiver fix aplicado, aguarda 50+ alertas v1.2 antes de validação contra outcomes.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_external_factors.md',
  'superseded'
),
(
  md5('seed:memory_cards_wave2final:project_naming_proposal.md')::uuid,
  'private', 'private', 'project',
  'project_naming_proposal',
  'Proposta de renomear classificações para refletir o discriminador REAL de edge (entry_model), não escala fuzzy de confiança. Aguardando validação manual com Leonardo antes de implementar.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_naming_proposal.md',
  'unknown_review'
),
(
  md5('seed:memory_cards_wave2final:project_operational_decisions.md')::uuid,
  'private', 'private', 'project',
  'project_operational_decisions',
  'Decisões operacionais aprovadas em 2026-05-13 e implementadas em strategy_rules.json + claude_recheck.py + launchd. Status do que está ativo no sistema HOJE.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_operational_decisions.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:project_oracle_score.md')::uuid,
  'private', 'private', 'project',
  'project_oracle_score',
  'DEACTIVATED 2026-05-21 — frente morta no cleanup. 3 abordagens testadas e falharam. Achado top isolado (confirmation_close+sweep=FALSE n=15) documentado. Retomar se n_jewels >= 100',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_oracle_score.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2final:project_pending_work.md')::uuid,
  'private', 'private', 'project',
  'project_pending_work',
  'Lista priorizada de tópicos pendentes. Atualizada 2026-05-14 após PR 4 e Fase 3 da renomeação. NÃO emergir sem que usuário traga.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_pending_work.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:project_xau_losing_patterns.md')::uuid,
  'private', 'private', 'project',
  'project_xau_losing_patterns',
  'Padrões concretos extraídos dos 7 trades XAU 0/7 (depois reabsorvido com n maior, mas padrões operacionais permanecem válidos).',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_losing_patterns.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:reference_d2r_mechanics.md')::uuid,
  'private', 'private', 'reference',
  'reference_d2r_mechanics',
  'Sequência detalhada de como evaluate_r_outcomes.py computa R-multiple post-hoc. Útil quando usuário pergunta "como o D2R mede isso?" ou ao depurar discrepâncias entre alerta e outcome.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_d2r_mechanics.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2final:reference_files.md')::uuid,
  'private', 'private', 'reference',
  'reference_files',
  'Onde vivem os principais artefatos do sistema. Usar para navegação rápida em futuras sessões.',
  array['seed:memory_cards_wave2final','wave:2FINAL','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_files.md',
  'unknown_review'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- ROLLBACK (NAO EXECUTAR JUNTO — so em DEV, manual, sob autorizacao)
-- ============================================================================
-- begin;
-- delete from memory_items where 'seed:memory_cards_wave2final' = any(tags);
-- commit;
-- ============================================================================
