# SUPABASE MEMORY — WAVE 2 PLAN (migração dos 229 memory cards, 2026-07-02)

**Bloco:** SUPABASE_MEMORY_FULL_MIGRATION — Wave 2 (após Wave 1 COMPLETE, checkpoint aprovado).
**Regras invariantes:** aplicação SEMPRE manual (Cris/SQL Editor, DEV) · MCP read-only · zero RAW/candles/logs/journal/secrets · RAW = fonte de verdade · Supabase = index/store/retrieval.

## 1. Total de cards

**229 memory cards** em `~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/` (excluídos: MEMORY.md, MEMORY_ARCHIVE.md, backup pré-tiering, 4 strays não-memória `_compute.py`/`_ohlcv*.py`/`_tmp_ohlcv.json`).

## 2. Classificação por tipo

- **user:** 2 · **feedback:** 77 (74 `feedback_` + 3 `PRINCIPAL_`) · **project:** 128 · **reference:** 22
- **legacy/formato antigo:** 17 cards sem `metadata.type` explícito no formato novo (5 feedback_, 9 project_, 2 reference_, 1 user_) — tipo inferível do prefixo; tratados com cuidado extra na Wave 2D.

## 3. Regras de inclusão/exclusão

**Entra (por card):** 1 card = 1 row em `memory_items` — `title` = filename (identificador estável usado nos [[links]]), `body` = **frontmatter description apenas** (resumo curado; nunca o corpo do card), `category` = type, `source_ref` = path do card local, `status` correto, tags com batch tag + wave + type.

**Nunca entra:** corpo integral de cards (fica no card local — nuance/Why/How preservados na fonte) · parâmetros de edge/thresholds · RAW/candles/backtests/logs/journal real · broker/account data · secrets · TradingView restricted data · dados massivos. O gerador (`scripts/memory/generate_wave2a_seed.py`) aborta se detectar padrão proibido na description.

**Card sem description utilizável:** override manual explícito (ex.: PRINCIPAL_3 stub) ou `UNKNOWN_REVIEW` — nunca inserção cega.

## 4. Batches propostos

- **Wave 2A — 50 cards críticos/atuais (este seed, EXATO):** 3 PRINCIPAL + 23 protocolos permanentes hot + 4 production-safety/regras operacionais + 11 estratégias estado-atual + 5 produção dormant/paused + 2 user + Supabase migration card + fontes gold EF. Composição: 28 feedback · 17 project · 3 reference · 2 user; 18 product/internal · 32 private/private; 45 active · 4 dormant · 1 paused.
- **Wave 2B — project/feedback ativos (~2 sub-batches ≤50):** feedback restantes ainda operacionais + project cards vivos (L2/BPT knowledge, 15M labs, EF, RTSE, Reader, arquitetura). Superseded/retratado → status `superseded`/`deprecated`.
- **Wave 2C — reference/histórico (~2 sub-batches ≤50):** reference restantes (lookup) + project históricos/refutados/invalidados/sessão — status `archived`/`superseded`/`refuted`; preservados como índice de pesquisa, **não** hot memory.
- **Wave 2D — legacy/no-metadata (16 restantes):** revisão card a card (1 dos 17, `user_role`, já migra na 2A com tipo explícito); tipo normalizado na migração; dúvida → `UNKNOWN_REVIEW`, não inserir.

Listas exatas de 2B/2C/2D geradas na abertura de cada batch (com status por card revisado); contagens acima são aproximadas exceto 2A.

## 5. Tabela de mapeamento

- **Todos os cards → `memory_items`** (são memórias; 1:1).
- Nenhuma outra tabela é tocada na Wave 2 (decisions/artifacts/source_registry/safety_reports/agent_runs já tratadas na Wave 1; novas entradas dessas classes = batches delta futuros, fora da Wave 2).
- Vocabulário de `status` (campo text, sem constraint): `active` · `dormant` · `paused` · `superseded` · `deprecated` · `archived` · `refuted` · `UNKNOWN_REVIEW`.

## 6. Riscos

