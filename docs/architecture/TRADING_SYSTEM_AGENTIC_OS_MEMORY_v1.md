# TRADING SYSTEM AGENTIC OS — ARCHITECTURE MEMORY v1

**Data:** 2026-07-02
**Estado:** DECISÃO DE DIREÇÃO (não implementação). Salvo no repo git como memória durável antes de qualquer inventário/corte.
**Regra-mãe:** minimum safe execution · RAW/source-first · não apagar/mover/tocar produção sem aprovação explícita.

> Este documento fixa a DIREÇÃO de arquitetura aprovada e a avaliação da proposta GPT. **Não autoriza deleção, movimentação, nem produção.** O plano de implementação detalhado é responsabilidade do **Plan agent** (CLAUDE.md: mudanças arquiteturais exigem Plan agent antes de escrever código).

---

## 1. Objetivo do sistema
Transformar o trabalho atual (Trading System + External Factor v2 + RTSE + governança) num **Trading System Agentic OS**: pequeno, portável, auditável, automatizável e **comercializável**, sem sacrificar segurança operacional nem verdade RAW-first.

Metas de produto: **portabilidade** (rodar noutra máquina/cliente), **automação** (agentes subordinados a um orquestrador), **comercialização** (separar engine portável de dados/pesquisa privados).

---

## 2. Arquitetura final ENXUTA (aprovada como direção)
Rejeitado o desenho grande de ~30 agentes. Núcleo em **4 blocos** sob **um** orquestrador (Master Agent que orquestra, NÃO decide trade):

```
trading-system-agentic-os/
├── CLAUDE.md
├── .claude/ { skills/ agents/ hooks/ }
├── system/
│   ├── trading_core/     (RAW Mapper · Backtest Validator · Reader Vivo Dossier · Strategy Governance · Production Safety)
│   ├── external_factor/  (Calendar · Macro · Fed/CB · News · Geopolitical · Gold Drivers · USD/Yields · Validation/Dedup · Synthesizer)
│   ├── memory/           (Supabase mirror + índice semântico)
│   └── safety/           (hooks · MCP permissions · forbidden paths · human approval)
├── data/ { raw/ normalized/ evidence/ derived/ }
├── reports/  docs/  archive/
```

Separação de produto (adição minha à proposta): distinguir **engine portável/vendável** de **dados/pesquisa privados** (RAW não é vendável). O corte de pastas deve refletir isto.

---

## 3. TRAVAS INEGOCIÁVEIS (contratos)
1. **External Factor = camada de CONTEXTO/EVIDÊNCIA, NUNCA gate/trigger automático de trade.** Fluxo proibido: `news/macro → Claude → trade`. Fluxo obrigatório: `raw → collector → normalizer → dedup → validation → evidence → context → review → autorização humana/regra`. (Consistente com memória: EF v2 é passive-logging, gate só Fase 4; validado só Camada A event-reaction; resto = contexto/flag, nunca edge.)
2. **RAW/source-first é a verdade.** SLIM/proxy/derived NUNCA validam. Supabase/Graphify/Obsidian = memória e navegação, NÃO validação.
3. **Master Agent orquestra, não decide trade.** Agentes pequenos, especializados, auditáveis, subordinados.
4. **Nada de produção automática** (broker/Telegram send/monitor write/cron write/strategy_rules/catalog) sem autorização explícita.
5. **Hooks > mais agentes.** Segurança por hook (report-only → depois bloqueante) + GitHub Actions como 2º cinturão.
6. **Skills próprias, não importar de marketplace** (risco supply-chain/semântico em SKILL.md): ler → extrair padrão → reescrever nossa → commit auditado.
7. **Supabase = memória/índice, não fonte de validação.** Chaves em `.env` (gitignored). MCP read-only por padrão.

---

