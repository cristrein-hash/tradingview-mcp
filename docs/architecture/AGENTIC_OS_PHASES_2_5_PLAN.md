# AGENTIC OS — PLANO FASES 2–5 (read-only planning; nenhuma implementação)

**Data:** 2026-07-02 · **Proveniência:** desenhado por planeamento read-only (ferramenta de fan-out Plan do Claude Code). **Nenhum código escrito, nada movido/apagado.**
**Contexto:** `TRADING_SYSTEM_AGENTIC_OS_MEMORY_v1.md` (contratos) + `AGENTIC_OS_PHASE1_INVENTORY_2026_07_02.md` (inventário).

## Descoberta que reformula o plano
Os "248 ficheiros com paths hardcoded" estão **quase todos no tier PRIVADO de pesquisa**; as superfícies de **PRODUTO já estão portáveis**:

| Superfície | Papel | Abs-paths | Portabilidade hoje |
|---|---|---|---|
| `src/` (MCP Node) | PRODUTO | **0** | já portável |
| `external_factors_v2/collectors+runtime` | PRODUTO (EF v2) | relativo + `load_env.py` | quase portável |
| `alert-bridge/` daemons | PRODUÇÃO | maioria relativo/config | quase portável |
| `regime_turnstate_engine/validation/` | PESQUISA (in-sample) | **111** (usam `/tmp/causal_segments_v10.json`) | não-portável (e não precisa) |
| `research/`, `my-strategy/research/**` | PESQUISA (rulers) | ~100 | privado |

Dois factos que guiam o desenho:
1. `external_factors_v2/runtime/load_env.py` **já** implementa o padrão backward-compatible (env override + `.env` local/root + `setdefault`, nunca loga). **Fase 2 = generalizar, não inventar.**
2. `/tmp/causal_segments_v10.json` é **gerado** por `phase10_hybrid_regime.py` (re-run via `P.run(...)`) = artefacto reprodutível, não estado precioso. Pode continuar a default para `/tmp`.

**Consequência: Fase 2 NÃO edita 248 ficheiros.** Resolver central cujos *defaults = paths absolutos atuais*, adotado primeiro no produto; os 111 scripts RTSE continuam a correr inalterados nos defaults e migram só oportunisticamente.

---

## FASE 2 — Camada config/env portabilidade
- **Meta:** engine portável via resolver central, **zero breakage** dos scripts RTSE aprovados. Portabilidade = env-override-com-defaults-atuais, não relocação.
- **Alvos (novos):** `config/paths.py` (+ `config/paths.js` parid.), `.env.example` na raiz (`TVMCP_REPO_ROOT/DATA_DIR/TMP_DIR/COLD_DIR`); `load_env.py` vira thin re-export de `config.paths`.
- **Passos:** (1) `paths.py` resolve env→default (`REPO_ROOT=parents[1]`, `TMP_DIR=/tmp`, `COLD_DIR=/Volumes/GUTS_ LACIE/TradingData`); helpers `causal_segments()`, `ruler()`, `cold_path()`. (2) dobrar `load_env` em `paths.py`. (3) `.env.example`. (4) adotar só no produto (EF collectors → src → helpers). (5) migrar 3–5 scripts RTSE como referência, não 111.
- **Riscos:** editar `external_factors_v2/runtime` ou `alert-bridge/` = **produção → gate**; `parents[N]` errado muda REPO_ROOT.
- **Rollback:** adições puras → apagar 2 ficheiros; re-export = revert 1 linha.
- **Aceitação:** `from config.paths import ...` imprime paths byte-idênticos aos literais atuais; `TVMCP_REPO_ROOT=/tmp/clone` vira tudo; 3 scripts RTSE correm inalterados com output idêntico.
- **Fora de escopo:** editar 248 ficheiros; mover pastas; tocar `.env` real/plist.

## FASE 3 — Consolidar External Factor v2 (NÃO reconstruir)
- **Meta:** mapear EF v2 operacional para `system/external_factor/` por referência/registry + audit vivo-vs-morto; preservar contrato "EF = contexto, nunca gate".
- **Alvos (audit):** `collectors/` (7), `runtime/`, `config/{factor_registry,sources_whitelist}.json`+`lint_registry.py`, `agents/skills/*`, `snapshots/` (freshness).
- **Passos:** (1) **liveness audit** (Pre-Change Discipline: último snapshot 7d + eventos/dia → ALIVE/DORMANT/DEAD). (2) reconciliar registry vs emitido; `lint_registry.py` read-only. (3) `docs/architecture/EF_V2_CONSOLIDATION_MAP.md` (lineage collector→snapshot→registry + mapeamento lógico Calendar=forexfactory/Macro=fred/Fed=fed_news+fedwatch/News=av_news/Gold=gold). (4) reafirmar anti-gate + passive-logging.
- **Riscos:** editar `run_cycle.sh`/plist/collectors = produção → gate; repetir erro 2026-05-18 (fix em canal DORMANT) → liveness audit é o guard.
- **Rollback:** só doc/read-only.
- **Aceitação:** verdicto ALIVE/DORMANT/DEAD por collector com timestamps; lint passa; mapa existe; 0 bytes em collectors/runtime/plist.

