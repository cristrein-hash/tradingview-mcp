# SUPABASE MEMORY SEED — PRE-REVIEW (2026-07-02)

**Ficheiro:** `supabase/seeds/memory_core_seed.sql` · **Batch tag:** `seed:memory_core_v1` · **Estado: CRIADO, NÃO APLICADO.**
**Zero conexão/mutation Supabase nesta fase. MCP permanece read-only** (única interação: 1 SELECT read-only validando o cast `md5(...)::uuid` no Postgres DEV — funciona; role `supabase_read_only_user` confirmada).
**Aplicação futura (M3):** manual pelo Cris via SQL Editor, DEV apenas, após aprovação deste review.

## 1. Rows por tabela (total 44 — teto aprovado era 60–80; Wave 1 deliberadamente curada)

- `memory_items` — **10** (9 Batch A + 1 Batch E contexto do WARNING)
- `decisions` — **8** (Batch B)
- `artifacts` — **12** (Batch C)
- `source_registry` — **7** (Batch D)
- `safety_reports` — **1** (Batch E)
- `agent_runs` — **6** (Batch E, resumos de milestone, não logs)
- Não usadas (fases posteriores): `external_factor_events`, `market_context_snapshots`, `trade_journal_events`, `episode_context_links`, `retrieval_queries`, `memory_embeddings` — **0 rows**, conforme spec.

## 2. Decision keys (8, prefixo `core_`, unique natural `decision_key`)

1. `core_supabase_memory_architecture_approved`
2. `core_product_private_boundary_approved`
3. `core_external_commercialization_deferred`
4. `core_production_runtime_no_auto_trading`
5. `core_ef_v2_live_passive_context_daemon`
6. `core_xau_15m_regime_readaptation_before_short`
7. `core_supabase_migration_before_strategy_work`
8. `core_safety_layer_report_only_calibrated`

Todas: `status='approved'`, `approved_by='Cris'`, `decision_date='2026-07-02'`, `source_ref` com batch tag + doc de origem, `commit_sha=174932c` (full sha).

## 3. Artifacts (12 pointers — path + sha256 + commit; zero conteúdo embutido)

1. SUPABASE_MEMORY_DATA_ARCHITECTURE.md (design_doc)
2. SUPABASE_IMPLEMENTATION_PLAN.md (plan)
3. SUPABASE_S2_SETUP_AND_MCP_REPORT.md (report)
4. SUPABASE_MEMORY_FULL_MIGRATION_PLAN.md (plan)
5. AGENTIC_OS_PORTABILITY_CHECKPOINT_20260702.md (checkpoint)
6. PRODUCTION_LOGIC_REAUDIT_20260702.md (audit)
7. PRODUCTION_RUNBOOK_20260702.md (runbook)
8. PRODUCT_PRIVATE_SPLIT_PLAN.md (plan)
9. PACKAGE_COMMERCIAL_READINESS_AUDIT.md (audit)
10. COLD_STORAGE_MANIFEST_20260702.md (manifest)
11. SAFETY_LAYER_USAGE.md (doc)
12. 04_STRATEGY_STATUS_MASTER.md (status_master — pointer; edge detalhado fica no repo)

Checksums sha256 calculados no estado do repo em `174932c` (drift futuro do doc = esperado; checksum regista o estado na migração).

## 4. Exemplos de memory_items (título · scope/visibility · categoria)

- "RAW/source first — hierarquia de fontes de dados" · product/internal · feedback
- "Proibido SLIM/proxy como validacao" · product/internal · feedback
- "Nenhum backtest serio sem manifest/mapping/predicados/sanity" · product/internal · feedback
- "Production safety — regras operacionais duras" · product/internal · feedback
- "Supabase = index/store/retrieval, nunca source of truth" · product/internal · architecture
- "Ordem de tarefas vigente (2026-07-02, aprovada Cris)" · **private/private** · project
- "Safety baseline — contexto do unico WARNING" · **private/private** · project

Bodies = resumos de 1–4 frases; nenhum parâmetro de edge; todo row com `source_ref` apontando ao card/doc de origem.

## 5. Classificação scope

