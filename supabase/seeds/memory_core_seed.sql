-- ============================================================================
-- SUPABASE MEMORY — CORE SEED (Wave 1) · seed:memory_core_v1 · 2026-07-02
-- ============================================================================
-- Plano: docs/architecture/SUPABASE_MEMORY_FULL_MIGRATION_PLAN.md (aprovado, commit 174932c)
-- Review: docs/architecture/SUPABASE_MEMORY_SEED_REVIEW_20260702.md
-- APLICACAO: MANUAL pelo Cris via Supabase Dashboard SQL Editor (DEV apenas,
--   projeto trading-system-memory-dev / vgfofofozptrtjvtuyzy). MCP permanece read-only.
-- IDEMPOTENTE: ids deterministicos md5(seed_key)::uuid + ON CONFLICT DO NOTHING.
--   Re-executar o ficheiro inteiro e seguro (0 duplicados).
-- CONTEUDO: zero RAW/candles/OHLCV, zero logs, zero secrets/tokens, zero
--   parametros de edge/alpha, zero dados restritos TradingView. So titulos,
--   resumos, status, pointers (path/checksum/commit).
-- ROLLBACK: bloco comentado no fim do ficheiro (por batch tag / ids deterministicos).
-- Total: 44 rows = A:9 memory_items · B:8 decisions · C:12 artifacts ·
--   D:7 source_registry · E:1 safety_reports + 1 memory_items + 6 agent_runs.
-- ============================================================================

