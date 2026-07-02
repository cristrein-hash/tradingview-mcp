# SUPABASE MEMORY — WAVE 2B VALIDATION (2026-07-02)

**Resultado: PASS ✅ — 100 dos 229 cards migrados; base = 110 memory_items.**
**Modo:** validação 100% read-only via MCP (`supabase_read_only_user`). Zero escrita pelo Claude.

## 1. Aplicação (M3 Wave 2B)

`supabase/seeds/memory_cards_wave2b_seed.sql` (commit `475cf31`, tag `seed:memory_cards_wave2b`) aplicado **manualmente pelo Cris** via SQL Editor (query `20260702_memory_cards_wave2b_seed`), cópia via `pbcopy` do ficheiro — **sucesso na 1ª tentativa**.

## 2. Counts esperados vs reais

| Métrica | Esperado | Real | |
|---|---|---|---|
| memory_items total | 110 (10 W1 + 50 W2A + 50 W2B) | **110** | ✅ |
| tag wave2b | 50 | **50** | ✅ |
| tag wave2a (intacta) | 50 | **50** | ✅ |
| scope private | 55 | **55** | ✅ |
| scope product | 55 | **55** | ✅ |
| status active | 105 | **105** | ✅ |
| status dormant / paused | 4 / 1 | **4 / 1** | ✅ |

## 3. Amostras recuperadas

Filtro por tag wave2b (LIMIT 10): 10 primeiros cards na ordem do seed (anticipate_platform_constraints → deep_source_reading), scope/status exatos, payload pequeno. Idempotência preservada (2A intacta; zero colisões).

## 4. Role / read-only

`transaction_read_only = on` · `current_user = supabase_read_only_user` na mesma sessão. Só os testes autorizados; nenhum INSERT/UPDATE/DELETE/migration/schema/RLS pelo Claude.

## 5. Confirmação de conteúdo

Zero RAW/candles/logs/backtests/journal/secrets — rows = filename + frontmatter description + tags + source_ref + status; grep de secrets no seed: 0 hits (pré-review).

## 6. Safety report

**BLOCKER=0 · WARNING=1 · INFO=50** — WARNING único = Caminho B TRUE_RISK (preservado de propósito). Gerador 2B não dispara o scanner.

## 7. Item marcado para revisão futura (decisão Cris 2026-07-02)

- `feedback_strategy_validity_gate` ("válida se win% ≥ 70%") — **REVIEW_FUTURE_CANON_ALIGNMENT**: possível tensão com canon posterior (engine = lucro/expectancy; FundedNext WR 50–60%). Mantido migrado fielmente como active; supersessão futura, se decidida, via batch delta + card local.

## 8. Próximos batches

- **Wave 2C** — reference restantes (19) + project históricos/refutados/sessão (~96) como archive/index com status próprio (superseded/refuted/archived), em sub-batches ≤50. Próximo passo imediato.
- **Wave 2D** — ~16 legacy/no-metadata, revisão card a card, `UNKNOWN_REVIEW` quando duvidoso.
- Restantes após 2B: **129 cards**.
- **Gate estratégico:** XAU 15M LONG Regime Detector e XAU SHORT **continuam bloqueados**; nenhuma ação estratégica até migração total ou decisão explícita do Cris.
