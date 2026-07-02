# SUPABASE MEMORY — FULL MIGRATION PLAN (2026-07-02)

**Modo:** plano + inventário read-only. **Nenhum dado aplicado. Nenhum runtime tocado. MCP permanece read-only.**
**Base:** `SUPABASE_MEMORY_DATA_ARCHITECTURE.md` (design aprovado) · `SUPABASE_IMPLEMENTATION_PLAN.md` (S1) · `SUPABASE_S2_SETUP_AND_MCP_REPORT.md` §5.e (MCP validado) · schema DEV aplicado (11 tabelas, ref `vgfofofozptrtjvtuyzy`).
**Prioridade aprovada pelo Cris (2026-07-02):** SUPABASE_MEMORY_FULL_MIGRATION = **ACTIVE_NEXT_BLOCK** · XAU_15M_LONG_REGIME_DETECTOR = DEFERRED_UNTIL_SUPABASE_MEMORY_FULL_MIGRATION_COMPLETE · XAU_SHORT = DEFERRED_AFTER_XAU_15M.

---

## 1. Executive verdict

**READY_FOR_STRUCTURED_MIGRATION** ✅

Justificativa:
- Schema DEV aplicado e validado via MCP read-only (11 tabelas, RLS on, counts 0, role `supabase_read_only_user` confirmada).
- Fontes 100% inventariadas (este doc, §3): 229 memory cards + MEMORY.md hot + MEMORY_ARCHIVE + 47 docs repo.
- Design boundaries já aprovados (RAW = verdade · Supabase = index/store/retrieval · product/private scope).
- Caminho de escrita seguro definido: seed SQL idempotente aplicado **manualmente pelo Cris via SQL Editor** — Claude nunca escreve.

Condições (não bloqueiam, moldam o plano):
- `memory_items`/`artifacts`/`source_registry` **não têm unique constraint natural** → idempotência via **id determinístico** (`md5(seed_key)::uuid`), sem alterar schema.
- MEMORY_ARCHIVE entra como **1 artifact pointer**, não como ~200 memory_items (anti-duplicação, §10).
- Conteúdo edge-sensível entra como título+resumo+`source_ref` com `scope='private'`, nunca parâmetros/thresholds completos (§5).

## 2. Migration definition — o que significa “migração total”

**MIGRA (como conteúdo estruturado):**
- Toda a memória durável do projeto: protocolos permanentes, feedbacks de método, estado de estratégias, referências operacionais (229 cards + índice hot).
- Todas as decisões (aprovadas/deferidas/rejeitadas/retratadas/superseded) como registros `decisions` com `decision_key` estável.
- Todos os artefatos importantes **como referência** (path + checksum + commit), nunca conteúdo embutido.
- Metadados de safety/runbook/checkpoint (baseline BLOCKER0/WARNING1/INFO47, runbook, portability checkpoint).

**NÃO MIGRA (como conteúdo bruto):** RAW/candles, backtests massivos, logs vivos, TradingView market data, secrets. Esses entram **só** como pointer/checksum/summary/status (§5). **RAW/source continua fonte de verdade. Supabase = store/index/retrieval layer, não validador nem data lake.**

## 3. Source inventory (read-only, 2026-07-02)

### 3.1 Memória persistente Claude (`~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/`)
- **MEMORY.md hot** — índice curado pós-tiering (~50 entradas ativas; protocolos ⭐⭐, estratégias aprovadas, produção, arquitetura, próximos blocos).
- **229 memory cards** com frontmatter: **user 2 · feedback 77** (74 `feedback_` + 3 `PRINCIPAL_`) **· project 128 · reference 22**. 17 cards em formato antigo sem `metadata.type` (tipo inferível do prefixo — normalizar na migração).
- **MEMORY_ARCHIVE.md** (66KB, ~200 bullets) — snapshot integral do índice pré-tiering; conteúdo já refletido nos cards → **entra como artifact pointer, não como items**.
- Strays não-memória (`_compute.py`, `_ohlcv*.py`, `_tmp_ohlcv.json`, `MEMORY.md.pre_tiering_20260702.bak`) — **fora da migração**.

