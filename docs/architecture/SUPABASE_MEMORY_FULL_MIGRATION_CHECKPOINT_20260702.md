# SUPABASE MEMORY — FULL MIGRATION CHECKPOINT (2026-07-02)

## 1. Executive verdict

**SUPABASE_MEMORY_FULL_MIGRATION_COMPLETE** ✅

A migração total da memória durável do projeto (operacional, decisória, arquitetural e indexável) para o Supabase DEV está completa para o estado atual do projeto: 230/230 memory cards + camada core Wave 1, tudo aplicado manualmente pelo Cris, validado via MCP read-only, com zero escrita pelo Claude, zero RAW e zero secrets.

## 2. What is complete

- Schema aplicado em DEV (11 tabelas, `trading-system-memory-dev` / `vgfofofozptrtjvtuyzy`).
- MCP `supabase-dev` validado **read-only** (typo de ref corrigido; role Postgres verificada).
- Wave 1 aplicada e validada (44 rows: sínteses core, decisions, artifacts, source_registry, safety_reports, agent_runs).
- Wave 2 completa: **230/230 cards** migrados em 5 batches revisáveis, reconciliação por hard-abort no gerador do fecho.
- Retrieval validado (counts, samples por tag, filtros scope/status; payloads pequenos).
- Read-only enforcement validado em todas as sessões de validação (`supabase_read_only_user`, `transaction_read_only=on`).
- Safety baseline mantida fim-a-fim (BLOCKER=0 · WARNING=1 Caminho B TRUE_RISK · INFO=50).
- Zero RAW/candles/backtests/logs/journal/broker-data/TradingView-restricted/secrets em qualquer row.

## 3. Final counts (DEV, 2026-07-02)

| Tabela | Rows |
|---|---|
| memory_items | **240** (230 cards espelho 1:1 + 10 sínteses W1) |
| decisions | 8 |
| artifacts | 12 |
| source_registry | 7 |
| safety_reports | 1 |
| agent_runs | 6 |
| **TOTAL DEV** | **274** |
| Tabelas futuras (EF events, snapshots, journal, links, retrieval log, embeddings) | 0 (por design) |

Por wave (memory_items): core_v1 10 · wave2a 50 · wave2b 50 · wave2c 50 · wave2c_b 50 · wave2final 30.
Por scope: private **179** · product **61**.
Por status: active **135** · archived **62** · dormant **24** · deprecated **12** · superseded **4** · unknown_review **2** · paused **1**.

## 4. Migration waves summary

| Wave | Objetivo | Rows | Batch tag | Commit seed | Validação |
|---|---|---|---|---|---|
| 1 — core | Sínteses operacionais + decisions + artifacts + registry + safety + milestones | 44 (6 tabelas) | `seed:memory_core_v1` | `665c113` | `SUPABASE_MEMORY_MIGRATION_VALIDATION_20260702.md` (`9aed53a`) |
| 2A | 50 cards críticos/atuais (PRINCIPALs, protocolos, estratégias estado-atual, user) | 50 | `seed:memory_cards_wave2a` | `722755d` | `..._WAVE2A_VALIDATION...` (`e886e17`) |
| 2B | 43 feedback restantes + 7 project ativos | 50 | `seed:memory_cards_wave2b` | `475cf31` | `..._WAVE2B_VALIDATION...` (`8af0d6c`) |
| 2C-1 | 17 reference + 33 project históricos (archive/index) | 50 | `seed:memory_cards_wave2c` | `80d1bee` | `..._WAVE2C_VALIDATION...` (`ba57a47`) |
| 2C-b | 50 project históricos (L2 findings, 15M labs, linhagem 4H/1H) | 50 | `seed:memory_cards_wave2c_b` | `c276ba5` | `..._WAVE2C_B_VALIDATION...` (`3387f06`) |
| 2FINAL | 12 operacionais/config + 2 recuperados + 16 legacy card-a-card | 30 | `seed:memory_cards_wave2final` | `de3cc70` | `..._WAVE2FINAL_VALIDATION...` (`36f0742`) |

Todas: aplicação **manual Cris via SQL Editor** · validação MCP read-only · gerador Python versionado (`scripts/memory/generate_wave2*_seed.py`) · idempotente (md5-uuid + ON CONFLICT) · rollback comentado por tag.

## 5. Source of truth policy (reafirmada)

- **RAW/source continua a autoridade** (HD externo `GUTS_ LACIE/TradingData`, rulers, manifests).
- Supabase = **memory/index/retrieval** — nunca source of truth, **nunca valida backtest**.
- Market data massivo NÃO entra · TradingView restricted data NÃO entra · secrets NÃO entram.
- Todo derivado carrega `source_ref`; pointers de RAW só via `source_registry` (path+checksum+authority_level).

## 6. Retrieval protocol

