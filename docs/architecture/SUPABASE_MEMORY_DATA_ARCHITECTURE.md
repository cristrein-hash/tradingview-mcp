# SUPABASE MEMORY & DATA ARCHITECTURE — design (doc-only)

**Data:** 2026-07-02 · **Modo:** read-only / doc-first. **Sem implementação, sem tabelas, sem secrets, sem migração, sem tocar produção/CLAUDE.md/MEMORY.md.**
**Base:** `PRODUCT_PRIVATE_SPLIT_PLAN.md`, `AGENTIC_OS_PORTABILITY_CHECKPOINT_20260702.md`, `CONFIG_ENV_CONTRACT.md`.

## 1. Problema
Quatro problemas distintos, hoje misturados:
- **Persistência entre sessões** (decisões, estado do projeto, arquitetura, runtime status, outputs de execução, checkpoints).
- **Recuperação para janela de contexto** (trazer só o necessário; não entupir o modelo com dados brutos).
- **Armazenamento estruturado de trading data** (query por símbolo/timeframe/tempo/estratégia/episódio/artefato).
- **Context loss / compactação** (o que salvar antes de compactar; como reabrir).

## 2. Princípio central
**Trading data não vive na memória conversacional.** O modelo **recupera slices/contexto**, não carrega o universo. RAW/source continua fonte de verdade; Supabase indexa e recorda, **não valida**.

## 3. O que fica onde
| Camada | Função | Pode entrar | Proibido | Tamanho | Autoridade? |
|---|---|---|---|---|---|
| `CLAUDE.md` | regras/guardrails mínimos + ponteiros | regras operacionais, comandos de segurança, links p/ docs canónicos | estado diário, dados de trading, o que é inferível do código | <200 linhas (hoje 247 ⚠️) | não (aponta) |
| `MEMORY.md` + auto-memory | índice + factos curados de memória | user/feedback/project/reference curados | dumps, candles, backtests, análises massivas | índice curto (hoje 253l/186 entradas ⚠️) | não (índice) |
| Git docs/checkpoints | decisões duráveis, arquitetura, manifests, restore | checkpoints, planos aprovados, incidentes | secrets, RAW massivo | versionado | **sim** (registo durável) |
| **Supabase / structured store** | dados consultáveis, memória durável, índices, slices | memory_items, decisions, artifacts, EF events, snapshots derivados (c/ source_ref) | secrets, RAW bruto massivo sem política, dados redistribuíveis | escalável | índice/derivado (não fonte) |
| RAW/source files | fonte de verdade mercado/backtests | RAW replay, rulers | — | grande (HD externo) | **sim** (autoridade) |
| local artifacts / cold storage externo | outputs pesados / arquivo | reports, dumps arquivados | — | grande | não |
| conversation context | raciocínio da tarefa atual | plano ativo, contexto recuperado sob demanda | store permanente | efémero | não |

## 4. Supabase schema proposto (sem implementar)
| Tabela | Finalidade | Campos principais | Chave/índice | Retenção | Priv/Prod | Autoridade? |
|---|---|---|---|---|---|---|
| `memory_items` | memórias/resumos/regras | id, type, title, body, tags, created_at, commit_ref | id; idx(type,tags) | longa | ambos (flag) | índice |
| `memory_embeddings` | busca semântica | item_id, embedding(vector), model | pgvector idx | longa | ambos | índice |
| `decisions` | decisões aprovadas/rejeitadas | id, topic, status, date, rationale, commit_ref | idx(topic,date) | permanente | ambos | registo |
| `artifacts` | ficheiros/relatórios/outputs | id, path, kind, sha256, commit_ref, created_at | idx(kind,created_at) | longa | ambos | ponteiro |
| `task_runs` | logs de execução (orquestrador/sub-executores) | id, task, executor_type, inputs_ref, output_ref, status, tokens, ts | idx(ts,executor_type) | média | produto | log |
| `safety_reports` | outputs do safety layer | id, run_ts, blocker, warning, info, findings_ref | idx(run_ts) | média | produto | log |
| `external_factor_events` | macro/news/gold normalizados | id, source, event_time, asset, kind, value, confidence, source_ref | idx(event_time,asset) | longa | produto(schema)/privado(uso) | derivado |
| `market_context_snapshots` | slices derivados p/ retrieval | id, symbol, timeframe, time_range, regime, summary_json, source_ref, commit | idx(symbol,timeframe,time_range) | rolling | privado | derivado |
| `trade_journal_events` | journal por trade/evento | id, strategy, symbol, entry_ts, r, notes, source_ref | idx(strategy,entry_ts) | longa | **privado** | registo privado |
| `episode_context_links` | episódio/trade ↔ contexto externo | episode_id, ef_event_id, artifact_id, note | idx(episode_id) | longa | privado | ligação |
| `source_registry` | RAW/datasets/manifests | id, path, sha256, kind, rows, coverage, machine | idx(kind) | permanente | ambos | ponteiro+checksum |
| `retrieval_queries` | log de queries de contexto | id, query, params, returned_refs, ts | idx(ts) | curta | produto | log |

## 5. Trading data policy
- RAW/source **fora da memória**, fonte de verdade.
- Supabase guarda **metadados, índices, slices normalizados ou snapshots derivados** — nunca o RAW bruto como autoridade.
- Todo derivado carrega **`source_ref` + timestamp + commit/hash + causal boundary**.
- Backtest sério continua a exigir **RAW mapping + manifest + sanity checks** (Supabase não substitui).