### 3.2 Docs repo (47 ficheiros)
- **docs/architecture/ (23):** 6 ativos-autoridade ⭐ (TRADING_SYSTEM_AGENTIC_OS_MEMORY_v1, AGENTIC_OS_PORTABILITY_CHECKPOINT_20260702, PRODUCTION_RUNBOOK_20260702, PRODUCTION_LOGIC_REAUDIT_20260702, PACKAGE_COMMERCIAL_READINESS_AUDIT, PRODUCT_PRIVATE_SPLIT_PLAN) + 3 Supabase (ARCHITECTURE/IMPLEMENTATION/S2_REPORT) + políticas ativas (DATA_STORAGE_POLICY, INDICATOR_SIGNAL_POLICY, LOG_MUTATION_POLICY, OPERATIONAL_INVENTORY, CONFIG_ENV_CONTRACT) + drafts (SIGNAL_OUTCOME_LAB×2, AGENTIC_OS plans×2) + históricos (SESSION_STATE, NAS_SMC_INCIDENT, XAU_L1_CYCLE_PAUSED).
- **docs/project_authority/ (19+1):** 00–10 autoridade + SKILL_01–07 + README + cópia versionada de MEMORY_ARCHIVE. Destaque: **04_STRATEGY_STATUS_MASTER.md** (status canônico, atualizado 2026-07-02).
- **docs/governance/ (1):** SAFETY_LAYER_USAGE.md ⭐ (baseline safety report-only).
- **docs/cleanup/ (3):** COLD_STORAGE_MANIFEST_20260702 ⭐ · SLIM_PIPELINE_DELETE_MANIFEST · SLIM_CLUSTER_STATUS.
- **supabase/ (2):** schema.sql (S1, 12 tabelas draft / 11 aplicadas) + README.md.

### 3.3 Baselines operacionais
- **Safety baseline:** `scripts/safety/run_safety_report.py` → BLOCKER=0 · WARNING=1 (SLIM pré-existente `xau_4h_caminho_b` candidate) · INFO=47 (2026-07-02).
- **Status master:** 04_STRATEGY_STATUS_MASTER.md + MEMORY.md (L2/BPT USER_APPROVED_NOT_PRODUCTION · XAU 15M swept-runner aprovada pendente slippage · runtime estreito, zero auto-trading).
- **Runtime vivo:** receiver + cloudflared + EF v2 passivo + MCP server (PRODUCTION_RUNBOOK/REAUDIT 20260702).

## 4. Table mapping (origem → tabela)

- **MEMORY.md hot (entradas ativas)** → `memory_items` (category do tipo do card; tags do índice; `source_ref` = path do card).
- **229 memory cards** → `memory_items` (1 card = 1 row: title=frontmatter name/título · body=resumo curto, NÃO o ficheiro inteiro quando edge-sensível · category=user/feedback/project/reference · status=active/superseded/refuted/deprecated conforme card · scope: PRINCIPAL/feedback de método = `product`-elegível; estratégia/edge = `private`).
- **MEMORY_ARCHIVE (selected/tiered)** → **NÃO** re-migrar bullets (duplicaria os cards). Entra como `artifacts` (2 pointers: memória local + cópia versionada) + eventuais decisões históricas ainda não capturadas → `decisions`.
- **Decisões aprovadas/deferidas/rejeitadas** → `decisions` com `decision_key` estável (ex.: `l2_bpt_ok_final_2026_07_02`, `xau_15m_deferred_until_supabase_migration`), `approved_by='Cris'`, `source_ref` p/ card/doc, `commit_sha` quando aplicável.
- **Docs/reports/manifests/checkpoints (47)** → `artifacts` (artifact_type=doc/report/manifest/checkpoint · path repo · commit_sha HEAD da migração · checksum sha256 dos ⭐).
- **Safety scan baseline** → `safety_reports` (1 row baseline 2026-07-02: 0/1/47, report_path=SAFETY_LAYER_USAGE.md, status=report_only).
- **RAW/artifact pointers** → `source_registry` (raiz RAW HD externo `/Volumes/GUTS_ LACIE/TradingData`, datasets XAU 15M/30M/1H, cold storage archives, manifests — path+checksum+authority_level=source_of_truth; **zero conteúdo**).
- **Agent/session blocks (milestones)** → `agent_runs` (marcos: Agentic OS phases, Supabase S1/S2, tiering de memória, production re-audit — prompt_ref/output_ref = docs).
- **Production/runtime status** → `memory_items` (category=architecture, status runtime) + `artifacts` (runbook/reaudit).
- **Retrieval tests** → `retrieval_queries` (preenchida na Fase M4 pelos testes de validação, não pelo seed).
- **External factor docs/events** → docs de EF → `artifacts`; eventos normalizados → `external_factor_events` **só em fase futura** (ingest EF v2 fora deste bloco; nada agora).
- **Sem uso neste bloco:** `market_context_snapshots`, `trade_journal_events`, `episode_context_links` (ficam vazias; população futura pós-checkpoint, sob autorização).

