-- ============================================================================
-- SUPABASE MEMORY — CARDS WAVE 2B · seed:memory_cards_wave2b · gerado por scripts/memory/generate_wave2b_seed.py
-- ============================================================================
-- Review: docs/architecture/SUPABASE_MEMORY_WAVE2B_REVIEW_20260702.md
-- 50 memory cards -> memory_items (1 card = 1 row).
-- body = frontmatter description (resumo curado); conteudo integral permanece
--   no card local (source_ref). Zero RAW, zero edge detalhado, zero secrets.
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV). MCP permanece read-only.
-- IDEMPOTENTE: md5-uuid deterministico + ON CONFLICT (id) DO NOTHING.
-- Copiar SEMPRE do ficheiro/raw (nunca de render de chat — corrompe aspas).
-- ============================================================================

begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_cards_wave2b:feedback_anticipate_platform_constraints.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_anticipate_platform_constraints',
  'Antes de executar ação em lote (plotagem, coleta), antecipar limites da plataforma e modos de falha — verificar ANTES de agir, não depois',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_anticipate_platform_constraints.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_audit_full_list_mandatory.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_audit_full_list_mandatory',
  'Toda auditoria de trades/candidatos exige a LISTA COMPLETA; amostra só prioriza, nunca substitui',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_audit_full_list_mandatory.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_bonferroni_pedidos_disciplina.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_bonferroni_pedidos_disciplina',
  '🚨 REGRA PERMANENTE 2026-06-06 — Considerar Bonferroni de forma REALISTA em cada rodada. Pedir poucas coisas ao mesmo tempo (idealmente N ≤ 4 hipóteses por rodada de análise). Cris reconheceu que pedir muitas coisas simultâneas é um erro recorrente que sabota validade estatística.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_bonferroni_pedidos_disciplina.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_chart_cleanup_manual_cris.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_chart_cleanup_manual_cris',
  'Chart encontrado com 0 desenhos antes de plotagem = limpeza manual do Cris (rotina dele antes de cada nova plotagem), não anomalia',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_chart_cleanup_manual_cris.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_check_input_alive_before_code.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_check_input_alive_before_code',
  'Antes de propor mudança em código de produção, validar se o INPUT/canal que a mudança opera ainda está vivo no sistema atual; caso 2026-05-18 Caminho B falhou nessa validação',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_check_input_alive_before_code.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_collaboration_signals.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_collaboration_signals',
  '4 frases-gatilho que Cris usa pra forçar pausa de Claude + 3 red flags pra interromper cedo + quando ATIVAMENTE pedir Plan agent; combate à superficialidade em colaboração',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_collaboration_signals.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_communication_style.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_communication_style',
  'Cris quer respostas sintéticas e objetivas. Sem \"parceiro\". Preservar qualidade da informação mas remover detalhes técnicos esmiuçados.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_communication_style.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_convergent_contextual_vs_aggregate_stats.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_convergent_contextual_vs_aggregate_stats',
  'ERRO META RECORRENTE — colapsar problema contextual per-trade em otimização estatística agregada; o sinal real é convergência contextual ortogonal, não significância dura',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_convergent_contextual_vs_aggregate_stats.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_DA_calibrado_veto_vs_reporta.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_DA_calibrado_veto_vs_reporta',
  '🚨 REGRA PERMANENTE 2026-06-06 — Framework calibrado para DA (Devil''s Advocate): 2 categorias (VETÁVEL no pré-registro / AUDITÁVEL pós-backtest) + 3 níveis de severidade (CRÍTICO/IMPORTANTE/MENOR). Evita paralisia de análise. Aplicar em TODOS pré-registros L1-L5 e futuros.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_DA_calibrado_veto_vs_reporta.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_deep_source_reading.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_deep_source_reading',
  '2026-05-18 — antes de re-implementar lógica complexa de Pine alheio, ler o source em chunks pequenos diretamente, não delegar análise superficial a agent',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_deep_source_reading.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_defense_in_depth_ordering.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_defense_in_depth_ordering',
  'Ao limpar sistema com múltiplas frentes pendentes, ordenar de menor blast radius pra maior, terminando com defesa permanente antes de trabalho manual irreversível',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_defense_in_depth_ordering.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_defenses_dimensioned_to_signal_origin.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_defenses_dimensioned_to_signal_origin',
  'Camadas de defesa (hard blocks, gates, filtros) devem ser dimensionadas à ORIGEM do sinal — não aplicar régua genérica em sinais pré-validados',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_defenses_dimensioned_to_signal_origin.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_distance_quality_not_binary_presence.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_distance_quality_not_binary_presence',
  'Medir contexto estrutural (demand/supply/zonas) por DISTÂNCIA+QUALIDADE, não flag binária; threshold ATR apertado fabrica falso-nulo. Reconciliar contra visual antes de concluir.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_distance_quality_not_binary_presence.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_dont_conclude_from_broken_period.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_dont_conclude_from_broken_period',
  'Não tirar conclusão sobre comportamento do sistema usando dados de período em que o próprio sistema estava com bugs ativos',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_dont_conclude_from_broken_period.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_em_validacao_term.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_em_validacao_term',
  'Sempre usar \"em validação\" no lugar de \"shadow\" — Cris não tolera o termo shadow, gera confusão de entendimento',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_em_validacao_term.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_especificidade_ativo_vs_generalizacao.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_especificidade_ativo_vs_generalizacao',
  '🚨 REGRA PERMANENTE 2026-06-06 — Cada ativo tem personalidade própria. Validação genérica cross-asset pode ser falso ideal estatístico. Especificidade XAU-only/EUR-only/USOUSD-only NÃO é falta de eficiência matemática — é fruto de especificidade diferencial entre ativos. Se uma estratégia funciona em XAU mas não em EUR, isso NÃO refuta o XAU.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_especificidade_ativo_vs_generalizacao.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_estatistica_aplicada_realidade.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_estatistica_aplicada_realidade',
  '🚨 REGRA PERMANENTE 2026-06-06 — Estatística matemática (Bonferroni, Wilson lower, p-value) tem valor SÓ quando aplicada à REALIDADE visual do chart. Sem isso vira ''overfit de insegurança aplicada como regra''. SEMPRE olhar prints/chart antes de aplicar verdict matemático. Frequência baixa pode ser feature de seletividade, não bug. Cada layer tem perfil próprio — exit NÃO é uniforme entre layers.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_estatistica_aplicada_realidade.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_event_driven_failures.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_event_driven_failures',
  '2026-05-20 Alguns clusters de losses são event-driven externos (calendar), NÃO detectáveis via indicators internos; usar defesa de calendar não filtro estatístico',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_event_driven_failures.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_full_scan_after_pattern_fix.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_full_scan_after_pattern_fix',
  'Ao corrigir bug de classe (ex: f-string escape), varrer TODO o arquivo pra mesma classe — fix isolado deixa irmãos latentes',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_full_scan_after_pattern_fix.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_manual_over_token.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_manual_over_token',
  'Cris prefere fazer manualmente quando MCP é frágil/lento — não queimar tokens forçando automação',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_manual_over_token.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_memory_proactive_consultation.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_memory_proactive_consultation',
  'PROTOCOLO PERMANENTE 2026-05-21 — antes de propor solução não-trivial READ memories relevantes; NUNCA perguntar a Cris algo que está em memory; frase-gatilho dele = pausar e auditar; sucesso = Cris não precisar dizer ''está em memory''',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_memory_proactive_consultation.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_multi_window_validation.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_multi_window_validation',
  '2026-05-20 Validação de estratégia exige 5+ janelas históricas independentes; combined alto pode mascarar falha por janela',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_multi_window_validation.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_name_vs_definition_mismatch.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_name_vs_definition_mismatch',
  'Quando o usuário diz "voltar para X" ou referencia uma config nomeada (variant/preset/script), comparar os componentes que ele LISTA na mesma mensagem contra a definição INTERNA de X — se houver divergência, PARAR e confirmar antes de regenerar dados. Não tratar nomes como atalho semântico.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_name_vs_definition_mismatch.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_no_easy_paths.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_no_easy_paths',
  '2026-05-20 Não sugerir \"caminho fácil\" / conformidade quando a complexidade é real e necessária. Cris reconhece dificuldade e quer persistir até resolver',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_no_easy_paths.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_no_generalize_negative_findings.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_no_generalize_negative_findings',
  'PROTOCOLO PERMANENTE 2026-05-23 — achado negativo de um contexto (1 ativo × 1 estratégia × 1 TF) NÃO aplica a outros contextos sem teste explícito. Não recomendar remoção/desativação baseado em generalização',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_no_generalize_negative_findings.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_no_stderr_suppress_in_git.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_no_stderr_suppress_in_git',
  'Nunca usar 2>/dev/null em git add — mascara erro de path inexistente e divide commit silenciosamente',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_no_stderr_suppress_in_git.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_no_tables_in_chat.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_no_tables_in_chat',
  'PROTOCOLO PERMANENTE 2026-05-22 — NUNCA usar tabelas markdown (| col | col |) no chat; Cris não consegue copiar/colar. Sempre texto puro com bullets ou listas numeradas',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_no_tables_in_chat.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_ob_detectors_micro_vs_macro.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_ob_detectors_micro_vs_macro',
  '2026-05-21 detectores OB existentes (Custom OB v11, LuxAlgo SMC) são micro-estruturais ($15-25 altura); Cris pensa em zonas macro ($150-200) que desenha manualmente — não tentar automatizar entry em OB sem reconhecer essa diferença',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_ob_detectors_micro_vs_macro.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_outcome_proxy_lift_and_episode.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_outcome_proxy_lift_and_episode',
  'Proxy de outcome (MFE/MAE forward) deve medir LIFT sobre a taxa-base incondicional e POR EPISÓDIO (dedup serial), nunca taxa absoluta por candidato — senão mede o drift do mercado, não edge.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_outcome_proxy_lift_and_episode.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_pine_alert_no_chart_required.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_pine_alert_no_chart_required',
  '2026-05-19 — TV executa Pine em background pra alertas criados via alert(); Pine NÃO precisa ficar no chart pra disparar. WORKFLOW: cola Pine → cria alert → APAGA Pine do chart (não polui outros ativos)',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_pine_alert_no_chart_required.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_python_path_for_new_strategies.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_python_path_for_new_strategies',
  '2026-05-21 decisão DAQUI EM DIANTE — novas estratégias em Python (Caminho D), não Pine. Os 9 Pines mecânicos existentes ficam. Razão: Pine não consegue ler labels de outros indicators externos (NAS, LuxAlgo, Bubbles)',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_python_path_for_new_strategies.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_raw_data_lookup_order.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_raw_data_lookup_order',
  '🚨 REGRA PERMANENTE 2026-06-07 — Ordem obrigatória para verificar disponibilidade de dados RAW de qualquer símbolo/timeframe. NUNCA concluir ausência olhando só /tmp ou working files. Sempre: 1) registry → 2) HD externo RAW → 3) HD externo slim → 4) só então locais. Erro custou declarar XAU 1H inviável quando 3 blocos estavam no HD externo.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_raw_data_lookup_order.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_recall_gate_before_backtest.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_recall_gate_before_backtest',
  'Quando existe Ground Truth de winners desejados, validar RECALL do detector contra ele ANTES de rodar censo/backtest. Detector que não recaptura os winners conhecidos torna o backtest nulo.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_recall_gate_before_backtest.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_review_cadence.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_review_cadence',
  '2026-05-15 — cadência institucional de revisão. Semanal domingo (~30min) + mensal 1ª sexta (~2h). Aprovado por Cris.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_review_cadence.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_root_cause_over_symptom.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_root_cause_over_symptom',
  '2026-05-20 Preferir filtros que endereçam causa raiz (regime macro) sobre filtros sintomáticos (signal proxy). Caso XAU 4H V4 vs V1c',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_root_cause_over_symptom.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_sample_gate_for_rules.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_sample_gate_for_rules',
  '2026-05-15 — disciplina institucional. Tamanho de amostra exigido antes de criar/alterar regras operacionais. Evita overfitting com n<30.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_sample_gate_for_rules.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_self_verification_protocol.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_self_verification_protocol',
  'REGRA PERMANENTE 2026-06-05 — Protocolo de auto-verificação obrigatório antes de responder \"está OK\" ou aprovar estratégia. Resposta a falha onde \"respondi OK\" sem verificar e propaguei bug de mapping plot_id por 2 dias.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_self_verification_protocol.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_strategy_validity_gate.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_strategy_validity_gate',
  '2026-05-20 Estratégia é considerada VÁLIDA se win% >= 70%. Parâmetro operacional definido por Cris durante backtest XAU 4H',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_strategy_validity_gate.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_telegram_chat_ids_loop.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_telegram_chat_ids_loop',
  '2026-05-18 — bug em 2 monitor scripts passava TELEGRAM_CHAT_ID como string única \"id1,id2\" pra Telegram API que ignora 2º; padrão correto é split por vírgula + loop',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_telegram_chat_ids_loop.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_tv_alert_caches_pine.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_tv_alert_caches_pine',
  'TradingView congela snapshot do alert() function call no momento da criação; mudanças no Pine NÃO propagam para alerts existentes',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_tv_alert_caches_pine.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_validate_before_manual_user_work.md')::uuid,
  'product', 'internal', 'feedback',
  'feedback_validate_before_manual_user_work',
  'PROTOCOLO PERMANENTE 2026-05-22 — SEMPRE validar template/contrato end-to-end com 1 exemplo ANTES de pedir Cris executar trabalho manual repetitivo. Falha em validar = bug silencioso compromete 5+ dias de produção',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_validate_before_manual_user_work.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_validate_plot_id_mapping.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_validate_plot_id_mapping',
  'REGRA PERMANENTE — SEMPRE validar mapping plot_id→BUY/SELL antes de usar bubbles em ANY backtest/score/filtro. MAPPING CORRETO 2026-06-07 (confirmado por Cris): BUY=plot_0/plot_2/plot_4, SELL=plot_6/plot_8/plot_10, POC=plot_12. Mapping anterior 2026-06-05 está superseded.',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_validate_plot_id_mapping.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:feedback_xau_only_focus.md')::uuid,
  'private', 'private', 'feedback',
  'feedback_xau_only_focus',
  '2026-05-20 Foco operacional EXCLUSIVO em XAU. Roadmap timeframes XAU 4H → 1H → 30M → 15M. NÃO sugerir replicação cross-asset (EUR/SPX/ETH/XAG/etc.)',
  array['seed:memory_cards_wave2b','wave:2B','type:feedback'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/feedback_xau_only_focus.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:project_l2_bpt_consolidated_knowledge.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_consolidated_knowledge',
  'L2/BPT XAU 4H LONG — conhecimento consolidado: legpos é o eixo causal validado; indicadores identificam topo macro (não comparam trades); bloqueio sequencial/legbear RETRATADO (não validou base 276); exit partial50@2R+6R aprovado, BE rejeitado; próximo foco = SL estrutural trade-a-trade.',
  array['seed:memory_cards_wave2b','wave:2B','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_consolidated_knowledge.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:project_l2_bpt_reader_layer2_library_and_dossier.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_reader_layer2_library_and_dossier',
  'L2/BPT Reader vivo — Camada 2 (biblioteca de 93 lentes de evidência condicional, commit fdfe1f6) + dossiê/assembler que compõe Camadas 0,1,2,3a,3b por episódio; biblioteca NÃO decide, aprofunda a leitura',
  array['seed:memory_cards_wave2b','wave:2B','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_reader_layer2_library_and_dossier.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:project_l2_bpt_loser_cuts_consolidated.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_loser_cuts_consolidated',
  'Consolidado dos filtros de LOSER-CUT que funcionaram na L2/BPT (cortam loser sem matar runner) + os que mataram runner (não usar) + verdade de fundo (auction-irredutível além de 2). Base p/ testar em outras estratégias (L1 EMA).',
  array['seed:memory_cards_wave2b','wave:2B','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_loser_cuts_consolidated.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:project_l2_bpt_trade_qualification_engine.md')::uuid,
  'private', 'private', 'project',
  'project_l2_bpt_trade_qualification_engine',
  'L2/BPT Trade Qualification Engine — raciocínio multifatorial trade-a-trade (84 fatores, cego ao outcome) supera baselines P>=0.99; lead validado não promovido',
  array['seed:memory_cards_wave2b','wave:2B','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_l2_bpt_trade_qualification_engine.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:project_xau_15m_fase1_state.md')::uuid,
  'private', 'private', 'project',
  'project_xau_15m_fase1_state',
  'Estado consolidado da FASE 1 do XAU 15M (Anel 1 determinístico) — 4 setups construídos+caracterizados+DA-validados, com features/lentes, números e veredito por setup. Visão de conjunto p/ Cris. Anel 2 (readers por episódio) roda SOBRE isto.',
  array['seed:memory_cards_wave2b','wave:2B','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_15m_fase1_state.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:project_macro_structural_reading_engine.md')::uuid,
  'private', 'private', 'project',
  'project_macro_structural_reading_engine',
  'Nova frente — Macro Structural Reading Engine strategy-agnostic (multi-TF + volumetria + confluência), design+censo feitos; resolve a falha de leitura-de-conjunto do L2/BPT',
  array['seed:memory_cards_wave2b','wave:2B','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_macro_structural_reading_engine.md',
  'active'
),
(
  md5('seed:memory_cards_wave2b:project_indicator_signals_pipeline.md')::uuid,
  'private', 'private', 'project',
  'project_indicator_signals_pipeline',
  'Pipeline de coleta passiva 2026-05-17 de signals de 5 indicadores × 5 TFs × 5 ativos (~125 alerts) → indicator_signals.jsonl → enrichment diário → relatório mensal',
  array['seed:memory_cards_wave2b','wave:2B','type:project'],
  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_indicator_signals_pipeline.md',
  'active'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- ROLLBACK (NAO EXECUTAR JUNTO — so em DEV, manual, sob autorizacao)
-- ============================================================================
-- begin;
-- delete from memory_items where 'seed:memory_cards_wave2b' = any(tags);
-- commit;
-- ============================================================================