## 6. Retrieval model
**Como recuperar as últimas N velas 4H sem carregar tudo?** Via ferramenta de query que devolve **resumo estruturado pequeno + ponteiros**, não candles brutas:
```
get_market_context(symbol="XAUUSD", timeframe="4H", bars=120) ->
  { regime_summary, last_bars_meta[≤N compacto], key_events[], strategy_candidates[],
    external_factor_flags[], artifact_refs[], raw_source_pointer, token_budget_note }
```
Regras: query por symbol/timeframe/time_range · devolver só campos necessários · limite de tokens · citar `source_ref` · drill-down por demanda (candles brutas só se `raw=true`).

## 7. Context window protocol
- Compactar **proativamente a 60–70%**.
- **Antes** de compactar → salvar session checkpoint (§8).
- Prompt de compactação focado.
- **Após** compactar, reabrir só: `CLAUDE.md` · último architecture checkpoint · estado da tarefa ativa · retrieval Supabase relevante (quando existir) — **não** docs inteiros sem necessidade.

## 8. Session checkpoint protocol
Template (versionar no Git quando relevante, não só memory.md): tarefa atual · estado git (HEAD/branch/ahead) · decisões tomadas · ficheiros tocados · próximos passos · riscos · **o que não tocar** · links para artifacts.

## 9. Protocolo de contexto multi-executor
Orquestrador mantém contexto mínimo · sub-executores recebem tarefa estreita · outputs estruturados e salvos (artifacts/`task_runs`) · sub-executor **não decide produção** · sub-executor **não carrega RAW massivo** · recuperação via store/artifacts, não via conversa.

## 10. CLAUDE.md audit + MEMORY.md evaluation (AUDIT ONLY — não editar agora)
### CLAUDE.md (projeto)
- **Estado:** 247 linhas · 20K · 27 secções `##` (alvo <200 ⚠️).
- **Essencial (manter):** decision-tree de tools · Pre-Change Discipline (4 perguntas) · safety defaults · nunca-SLIM · regras de plot canónico.
- **Mover p/ doc + deixar ponteiro:** "Workflow Orchestration", "Session Bootstrap & Skill Selection", "Plugin & Skill Routing Policy" (detalhados) → `docs/project_authority/` (já existe 01_ASSISTANT_OPERATING_SYSTEM etc.); CLAUDE.md só aponta.
- **Inferível do código (remover):** listas longas de tools (já nas instruções do MCP server) → resumir + apontar.
- **Proposta:** CLAUDE.md compacto <200 linhas = guardrails + Pre-Change Discipline + ponteiros para `docs/project_authority/`. (Não editar agora; proposta.)

### MEMORY.md (auto-memory, fora do repo)
- **Estado:** 253 linhas · **64K** · **186 entradas de índice** · 230 ficheiros de memória (1,7M). O próprio ficheiro já avisa ">253 linhas". **Carregar 186 entradas toda sessão é pesado e dilui sinal.**
- **Problema:** índice plano gigante; mistura ⭐ princípios permanentes com leads de research já resolvidos/refutados.
- **Opções (a decidir):**
  1. **Tiering local (mais simples, imediato):** `MEMORY.md` fica só com ⭐/⭐⭐ PRINCIPAIS + leads ATIVOS (~30–50 linhas); resto → `MEMORY_ARCHIVE.md` **não auto-carregado** (consultado sob demanda).
  2. **Supabase `memory_items` + retrieval (durável):** índice migra para `memory_items` (com embeddings); cada sessão recupera top-N relevante por query; `MEMORY.md` vira ponteiro fino. Alinha com esta arquitetura.
  3. **Híbrido (recomendado):** tiering local agora (rápido, sem deps) → depois Supabase como home durável quando S3 existir.
- **Regra futura:** entradas de research refutado/resolvido → arquivar; só princípios + leads vivos ficam no índice quente.

## 11. Supabase boundaries
- **Product memory:** docs, templates, safety schemas, generic artifacts, `task_runs` do engine, EF **normalized schema**.
- **Private memory:** estratégias do Cris, XAU alpha, RTSE, `trade_journal_events`, RAW references, private outcomes, production decisions.
- **Never store:** secrets · broker credentials · API keys · RAW massivo sem política · dados copyrighted/paywalled redistribuíveis · logs sensíveis sem política · **TradingView restricted market data para redistribuição**.

## 12. Security / RLS / secrets (requisitos futuros)
`SUPABASE_URL` via env · separação anon vs service role · **service role nunca no repo** · RLS por tabela (private vs product) · split local/dev/prod · backup/restore · retenção · audit log. Chaves em `.env` gitignored (padrão já usado).

## 13. Implementation phases
- **S0** design/doc (este doc). · **S1** `schema.sql` draft (só ficheiro). · **S2** setup manual do projeto Supabase (Cris). · **S3** MVP `memory_items`+`decisions`+`artifacts`. · **S4** `source_registry`+`task_runs`. · **S5** `external_factor_events`. · **S6** `market_context_snapshots`. · **S7** retrieval tools/MCP (read-only default). · **S8** integração Agentic OS.

## 14. Acceptance criteria (doc-only)
Nenhum código alterado ✅ · nenhum dado migrado ✅ · CLAUDE.md audit incluído ✅ · MEMORY.md evaluation incluída ✅ · boundaries claros ✅ · schema proposto ✅ · retrieval model claro ✅ · próximos passos seguros ✅.

---
**Próximo (a decidir):** (a) tiering imediato do MEMORY.md (local, sem deps) — recomendado antes de qualquer implementação Supabase; (b) `schema.sql` draft (S1) doc-only; (c) Production Logic Re-Audit. Nada implementado sem nova autorização.