## 5. Exclusion policy — o que NUNCA entra como conteúdo

**Excluídos como conteúdo bruto:** RAW/candles (qualquer TF) · logs vivos (`alert-bridge/logs/`, signals, d2r) · backtests massivos (CSVs/JSONLs de trades, episode libraries) · broker/TradingView market data redistribuível · secrets/tokens/URLs de webhook/`.env` · dados paywalled/restritos (LuxAlgo/BigBeluga internals, fontes Tier-2 pagas) · outputs pesados (dumps, episode dossiers) · screenshots/plots/prints.

**Forma permitida de entrada (só metadado):** `path` · `checksum` (sha256) · `source_ref` · `artifact_ref` · `summary` curto · `status`. Exemplo: dataset XAU 15M RAW → `source_registry(path, checksum, symbol, timeframe, coverage)`, nunca as velas.

**Regra edge-sensível adicional:** parâmetros finos de estratégia (thresholds, stacks, rulers) ficam nos cards/docs (fonte); `memory_items` correspondente carrega título+estado+resumo de 1–3 linhas+`source_ref`, com `scope='private'`. Supabase recorda **onde está e em que estado está**, não replica o edge.

## 6. Batch plan

**Wave 1 — seed curado (`memory_core_seed.sql`, ~60–80 rows, aplicação manual Cris):**

- **Batch A — Core operating memory → `memory_items` (~15 rows, tag `batch:A`):** RAW-first · nunca-SLIM · production safety (receiver nunca `python3` direto; pausar daemon E cron; restore-first) · nenhum backtest sério sem RAW mapping+manifest · ordem de tarefas atual (Supabase ACTIVE · XAU 15M/SHORT deferred) · arquitetura de memória Agentic OS (camadas: CLAUDE.md/MEMORY/git/Supabase/RAW) · CLOSE-ONLY-CAUSAL universal · episódio = unidade de análise · painel completo sempre · trava OOS/cross-asset · devil's advocate full-time · runtime estreito zero auto-trading.
- **Batch B — Decisions → `decisions` (~12 rows, `decision_key` prefixo `core_`):** supabase_is_index_not_source_of_truth · trading_data_not_in_claude_memory · product_private_boundary · external_commercialization_deferred (P0 compliance) · xau_15m_before_short · runtime_no_auto_trading · l2_bpt_ok_final_2026_07_02 (USER_APPROVED_NOT_PRODUCTION) · xau_15m_swept_runner_approved_pending_slippage · xau_l1_cycle_paused · slim_pipeline_deleted_cluster_retained · memory_tiering_2026_07_02 · supabase_migration_priority_2026_07_02.
- **Batch C — Artifacts → `artifacts` (~14 rows, tag via `source_ref` `seed:memory_core_v1`):** SUPABASE_MEMORY_DATA_ARCHITECTURE · SUPABASE_IMPLEMENTATION_PLAN · SUPABASE_S2_SETUP_AND_MCP_REPORT · este plano · AGENTIC_OS_PORTABILITY_CHECKPOINT · PRODUCTION_LOGIC_REAUDIT · PRODUCTION_RUNBOOK · PRODUCT_PRIVATE_SPLIT_PLAN · PACKAGE_COMMERCIAL_READINESS_AUDIT · COLD_STORAGE_MANIFEST · SAFETY_LAYER_USAGE · 04_STRATEGY_STATUS_MASTER · MEMORY_ARCHIVE (2 cópias: memória local + docs/project_authority).
- **Batch D — Source registry → `source_registry` (~8 rows):** raiz RAW HD externo · datasets RAW XAU 15M/30M/1H (paths+checksums dos manifests) · cold storage archive 20260702 · manifests principais. **Só pointers.**
- **Batch E — Safety/agent runs (~6 rows):** `safety_reports` baseline 2026-07-02 (0/1/47) · `agent_runs` marcos (Agentic OS Fase 1–2, Supabase S1, S2+MCP validation, memory tiering, full migration plan).