## FASE 4 — Split ENGINE portável vs DATA/RESEARCH privado + `git mv` incremental
- **Meta:** definir produto-vs-privado e mover incremental com `git mv` (preserva histórico) + testes de import. Só APÓS resolver da Fase 2.
- **Classificação:** PRODUTO=`src/`, `config/paths.*`, `external_factors_v2/{collectors,runtime,config,agents}`, `skills/`, `.claude/*`, `ops/`, `tests/`. PRIVADO=`regime_turnstate_engine/*`, `research/`, `my-strategy/research+strategies/`, `backups/`, temp. PRODUÇÃO (gate)=`alert-bridge/`, plist. **Dep cruzada:** RTSE lê rulers em `my-strategy/research/revalidation/.../v1/results/*.csv` (49 refs) — mover em par.
- **Passos:** (1) spec `ENGINE_VS_PRIVATE_SPLIT.md` (MOVE/STAY/GATE por dir, sem mover). (2) harness de teste de imports + golden baseline (spot-run 3 RTSE). (3) mover produto low-coupling primeiro (1 dir/commit, re-run harness). (4) mover pesquisa por último e só após migrar refs para `paths.*`. (5) nunca mover `alert-bridge`/plist sem aprovação.
- **Riscos:** 49 refs de ruler + 111 `/tmp` partem se adoção da Fase 2 incompleta → moves gated atrás de "refs migradas".
- **Rollback:** 1 move = 1 commit → revert; harness deteta drift.
- **Aceitação:** harness verde antes/depois de cada move; `git log --follow` preserva histórico; produto importável de clone fresco só com `.env`.

## FASE 5 — Supabase memory MIRROR (índice, nunca validação)
- **Meta:** memória semântica opcional. RAW/source-first continua a única verdade de validação. Offline-capável (funciona sem Supabase).
- **Alvos (novos, isolados):** `system/memory/` `{schema.sql, memory_ingest.py, memory_search.py, decision_log.py, artifact_register.py}`; `.env` ganha `SUPABASE_URL/KEY`; `.mcp.json` Supabase **read-only default**.
- **Passos:** (1) schema (memory_items/embeddings pgvector/decisions/artifacts/source_registry/agent_runs/external_factor_events/episode_context_links). (2) `artifact_register` regista **pointers+checksums**, não RAW. (3) ingest docs/governança/EF events (passive). (4) `memory_search` top-k → devolve pointer p/ RAW. (5) `decision_log`. (6) MCP read-only.
- **Riscos:** Supabase virar fonte de validação = **violação de contrato** → só pointers+checksums, todo record liga a path RAW; nenhum script de validação lê resultado do Supabase. Segredos só em `.env` gitignored.
- **Rollback:** drop projeto / apagar `system/memory/` (é mirror, nada depende).
- **Aceitação:** sistema corre com `SUPABASE_URL` unset; schema aplica; round-trip ingest→search devolve pointer; MCP nega write; CI confirma que nenhum backtest importa Supabase como fonte.

---

## ORDEM MÍNIMA end-to-end (menor risco / maior ROI de portabilidade)
1. **Fase 2 passos 1–3** (resolver + `.env.example`) — adições puras, zero produção, desbloqueia tudo.
2. **Fase 2 passo 4** (adotar em EF collectors não-runtime) — runtime = gate.
3. **Fase 3 liveness audit + consolidation map** — read-only, cumpre Pre-Change Discipline.
4. **Fase 4 passos 1–2** (spec + harness de imports).
5. **Fase 4 passo 3** (mover produto low-coupling, 1 dir/commit).
6. **Fase 5** (Supabase mirror MVP) — último, aditivo, opcional.
7. **Adiar:** moves de pesquisa + migração dos 111 scripts (oportunístico; defaults mantêm a correr). Cleanup/cold-storage corre em track próprio, nunca entrelaçado.

## Gates de produção (exigem aprovação humana explícita)
- Qualquer edição em `alert-bridge/` — PRODUÇÃO.
- `external_factors_v2/runtime/run_cycle.sh`, `monitor_external_factors.py`, `com.cristrein.external-factors-v2.plist` — PRODUÇÃO.
- Adoção do resolver no runtime EF — gate (janela de manutenção + verificar 1 ciclo).
- `git mv` de dir de produção/plist (Fase 4) — gate.
- `.env`/segredos reais — nunca editados por estas fases; só `.env.example`.
