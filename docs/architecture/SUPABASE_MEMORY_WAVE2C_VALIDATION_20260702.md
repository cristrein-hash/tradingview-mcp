# SUPABASE MEMORY — WAVE 2C VALIDATION (sub-batch 1, 2026-07-02)

**Resultado: PASS ✅ — 150 dos 229 cards migrados; base = 160 memory_items.**
**Modo:** validação 100% read-only via MCP (`supabase_read_only_user`). Zero escrita pelo Claude.

## 1. Aplicação (M3 Wave 2C sub-batch 1) — com incidente registrado

- `supabase/seeds/memory_cards_wave2c_seed.sql` (commit `80d1bee`, tag `seed:memory_cards_wave2c`) aplicado **manualmente pelo Cris** via SQL Editor (`20260702_memory_cards_wave2c_seed`).
- **Incidente (resolvido, capturado pela validação):** na 1ª confirmação de aplicação, a validação M4 retornou **FAIL** — total 110, wave2c=0, estado pré-2C intacto. Causa-raiz: **Run não tinha sido executado** no SQL Editor (paste feito, execução esquecida). Nenhum doc foi criado com resultado falso; validação repetida após Run real → PASS. **Lição:** a validação M4 pós-apply é obrigatória exatamente para isto — "apliquei" só conta depois do count bater; o passo 5 do protocolo (verificação imediata no próprio SQL Editor: `SELECT count(*) ... where tags @> ARRAY['<tag>']`) fica **padrão para todos os batches futuros**.

## 2. Counts esperados vs reais

| Métrica | Esperado | Real | |
|---|---|---|---|
| memory_items total | 160 (10 W1 + 50×3 waves) | **160** | ✅ |
| tag wave2c | 50 | **50** | ✅ |
| tag wave2a / wave2b (intactas) | 50 / 50 | **50 / 50** | ✅ |
| scope private / product | 102 / 58 | **102 / 58** | ✅ |
| status active | 121 | **121** | ✅ |
| status archived / deprecated / dormant / paused | 22 / 11 / 5 / 1 | **22 / 11 / 5 / 1** | ✅ |

## 3. Amostras recuperadas

Filtro por tag wave2c (LIMIT 10): 10 primeiros na ordem do seed (bubbles_auction_theory → microstructure_philosophy), incluindo `reference_d2r_daily_logs` corretamente **archived** e scopes product/private exatos. Payload pequeno.

## 4. Role / read-only / conteúdo

`transaction_read_only = on` · `current_user = supabase_read_only_user`. Só os testes autorizados; zero INSERT/UPDATE/DELETE/migration/schema/RLS pelo Claude. Zero RAW/candles/logs/backtests/journal/secrets (rows = filename + description + tags + source_ref + status; grep pré-apply 0 hits).

## 5. Safety report

**BLOCKER=0 · WARNING=1 · INFO=50** — WARNING único = Caminho B TRUE_RISK (preservado).

## 6. Próximos passos

- **Wave 2C sub-batch 2** — ~64 project históricos restantes (labs L2/BPT concluídos incl. `l2_bpt_overfade_irreducible`, 15M labs/estudos, D2R/pipeline, incidentes resolvidos, SMC/EUR audits, roadmaps) como archive/index, ≤50 por batch (serão 2 batches ou 1 batch de ~50 + resto no seguinte). Próximo passo imediato.
- **Wave 2D** — ~15–16 legacy/no-metadata, revisão card a card, `UNKNOWN_REVIEW` quando duvidoso.
- **Depois:** checkpoint final da migração total.
- **Gate estratégico:** XAU 15M e XAU SHORT continuam bloqueados.

Progresso: **150/229 cards (65,5%)** + 44 rows Wave 1. Restam **79**.