**Wave 2 — corpus completo (após validação da Wave 1):** os 229 memory cards → `memory_items` via **SQL gerado por script local** (lê frontmatter + resumo, emite INSERTs idempotentes; mesmo formato do seed; sem tocar Supabase). Batches de ~50 rows por tipo (W2-user+feedback, W2-project ×3, W2-reference) para revisão humana viável. Cris aplica cada batch via SQL Editor. Normaliza os 17 cards sem `metadata.type`.

## 7. Proposed seed format

**SQL idempotente** (preferido sobre JSONL — aplicável direto no SQL Editor, sem loader):
- **Id determinístico:** `id = md5('seed:memory_core_v1:<tabela>:<slug>')::uuid` + `ON CONFLICT (id) DO NOTHING` → re-execução segura sem unique constraints extras e **sem alterar schema**.
- **`decisions`:** usa o unique natural `decision_key` + `ON CONFLICT (decision_key) DO NOTHING`.
- **Batch tag:** `memory_items.tags` inclui `{'seed:memory_core_v1','batch:A'}`; demais tabelas carregam `seed:memory_core_v1` em `source_ref` (artifacts/decisions), `path`-prefixo lógico não usado; `agent_runs.notes` e `safety_reports.report_path` registram o batch.
- **Transação única** por batch (`begin; ... commit;`) para aplicação atômica no SQL Editor.
- **Zero secrets, zero RAW, zero candles, zero logs, zero edge detalhado, zero broker data.**
- JSONL + loader fica como alternativa futura para Wave 2 se o volume tornar SQL manual impraticável (loader = script local que Cris roda; MCP continua read-only).

## 8. Validation plan (Fase M4, via MCP read-only)

1. **Counts por tabela** — esperado Wave 1: `memory_items≈15 · decisions≈12 · artifacts≈14 · source_registry≈8 · safety_reports=1 · agent_runs≈5`; `external_factor_events/market_context_snapshots/trade_journal_events/episode_context_links/retrieval_queries = 0`.
2. **Sample select por tabela** (limit 3–5, colunas-chave) — verificar encoding, tags, scope, status.
3. **Retrieval query simulada por tema** — ex.: “o que sei sobre validação de backtest?” → `select title, source_ref from memory_items where 'validation' = any(tags) or category='feedback' limit 10`; “estado XAU 15M?” → decisions + memory_items por tag; medir tamanho da resposta (contexto pequeno: <2KB por retrieval).
4. **Confirmar ausência de RAW bruto** — `select max(length(body)) from memory_items` (esperado < ~2000 chars); nenhum campo com arrays de OHLCV/logs.
5. **Confirmar MCP read-only** — `select current_user, current_setting('transaction_read_only', true)` → `supabase_read_only_user` / `on`.
6. **Safety report** — re-rodar `run_safety_report.py`; esperado baseline (BLOCKER=0).
7. Registrar os retrievals de teste em `retrieval_queries` (INSERT incluído no fim do script de validação **para o Cris aplicar**, ou deixado para fase futura — MCP não escreve).