- Claude recupera **slices pequenos** por tags/status/scope/category/source_ref (ex.: `tags @> ARRAY['batch:A']`, `status='active'`, `scope='product'`).
- **Nunca carregar o archive inteiro** — archived/deprecated ficam frios; hot = active + filtro específico.
- `source_ref` = drill-down para o card/doc integral (nuance mora na fonte).
- Consultas via **MCP read-only**; escrita **só manual (Cris/SQL Editor) ou processo futuro explicitamente autorizado**.

## 7. Sync/delta protocol

- Novos cards/docs/decisões relevantes → **delta seed** (`seed:memory_delta_<data>`), mesmo contrato: gerador versionado, id determinístico, ON CONFLICT, rollback comentado, zero secrets/RAW.
- **Nunca edição ad hoc** de rows sem registro; supersessão via `status='superseded'` em batch delta, nunca DELETE silencioso.
- Validação dupla: count no SQL Editor pós-Run (protocolo consolidado) + MCP read-only.
- Batch delta relevante → checkpoint/nota em docs.

## 8. Pending non-blockers

- 2 `unknown_review` aceitos (Decisão Cris): `project_naming_proposal`, `reference_files` — pendência leve.
- `feedback_strategy_validity_gate` = REVIEW_FUTURE_CANON_ALIGNMENT (WR≥70% vs canon lucro/expectancy).
- RLS policies product/private — fase futura (RLS habilitado sem policies).
- Embeddings/pgvector — deferred (só se busca semântica for necessária).
- Sync automation — deferred (delta manual por enquanto).
- Service role — **nunca** no Claude (permanente).
- Waves delta futuras conforme o projeto evoluir.

## 9. Safety/security

- MCP permanentemente read-only (`--read-only`); `transaction_read_only=on` e role `supabase_read_only_user` verificados em toda validação.
- Token via `SUPABASE_ACCESS_TOKEN` em env local — nunca em repo/config versionável/chat.
- Sem service role em qualquer fase. Sem secrets no repo (grep em todos os seeds: 0 hits).
- Safety scanner report-only calibrado (regra GUARDRAIL_CARD, commit `4af8e16`); baseline **0/1/50**; **Caminho B TRUE_RISK preservado de propósito** do início ao fim.

## 10. Gate status (2026-07-02)

- SUPABASE_MEMORY_FULL_MIGRATION = **COMPLETE** ✅
- XAU_15M_LONG_REGIME_DETECTOR = **GATE PODE SER REAVALIADO** — mas **NÃO abre automaticamente**; abertura só com autorização explícita do Cris (modo previsto: read-only / audit-first / no production / no Telegram / no serious backtest).
- XAU_SHORT = permanece **DEFERRED_AFTER_XAU_15M**.

## 11. Next recommended actions

A. Push deste checkpoint (autorização Cris).
B. MEMORY.md hot atualizado com ponteiro curto (feito nesta sessão — fora do repo git).
C. Abrir XAU 15M LONG Regime Detector Re-Adaptation em modo read-only/audit-first (decisão Cris).
D. XAU SHORT depois do XAU 15M.
E. Supabase RLS/embeddings/sync automation — deferred, blocos próprios sob autorização.

## 12. Rollback/recovery

- Rollback cirúrgico por batch tag (blocos comentados no fim de cada seed; 6 tags independentes).
- Restore = re-aplicar seeds idempotentes (0 duplicados; estado reconstituível do git).
- Audit trail completo: 16 commits + 10 docs versionados (git = registro durável).
- Tudo **DEV only** — produção nunca tocada.

## 13. Evidence appendix

- **Commits do bloco:** `d7d8bc9` (MCP validation) · `174932c` (plano) · `665c113` (W1 seed) · `9aed53a` (W1 valid.) · `0faefd4` (W1 checkpoint) · `722755d` (2A seed) · `e886e17` (2A valid.) · `4af8e16` (safety calibration) · `475cf31` (2B seed) · `8af0d6c` (2B valid.) · `80d1bee` (2C seed) · `ba57a47` (2C valid.) · `c276ba5` (2C-b seed) · `3387f06` (2C-b valid.) · `de3cc70` (2FINAL seed) · `36f0742` (2FINAL valid.).
- **Docs:** FULL_MIGRATION_PLAN · SEED_REVIEW · MIGRATION_VALIDATION · MIGRATION_CHECKPOINT (W1) · WAVE2_PLAN · WAVE2A/2B/2C/2C_B/2FINAL reviews+validations · S2_SETUP_AND_MCP_REPORT §5.e · SAFETY_LAYER_USAGE (calibrações).
- **Batch tags:** `seed:memory_core_v1` · `seed:memory_cards_wave2a/2b/2c/2c_b/2final`.
- **Validation counts finais:** 240 memory_items (10+50+50+50+50+30) · 274 rows DEV · 230/230 cards · scope 179/61 · status 135/62/24/12/4/2/1.
- **Safety:** BLOCKER=0 · WARNING=1 (Caminho B TRUE_RISK) · INFO=50 — constante.
- **No-write confirmation:** todas as 6 aplicações manuais (Cris/SQL Editor); Claude executou exclusivamente SELECTs read-only; role/transação read-only comprovadas em cada validação.