**PRIVATE (2 rows memory_items):**
- `current-task-order-2026-07-02` (status operacional do Cris)
- `safety-baseline-warning-context` (menciona candidato de estratégia privada)

**PRODUCT (8 rows memory_items):** raw-source-first · no-slim-proxy-validation · no-backtest-without-manifest · production-safety · no-prod-change-without-approval · trading-data-not-in-claude-memory · supabase-index-not-source-of-truth · agentic-os-memory-architecture. (Método/engine/safety genéricos — sem edge.)

Decisions/artifacts/source_registry/safety_reports/agent_runs não têm coluna scope no schema; conteúdo revisado: decisões citam estratégias só por nome+estado (sem parâmetros); artifacts/registry são pointers puros.

## 6. Confirmação de conteúdo seguro

- **Zero RAW/candles/OHLCV** — nenhuma barra, preço ou série; grep `candle` → 2 hits, ambos **falsos positivos** (texto de política declarando que candles NÃO entram: header do seed + body do item "trading data não vive na memória").
- **Zero logs vivos** — cold storage entra só como path+sha256 do arquivo `.tar.zst`.
- **Zero secrets** — grep `SUPABASE_SERVICE_ROLE_KEY|sbp_|eyJ|password|api_key` → **0 hits**; grep termos de corretora → **0 hits**.
- **Zero trade journal real, zero dados TradingView restritos, zero screenshots/plots, zero parâmetros de edge** (estratégias aparecem só como nome+estado+pointer).
- **Sem dependência de pgvector · sem schema change · sem alteração de RLS.**
- Cast `md5(text)::uuid` **testado no Postgres DEV via SELECT read-only** → uuid válido (mecanismo de idempotência confirmado no banco alvo).

## 7. Idempotência

- Todos os 6 INSERTs: id determinístico `md5('seed:memory_core_v1:<tabela>:<slug>')::uuid` + `ON CONFLICT (id) DO NOTHING` (7 cláusulas: 6 por id + decisions também protegida por `ON CONFLICT (decision_key)` — nota: decisions usa a cláusula por decision_key; id determinístico presente na mesma linha).
- Cada batch em transação própria (`begin; … commit;`) — aplicável batch a batch ou o ficheiro inteiro de uma vez; re-execução completa = 0 duplicados.

## 8. Rollback proposto (DEV only, manual via SQL Editor, sob autorização — NUNCA via MCP)

```sql
begin;
delete from memory_items    where 'seed:memory_core_v1' = any(tags);
delete from decisions       where source_ref like 'seed:memory_core_v1%';
delete from artifacts       where source_ref like 'seed:memory_core_v1%';
delete from agent_runs      where notes like 'seed:memory_core_v1%';
delete from safety_reports  where id = md5('seed:memory_core_v1:safety_reports:baseline-2026-07-02')::uuid;
delete from source_registry where id in ( /* 7 ids determinísticos — lista completa no fim do seed */ );
commit;
```
Nota: `source_registry` e `safety_reports` não têm coluna de tag → rollback por id determinístico (recomputável do seed; bloco comentado completo no fim de `memory_core_seed.sql`).

## 9. Verificações executadas (M2)

- Grep padrões perigosos → PASS (0 hits reais; 2 falsos positivos documentados em §6).
- `python3 scripts/safety/run_safety_report.py` → **BLOCKER=0 · WARNING=1 (pré-existente) · INFO=47** — baseline inalterada.
- `git status --short` → working tree limpo exceto untracked vivos esperados (`.mcp.json`, `alert-bridge/logs/`).
- SELECT read-only no DEV validando mecanismo md5-uuid → PASS.

## 10. Critério de aceitação M2

- [x] Seed criado (`supabase/seeds/memory_core_seed.sql`, 44 rows)
- [x] NÃO aplicado — zero INSERT executado no banco
- [x] Zero conexão de escrita / mutation Supabase (MCP read-only confirmado)
- [x] Zero runtime/produção/RAW tocado
- [x] Seed revisável (este doc + SQL comentado, batches separados)
- [x] Rollback documentado (§8 + bloco no seed)
- [x] Safety report OK

**Próximo passo (requer aprovação do Cris):** M3 — aplicação manual do seed via SQL Editor no DEV, batch a batch ou integral.
