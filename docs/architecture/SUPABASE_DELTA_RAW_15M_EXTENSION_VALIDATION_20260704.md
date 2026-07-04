# SUPABASE DELTA — RAW 15M EXTENSION · VALIDAÇÃO (2026-07-04)

**Bloco:** SUPABASE_DELTA_RAW_15M_EXTENSION_APPLY_20260704 · **VALIDATED ✅**

## Aplicação
Manual pelo Cris (SQL Editor, projeto DEV `trading-system-memory-dev`), via `pbcopy` direto do arquivo `supabase/seeds/memory_delta_raw_15m_extension_20260704.sql`; count pós-Run confirmado pelo Cris no SQL Editor ANTES desta validação. **Zero escrita pelo Claude** (nenhum INSERT/UPDATE/DELETE/DDL nesta sessão; MCP usado só para SELECT).

## Validação MCP read-only
- **Role:** `supabase_read_only_user` ✅ · **transaction_read_only = on** ✅
- **Count:** esperado 5 · **real 5** ✅ (tag `seed:memory_delta_raw_15m_extension_20260704`)
- **Rows (title · scope · status):**
  1. HTF 4H/1D staleness = DEFERRED (exige novas coletas de chart) · product · active
  2. RAW 15M extension COMPLETE — cobertura 2024-05-25 → 2026-07-03 16:30 UTC (9 blocos) · product · active
  3. Sistema A EMA-SHAKEOUT — kill-check virgem = VIRGIN_INCONCLUSIVE_N_LT_20 (N=0) · product · active
  4. Sistema A stand-aside em BEAR = PASS_BEHAVIORAL_OBSERVATION_NOT_VALIDATION · product · active
  5. Source guard 15M calibrado (2 classes de falso-positivo) — política RAW-first intacta · product · active
- **Sem dados massivos:** bodies 367-496 chars (só memória/index + pointers path/sha/commit); **zero RAW/candles, zero secrets, zero dados de broker** ✅

## Safety
BLOCKER=0 · WARNING=1 (Caminho B TRUE_RISK, esperado) · INFO=50.

## Próxima ação
Delta sedimentado. Próximo bloco = decisão Cris entre as opções registradas (Decisão 5): **A** Lab B r2 estrutural · **B** F4 sizing/exposure como camada de conta · **C** aguardar janela não-BEAR para o kill-check real do Sistema A · **D** HTF 4H/1D extension plan. (Preferência inicial declarada do Cris: A ou B.)