-- ============================================================================
-- BATCH A — Core operating memory → memory_items (9 rows)
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_core_v1:memory_items:raw-source-first')::uuid,
  'product', 'internal', 'feedback',
  'RAW/source first — hierarquia de fontes de dados',
  'Todo dado de mercado/indicador vem do RAW replay original ou da fonte de autoridade. Derivados so com source_ref + causal boundary. Ordem de lookup obrigatoria: registry -> RAW HD externo -> derivados -> local. Nunca declarar dado ausente/bloqueado sem busca de proveniencia.',
  array['seed:memory_core_v1','batch:A','raw-first','data-policy'],
  '~/.claude memory: feedback_indicators_raw_first.md · docs/project_authority/02_DATA_SOURCE_POLICY_RAW_FIRST.md',
  'active'
),
(
  md5('seed:memory_core_v1:memory_items:no-slim-proxy-validation')::uuid,
  'product', 'internal', 'feedback',
  'Proibido SLIM/proxy como validacao',
  'Ban permanente de features derivadas (SLIM) como fonte de validacao. Validacao sempre sobre RAW pine_boxes/labels/study_values. Derivados servem no maximo como indice, nunca como evidencia de edge.',
  array['seed:memory_core_v1','batch:A','no-slim','validation'],
  '~/.claude memory: feedback_never_use_slim_features.md',
  'active'
),
(
  md5('seed:memory_core_v1:memory_items:no-backtest-without-manifest')::uuid,
  'product', 'internal', 'feedback',
  'Nenhum backtest serio sem manifest/mapping/predicados/sanity',
  'Backtest serio exige: RAW mapping documentado, manifest com checksums, predicados causais explicitos (close-only, sem look-ahead) e sanity checks antes de reportar. Checklist canonico de 15 problemas metodologicos aplica-se sempre.',
  array['seed:memory_core_v1','batch:A','backtest','methodology'],
  '~/.claude memory: reference_backtest_methodology_checklist.md · docs/project_authority/03_BACKTEST_VALIDATION_PROTOCOL.md',
  'active'
),
(
  md5('seed:memory_core_v1:memory_items:production-safety')::uuid,
  'product', 'internal', 'feedback',
  'Production safety — regras operacionais duras',
  'Receiver nunca iniciado com python3 direto (usar LaunchAgent/start_receiver.sh). Pausar daemon E cron antes de tocar chart. Replay so via safe_backtest_window.sh. Se algo falhar: restaurar producao primeiro, diagnosticar depois. Nunca expor .env/tokens/URLs secretas.',
  array['seed:memory_core_v1','batch:A','production','safety'],
  'CLAUDE.md (safety defaults) · docs/architecture/PRODUCTION_RUNBOOK_20260702.md',
  'active'
),
(
  md5('seed:memory_core_v1:memory_items:no-prod-change-without-approval')::uuid,
  'product', 'internal', 'feedback',
  'Nada de producao/runtime/Telegram/catalogo/strategy_rules sem aprovacao explicita',
  'Mudancas em producao, runtime, canais Telegram, catalogo de estrategias ou strategy_rules exigem aprovacao explicita do Cris. Pre-Change Discipline (4 perguntas: input? vivo? volume? canal dormant = parar) antes de qualquer codigo em ficheiros de producao.',
  array['seed:memory_core_v1','batch:A','production','governance'],
  'CLAUDE.md (Pre-Change Discipline) · docs/project_authority/10_DO_NOT_DO_RULES.md',
  'active'
),
(
  md5('seed:memory_core_v1:memory_items:trading-data-not-in-claude-memory')::uuid,
  'product', 'internal', 'architecture',
  'Trading data nao vive na memoria conversacional do Claude',
  'Candles, backtests, logs e journal nao entram na memoria do assistente nem no indice MEMORY. O modelo recupera slices/contexto sob demanda via store estruturado com pointers para a fonte RAW.',
  array['seed:memory_core_v1','batch:A','memory-architecture'],
  'docs/architecture/SUPABASE_MEMORY_DATA_ARCHITECTURE.md §2',
  'active'
),
(
  md5('seed:memory_core_v1:memory_items:supabase-index-not-source-of-truth')::uuid,
  'product', 'internal', 'architecture',
  'Supabase = index/store/retrieval, nunca source of truth',
  'Supabase indexa e recorda; nao valida backtest nem substitui RAW/source. Todo registro derivado carrega source_ref + timestamp + commit/checksum. Nenhum fluxo de validacao le edge do Supabase.',
  array['seed:memory_core_v1','batch:A','memory-architecture','supabase'],
  'docs/architecture/SUPABASE_MEMORY_DATA_ARCHITECTURE.md §2 · SUPABASE_MEMORY_FULL_MIGRATION_PLAN.md §2',
  'active'
),
(
  md5('seed:memory_core_v1:memory_items:agentic-os-memory-architecture')::uuid,
  'product', 'internal', 'architecture',
  'Agentic OS — arquitetura de memoria em camadas',
  'Camadas: CLAUDE.md (guardrails+pointers) · MEMORY index+cards (factos curados) · git docs/checkpoints (registo duravel, autoridade) · Supabase (store/index/retrieval escalavel) · RAW/source (autoridade de mercado) · cold storage (outputs pesados) · contexto conversacional (efemero). Cada camada tem o que pode e o que e proibido conter.',
  array['seed:memory_core_v1','batch:A','memory-architecture','agentic-os'],
  'docs/architecture/TRADING_SYSTEM_AGENTIC_OS_MEMORY_v1.md · SUPABASE_MEMORY_DATA_ARCHITECTURE.md §3',
  'active'
),
(
  md5('seed:memory_core_v1:memory_items:current-task-order-2026-07-02')::uuid,
  'private', 'private', 'project',
  'Ordem de tarefas vigente (2026-07-02, aprovada Cris)',
  'SUPABASE_MEMORY_FULL_MIGRATION = ACTIVE_NEXT_BLOCK (antes de qualquer estrategia). XAU_15M_LONG_REGIME_DETECTOR = DEFERRED ate migracao completa. XAU_SHORT = DEFERRED apos XAU 15M. Proibido no bloco: nova pesquisa estrategica, Fase 4C, comercializacao externa.',
  array['seed:memory_core_v1','batch:A','task-order','status'],
  'docs/architecture/SUPABASE_MEMORY_FULL_MIGRATION_PLAN.md (Status block)',
  'active'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- BATCH B — Decisions → decisions (8 rows, ON CONFLICT decision_key)
-- ============================================================================
begin;

insert into decisions (id, decision_key, title, decision, status, rationale, approved_by, decision_date, source_ref, commit_sha) values
(
  md5('seed:memory_core_v1:decisions:core_supabase_memory_architecture_approved')::uuid,
  'core_supabase_memory_architecture_approved',
  'Arquitetura de memoria Supabase aprovada',
  'Design SUPABASE_MEMORY_DATA_ARCHITECTURE aprovado: camadas de memoria definidas, schema de 12 tabelas (11 aplicadas em DEV), Supabase como index/store/retrieval.',
  'approved',
  'Resolve persistencia entre sessoes + retrieval estruturado sem inflar contexto; RAW continua autoridade.',
  'Cris', '2026-07-02',
  'seed:memory_core_v1:batch_B · docs/architecture/SUPABASE_MEMORY_DATA_ARCHITECTURE.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3'
),
(
  md5('seed:memory_core_v1:decisions:core_product_private_boundary_approved')::uuid,
  'core_product_private_boundary_approved',
  'Fronteira product/private aprovada',
  'Split produto/privado: produto = engine/arquitetura/safety (vendavel); privado = alpha/estrategias/status operacional do Cris. Comprador leva motor, nao edge. Refletido em scope/visibility no Supabase.',
  'approved',
  'Permite comercializar o engine sem expor o edge; organiza visibilidade da memoria.',
  'Cris', '2026-07-02',
  'seed:memory_core_v1:batch_B · docs/architecture/PRODUCT_PRIVATE_SPLIT_PLAN.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3'
),
(
  md5('seed:memory_core_v1:decisions:core_external_commercialization_deferred')::uuid,
  'core_external_commercialization_deferred',
  'Comercializacao externa adiada (P0 compliance)',
  'Venda externa do pacote = NO-GO ate resolver P0 de compliance (audit PACKAGE_COMMERCIAL_READINESS). Uso interno = GO. Adiamento tambem justificado por XAU SHORT pendente.',
  'approved',
  'Audit identificou pendencias P0; edge privado precisa de fronteira consolidada antes de exposicao externa.',
  'Cris', '2026-07-02',
  'seed:memory_core_v1:batch_B · docs/architecture/PACKAGE_COMMERCIAL_READINESS_AUDIT.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3'
),
(
  md5('seed:memory_core_v1:decisions:core_production_runtime_no_auto_trading')::uuid,
  'core_production_runtime_no_auto_trading',
  'Runtime de producao: zero auto-trading',
  'Runtime vivo = receiver + cloudflared + External Factors v2 (passivo) + MCP server. Nada auto-negocia. Camada 4H DORMANT/SUPERSEDED; nao religar sem autorizacao.',
  'approved',
  'Production Logic Re-Audit 2026-07-02 confirmou runtime estreito; execucao e sempre humana (validacao por proxy, nao automacao).',
  'Cris', '2026-07-02',
  'seed:memory_core_v1:batch_B · docs/architecture/PRODUCTION_LOGIC_REAUDIT_20260702.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3'
),
(
  md5('seed:memory_core_v1:decisions:core_ef_v2_live_passive_context_daemon')::uuid,
  'core_ef_v2_live_passive_context_daemon',
  'External Factors v2 = daemon de contexto passivo, vivo',
  'EF v2 opera em passive logging (macro/calendar/rates), como contexto — nao integrado a decisao de trading e sem gerar sinais.',
  'approved',
  'Contexto macro util para leitura convergente; integracao ao trading exigiria validacao propria (nao feita).',
  'Cris', '2026-07-02',
  'seed:memory_core_v1:batch_B · memory: project_external_factors_v2_plan.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3'
),
(
  md5('seed:memory_core_v1:decisions:core_xau_15m_regime_readaptation_before_short')::uuid,
  'core_xau_15m_regime_readaptation_before_short',
  'XAU 15M: readaptacao de regime antes do SHORT',
  'Sequencia aprovada: XAU 15M LONG (regime detector/readaptacao) primeiro; XAU SHORT so depois (espelho nao-simetrico: mirror simetrico ja refutado).',
  'approved',
  'LONG bottom aprovado (swept-runner) e base de regime v5 MTF existente; SHORT sem base propria ainda.',
  'Cris', '2026-07-02',
  'seed:memory_core_v1:batch_B · memory: project_xau_15m_regime_detector_and_direction.md · project_xau_15m_direction_short_mirror_refuted.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3'
),
(
  md5('seed:memory_core_v1:decisions:core_supabase_migration_before_strategy_work')::uuid,
  'core_supabase_migration_before_strategy_work',
  'Migracao total da memoria Supabase antes de trabalho de estrategia',
  'Mudanca de prioridade 2026-07-02: concluir migracao da memoria (M1-M5) antes de abrir XAU 15M LONG Regime Detector ou qualquer nova pesquisa.',
  'approved',
  'Novas pesquisas geram muito estado; sem camada de memoria estruturada o custo de contexto/perda de continuidade cresce.',
  'Cris', '2026-07-02',
  'seed:memory_core_v1:batch_B · docs/architecture/SUPABASE_MEMORY_FULL_MIGRATION_PLAN.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3'
),
(
  md5('seed:memory_core_v1:decisions:core_safety_layer_report_only_calibrated')::uuid,
  'core_safety_layer_report_only_calibrated',
  'Safety layer report-only calibrado',
  'Safety scanner roda em modo report-only (nao bloqueia). Baseline calibrada: BLOCKER=0, WARNING=1 (conhecido), INFO informativo. Passagem a blocking = decisao futura separada.',
  'approved',
  'Report-only permite calibrar sem travar operacao; unico WARNING e residual conhecido em research privado.',
  'Cris', '2026-07-02',
  'seed:memory_core_v1:batch_B · docs/governance/SAFETY_LAYER_USAGE.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3'
)
on conflict (decision_key) do nothing;

commit;

-- ============================================================================
-- BATCH C — Artifacts (pointers) → artifacts (12 rows)
-- commit_sha = 174932c (HEAD na criacao do seed) · checksum = sha256 do ficheiro
-- ============================================================================
begin;

insert into artifacts (id, artifact_type, path, title, description, checksum, commit_sha, source_ref, status) values
(
  md5('seed:memory_core_v1:artifacts:supabase-memory-data-architecture')::uuid,
  'design_doc', 'docs/architecture/SUPABASE_MEMORY_DATA_ARCHITECTURE.md',
  'Supabase Memory & Data Architecture (design aprovado)',
  'Design das camadas de memoria + schema proposto + trading data policy + retrieval model.',
  '9d29c7514756b1fad3d7851f9360de58a3b4a9cafc5c726949069d7527bfe02c',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:supabase-implementation-plan')::uuid,
  'plan', 'docs/architecture/SUPABASE_IMPLEMENTATION_PLAN.md',
  'Supabase Implementation Plan (S1)',
  'Plano S1: schema draft + boundary docs + fases S2-S8.',
  'e1d1a52f146213168d8b60ef1a34ac926e63f64c79203e3384512b36f076e26c',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:supabase-s2-setup-mcp-report')::uuid,
  'report', 'docs/architecture/SUPABASE_S2_SETUP_AND_MCP_REPORT.md',
  'Supabase S2 Setup & MCP Report',
  'Schema aplicado em DEV + MCP read-only validado (§5.e; ref correto vgfofofozptrtjvtuyzy).',
  'c35de65b40bcaefb3d6d5ca818d8242560fc3186e2c937163ec8904f3b72dd17',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:supabase-memory-full-migration-plan')::uuid,
  'plan', 'docs/architecture/SUPABASE_MEMORY_FULL_MIGRATION_PLAN.md',
  'Supabase Memory Full Migration Plan (M1, aprovado)',
  'Plano da migracao total: inventario, mapping, batches A-E, seed format, validacao, rollback.',
  'bde670b3c6a976f6859b19676f4452e570ca8beb464b2359bb99438b6bbcd3ec',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:agentic-os-portability-checkpoint')::uuid,
  'checkpoint', 'docs/architecture/AGENTIC_OS_PORTABILITY_CHECKPOINT_20260702.md',
  'Agentic OS Portability Checkpoint (2026-07-02)',
  'Checkpoint congelando estado do repo/decisoes/commits da fase de portabilidade.',
  '57503986bc7bacb7a5911879cae1d112f53be595adbab961d7abe3be7c16a2cb',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:production-logic-reaudit')::uuid,
  'audit', 'docs/architecture/PRODUCTION_LOGIC_REAUDIT_20260702.md',
  'Production Logic Re-Audit (2026-07-02)',
  'Auditoria do runtime vivo vs docs: runtime estreito, camada 4H dormant, zero auto-trading.',
  '08b8398b6fe91493920c808534c2761adcc023ad71ed796f959a9685818fb091',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:production-runbook')::uuid,
  'runbook', 'docs/architecture/PRODUCTION_RUNBOOK_20260702.md',
  'Production Runbook (2026-07-02)',
  'Runbook operacional do runtime vivo (receiver, tunnel, EF v2, MCP).',
  '19977e283a0794edf27200f8f89a68be7ecc582f6d2ac39e2be3f5decaed2675',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:product-private-split-plan')::uuid,
  'plan', 'docs/architecture/PRODUCT_PRIVATE_SPLIT_PLAN.md',
  'Product/Private Split Plan',
  'Plano da fronteira produto (engine) vs privado (alpha).',
  '39c7602f44157f3098ffb258bfc9e7ad924bf91044192262cef71418f1983cfe',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:package-commercial-readiness-audit')::uuid,
  'audit', 'docs/architecture/PACKAGE_COMMERCIAL_READINESS_AUDIT.md',
  'Package Commercial Readiness Audit',
  'Audit comercial: interno GO, externo NO-GO (P0 compliance).',
  'ca3c0f98a6de093f6727594a042768633fa8ccd3c7b9fa76656129a7d25f516a',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:cold-storage-manifest-20260702')::uuid,
  'manifest', 'docs/cleanup/COLD_STORAGE_MANIFEST_20260702.md',
  'Cold Storage Manifest (2026-07-02)',
  'Manifest do arquivamento 2,2G para HD externo com SHA256 + roundtrip verificado + restore instructions.',
  'e52ebdb78ef73f95354dd24e6a696a67e7ae6fb94ae7e7c6a99037cfe04a49f8',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:safety-layer-usage')::uuid,
  'doc', 'docs/governance/SAFETY_LAYER_USAGE.md',
  'Safety Layer Usage (report-only)',
  'Como rodar os scanners de safety report-only; baseline e interpretacao.',
  '443adf7701b8f9dea5309a5ac8db58e27faf3c2ecd197b3e15c6c3df4db7adb1',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
),
(
  md5('seed:memory_core_v1:artifacts:strategy-status-master')::uuid,
  'status_master', 'docs/project_authority/04_STRATEGY_STATUS_MASTER.md',
  'Strategy Status Master (canonico)',
  'Mapa canonico de status de todas as estrategias (atualizado 2026-07-02). Pointer: conteudo detalhado (edge) fica no repo.',
  '9f86fe9f3ec5cd6da2c6ac8dec053f9f6ef424c871b02df81ec40aed4e25554f',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_C', 'active'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- BATCH D — Source registry (pointers/checksums, ZERO conteudo) → source_registry (7 rows)
-- Nota: source_registry nao tem coluna de tag; rollback = ids deterministicos (fim do ficheiro).
-- ============================================================================
begin;

insert into source_registry (id, source_type, path, symbol, timeframe, checksum, authority_level) values
(
  md5('seed:memory_core_v1:source_registry:raw-root-tradingdata')::uuid,
  'raw_root', '/Volumes/GUTS_ LACIE/TradingData/', null, null, null, 'source_of_truth'
),
(
  md5('seed:memory_core_v1:source_registry:raw-manifests-dir')::uuid,
  'manifest_dir', '/Volumes/GUTS_ LACIE/TradingData/manifests/', null, null, null, 'source_of_truth'
),
(
  md5('seed:memory_core_v1:source_registry:cold-storage-backtests-archive')::uuid,
  'cold_archive', '/Volumes/GUTS_ LACIE/trading_system_cold_storage/alert-bridge-logs-backtests_20260702.tar.zst',
  null, null,
  '89e79ebe4f803143e16698437306680fbe6a2c5c486ec1afec9dcdf3de5f5e34', 'log'
),
(
  md5('seed:memory_core_v1:source_registry:cold-storage-backups-archive')::uuid,
  'cold_archive', '/Volumes/GUTS_ LACIE/trading_system_cold_storage/backups-dated_20260702.tar.zst',
  null, null,
  '41acabcc1006cf6de80d77502f2556c8b0d69cf16b445c8129911be63556f97a', 'log'
),
(
  md5('seed:memory_core_v1:source_registry:cold-storage-sha256sums')::uuid,
  'checksum_file', '/Volumes/GUTS_ LACIE/trading_system_cold_storage/SHA256SUMS.txt', null, null, null, 'index'
),
(
  md5('seed:memory_core_v1:source_registry:cold-storage-manifest-doc')::uuid,
  'manifest', 'docs/cleanup/COLD_STORAGE_MANIFEST_20260702.md', null, null,
  'e52ebdb78ef73f95354dd24e6a696a67e7ae6fb94ae7e7c6a99037cfe04a49f8', 'index'
),
(
  md5('seed:memory_core_v1:source_registry:slim-pipeline-delete-manifest')::uuid,
  'manifest', 'docs/cleanup/SLIM_PIPELINE_DELETE_MANIFEST_20260702.md', null, null,
  '61004065548b65d9fa55590b8d3f6eff54709ea24519bdd551ce67275b34a7fd', 'index'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- BATCH E — Safety baseline + milestones → safety_reports (1) + memory_items (1) + agent_runs (6)
-- ============================================================================
begin;

insert into safety_reports (id, run_at, blocker_count, warning_count, info_count, report_path, commit_sha, status) values
(
  md5('seed:memory_core_v1:safety_reports:baseline-2026-07-02')::uuid,
  timestamptz '2026-07-02 00:00:00+00', 0, 1, 47,
  'docs/governance/SAFETY_LAYER_USAGE.md',
  '174932ced7c7aff2696051c1baf10a999b9138d3',
  'report_only'
)
on conflict (id) do nothing;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_core_v1:memory_items:safety-baseline-warning-context')::uuid,
  'private', 'private', 'project',
  'Safety baseline — contexto do unico WARNING',
  'WARNING unico da baseline (2026-07-02): contaminacao SLIM num candidato caminho_b — ambito private/research, nao toca product/runtime. Conhecido e aceito; nao e regressao.',
  array['seed:memory_core_v1','batch:E','safety','baseline'],
  'scripts/safety/run_safety_report.py (output 2026-07-02) · docs/cleanup/SLIM_CLUSTER_STATUS_HISTORICAL_COMPATIBILITY.md',
  'active'
)
on conflict (id) do nothing;

insert into agent_runs (id, agent_name, task_type, prompt_ref, output_ref, status, started_at, completed_at, commit_sha, notes) values
(
  md5('seed:memory_core_v1:agent_runs:agentic-os-phase1-2')::uuid,
  'claude-code', 'milestone', 'Agentic OS Fases 1-2 (inventario + portabilidade config/env)',
  'docs/architecture/AGENTIC_OS_PORTABILITY_CHECKPOINT_20260702.md',
  'completed', timestamptz '2026-07-02 00:00:00+00', timestamptz '2026-07-02 00:00:00+00',
  null, 'seed:memory_core_v1:batch_E · resumo de milestone, nao log'
),
(
  md5('seed:memory_core_v1:agent_runs:supabase-s1-schema-draft')::uuid,
  'claude-code', 'milestone', 'Supabase S1: schema draft 12 tabelas + boundary docs',
  'supabase/schema.sql · docs/architecture/SUPABASE_IMPLEMENTATION_PLAN.md',
  'completed', timestamptz '2026-07-02 00:00:00+00', timestamptz '2026-07-02 00:00:00+00',
  null, 'seed:memory_core_v1:batch_E · resumo de milestone, nao log'
),
(
  md5('seed:memory_core_v1:agent_runs:supabase-s2-schema-applied-dev')::uuid,
  'cris-manual', 'milestone', 'Supabase S2: schema aplicado manualmente em DEV via SQL Editor (11 tabelas)',
  'docs/architecture/SUPABASE_S2_SETUP_AND_MCP_REPORT.md',
  'completed', timestamptz '2026-07-02 00:00:00+00', timestamptz '2026-07-02 00:00:00+00',
  null, 'seed:memory_core_v1:batch_E · resumo de milestone, nao log'
),
(
  md5('seed:memory_core_v1:agent_runs:supabase-mcp-readonly-validation')::uuid,
  'claude-code', 'milestone', 'Supabase MCP read-only validado (typo de ref corrigido; role read-only confirmada)',
  'docs/architecture/SUPABASE_S2_SETUP_AND_MCP_REPORT.md §5.e',
  'completed', timestamptz '2026-07-02 00:00:00+00', timestamptz '2026-07-02 00:00:00+00',
  'd7d8bc9', 'seed:memory_core_v1:batch_E · resumo de milestone, nao log'
),
(
  md5('seed:memory_core_v1:agent_runs:memory-tiering-20260702')::uuid,
  'claude-code', 'milestone', 'Memory tiering: MEMORY.md hot + MEMORY_ARCHIVE (indice 186 entradas -> hot curado)',
  'docs/project_authority/MEMORY_ARCHIVE.md',
  'completed', timestamptz '2026-07-02 00:00:00+00', timestamptz '2026-07-02 00:00:00+00',
  null, 'seed:memory_core_v1:batch_E · resumo de milestone, nao log'
),
(
  md5('seed:memory_core_v1:agent_runs:supabase-full-migration-plan-m1')::uuid,
  'claude-code', 'milestone', 'Fase M1: inventario completo (229 cards + 47 docs) + plano de migracao total aprovado',
  'docs/architecture/SUPABASE_MEMORY_FULL_MIGRATION_PLAN.md',
  'completed', timestamptz '2026-07-02 00:00:00+00', timestamptz '2026-07-02 00:00:00+00',
  '174932ced7c7aff2696051c1baf10a999b9138d3', 'seed:memory_core_v1:batch_E · resumo de milestone, nao log'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- ROLLBACK (NAO EXECUTAR JUNTO COM O SEED — so em DEV, manual, sob autorizacao)
-- ============================================================================
-- begin;
-- delete from memory_items    where 'seed:memory_core_v1' = any(tags);
-- delete from decisions       where source_ref like 'seed:memory_core_v1%';
-- delete from artifacts       where source_ref like 'seed:memory_core_v1%';
-- delete from agent_runs      where notes like 'seed:memory_core_v1%';
-- delete from safety_reports  where id = md5('seed:memory_core_v1:safety_reports:baseline-2026-07-02')::uuid;
-- delete from source_registry where id in (
--   md5('seed:memory_core_v1:source_registry:raw-root-tradingdata')::uuid,
--   md5('seed:memory_core_v1:source_registry:raw-manifests-dir')::uuid,
--   md5('seed:memory_core_v1:source_registry:cold-storage-backtests-archive')::uuid,
--   md5('seed:memory_core_v1:source_registry:cold-storage-backups-archive')::uuid,
--   md5('seed:memory_core_v1:source_registry:cold-storage-sha256sums')::uuid,
--   md5('seed:memory_core_v1:source_registry:cold-storage-manifest-doc')::uuid,
--   md5('seed:memory_core_v1:source_registry:slim-pipeline-delete-manifest')::uuid
-- );
-- commit;
-- ============================================================================
