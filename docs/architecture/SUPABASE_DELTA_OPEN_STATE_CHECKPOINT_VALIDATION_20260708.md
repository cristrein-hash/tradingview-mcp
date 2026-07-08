# Supabase Delta Validation — Open State Checkpoint 2026-07-08

**Cris 2026-07-08.** Validação da aplicação do seed `supabase/seeds/memory_delta_open_state_checkpoint_20260708.sql` (autorizada). Aplicado via `scripts/supabase/apply_memory_delta.py` (guardas G1-G7); validado via MCP **read-only**.

## Aplicação
- Comando: `python3 scripts/supabase/apply_memory_delta.py supabase/seeds/memory_delta_open_state_checkpoint_20260708.sql`
- Resultado: **`APLICADO: memory_items 281→286 · rows com tag: 5/5 · OK`** (G7 read-back PASS).
- Guardas: G1-G6 PASS (seed commitado, 1 INSERT em `memory_items`, 5 rows, tag `seed:memory_delta_open_state_checkpoint_20260708`). Auditoria em `supabase/seeds/APPLY_LOG.md`.
- SUPABASE_ACCESS_TOKEN só do env (nunca impresso). Zero RAW/candles/secrets. Zero DDL/RLS/schema.

## Validação MCP (read-only)
- `current_user = supabase_read_only_user` · `transaction_read_only = on` (conexão read-only confirmada).
- `count(tag) = 5` · `count(memory_items) = 286` (281→286 consistente).
- Bodies 577–1375 chars (todos <2KB — **zero dados massivos**). Todas `status=active`, `scope=product`.

## Rows aplicadas (5)
| # | category | status | title |
|---|---|---|---|
| 1 | project | active | L2/BPT XAU 4H trend-exit / regime-flip = **USER_APPROVED_OFFICIAL_NOT_PRODUCTION** |
| 2 | reference | active | XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 = **ACTIVE** |
| 3 | project | active | XAU 15M N96 ENTRY ENGINE = **USER_APPROVED_NOT_PRODUCTION** |
| 4 | project | active | XAU 15M LONG swept-runner = **RESEARCH_BASE_NOT_OFFICIAL** (ex-OFICIAL_FN revogado) |
| 5 | project | active | Open state checkpoint 2026-07-08 (git sync, untracked KEEP_COMMIT) |

## Estado sincronizado
Supabase memory/index agora reflete o estado pushed (`08b5b61`): L2/BPT trend-exit oficial-not-production · swept-runner research-base-not-official · N96 approved-not-production · protocolo 15M active · open-state checkpoint.

## Rollback (se necessário, só Cris)
```
delete from memory_items where tags @> array['seed:memory_delta_open_state_checkpoint_20260708'];
```

## Não tocado
Produção · runtime · Telegram · RAW · schema/RLS. MCP read-only. Nenhum lab novo aberto.
