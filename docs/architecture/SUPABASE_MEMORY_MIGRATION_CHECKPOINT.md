# SUPABASE MEMORY MIGRATION — CHECKPOINT FINAL (2026-07-02)

**Bloco:** SUPABASE_MEMORY_FULL_MIGRATION (prioridade aprovada Cris 2026-07-02).
**Estado: WAVE 1 COMPLETE ✅ — Supabase DEV operacional como store/index/retrieval de memória.**

## 1. O que foi feito (M0–M5)

| Fase | Entrega | Commit |
|---|---|---|
| M0 | Push checkpoint (`d7d8bc9` MCP validation) | — |
| M1 | Inventário total (229 cards + 47 docs) + plano aprovado | `174932c` |
| M2 | Seed curado 44 rows, idempotente, pré-review | `665c113` |
| M3 | **Aplicação manual pelo Cris** via SQL Editor (DEV) | — (fora do git) |
| M4 | Validação read-only via MCP: 44/44, PASS | `9aed53a` |
| M5 | Este checkpoint | (este commit) |

Docs do bloco: `SUPABASE_MEMORY_FULL_MIGRATION_PLAN.md` · `SUPABASE_MEMORY_SEED_REVIEW_20260702.md` · `SUPABASE_MEMORY_MIGRATION_VALIDATION_20260702.md` · seed em `supabase/seeds/memory_core_seed.sql`.

## 2. Estado do Supabase DEV (`trading-system-memory-dev` / `vgfofofozptrtjvtuyzy`)

- **44 rows** (tag `seed:memory_core_v1`): 10 memory_items (8 product/internal + 2 private/private) · 8 decisions (`core_*`, approved) · 12 artifacts (pointers+sha256@`174932c`) · 7 source_registry (RAW roots/cold storage, só pointers) · 1 safety_reports (baseline 0/1/47) · 6 agent_runs (milestones).
- Tabelas futuras (EF events, snapshots, journal, links, retrieval log, embeddings): **0 rows / não usadas**.
- **MCP `supabase-dev`: read-only permanente** (role `supabase_read_only_user`, `transaction_read_only=on` verificado em M4). Toda escrita = manual Cris via SQL Editor. Sem service role.
- RLS habilitado nas 11 tabelas, **sem policies** (fase futura product/private).

## 3. Invariantes (não mudam com este bloco)

- **RAW/source = fonte de verdade.** Supabase = index/store/retrieval — **não valida backtest, não é data lake**.
- Zero RAW/candles/logs/backtests/journal real/secrets no Supabase — só título/resumo/status/pointer/checksum.
- Edge sensível: nome+estado+source_ref (`scope=private`); parâmetros ficam nos cards/docs locais.
- Memória local (MEMORY.md + cards) **continua operacional e primária nesta fase**; Supabase é espelho estruturado consultável — não substitui o fluxo de memória do Claude Code ainda.

## 4. Protocolo de sync (mínimo, até Wave 2)

1. Mudança durável relevante (decisão nova, estratégia muda de estado, doc-autoridade novo) → continua indo para card local + doc git (fluxo atual, inalterado).
2. Acúmulo dessas mudanças → **batch SQL incremental** com tag própria (`seed:memory_delta_<data>`), mesmo formato do seed (md5-uuid + ON CONFLICT), aplicado pelo Cris via SQL Editor sob demanda.
3. Nunca editar rows do Supabase à mão sem tag/registro; nunca via MCP.
4. Row obsoleta → `status='superseded'` no próximo batch (UPDATE manual pelo Cris), nunca DELETE silencioso.

## 5. Pendências / gates (decisões do Cris, não do assistente)

- **Wave 2 — 229 memory cards** → SQL gerado por script local, batches revisáveis ~50 rows, tag `seed:memory_full_w2` (plano §6). **Timing em aberto: antes, em paralelo, ou depois do XAU 15M — decisão do Cris.**
- **RLS policies** product/private (design no fim do `schema.sql`) — fase futura.
- **Retrieval tooling** (get_market_context, log em retrieval_queries) — S7 do implementation plan, futuro.
- pgvector/embeddings — só se busca semântica for necessária.

## 6. Status master do bloco (2026-07-02)

- SUPABASE_MEMORY_FULL_MIGRATION: **WAVE_1_COMPLETE · CHECKPOINT_CREATED** (aguarda aprovação M5 do Cris)
- XAU_15M_LONG_REGIME_DETECTOR: **DEFERRED até aprovação deste M5** → depois **PODE ABRIR**
- XAU_SHORT: **DEFERRED_AFTER_XAU_15M**
- Produção/runtime/daemons/Telegram/RAW: **intocados durante todo o bloco**
- Safety: BLOCKER=0 · WARNING=1 (pré-existente, contextualizado no seed) · INFO=47
