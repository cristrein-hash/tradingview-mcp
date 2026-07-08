# Supabase Delta Review — Open State Checkpoint 2026-07-08

**Cris 2026-07-08.** Review do seed `supabase/seeds/memory_delta_open_state_checkpoint_20260708.sql`. **NÃO aplicado.** Aplicação só com autorização explícita.

## Seed
- `seed:memory_delta_open_state_checkpoint_20260708` · **4 rows** · idempotente (`on conflict (id) do nothing`) · rollback comentado no topo.
- Só `insert into memory_items` (nenhum UPDATE/DELETE/DDL). MCP segue read-only.

## Rows
| # | id-slug | category | conteúdo |
|---|---|---|---|
| 1 | n96-approved | project | XAU 15M N96 = USER_APPROVED_NOT_PRODUCTION + intra-BEAR filter + review-layers |
| 2 | protocol-active | reference | XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 = ACTIVE + blockers + regra-mãe |
| 3 | l2bpt-trend-exit | project | L2/BPT trend-exit = EXPLORATORY_NOT_APPROVED / NOT_FOR_DECISION + caveats honestos |
| 4 | open-state | project | Git synced (b517312), untracked KEEP_COMMIT, decisões abertas |

## Guardas cumpridas
- **Zero RAW/candles/secrets.** Zero outputs massivos (só sumários/decisões).
- Cada row com `source_ref` a docs/commits. `status='active'`.
- **NOT_FOR_DECISION** explícito no trend-exit (não é resultado validado).
- Não altera rows existentes (só INSERT idempotente novo).

## Como aplicar (só com autorização Cris)
```
python scripts/supabase/apply_memory_delta.py --seed supabase/seeds/memory_delta_open_state_checkpoint_20260708.sql
```
(Guardas G1-G7: seed commitado primeiro; só INSERT idempotente em memory_items; read-back; APPLY_LOG. DELETE/UPDATE/schema = só Cris.)

## Estado
Seed criado e commitado (parte do checkpoint). **NÃO aplicado ao Supabase.** Aguarda autorização explícita.