## 9. Rollback (DEV only, manual via SQL Editor — nunca via MCP)

- **Por batch tag:** `delete from memory_items where 'seed:memory_core_v1' = any(tags);`
- **Por prefixo de decision_key:** `delete from decisions where decision_key like 'core_%' and source_ref like 'seed:memory_core_v1%';`
- **Por source_ref prefix:** `delete from artifacts where source_ref like 'seed:memory_core_v1%';` (idem agent_runs via notes, safety_reports via linha única conhecida).
- **Por id determinístico:** todos os ids são recomputáveis do seed file → delete exato linha a linha se necessário.
- Wave 2 usa tag própria (`seed:memory_full_w2`) → rollback independente da Wave 1.
- Rollback total DEV (último recurso): truncate das 5 tabelas seeded — **só com autorização explícita do Cris**.

## 10. Risks

- **Duplicação** (card + bullet do ARCHIVE + doc dizendo o mesmo) → mitigação: ARCHIVE entra só como pointer; 1 card = 1 row; decisions deduplicadas por `decision_key`.
- **Memória fria demais** (resumo perde o “porquê”) → mitigação: body preserva Why/How-to-apply resumidos; `source_ref` sempre aponta ao card integral; card local continua existindo (Supabase não substitui a memória local nesta fase — é espelho estruturado).
- **Perda de nuance** em cards longos (PRINCIPAL_1/2) → mitigação: PRINCIPALs entram como pointers com resumo de 3–5 linhas; nunca como substituto do ficheiro.
- **Classificação errada** (scope/status/category) → mitigação: Wave 1 pequena e revisável linha a linha; Wave 2 gerada por script com revisão amostral por batch antes de aplicar.
- **Inserir edge sensível** → mitigação: regra §5 (título+estado+resumo, scope=private); revisão explícita dos rows de estratégia antes do apply.
- **Confiar em Supabase como verdade** → mitigação: decision `supabase_is_index_not_source_of_truth` seeded no próprio Batch B; `authority_level` em source_registry; nenhum fluxo de validação lê edge do Supabase.
- **MCP read-only não escrever** — garantido por config (`--read-only`) + role Postgres validada; toda escrita = Cris via SQL Editor.
- **Drift memória-local ↔ Supabase** (pós-migração) → registrar como pendência para o checkpoint M5: protocolo de sync (quando um card muda, atualizar row) fica definido lá.

## 11. Acceptance criteria (Fase M1)

- [x] Plano criado (este doc).
- [x] Migration batches definidos (A–E Wave 1 + Wave 2).
- [x] Seed proposto (formato §7; ficheiro em M2 após aprovação).
- [x] Nenhum dado aplicado.
- [x] Nenhum runtime tocado.
- [x] Safety OK (baseline BLOCKER=0 · WARNING=1 pré-existente · INFO=47).

## Status block (2026-07-02, aprovado Cris)

- SUPABASE_MEMORY_FULL_MIGRATION = **ACTIVE_NEXT_BLOCK** (fase M1 concluída com este doc)
- XAU_15M_LONG_REGIME_DETECTOR = **DEFERRED_UNTIL_SUPABASE_MEMORY_FULL_MIGRATION_COMPLETE**
- XAU_SHORT = **DEFERRED_AFTER_XAU_15M**
- Proibido neste bloco: nova pesquisa estratégica · Fase 4C · comercialização · qualquer escrita via MCP · qualquer toque em produção/runtime/daemons/Telegram/receiver.
- Sequência: M1 (este plano) → aprovação → M2 seed → aprovação → M3 apply manual (Cris) → M4 validação MCP read-only → M5 checkpoint → só então XAU 15M LONG.