- **Duplicação temática com Wave 1:** os 10 memory_items da Wave 1 são **sínteses agregadas** (tag `seed:memory_core_v1`); os rows da Wave 2 são **espelhos 1:1 de cards** (tag/id-namespace próprios). Coexistência intencional e distinguível por tag — não é duplicata (ver §8).
- **Memória fria/perda de nuance:** body = description de 1 linha; mitigado por source_ref → card integral local.
- **Classificação errada de scope/status:** batches ≤50 revisáveis linha a linha antes do apply; dormant/paused/superseded marcados explicitamente.
- **Edge sensível vazando via description:** descriptions contêm métricas agregadas (N/WR/R) mas não parâmetros/regras de entrada; tudo scope `private`; gerador com guard de padrões proibidos.
- **Drift pós-migração:** cards continuam evoluindo; sync via batches delta (`seed:memory_delta_<data>`) — protocolo do checkpoint M5 §4.
- **Clipboard mangling (lição M3):** aplicar sempre copiando do ficheiro/raw (`pbcopy < ficheiro`), nunca de render de chat.

## 7. Rollback (DEV, manual via SQL Editor, nunca MCP)

Por batch tag, independente por wave:
```sql
delete from memory_items where 'seed:memory_cards_wave2a' = any(tags);
```
(idem `seed:memory_cards_wave2b/c/d` futuros). Ids determinísticos `md5('seed:memory_cards_wave2a:<filename>')::uuid` recomputáveis para delete cirúrgico. Bloco comentado no fim de cada seed.

## 8. Anti-duplicação

- **Chave natural = filename do card** → id determinístico por filename; re-execução = 0 duplicados (ON CONFLICT).
- Um card aparece **no máximo em 1 wave-batch** (2A tem lista fechada de 50; 2B/2C/2D excluem os já migrados por filename).
- Wave 1 (sínteses) vs Wave 2 (cards): namespaces de id e tags distintos; retrieval pode filtrar por tag; nenhum filename de card foi usado na Wave 1 como row própria.
- MEMORY_ARCHIVE continua **fora** (é snapshot do índice antigo; conteúdo já vive nos cards — artifact pointer na Wave 1).

## 9. Plano de validação

**Antes do apply (feito para 2A):** rows por tabela (50 → memory_items; demais 0) · exemplos inspecionados · grep secrets (PASS) · parse Postgres local (PASS, 4 statements) · safety report · `git diff --stat` · aprovação do Cris.

**Depois do apply manual (por batch):** via MCP read-only —
1. `SELECT count(*) FROM memory_items;` (esperado 2A: 10 Wave1 + 50 = **60**)
2. `SELECT count(*) FROM memory_items WHERE 'seed:memory_cards_wave2a' = any(tags);` (esperado **50**)
3. Sample selects (title, category, scope, status) por wave tag
4. Retrieval por tema (ex.: tags/category) medindo payload pequeno
5. Confirmar `transaction_read_only = on`
6. Safety report · documentar em doc de validação do batch

## 10. Gate estratégico (confirmação)

**XAU_15M_LONG_REGIME_DETECTOR permanece BLOQUEADO** até: (a) Wave 2A no mínimo validada via MCP read-only, **ou** (b) Cris decidir explicitamente parar a Wave 2 e liberar a estratégia. XAU_SHORT = DEFERRED_AFTER_XAU_15M. Nenhuma nova pesquisa estratégica durante a Wave 2.

Estado: XAU_15M_LONG_REGIME_DETECTOR = DEFERRED_UNTIL_SUPABASE_MEMORY_FULL_MIGRATION_PROGRESS · XAU_SHORT = DEFERRED_AFTER_XAU_15M · SUPABASE_MEMORY_WAVE_2 = ACTIVE.

---

## Anexo — Pré-review Wave 2A (Decisão 7, pré-apply)

- **Seed:** `supabase/seeds/memory_cards_wave2a_seed.sql` — **50 rows**, só `memory_items`, 1 transação, idempotente.
- **Gerador versionado:** `scripts/memory/generate_wave2a_seed.py` (reproduzível — regenera o seed byte a byte; guard interno de padrões proibidos; adicionado ao commit por exigência do guard de reprodutibilidade).
- **Distribuição:** scope 18 product / 32 private · status 45 active / 4 dormant / 1 paused · tipo 28 feedback / 17 project / 3 reference / 2 user.
- **Exemplos:** `PRINCIPAL_1_claude_behavior` (product/internal/feedback/active) · `project_l2_bpt_structural_regime_level_engine` (private/private/project/active) · `project_xau_4h_caminho_b_long` (private/private/project/**dormant**) · `user_name_ris` (private/private/user/active).
- **Verificações:** grep `sbp_|eyJ|password|api_key|SERVICE_ROLE` → **0 hits** · parse Postgres (sqlglot) → **OK** · 50/50 ids determinísticos · descriptions com aspas YAML normalizadas e apóstrofos escapados · max body 488 chars (payload pequeno).
- **Não aplicado.** Aguarda aprovação do Cris → apply manual → validação §9.
