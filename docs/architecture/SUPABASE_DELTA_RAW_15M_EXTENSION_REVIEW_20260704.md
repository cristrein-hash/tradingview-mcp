# SUPABASE DELTA — RAW 15M EXTENSION · REVIEW (2026-07-04)

**Seed:** `supabase/seeds/memory_delta_raw_15m_extension_20260704.sql` · batch tag `seed:memory_delta_raw_15m_extension_20260704` · **NÃO APLICADO** (MCP read-only; aplicação = manual Cris via SQL Editor, DEV `trading-system-memory-dev`).

## Conteúdo (5 rows `memory_items`, todas `project/internal/active`)
1. **raw-15m-extension-complete** — cobertura 2024-05-25→2026-07-03 16:30 UTC, 9 blocos, pointers HD/manifest/commits.
2. **system-a-virgin-killcheck-inconclusive** — N=0, janela 100% BEAR, critérios congelados, status inalterado.
3. **system-a-stand-aside-bear** — observação comportamental (NÃO validação), com as negações explícitas do Cris (não validado/refutado/produção/SHORT).
4. **htf-staleness-deferred** — cobertura htf_4H/1D, causa, impacto nulo atual, bloco futuro.
5. **source-guard-calibrated** — 2 classes de falso-positivo corrigidas, política intacta, PASS 7/7.

## Conformidade
Idempotente (md5(seed_key)::uuid + `on conflict (id) do nothing`) · re-executável · zero RAW/candles/logs/secrets/edge-params · só títulos/resumos/pointers (path+sha+commit) · rollback comentado no ficheiro (delete por batch tag) · formato idêntico às waves aprovadas. Validação: estrutural (aspas/parens/contagens; sqlglot indisponível no ambiente — rodar sqlglot/psql dry-run antes de aplicar se desejado). **Lembrete operacional das waves: copiar via `pbcopy < arquivo` (nunca do chat) e conferir count pós-Run:** `select count(*) from memory_items where tags @> array['seed:memory_delta_raw_15m_extension_20260704'];` → esperado **5**.

## Quando aplicar
Opção registrada para o Cris (sem pressa): aplicar junto com o próximo lote de deltas pendentes (há também o delta L1-V1 e decisões de 2026-07-03 ainda não sedimentados — podem ser consolidados num próximo seed se preferir).
