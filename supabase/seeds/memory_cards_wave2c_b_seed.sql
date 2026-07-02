-- ============================================================================
-- SUPABASE MEMORY — CARDS WAVE 2C-b (sub-batch 2) · seed:memory_cards_wave2c_b
-- gerado por scripts/memory/generate_wave2c_b_seed.py
-- ============================================================================
-- Review: docs/architecture/SUPABASE_MEMORY_WAVE2C_B_REVIEW_20260702.md
-- 50 project historicos -> memory_items (archive/index, nao hot memory).
-- body = frontmatter description (resumo curado); conteudo integral permanece
--   no card local (source_ref). Zero RAW, zero edge detalhado, zero secrets.
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV). MCP permanece read-only.
--   Pos-Run, verificar no proprio SQL Editor:
--   SELECT count(*) FROM memory_items WHERE tags @> ARRAY['seed:memory_cards_wave2c_b'];  -- esperado 50
-- IDEMPOTENTE: md5-uuid deterministico + ON CONFLICT (id) DO NOTHING.
-- Copiar SEMPRE do ficheiro/raw (nunca de render de chat — corrompe aspas).
-- ============================================================================

begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_bearleg_refined_approved.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_bearleg_refined_approved',
  'Feature APROVADA por Cris — bear-leg refined loser-cut (bloqueia bear-pullback-trap, preserva runners/monumentais); vitória de corte de 8 losers limpos, com limitações implícitas reconhecidas (irredutibilidade do resíduo)',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_bearleg_refined_approved.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_convergence_elimination_signal_2026_06_24.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_convergence_elimination_signal_2026_06_24',
  'Leitura convergente NÃO seleciona runner, MAS sinal ASSIMÉTRICO de ELIMINAÇÃO (baixa-convergência/BEAR ⇒ não-runner, corta 0 runners) — fio vivo p/ skip-seguro→streak/winrate',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_convergence_elimination_signal_2026_06_24.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_dynamic_structural_path_aggregator.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_dynamic_structural_path_aggregator',
  'DSPA — novo engine AGREGADOR de 2ª ordem acoplado ao Macro Structural Reading Engine (NÃO sucessor); lê TRAJETÓRIA 4H/1D que produziu o estado, não snapshot na barra de entrada; resolve mislabels preservando monumentais',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_dynamic_structural_path_aggregator.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_episode_reading_276_library.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_episode_reading_276_library',
  'L2/BPT — biblioteca de 276 leituras VIVAS (Episode Reading block) executada + auditada; leitura forte em EVITAR (trap/skip), fraca em CAPTURAR (legitimate-buy); 5 monumentais skipados p/ plotar antes de Managed Agents',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_episode_reading_276_library.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_exit_lab_regime_bound.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_exit_lab_regime_bound',
  'Exit lab L2/BPT (R/BE/parcial/trail sobre SL estrutural fixo): nenhuma política bate baseline +3R fora do ruído. Teste decisivo revelou edge NÃO-ESTACIONÁRIO — build 2020-22 chato (avgR +0.02), holdout 2023-26 carrega tudo (+0.39); 13/15 monumentais no build. Exit = ruído; lever real = regime.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_exit_lab_regime_bound.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_feature_clean_sky_room_above.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_feature_clean_sky_room_above',
  'FEATURE CANDIDATA PRÉ-APROVADA (Cris) — clean_sky / room-above (distância à oferta overhead) = qualidade do piso (espaço pra correr); testar nos 276 com medição correta',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_feature_clean_sky_room_above.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_feature_conv_le1_skip.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_feature_conv_le1_skip',
  'FEATURE CANDIDATA (não aprovada) — conv≤1 skip por baixa-convergência; regime-dominante, não-redundante; MÉTRICAS A RE-MEDIR com exit V_stair + SL estrutural antes de qualquer aprovação',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_feature_conv_le1_skip.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_lineB_bottom_add_rescue.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_lineB_bottom_add_rescue',
  'RESCUE_MAP (NÃO promove estratégia nova; bottom-add layer NÃO construído/NÃO aprovado): resgate dos aprendizados do Caminho B p/ a LINHA B do L2/BPT. DURÁVEL vs SLIM-contaminado mapeado. Itens já-aprovados referenciados carregam sua própria auditoria.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_lineB_bottom_add_rescue.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_lineB_bull_absorb_preapproved.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_lineB_bull_absorb_preapproved',
  'Linha B — ESTRATÉGIA PRÉ-APROVADA (Cris 2026-06-25): base BULL pullback + filtro absorb (bubble SELL). PRE_APPROVED_PENDING_VALIDATION — NÃO oficial; lookahead-audit + jackknife/cap PENDENTES; DA sinalizou beta.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_lineB_bull_absorb_preapproved.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_overfade_irreducible_at_entry_2026_06_23.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_overfade_irreducible_at_entry_2026_06_23',
  '2a rodada direcionada (multi-papel Reader/Challenger/Judge + VA real) CONFIRMOU empiricamente: o over-fade de continuação/runners NÃO se resolve por leitura no ENTRY; value-migration-phase e floor-backed-triad ambos REFUTED (invertem contra outcome). Separador runner-vs-stop NÃO existe nas features de entry.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_overfade_irreducible_at_entry_2026_06_23.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_rabbithole_audit.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_rabbithole_audit',
  'Auditoria completa do processo L2/BPT (7 agentes, corpus inteiro) — a premissa \"selecionar entre entradas\" é falsa porque a entrada não tem edge e os losers são auction-irredutíveis; programa inteiro estava otimizando seletor sobre substrato inselecionável',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_rabbithole_audit.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_raw_backbone_rebuild_2026_06_23.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_raw_backbone_rebuild_2026_06_23',
  'Reader Vivo L2/BPT — débito baseline da Camada-1 ELIMINADO: backbone (sup_cat/clean_sky/dist_supply/dist_demand) reconstruído do RAW Custom OB; gate v2 com input manifest; clusters 1/2 refeitos RAW-clean; SVP=UNKNOWN_BLOCKED honesto',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_raw_backbone_rebuild_2026_06_23.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_svp_acceptance_raw_2026_06_23.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_svp_acceptance_raw_2026_06_23',
  'SVP/acceptance ao RAW: VA de VOLUME LuxAlgo (POC/VAL/VAH) NÃO reconstruível do RAW (nunca serializado) → BLOCKED honesto; mas volume real por-barra (RAW) + TPO value-area (tempo, derivado) resolvem PARCIALMENTE FUEL-vs-WALL (ACCEPTED_ABOVE_VALUE→FUEL 3/3)',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_svp_acceptance_raw_2026_06_23.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_l2_bpt_telegram_bear_flags_FUTURE.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_telegram_bear_flags_FUTURE',
  'FUTURO (não operacionalizar agora, não mexer produção): adicionar flags legbear-ativo + overbought aos sinais de Telegram do L2/BPT pra Cris VETAR manualmente losers de bear-market por decisão humana, sem perder monumentais (humano é o juiz que mantém as reversões-de-fundo).',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_telegram_bear_flags_FUTURE.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_bb_nas_leonardo_kickoff.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_bb_nas_leonardo_kickoff',
  'KICKOFF XAU 15M BigBeluga+NAS (Leonardo) — tese da estratégia, discriminadores winner/loser dos 5 PDFs lidos página a página, inventário do que já existe no repo, GATE de proveniência BigBeluga, e plano passo-a-passo sob Auction Theory. Próxima frente após XAU 4H LONG finalizada.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_bb_nas_leonardo_kickoff.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_bottom_power_engine.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_bottom_power_engine',
  'XAU 15M LONG BOTTOM — engine multi-agente de potência de fundo. Achado POSITIVO (raro): potência de fundo É causalmente separável, eixo NOVO (não beta-de-bull). Base p/ a 2ª estratégia.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_bottom_power_engine.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_bubbles_nas_clusters.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_bubbles_nas_clusters',
  'Frente XAU 15M — leitura CONTEXTUAL de clusters de Bubbles + clusters de NAS p/ seleção de entrada em reversão (BUY em bubble-SELL-cluster+NAS-LONG no fundo / SELL em bubble-BUY-cluster+NAS-SHORT no topo). Inclui ground-truth de fundos/topos verdadeiros (zigzag ATR) + estrutura RAW das bubbles.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_bubbles_nas_clusters.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_engine_learnings.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_engine_learnings',
  'Registro dos APRENDIZADOS (rodadas/teorias que NÃO atingiram a meta) da engine multi-agente XAU 15M — caminhos criados/executados, p/ relatório geral. Cada entrada = teoria, resultado honesto, por que falhou, o que ensina.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_engine_learnings.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_managed_agents_engine.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_managed_agents_engine',
  'Engine multi-agente (Workflow) para XAU 15M — descoberta criativa de features/ângulos + crivo adversarial estrutural + leitura convergente dos prints, com padrão de validação RECALIBRADO (robustez estrutural across sub-janelas, não significância estatística). Cris liberou total (Claude 20x, sem limite de custo/tokens), free para criar.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_managed_agents_engine.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_range_t2_t3_study.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_range_t2_t3_study',
  'XAU 15M — estudo a fundo T2 (anti-topo-range) + T3 (capturar fundos de range) sobre a base SWEPT, só RANGE (BULL intacto). RANGE é regime fraco; nem subtrair (T2) nem adicionar (T3) bate BASE_SW r/DD18,31. Fundo-profundo rpos≤0,34 é a única bolsa boa, rara/não-fabricável.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_range_t2_t3_study.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_reversal_power.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_reversal_power',
  'XAU 15M — lab de POTÊNCIA das 414 reversões M8 (força da perna lançada por cada fundo/topo) + classificação por camadas. Caracterização (gabarito forward), NÃO feature causal. DA-auditado.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_reversal_power.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_session_patterns.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_session_patterns',
  'Dados/ensinamentos do levantamento por SESSÃO/HORA no XAU 15M (síntese válida, Cris). Referem-se ao SETUP 2 (reversão-exaustão / família sweep). Guardar p/ testar nos demais setups mais adiante.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_session_patterns.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_sl_exit_entry_lab.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_sl_exit_entry_lab',
  'XAU 15M — lab SL/exit/entry sobre os 170 (5ATR A2 + h1_eff + regime). Ground-truth do Cris no chart; regra causal de exit buscada. Achado robusto = runners do Cris NÃO são causalmente reproduzíveis.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_sl_exit_entry_lab.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_15m_transversal_monforte_entry.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_transversal_monforte_entry',
  'XAU 15M — NOVA frente (plano): engine TRANSVERSAL que estuda só os ~58 fundos MONSTER+FORTE p/ achar ponto de entrada EXCLUSIVO a eles (mecânica de entrada por episódio, não grid sobre universo ruidoso).',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_transversal_monforte_entry.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_4h_backtest_v1.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_backtest_v1',
  'Primeiro backtest XAU 4H via replay (540 bars, ~4 meses) descobriu 1 signal SÓLIDO + 20+ PRELIMINAR + tese empírica confirmada',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_backtest_v1.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_4h_breakout_d1a_maturation.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_breakout_d1a_maturation',
  'BREAKOUT/D1a é alto-potencial mas imaturo; entrada no rompimento é ingênua; losers são entradas em topos (ótimos SHORTs por inversão); re-arquitetar entrada via retrace a zona de demanda',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_breakout_d1a_maturation.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_4h_long_FINAL_l1_l2_approved.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_long_FINAL_l1_l2_approved',
  'CAPSTONE — XAU 4H LONG FINALIZADA (2026-06-25). Duas estratégias ortogonais APROVADAS por Cris p/ produção futura: L1 EMA21 Continuation (bull pullback) + L2/BPT (BOS/CHoCH bottom). Construção encerrada; próximo horizonte = 15M.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_long_FINAL_l1_l2_approved.md',
  'active'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_4h_reversal_capitulation_long.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_reversal_capitulation_long',
  '2026-05-20 SEGUNDA estratégia validada XAU 4H — REVERSAL LONG em capitulação de volatilidade. 83.7% win, 86 trades, 25/ano',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_reversal_capitulation_long.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_4h_reversal_discr_v1_base_sweep.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_reversal_discr_v1_base_sweep',
  'Snapshot congelado 2026-05-21 — REVERSAL_DISCRETIONARY_LONG V1 (BASE+SWEEP) antes da migração para V2 deferred entry; referência de comparação',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_reversal_discr_v1_base_sweep.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_4h_reversal_discretionary_long.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_reversal_discretionary_long',
  '2026-05-21 FINAL V3d (pragmático) — V1 BASE+SWEEP como sinalizadores Telegram, Cris desenha OB manualmente e decide entrada visualmente; V2 e V3a falharam (detectores OB existentes são micro, Cris pensa macro)',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_reversal_discretionary_long.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_4h_reversal_v1_4g_rws_a6.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_reversal_v1_4g_rws_a6',
  'V1.4g-RWS-A6 official XAU 4H REVERSAL_LONG strategy — FundedNext rigoroso (streak 4, DD 4.4R, WR 65.4%), preserva 100% monumentais ≥5R/≥10R, validado walk-forward 3/3',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_reversal_v1_4g_rws_a6.md',
  'superseded'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_4h_reversal_v1_4j.md')::uuid,
  'private', 'private', 'project',
  'project_xau_4h_reversal_v1_4j',
  'V1.4j official XAU 4H REVERSAL_LONG strategy — FundedNext-compliant with weekly regime gate, atende WR ≥50% + streak ≤5 + Calmar 22.79 walk-forward 3/3',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_reversal_v1_4j.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_zone_touch_smc_module.md')::uuid,
  'private', 'private', 'project',
  'project_zone_touch_smc_module',
  '2026-05-15 — módulo ZONE_TOUCH_SMC_CONVERGENT_LONG_INTERIM criado para resolver zero SETUP_VALIDO histórico. Caminho B (zone-touch) com 4+ confluências.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_zone_touch_smc_module.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_xau_1h_demand_reclaim_reentry_long_v1.md')::uuid,
  'private', 'private', 'project',
  'project_xau_1h_demand_reclaim_reentry_long_v1',
  'Hipótese oficial XAU_1H_DEMAND_RECLAIM_REENTRY_LONG v1.1 — duas vias paralelas (L4 capitulação aguda + Secondary v2 bottom NAS+RSI+demand+drop_20_filter), maturidade, BE@2R. 51 trades, +62R fix_5R, +34R dyn, hit_20R preservado, trade monumental evt14 +69R MFE.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_1h_demand_reclaim_reentry_long_v1.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_l1_refinement_approved_2026_06_16.md')::uuid,
  'private', 'private', 'project',
  'project_l1_refinement_approved_2026_06_16',
  'L1 EMA21 Continuation — refinamento aprovado (anti-extensão + NAS SHIFT1 + SL estrutural max(zona,swing6))',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l1_refinement_approved_2026_06_16.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_bubble_gate_relaxed_by_tf.md')::uuid,
  'private', 'private', 'project',
  'project_bubble_gate_relaxed_by_tf',
  '2026-05-15 — BUBBLE CLUSTER GATE relaxado por TF. Obrigatório em 15M/30M, opcional em 1H/4H/12H/1D. Decisão baseada em auditoria n=557 records.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_bubble_gate_relaxed_by_tf.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_bubble_sell_regime_dependent.md')::uuid,
  'private', 'private', 'project',
  'project_bubble_sell_regime_dependent',
  '2026-05-20 Bubble Sell em zona OB durante uptrend forte PIORA setup LONG (não ajuda); validar em outros regimes (range/pós-correção) onde a tese de absorção pode funcionar',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_bubble_sell_regime_dependent.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_cf_vs_obs_v2.md')::uuid,
  'private', 'private', 'project',
  'project_cf_vs_obs_v2',
  '2026-05-15 — Regra 5 reformulada. Inversão CF vs OBS é LOCAL (TF 1H SHORT, XAU SHORT marginal), não universal. Default agora promove CF.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_cf_vs_obs_v2.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_mtf_gate_audit.md')::uuid,
  'private', 'private', 'project',
  'project_mtf_gate_audit',
  'MTF gate (BOS/CHOCH HTF lookback 6) audit em 4 módulos reais. 3 ADOPT FORTE (XAU 4H, EUR 4H, EUR 1H). Implementado em shadow mode 2026-05-15.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_mtf_gate_audit.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_alerts_dataset_full.md')::uuid,
  'private', 'private', 'project',
  'project_alerts_dataset_full',
  'Inventário completo dos 314 alerts ativos no servidor TV 2026-05-18 — Pines mecânicos + 4 indicators principais alarmados pra coleta passiva (indicator_signals.jsonl)',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_alerts_dataset_full.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_autonomous_execution_plan.md')::uuid,
  'private', 'private', 'project',
  'project_autonomous_execution_plan',
  '🤖 Plano operacional XAU 4H LONG suite — 6 Blocos autônomos multi-dias (foundations cleanup → A1'' v2 → A1 BALANCE v2 → 6 novas lógicas → regime mapping → integration + SHORT bonus). Pré-registro TRAIN/VAL/TEST, Bonferroni, Wilson, DA spawn, leitura prints. ~12-15h estimado.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_autonomous_execution_plan.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_cdp_chart_lock.md')::uuid,
  'private', 'private', 'project',
  'project_cdp_chart_lock',
  'Race condition entre claude_recheck subprocess concorrentes resolvido via flock em /tmp/tradingview_chart.lock. Implementado 2026-05-14 commit 8830f54.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_cdp_chart_lock.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_creative_strategy_engine_managed_agents.md')::uuid,
  'private', 'private', 'project',
  'project_creative_strategy_engine_managed_agents',
  'Direção futura — engine CRIATIVO de estratégias via orquestração multi-agente (Managed Agents/Workflow), plugado na governança existente. Retomar mais adiante.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_creative_strategy_engine_managed_agents.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_d2r_indicator_appendix.md')::uuid,
  'private', 'private', 'project',
  'project_d2r_indicator_appendix',
  'auto_d2r_daily.py expandido com CLASSIFICATIONS legacy + appendix indicator outcomes no Telegram daily',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_d2r_indicator_appendix.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_enrich_outcomes_v2_multi_lens.md')::uuid,
  'private', 'private', 'project',
  'project_enrich_outcomes_v2_multi_lens',
  'enrich_indicator_outcomes.py mede outcomes em 4 lentes (B+C+D+E) desde 2026-05-19; legacy long/short_outcome preservado',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_enrich_outcomes_v2_multi_lens.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_forward_outcome_layer_spec.md')::uuid,
  'private', 'private', 'project',
  'project_forward_outcome_layer_spec',
  'Forward Outcome Layer designed (spec-only, substitui conceito D2R) — status e ponteiro repo',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_forward_outcome_layer_spec.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_hard_blocks_mechanical_subset.md')::uuid,
  'private', 'private', 'project',
  'project_hard_blocks_mechanical_subset',
  'Pines mecânicos (Caminho A) usam subset de 4 hard blocks (não os 8 da régua clássica); FALLING_KNIFE removido por conflitar com BREAKOUT',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_hard_blocks_mechanical_subset.md',
  'dormant'
),
(
  md5('seed:memory_cards_wave2c_b:project_hard_blocks_refactor.md')::uuid,
  'private', 'private', 'project',
  'project_hard_blocks_refactor',
  '2026-05-15 — refatoração hard blocks. Enum fixo, NO_TRADE reason estruturado, MACRO_RED dormente, removidos fantasmas. Prepara D2R Phase 3.',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_hard_blocks_refactor.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_indicator_signals_dedup_bug.md')::uuid,
  'private', 'private', 'project',
  'project_indicator_signals_dedup_bug',
  '2026-05-22/23 BUG CRÍTICO descoberto e fixado — dedup hash sem ts_signal causou 88.8% perda de dados em 5 dias; templates JSON corrigidos + Pine v12 criado + 25 Custom OB recriados; aguarda Cris recriar/editar 289 outros alertas',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_indicator_signals_dedup_bug.md',
  'archived'
),
(
  md5('seed:memory_cards_wave2c_b:project_pine_slot_duplicate_bug.md')::uuid,
  'private', 'private', 'project',
  'project_pine_slot_duplicate_bug',
  '2026-05-17 — slot duplicado XAU 4H BREAKOUT_CONTINUATION RESOLVIDO 2026-05-23 (Cris deletou slot antigo)',
  array['seed:memory_cards_wave2c_b','wave:2C-b','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_pine_slot_duplicate_bug.md',
  'archived'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- ROLLBACK (NAO EXECUTAR JUNTO — so em DEV, manual, sob autorizacao)
-- ============================================================================
-- begin;
-- delete from memory_items where 'seed:memory_cards_wave2c_b' = any(tags);
-- commit;
-- ============================================================================