## 4. Veredito sobre a sugestão do GPT (resumo; detalhe na resposta da sessão)
**Direção correta, mas grande demais para v1 e reinventa infra que já existe.**
- ✅ ACEITO: EF = contexto (não gate); RAW-first; agentes pequenos sob orquestrador; hooks>agentes; Supabase=memória; skills próprias; evidência versionada com proveniência; rollout faseado sem produção; DECISÃO A (memória→inventário→classificar→aprovar→cortar).
- ✂️ CORTAR/ADIAR: frota de 9 agentes EF (já temos EF v2 com 6 coletores keyless + daemon — **consolidar, não reconstruir**); "Agent Brain" como autoridade (é só memória); frota grande de News/Geopolitical (memória: news>Camada A = contexto, nunca edge); Graphify/Obsidian (nice-to-have, adiar); MCPs redundantes Nível B (FRED/FF/CFTC já cobertos; FMP Starter não vale).
- ⚠️ RISCOS que a proposta subvaloriza:
  1. **Reconstruir EF quando EF v2 já é operacional** = repetir o erro "build sobre arquitetura morta/duplicada" (incidente 2026-05-18). Correto = AUDITAR vivo-vs-morto e consolidar.
  2. **Migração de pastas quebra imports** — scripts RTSE têm paths absolutos hardcoded (`/Users/cristrein/tradingview-mcp/...`, `/tmp/causal_segments_v10.json`). Mover em massa parte tudo. Exige incremental + `git mv` + teste de paths.
  3. **Portabilidade real = de-hardcodar paths + config central**, MAIOR alavanca que restruturar pastas. É o caminho mais curto para portabilidade/comercialização.
  4. **Supabase = dependência externa**; deve ser mirror OPCIONAL, nunca requisito para validação (sistema RAW-first offline-capável).

---

## 5. CAMINHO MAIS CURTO/SEGURO recomendado (a decidir com Cris)
- **Fase 0 (feito):** salvar esta memória no repo.
- **Fase 1 (read-only, em curso):** inventário + tabela de classificação. ZERO deleção.
- **Fase 2 (maior alavanca de portabilidade):** de-hardcodar paths → config central (`REPO_ROOT`/`DATA_DIR` via `.env`/config). Desbloqueia portabilidade + comercialização mais que mover pastas.
- **Fase 3:** consolidar (não reconstruir) EF v2 na arquitetura; auditar vivo vs morto.
- **Fase 4:** definir split portável/privado + MOVER incremental com `git mv` (preserva histórico) + teste de imports, só após inventário aprovado.
- **Fase 5:** Supabase memory como mirror OPCIONAL (schema + ingest/search), nunca fonte de validação; chaves gitignored; MCP read-only.
- Segurança contínua: hooks report-only→bloqueante; forbidden paths; aprovação humana antes de produção (já existem `post_backtest_devils_advocate.py`, `pre_analysis_myopia_guard.py`).

---

## 6. Supabase memory — MVP (mirror/índice, não validação)
```
Supabase Memory
├── memory_items          (memórias/resumos/regras/decisões)
├── memory_embeddings     (pgvector, busca semântica)
├── decisions             (aprovado/rejeitado, data, status)
├── artifacts             (ficheiros/relatórios/commits/outputs)
├── source_registry       (RAW files/datasets/manifests/checksums)
├── agent_runs            (logs de execução)
├── external_factor_events(macro/news/gold normalizados)
└── episode_context_links (episódio/trade ↔ contexto externo)
```
Scripts MVP: `schema.sql · memory_ingest.py · memory_search.py · decision_log.py · artifact_register.py`. Regra: Supabase indexa e recorda; a prova continua RAW/source-first.

---

## 7. Classes de inventário (para a Fase 1, sem apagar)
`SOURCE_OF_TRUTH` mantém · `PRODUCTION` intocável · `GOVERNANCE` patch controlado · `RESEARCH_VALID` mantém · `RESEARCH_EXPLORATORY` arquiva/marca · `SUSPECT_CONTAMINATED` quarentena · `SUPERSEDED` arquiva · `TEMP_LOCAL` candidato a delete · `DECOMMISSIONED` mantém registo, desativa · `UNKNOWN` não toca.

---

## 8. DECISÃO A (aprovada como método)
1. Salvar memória/decisão no repo (feito). 2. Inventário read-only. 3. Classificar redundâncias. 4. Aprovar plano de corte com Cris. 5. SÓ ENTÃO mover/arquivar/deletar. **Maior risco = misturar arquitetura nova com limpeza destrutiva. Separar sempre.**
