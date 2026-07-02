# SUPABASE MEMORY MIGRATION — VALIDATION M4 (2026-07-02)

**Resultado: PASS ✅ — Supabase DEV tem memória funcional (Wave 1).**
**Modo:** validação 100% read-only via MCP `supabase-dev` (role `supabase_read_only_user`). Zero escrita pelo Claude em qualquer fase.

## 1. Aplicação do seed (M3)

- `supabase/seeds/memory_core_seed.sql` (commit `665c113`, batch tag `seed:memory_core_v1`) aplicado **manualmente pelo Cris** via Supabase Dashboard SQL Editor, projeto DEV `trading-system-memory-dev` (`vgfofofozptrtjvtuyzy`).
- **Incidente de aplicação (resolvido):** 1ª tentativa falhou com `42601 syntax error at or near "product"` — causa-raiz = **mangling de aspas no clipboard** ao copiar o SQL do bloco de chat (aspas retas → tipográficas). Diagnóstico: ficheiro verificado byte a byte (zero aspas curvas) + parse local Postgres OK (18 statements). Solução: copiar direto do ficheiro (`pbcopy < supabase/seeds/memory_core_seed.sql`). 2ª aplicação: **sucesso**. Lição: seeds sempre copiados do ficheiro/raw, nunca de render de chat.

## 2. Counts esperados vs reais (teste 1–6 + tabelas futuras)

| Tabela | Esperado | Real | |
|---|---|---|---|
| memory_items | 10 | **10** | ✅ |
| decisions | 8 | **8** | ✅ |
| artifacts | 12 | **12** | ✅ |
| source_registry | 7 | **7** | ✅ |
| safety_reports | 1 | **1** | ✅ |
| agent_runs | 6 | **6** | ✅ |
| external_factor_events · market_context_snapshots · trade_journal_events · episode_context_links · retrieval_queries | 0 | **0** | ✅ (fases posteriores intocadas) |

Total seeded: **44 rows** — exatamente o aprovado no review M2.

## 3. Amostras recuperadas (testes 7–9)

- **memory_items (10/10):** ordem e conteúdo exatos do seed — 8 rows `product/internal` (RAW-first · no-SLIM · backtest-com-manifest · production safety · no-prod-change-sem-aprovação · trading-data-fora-da-memória · Supabase-não-é-verdade · Agentic OS camadas) + 2 rows `private/private` (ordem de tarefas vigente · contexto do WARNING). Categorias corretas (feedback/architecture/project); encoding íntegro (em-dash e acentos preservados).
- **decisions (8/8):** todos os `decision_key` prefixo `core_` presentes, todos `status=approved` — architecture_approved · product_private_boundary · commercialization_deferred · no_auto_trading · ef_v2_passive · xau_15m_before_short · migration_before_strategy · safety_report_only.
- **artifacts (10 primeiros de 12):** paths e artifact_types exatos (design_doc/plan/report/checkpoint/audit/runbook/manifest); todos `active`.

## 4. Confirmações

- **MCP read-only (teste 10):** `transaction_read_only = on` · `current_user = supabase_read_only_user` — na mesma sessão dos SELECTs. Toda escrita foi manual (Cris/SQL Editor).
- **Zero RAW/candles/logs/backtests/trades:** counts batem 1:1 com o seed auditado (44 rows conhecidas row a row no review M2); tabelas de dados de mercado/journal = 0; conteúdo = títulos/resumos/status/pointers+checksums apenas.
- **Supabase DEV tem memória funcional:** protocolos core, decisões, artifacts com checksum, registry de fontes com autoridade, baseline de safety e milestones — recuperáveis por SELECT com payload pequeno (~2–3 KB por consulta de 10 rows), adequado a retrieval de contexto.
- **Testes executados = exatamente os 10 autorizados.** Nenhum INSERT/UPDATE/DELETE/migration/schema change/RLS change.
- **Safety report pós-validação:** BLOCKER=0 · WARNING=1 (pré-existente, contextualizado no próprio seed) · INFO=47 — baseline inalterada.

## 5. Riscos remanescentes

- **Drift memória-local ↔ Supabase:** cards locais continuam a evoluir; as 44 rows são snapshot 2026-07-02. Protocolo de sync = definir no checkpoint M5.
- **Wave 2 pendente:** 229 memory cards ainda não migrados (plano §6: SQL gerado por script local, batches revisáveis ~50, tag `seed:memory_full_w2`).
- **Checksum drift:** sha256 dos artifacts registram o estado em `174932c`; edições futuras dos docs divergem do checksum (esperado; checksum = estado na migração, não invariante).
- **RLS ativo sem policies:** leitura atual funciona via role do MCP; fase de policies (product vs private) continua pendente (registrado desde §5.e do S2 report).
- **retrieval_queries vazia:** log de retrievals só será populado quando houver fluxo de escrita autorizado (fase futura; MCP não escreve).

## 6. Próximos passos (M5)

1. Criar `docs/architecture/SUPABASE_MEMORY_MIGRATION_CHECKPOINT.md` — checkpoint final do bloco: estado, decisões, protocolo de sync, gate para Wave 2.
2. Após aprovação do M5: **XAU 15M LONG Regime Detector pode abrir**; XAU SHORT continua depois do XAU 15M.
