# SUPABASE MEMORY — WAVE 2A VALIDATION (2026-07-02)

**Resultado: PASS ✅ — 50 cards críticos migrados e recuperáveis; base = 60 memory_items.**
**Modo:** validação 100% read-only via MCP (`supabase_read_only_user`). Zero escrita pelo Claude.

## 1. Aplicação (M3 Wave 2A)

`supabase/seeds/memory_cards_wave2a_seed.sql` (commit `722755d`, tag `seed:memory_cards_wave2a`) aplicado **manualmente pelo Cris** via SQL Editor no DEV, cópia direta do ficheiro via `pbcopy` (lição M3 Wave 1 aplicada) — **sucesso na 1ª tentativa**.

## 2. Counts esperados vs reais

| Métrica | Esperado | Real | |
|---|---|---|---|
| memory_items total | 60 (10 Wave 1 + 50 Wave 2A) | **60** | ✅ |
| rows com tag `seed:memory_cards_wave2a` | 50 | **50** | ✅ |
| scope private | 34 (2 W1 + 32 W2A) | **34** | ✅ |
| scope product | 26 (8 W1 + 18 W2A) | **26** | ✅ |
| status active | 55 (10 W1 + 45 W2A) | **55** | ✅ |
| status dormant | 4 | **4** | ✅ |
| status paused | 1 | **1** | ✅ |

## 3. Amostras recuperadas

Filtro por tag (`tags @> ARRAY['seed:memory_cards_wave2a']`, LIMIT 10) retornou os 10 primeiros cards na ordem do seed — PRINCIPAL_1/2/3, never_use_slim, no_oos_no_crossasset, validate_before_presenting, never_capture_screenshot, full_panel_always, devils_advocate_fulltime, close_only_causal — com scope/status exatos. Payload pequeno (~1 KB / 10 rows), adequado a retrieval de contexto por tag.

## 4. Role / read-only

`transaction_read_only = on` · `current_user = supabase_read_only_user` — verificados na mesma sessão dos SELECTs. Testes executados = exatamente os autorizados (counts, group by scope/status, sample por tag, read-only). Nenhum INSERT/UPDATE/DELETE/migration/schema/RLS.

## 5. Confirmação de conteúdo

Zero RAW/candles/logs/backtests/journal/secrets: rows = filename + frontmatter description (max 488 chars) + tags + source_ref + status. Corpo integral dos cards permanece **só** nos ficheiros locais (nuance preservada na fonte). Grep de secrets no seed: 0 hits (pré-review, plano §Anexo).

## 6. Safety report — ⚠️ 1 falso positivo NOVO a decidir

`BLOCKER=0 · WARNING=2 · INFO=47` (antes: 0/1/47).

- WARNING 1 (pré-existente, real/conhecido): `my-strategy/strategies/candidates/xau_4h_caminho_b_*` — SLIM em candidato de research privado.
- **WARNING 2 (NOVO, falso positivo):** `scripts/memory/generate_wave2a_seed.py:30` — o scanner `slim_policy` pattern-matched o **filename** `feedback_never_use_slim_features.md` na lista de cards do gerador. O gerador não consome SLIM como dado/validação; a linha referencia o card que **proíbe** SLIM. Ironia registrada.
- **Ação proposta (decisão do Cris, não executada):** adicionar `scripts/memory/generate_wave2a_seed.py` (ou o padrão "filename de memory card em lista de migração") ao contexto autorizado do scanner slim_policy → voltaria a 0/1/47. Alterar a safety layer está fora do escopo autorizado deste bloco; até lá, baseline operacional = **0/1/47 + 1 falso positivo documentado**.

## 7. Próximos batches (após aprovação desta validação)

- **Wave 2B** — feedback restantes ativos + project cards vivos (~2 sub-batches ≤50; superseded → status próprio). Próximo passo imediato.
- **Wave 2C** — reference restantes + project histórico/refutado como archive/index.
- **Wave 2D** — 16 legacy/no-metadata, revisão card a card, `UNKNOWN_REVIEW` quando duvidoso.
- **Gate estratégico:** XAU 15M LONG Regime Detector **continua bloqueado** (2A validada satisfaz o critério mínimo do gate SE o Cris decidir liberar; caso contrário, segue até Wave 2 completa). XAU_SHORT = DEFERRED_AFTER_XAU_15M.
