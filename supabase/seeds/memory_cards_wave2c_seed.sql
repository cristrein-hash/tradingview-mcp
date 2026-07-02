-- ============================================================================
-- SUPABASE MEMORY — CARDS WAVE 2C (sub-batch 1) · seed:memory_cards_wave2c
-- gerado por scripts/memory/generate_wave2c_seed.py
-- ============================================================================
-- Review: docs/architecture/SUPABASE_MEMORY_WAVE2C_REVIEW_20260702.md
-- 50 memory cards historicos/reference -> memory_items (archive/index).
-- body = frontmatter description (resumo curado); conteudo integral permanece
--   no card local (source_ref). Zero RAW, zero edge detalhado, zero secrets.
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV). MCP permanece read-only.
-- IDEMPOTENTE: md5-uuid deterministico + ON CONFLICT (id) DO NOTHING.
-- Copiar SEMPRE do ficheiro/raw (nunca de render de chat — corrompe aspas).
-- ============================================================================

begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_cards_wave2c:reference_bubbles_auction_theory.md')::uuid,
  'private', 'private', 'reference',
  'reference_bubbles_auction_theory',
  'Correct interpretation of Market Order Bubbles (Leviathan) via Auction Theory — bottoms have Bubbles SELL not BUY',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_bubbles_auction_theory.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_cdp_wedged_diagnosis.md')::uuid,
  'product', 'internal', 'reference',
  'reference_cdp_wedged_diagnosis',
  'How to diagnose a hung tv_health_check / MCP — wedged TradingView CDP command channel vs code timeout bug',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_cdp_wedged_diagnosis.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_cloudflared_tunnel.md')::uuid,
  'private', 'private', 'reference',
  'reference_cloudflared_tunnel',
  'Ingestão externa de alertas TradingView depende do cloudflared tunnel; agora supervisionado por LaunchAgent',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_cloudflared_tunnel.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_d2r_daily_logs.md')::uuid,
  'private', 'private', 'reference',
  'reference_d2r_daily_logs',
  'auto_d2r_daily.py NÃO escreve em stdout/stderr do launchd — logs reais ficam em alert-bridge/logs/d2r_daily/auto_d2r_YYYY-MM-DD.log',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_d2r_daily_logs.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:reference_hardware.md')::uuid,
  'private', 'private', 'reference',
  'reference_hardware',
  'Cris opera em MacBook Air 8GB RAM / M2 / 8 cores — limita decisões de arquitetura (paralelismo, multi-tab)',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_hardware.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_imac_bridge.md')::uuid,
  'private', 'private', 'reference',
  'reference_imac_bridge',
  'Endpoints HTTP da bridge iMac→MacBook que fornece external factors v1.2 antes de cada Claude recheck.',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_imac_bridge.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_L2_SMC_definitions_canonicas.md')::uuid,
  'private', 'private', 'reference',
  'reference_L2_SMC_definitions_canonicas',
  '🔬 Referência canônica das definições SMC operacionais para L2 v2 (Breakout polaridade reclaim). Estabelecida 2026-06-06 com Cris. Inclui: Pivot Williams 5/5 SHIFT5, Protected LH causal (não max), CHoCH com buffer 0.2 ATR, BOS obrigatório, polaridade CHoCH fixa, reclaim verde forte 0.1 ATR, invalidação por close abaixo de swing low estrutural.',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_L2_SMC_definitions_canonicas.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_long_position_overrides_ticks_bug.md')::uuid,
  'product', 'internal', 'reference',
  'reference_long_position_overrides_ticks_bug',
  'draw_shape long_position interpreta overrides stopLevel/profitLevel como TICKS de offset do entry, não preço absoluto — plots com preço absoluto saem errados',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_long_position_overrides_ticks_bug.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_market_microstructure_explained_leonardo.md')::uuid,
  'private', 'private', 'reference',
  'reference_market_microstructure_explained_leonardo',
  'Versão didática aprofundada dos fundamentos filosóficos do sistema (AMT + Order Flow + Bubbles Leviathan) para Leonardo entender por que as confluências funcionam; usar quando precisar explicar o sistema a alguém com background trading mas que precisa compreensão completa',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_market_microstructure_explained_leonardo.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_market_microstructure_philosophy.md')::uuid,
  'private', 'private', 'reference',
  'reference_market_microstructure_philosophy',
  'Base filosófica do sistema (Auction Market Theory + Order Flow Principles + Market Order Bubbles Leviathan); fundamenta por que achados do backtest XAU 4H funcionam',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_market_microstructure_philosophy.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_mcp_ohlcv_time_range.md')::uuid,
  'product', 'internal', 'reference',
  'reference_mcp_ohlcv_time_range',
  'data_get_ohlcv aceita from_time/to_time (unix epoch sec) para paginar OHLCV histórico. Adicionado 2026-06-04. Requer scroll manual no chart até a data desejada antes.',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_mcp_ohlcv_time_range.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_SMC_Unified_Rebuild_v0_preregistro.md')::uuid,
  'private', 'private', 'reference',
  'reference_SMC_Unified_Rebuild_v0_preregistro',
  '🔒 Pré-registro LOCKADO SMC Unified Rebuild v0 (2026-06-07). State-machine 5 estados com S4 como overlay/block, RSI granular 3 níveis, PF canônico, S3 SMC-only (não MA), exit v0 diagnóstico, período 2020-01 → 2025-12. Substitui filosofia ''L2/L2.5/L3 separados'' por estratégia SMC unificada com estados internos. Read-only /tmp/, sem produção, sem promoção. Pendente: implementação após autorização.',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_SMC_Unified_Rebuild_v0_preregistro.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_svp_value_area_provenance.md')::uuid,
  'private', 'private', 'reference',
  'reference_svp_value_area_provenance',
  'SVP value-area (POC/VAH/VAL) JÁ EXISTE no RAW e JÁ foi extraída+validada: session_vp.last3[i].v=[t,POC,VAH,VAL] → extract_svp.py → repro_recovery/svp_bars.jsonl → DSPA F6 (dist_poc/above_value/below_value), validada causal commit 7f3c852. NUNCA re-derivar, NUNCA chamar de blocked.',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_svp_value_area_provenance.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_system_leigo_map.md')::uuid,
  'private', 'private', 'reference',
  'reference_system_leigo_map',
  'Mapa do sistema em linguagem leiga (metáforas vigias/carteiros/contadores/cadernetas) — usar para explicar arquitetura a Cris, Leonardo, ou qualquer pessoa não-técnica',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_system_leigo_map.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_trade_plotting_canonical.md')::uuid,
  'private', 'private', 'reference',
  'reference_trade_plotting_canonical',
  'Formato canônico para plotar trades como Long Position nativa do TradingView. A referência viva está em alert-bridge/draw_xau_4h_trades.py — usar este formato sempre, NUNCA inventar overrides.',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_trade_plotting_canonical.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_xau_4h_backtest_resumo_leonardo.md')::uuid,
  'private', 'private', 'reference',
  'reference_xau_4h_backtest_resumo_leonardo',
  'Resumo formatado do backtest XAU 4H (540 bars, 2026-05-19) em linguagem técnica acessível para Leonardo — usar como template para próximos resumos de backtest',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_xau_4h_backtest_resumo_leonardo.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:reference_xau_4h_prints_archive.md')::uuid,
  'private', 'private', 'reference',
  'reference_xau_4h_prints_archive',
  'Mapa do arquivo visual de prints XAU 4H — qual estratégia está plotada em cada pasta + anotações do Cris',
  array['seed:memory_cards_wave2c','wave:2C','type:reference'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/reference_xau_4h_prints_archive.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_v3_A1_BALANCE_OFICIAL.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_v3_A1_BALANCE_OFICIAL',
  '🔴 INVALIDADA 2026-06-06 — A1 BALANCE OFICIAL confirmada com look-ahead em outcome. Audit empírico (/tmp/audit_A1_BALANCE_lookahead.py): ORIG (anchor by trigger) WR 68% / sumR +122.6R; POST+SHIFT1 (clean) WR 18% / sumR +12R / streak 9. Δ −110.6R (−90% do edge era artefato). Bug raiz: anchor bsw em winners B v1.5 usa ts_epoch do TRIGGER (outcome só conhecido após exit 50-200 bars depois). Mesma classe estrutural do A1'' SUPERTREND v1. lookahead-audited: 2026-06-06 INVALIDATED.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_v3_A1_BALANCE_OFICIAL.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_v3_A1_PRIME_SUPERTREND_OFICIAL.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_v3_A1_PRIME_SUPERTREND_OFICIAL',
  '🔴 INVALIDADO 2026-06-06 — A1'' SUPERTREND v1 estava com look-ahead bias. Versão limpa (SHIFT1): WR 46% / sumR +20R / DD -11R (vs 88%/+75R/-1R contaminado). Memory mantida só como referência histórica do erro.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_v3_A1_PRIME_SUPERTREND_OFICIAL.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_v3_PR50n_pullback_reclaim.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_v3_PR50n_pullback_reclaim',
  '🔴 PR50n (Pullback-Reclaim SMA50 next-bar) — Caminho A v3 continuation. Lógica visual: B v1.6 captura fundo → próximas semanas, comprar quando preço fura SMA50 e bar seguinte fecha verde acima. REFUTADO 2026-06-06 sob checklist 15 problemas (9/15 PASS, falhas críticas #4 multi-testing, #8 anchor info futura, #10 slippage, #11 correlação cluster, #15 best-of-grid). Wilson lower 39% < gate 45%. Fora de escopo (target +3R fixo incapaz de mons). Lógica preservada pra referência futura. lookahead-audited: 2026-06-06-REFUTADO.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_v3_PR50n_pullback_reclaim.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_xau_15m_direction_short_mirror_refuted.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_direction_short_mirror_refuted',
  'XAU 15M — espelho SHORT simétrico REFUTADO; correção dos longs-em-topo = FILTRAR, não inverter; engine de filtro long em curso',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_direction_short_mirror_refuted.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_xau_15m_macro_bottom_refuted.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_macro_bottom_refuted',
  'XAU 15M — corrigido erro de frame (micro-Donchian 1d ≠ range macro). Comprar o FUNDO-MACRO do range (golden zone do Cris) NÃO é produtivo em nenhum frame (episódio nem Donchian-5d), com/sem HTF. Money vem da continuação na metade de cima.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_macro_bottom_refuted.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_xau_15m_window_cleaning_refuted.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_window_cleaning_refuted',
  'XAU 15M — refino da base de entradas (janela ago2025→jan2026) por limpeza SUBTRATIVA (T1 de-interpola clusters + T2 anti-topo-range) REFUTADO; reconfirma parede de seleção-no-entry. Runner é entrada tardia do cluster, não a primeira.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_window_cleaning_refuted.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_xau_15m_entry_engine2.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_entry_engine2',
  'XAU 15M Engine 2 — entrada causal nos fundos MON+FORTE. REFUTADO no R (label separa, mas não paga). Mecanismo claro; lever real = exit/gestão no universo-todo, não seleção de entrada.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_entry_engine2.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_l2_bpt_legbear_block.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_legbear_block',
  'RETRATADO — o bloqueio legbear parecia ótimo nos 41 rótulos curados (6/9 cortado, 9/9 winners) mas NÃO validou na base completa: bloqueia 5/9 winners, REDUZ sumR, pior no held-out 2023-26. Era circular (set continha os winners-alvo).',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_legbear_block.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_l2_bpt_volume_1dbear_confluence.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_volume_1dbear_confluence',
  'RETRATADO — o gate volume×1D-bear era ARTEFATO de tick-volume; com volume REAL (Session VP) NÃO separa. E1 real_volclmx=4.88 (capitulação), não 0.78. Lição: validar com volume REAL.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_volume_1dbear_confluence.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_bubbles_nas_shadow.md')::uuid,
  'private', 'private', 'project',
  'project_bubbles_nas_shadow',
  'DEACTIVATED 2026-05-21 — frente morta no cleanup. Redundante com indicator_signals_pipeline + enrich_outcomes_v2 que já medem outcomes de Bubbles/NAS. Bubble Sell já validado anti-feature',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_bubbles_nas_shadow.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_smc_btc_audit_v3.md')::uuid,
  'private', 'private', 'project',
  'project_smc_btc_audit_v3',
  'DEACTIVATED 2026-05-21 — frente morta no cleanup. BTC fora do foco XAU-only. V3d backtest preservado: Sharpe 1.57, PF 2.04 (5.4 anos). Retomar se foco BTC abrir',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_smc_btc_audit_v3.md',
  'deprecated'
),
(
  md5('seed:memory_cards_wave2c:project_checkpoint_2026_06_14.md')::uuid,
  'private', 'private', 'project',
  'project_checkpoint_2026_06_14',
  'Checkpoint fim-de-dia 2026-06-14: onde paramos no cross-family stress test + plotagem 2 janelas; retomar amanhã sem reexplicar',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_checkpoint_2026_06_14.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_session_2026_05_21_consolidated.md')::uuid,
  'private', 'private', 'project',
  'project_session_2026_05_21_consolidated',
  'Snapshot consolidado da sessão 2026-05-21: XAU 4H operacional Caminho D Python, cleanup 3 frentes mortas, dashboard semanal, hard blocks decididos, Telegram silenciado, protocolo memory ativado',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_session_2026_05_21_consolidated.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_session_2026_05_22_23_consolidated.md')::uuid,
  'private', 'private', 'project',
  'project_session_2026_05_22_23_consolidated',
  'Snapshot consolidado das sessões 2026-05-22 e 2026-05-23: descoberta + fix do bug dedup indicator_signals (88.8% perda), Pine v12, 25 Custom OB recriados, 3 protocolos permanentes novos',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_session_2026_05_22_23_consolidated.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_sessao_autonoma_2026_06_06_resultados.md')::uuid,
  'private', 'private', 'project',
  'project_sessao_autonoma_2026_06_06_resultados',
  '📊 Sessão autônoma 2026-06-06 — Blocos 1-4.5 do plano XAU 4H LONG. Resultado: B v1.5 SHIFT1 clean confirmado; A1'' SUPERTREND v2, A1 BALANCE v2, e 6 lógicas Auction Theory TODAS REFUTADAS sob gates rigorosos. Regime mapping em 6 regimes ortogonais. Leads registrados pra próxima sessão. lookahead-audited: 2026-06-06.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_sessao_autonoma_2026_06_06_resultados.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_lookahead_audit_2026_06_06.md')::uuid,
  'private', 'private', 'project',
  'project_lookahead_audit_2026_06_06',
  '🔴 LOOK-AHEAD AUDIT 2026-06-06 — bug sistêmico: features daily/weekly consultadas em bar 4H usavam info do MESMO dia (close diário só conhecido às ~22:00 UTC). Derrubou A1'' SUPERTREND (WR 88%→46%), A1 BALANCE (suspeito), B v1.5 (delta +1%). Convenção shift1 + helpers canônicos + lista de scripts contaminados pendentes re-rodada.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_lookahead_audit_2026_06_06.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_raw_revalidation_2026_06_03.md')::uuid,
  'private', 'private', 'project',
  'project_raw_revalidation_2026_06_03',
  'Re-validação RAW de Caminho B FINAL + Caminho A V1.4g-RWS-A6-A7 em 2026-06-03 revelou que slim_features inflava artificialmente resultados; estratégias devem ser re-calibradas sobre RAW',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_raw_revalidation_2026_06_03.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_L1_roadmap_pos_eur_test.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_L1_roadmap_pos_eur_test',
  '🎯 Caminho A L1 — Roadmap de passos após teste EUR 4H. Independente do resultado EUR, os passos continuam válidos (Cris alertou: cada ativo tem personalidade própria, falha EUR não refuta XAU). Score composto, backtest amostra completa, calibração L1 v2 XAU-only seguem viáveis.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_L1_roadmap_pos_eur_test.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_L1_v1_F4F5_status_candidato_escasso.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_L1_v1_F4F5_status_candidato_escasso',
  '⭐ L1 v1 EMA21_A + F5 only — CANDIDATO ESCASSO operável na suite XAU 4H. Sem restrição de risco. CORREÇÃO 2026-06-07: F4 ≤ 7 era inerte (não cortava trades sob nenhum mapping). Métricas reais re-validadas: n=16, WR 43.8%, sumR +31.74R, big15W=1 (mon 2024-03-26 +18.2R preservado). F4 ≤ 2 stricter = hipótese candidata futura, NÃO promover. Status CANDIDATO ESCASSO mantido.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_L1_v1_F4F5_status_candidato_escasso.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_padroes_visuais_5_layers.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_padroes_visuais_5_layers',
  '🎯 Caminho A XAU 4H — 5 layers conceituais distintos + 8 padrões visuais identificados nos prints A_PLOTS_CRIS (2026-06-06). Excelente leitura de contextos variados de entradas válidas com grande potencial. Base para pré-registros futuros L1-L5. Arquitetura: 1 arquivo Python por layer, output JSONL por layer, integração no final.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_padroes_visuais_5_layers.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_pending_validations.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_pending_validations',
  'Achados do Caminho B (2026-06-04) que devem ser validados/testados quando revisarmos o Caminho A — pullback continuation em uptrend',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_pending_validations.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_v3_A1_prime_preregistro.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_v3_A1_prime_preregistro',
  'Pré-registro Caminho A v3 A1'' — versão para trend ultra-forte com trigger micro-breakout em consolidação apertada. Devil''s Advocate workflow aplicado. 2026-06-05 noite.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_v3_A1_prime_preregistro.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_a_v3_preregistro.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_a_v3_preregistro',
  'Pré-registro formal Caminho A v3 — 3 candidatas a validar em 2024 e testar em 2025-2026 LOCKED. Restart disciplinado após critica devil''s advocate. Bonferroni α/3.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_a_v3_preregistro.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_pine_alerts_v1.md')::uuid,
  'private', 'private', 'project',
  'project_pine_alerts_v1',
  '9 Pine Scripts mecânicos criados 2026-05-15/16/17 (Caminho A) — alert source nativo TV pra resolver \"zero SETUP_VALIDO emitido\"',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_pine_alerts_v1.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_fraqueza_2020_2022.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_fraqueza_2020_2022',
  'Caminho B v1 RAW DEFINITIVO tem cobertura em 2020-2022 mas edge fraca/negativa; agenda futura = detector pra reverter BE/L + considerar range/bear setup separado',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_fraqueza_2020_2022.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_hipoteses_30_grupos.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_hipoteses_30_grupos',
  'Catálogo das 30 hipóteses de refinamento de entrada para Caminho B v1 XAU 4H — geradas por 3 sub-agentes em 6 dimensões (2026-06-04). Ouro para qualquer backtest futuro e ampliação para novos ativos.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_hipoteses_30_grupos.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_raw_v1_strata_B_C.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_raw_v1_strata_B_C',
  'Caminho B RAW v1 — entrada estratificada B (cobertura) + C (alta convicção) sobre 55 fundos curados; resultado da busca exaustiva 829 regras (2026-06-04)',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_raw_v1_strata_B_C.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_score_filter_approved.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_score_filter_approved',
  'Composite Volume Score ≥1 aprovado como filtro de entrada do Caminho B XAU 4H (2026-06-05). Cruzado com V_stair exit, preserva 13/13 monumentais, +9R sumR, WR sobe 1.6pp, DD baixa 2R. Sem custo em winners.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_score_filter_approved.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_v_stair_exit_approved.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_v_stair_exit_approved',
  'V_stair — exit em degraus aprovada como feature de exit para Caminho B XAU 4H (2026-06-05). Validação backtest 124 trades, monumentais preservados, +17R sumR vs baseline, zero winners perdidos.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_v_stair_exit_approved.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_v15_AB_combined.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_v15_AB_combined',
  'Caminho B v1.5 candidato — V_stair puro + (A) time stop adaptive 200 bars em BDF + (B) BED gate ≥3 sustent 30d/15. sumR +222.7 / WR 29% / BW10 16 / streak 3 / DD -18.5R. Walk-forward 3/3 positivo. Validação visual + robustness pendentes antes de promover.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_v15_AB_combined.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_v16_composite_filter_approved.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_v16_composite_filter_approved',
  '⭐ Caminho B v1.6 — Filtro composto APROVADO 2026-06-06 (Cris): OB 1D demand thr=0.5 ATR OR ≥1 LARGE bubble plot_8 em 10 bars OR NAS_top5 LONG/BOTTOM. Aplicado sobre B v1.5 SHIFT1 preserva 13/14 mons, corta 24 BAD, sumR +238R vs +225R baseline. Escopo aprovado: 2020-início 2025. lookahead-audited: 2026-06-06.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_v16_composite_filter_approved.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_v16_vstair_v6_climax_approved.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_v16_vstair_v6_climax_approved',
  '⭐ V_stair V6 climax conditional APROVADA 2026-06-06 (Cris assume risco XAU). Trades F9 climax (size 2x) usam V_stair DELAYED (BE@+3R → +7R lock +2R → +10R lock +5R → +14R lock +8R → +18R lock +12R). Trades NÃO climax mantêm V_stair OFICIAL. sumR +282.7R vs +224.9R baseline (+57.8R), big10W 16 (+2), streak 3, DD 14R. Combinada com filtro v1.6 = B v1.6 completo. lookahead-audited: 2026-06-06.',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_v16_vstair_v6_climax_approved.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c:project_caminho_b_volume_features.md')::uuid,
  'private', 'private', 'project',
  'project_caminho_b_volume_features',
  'Features de Volume (bear-legs V1-V9 + Session VP nativo) sobre 55 fundos curados — descoberta de Tipo 1 (silent exhaustion) e Tipo 2 (climax wash) com cobertura V3 81%',
  array['seed:memory_cards_wave2c','wave:2C','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_caminho_b_volume_features.md',
  'archived'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- ROLLBACK (NAO EXECUTAR JUNTO — so em DEV, manual, sob autorizacao)
-- ============================================================================
-- begin;
-- delete from memory_items where 'seed:memory_cards_wave2c' = any(tags);
-- commit;
-- ============================================================================
