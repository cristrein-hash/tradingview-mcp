# PRODUCT / PRIVATE SPLIT PLAN — Fase 4 (planeamento read-only)

**Data:** 2026-07-02 · **Natureza:** planeamento DOCUMENTAL apenas. **Nada movido/apagado/alterado. Sem código, sem produção, sem runtime, sem RAW, sem Supabase.**
**Contexto:** `TRADING_SYSTEM_AGENTIC_OS_MEMORY_v1.md` (direção) · `AGENTIC_OS_PHASE1_INVENTORY_2026_07_02.md` (inventário) · `CONFIG_ENV_CONTRACT.md` (portabilidade). 10 scripts já no config path layer.

## Tese central (comercialização)
O **produto vendável** = o **motor** (MCP server + contratos + config/env layer + skills + framework de governança). A **alpha do Cris** (estratégias, rulers, RTSE, research, dados RAW, runtime de trading) = **privado, não vendável**. Um comprador recebe o engine portável; **nunca** os dados/edge. O split de pastas tem de tornar essa fronteira física e óbvia.

---

## 1. Mapa da arquitetura-alvo (lógico; NÃO mover ainda)
```
trading-system-agentic-os/
├── product_core/           # motor vendável, portável
│   ├── src/                # MCP server (server.js, cli, core, tools) — 78 tools
│   ├── config/             # path/env resolver (portabilidade)
│   ├── skills/             # skills de produto (chart/pine/scan/report)
│   ├── external_factor_engine/  # collectors + contracts (data-source-agnostic)
│   └── contracts/          # governança/validação/EF/reader (docs normativos)
├── private_runtime/        # instância viva do Cris (NÃO vendável)
│   ├── alert-bridge/       # receiver/webhook/evaluator/monitors + logs
│   └── external_factors_v2_runtime/  # daemon + plist + snapshots + .venv
├── research/               # pesquisa (privada)
│   ├── regime_turnstate_engine/
│   ├── xau_15m_bb_nas_leonardo/
│   └── my-strategy/research/
├── data/
│   ├── raw/                # RAW/source (HD externo; ponteiros)
│   └── private/            # rulers, ground-truth, calibração
├── reports/                # outputs
├── archive/                # superseded/historical
├── docs/                   # governança (produto) + reports (privado)
└── (cold storage externo)  # logs/backtests, backups
```
> Alvo LÓGICO. A implementação física (Fase 4C+) é incremental via `git mv`, gated, só após aprovação.

---

## 2. Classificação por diretório atual
| Diretório | Classe | Nota |
|---|---|---|
| `src/` | **KEEP_PRODUCT** | MCP server = núcleo vendável; 0 hardcodes; já portável |
| `config/` | **KEEP_PRODUCT** | path/env layer (Fase 2) |
| `skills/` | **KEEP_PRODUCT** (parcial) | chart/pine/scan/report = produto; operacionais (incident/replay/repo-gov/trading-operator) = produto-de-serviço |
| `tests/` | **KEEP_PRODUCT** | testes do engine + config |
| `external_factors_v2/collectors,config,agents` | **KEEP_PRODUCT** | engine EF (data-source-agnostic) |
| `external_factors_v2/runtime,snapshots,.venv-agents,*.plist` | **KEEP_PRIVATE_RUNTIME** | daemon vivo + estado + venv (DO_NOT_TOUCH) |
| `alert-bridge/` (receiver/recheck/evaluator/monitors) | **KEEP_PRIVATE_RUNTIME** | produção viva (DO_NOT_TOUCH) |
| `alert-bridge/logs/backtests/` (2,2G) | **COLD_STORAGE_CANDIDATE** | dump; gitignored |
| `docs/project_authority/`, `docs/strategy_governance/` | **KEEP_PRODUCT** | contratos/governança (framework vendável) |
| `docs/XAU_*`, `docs/architecture/*RESEARCH*` | **KEEP_RESEARCH_HISTORICAL** | reports de pesquisa (privado) |
| `regime_turnstate_engine/` | **KEEP_RESEARCH_ACTIVE** | RTSE (research da estratégia aprovada; privado) |
| `my-strategy/strategies/` | **KEEP_RESEARCH_ACTIVE** | candidatos/estratégias (privado, IP) |
| `my-strategy/research/revalidation/*/results/` | **DO_NOT_TOUCH** (SOURCE_OF_TRUTH) | rulers RAW (privado) |
| `research/xau_15m_bb_nas_leonardo/` | **KEEP_RESEARCH_ACTIVE** | lab vivo (gate proveniência aberto) |
| `my-strategy/research/backtests/*_audit_20260512/` | **KEEP_RESEARCH_HISTORICAL** / ARCHIVE_CANDIDATE | one-off cross-asset; inputs (~/Downloads) inexistentes |
| `backups/` (32M) | **COLD_STORAGE_CANDIDATE** | snapshots dated, untracked |
| `screenshots/` (6,9M) | **COLD_STORAGE_CANDIDATE** | untracked |
| `archive/` | **KEEP_RESEARCH_HISTORICAL** | já arquivado |
| `ops/` | **KEEP_PRIVATE_RUNTIME** | `start_trading_stack.sh` (orquestra runtime local) |
| `agents/` | **KEEP_PRODUCT** | def de agente (performance-analyst) |
| `node_modules/` | **DO_NOT_TOUCH** (regenerável) | npm-managed |
| `data/raw` (via `/Volumes/GUTS_ LACIE`) | **DO_NOT_TOUCH** (RAW/source) | externo, privado |

---

## 3. Módulos que PERTENCEM ao produto vendável
- **config/env layer + path resolver** (`config/paths.py`, `.env.example`, `CONFIG_ENV_CONTRACT.md`).
- **MCP server** (`src/` — server.js, cli, core, tools; 78 tools TradingView).
- **External Factor engine + contracts** (`external_factors_v2/{collectors,config,agents}`, `RTSE_EXTERNAL_FACTORS_BRIDGE_V0.md`) — o motor, não a instância.
- **Contratos de validação/governança** (`docs/project_authority/*`, `docs/strategy_governance/*`, `SKILL_0x_*`).
- **Skills de produto** (`skills/{chart-analysis,pine-develop,multi-symbol-scan,strategy-report,replay-practice}` + operacionais de serviço).
- **Scripts portáveis comprovados** (os já migrados para `config.paths`, quando reutilizáveis pelo produto).
- **Reader/dossier contracts** — SE existirem como contrato genérico (a confirmar na 4A; hoje vivem embutidos em research).

## 4. Módulos que NÃO pertencem ao produto vendável (por agora)
- **RAW/source privado** (`/Volumes/GUTS_ LACIE/TradingData`, rulers, ground-truth).
- **logs/backtests pesados** (2,2G) + **backups** (32M) + **screenshots**.
- **Research morto / one-off** (audits `*_20260512` com inputs ~/Downloads inexistentes; scripts `/tmp`-scratch sem inputs).
- **Estratégias/edge do Cris** (`my-strategy/strategies`, `regime_turnstate_engine`, `research/`) = IP privado.
- **venvs locais** (`.venv-agents`), **daemon privado** (alert-bridge, EF v2 runtime), **LaunchAgents/plists pessoais**.
- **Outputs privados** (`reports/` específicos, snapshots).

---

## 5. Matriz de decisão (resumo; detalhe por-módulo na 4A)
| Path atual | Função | Status | Risco | Valor comercial | Precisa portab.? | Precisa Supabase? | Ação | Prioridade | Aprovação? |
|---|---|---|---|---|---|---|---|---|---|
| `src/` | MCP server | KEEP_PRODUCT | baixo | **ALTO** | já portável | não | manter; futuro `product_core/` | P1 | N |
| `config/` | path layer | KEEP_PRODUCT | baixo | ALTO | é a base | não | expandir opt-in | P1 | N |
| `external_factors_v2/collectors+config+agents` | EF engine | KEEP_PRODUCT | médio | ALTO | já relativo | mirror-only depois | manter; separar de runtime | P2 | N |
| `external_factors_v2/runtime+plist+venv` | daemon | KEEP_PRIVATE_RUNTIME | **alto** | baixo (instância) | não | não | DO_NOT_TOUCH | — | **S** p/ mexer |
| `alert-bridge/` | produção | KEEP_PRIVATE_RUNTIME | **alto** | baixo | não | não | DO_NOT_TOUCH | — | **S** p/ mexer |
| `alert-bridge/logs/backtests` | dumps | COLD_STORAGE | médio | nenhum | não | não | cold storage (dedicado) | P3 | **S** |
| `docs/project_authority+strategy_governance` | contratos | KEEP_PRODUCT | baixo | ALTO | n/a | não | virar `contracts/` do produto | P2 | N |
| `regime_turnstate_engine/` | RTSE research | KEEP_RESEARCH_ACTIVE | médio | privado(IP) | parcial (feito) | não | manter privado | P3 | N |
| `my-strategy/` | estratégias/rulers | KEEP_RESEARCH_ACTIVE / SOURCE_OF_TRUTH | **alto** | privado(IP) | não (privado) | não | manter privado | — | N |
| `research/xau_15m_bb_nas_leonardo` | lab | KEEP_RESEARCH_ACTIVE | baixo | privado | parcial (feito) | não | manter privado | P4 | N |
| `my-strategy/research/backtests/*_20260512` | audits one-off | ARCHIVE_CANDIDATE | baixo | nenhum | não | não | archive (inputs mortos) | P4 | **S** |
| `backups/`, `screenshots/` | snapshots | COLD_STORAGE | baixo | nenhum | não | não | cold storage | P3 | **S** |
| `extract_raw_ohlc.py`, `extract_30m_ohlc.py` | extractores | DEFERRED_HIGH_VALUE | médio | médio | sim | não | copy-sandbox (bloco próprio) | P2 | **S** |

---

## 6. Plano de migração em fases
- **Fase 4A — split lógico/documental (SEM mover):** este doc + auditoria por-módulo fina (confirmar reader/dossier contracts, marcar cada dir com a classe). Entregável: matriz por-módulo completa.
- **Fase 4B — skeleton portable (se necessário):** criar `product_core/` VAZIO + README de contrato de fronteira; **sem mover conteúdo**. Decisão: só se ajudar a clareza de venda.
- **Fase 4C — migrar apenas product-core:** `git mv` incremental de `src/`, `config/`, `skills/`, `tests/` → `product_core/` (1 dir/commit, harness de import verde antes/depois). Gated.
- **Fase 4D — isolar private/runtime:** mapear `alert-bridge/`, EF runtime, `my-strategy/`, `regime_turnstate_engine/`, `research/` sob `private_runtime/` + `research/` + `data/`. **Só com aprovação; produção = gate.**
- **Fase 4E — decidir cold storage:** logs/backtests + backups → HD externo (tar.zst+SHA256+manifest+roundtrip+restore doc).
- **Fase 4F — desenhar Supabase mirror:** só depois do split, mirror da **memória de produto** vs privada; nunca validação.

---

## 7. Critérios de aceitação (Fase 4A, este doc)
- Nenhum arquivo vivo alterado; produção intocada; RAW/source intocado. ✅
- Classificação explícita de todos os diretórios top-level. ✅
- Lista clara: o que vira produto / o que fica privado / o que não merece migração. ✅
- Próximo lote de migração definido pelo split (não por grep bruto). ✅ (ver §8)

## 8. Riscos e rollback
- **Rollback deste doc:** apagar `PRODUCT_PRIVATE_SPLIT_PLAN.md` (documentação pura, zero efeito operacional).
- **Diretórios PERIGOSOS (não tocar sem autorização explícita):** `alert-bridge/`, `external_factors_v2/runtime` + `.venv-agents` + `*.plist`, `my-strategy/research/revalidation/*/results` (rulers), `/Volumes/GUTS_ LACIE` (RAW), `node_modules/`.
- **Risco maior da Fase 4C+:** `git mv` quebra imports (49 refs de ruler + 111 `/tmp`) → gated atrás do resolver + harness de import; mover 1 dir/commit.
- **Regra:** mover produção/plist/RAW = **proibido sem aprovação**; tudo o resto = incremental e reversível por commit.

---

## Próximo passo recomendado (pós-Fase-4A)
Com o split definido, o esforço de portabilidade deve ir para **product-core** (que já está quase portável) e para os **extractores com copy-sandbox** (valor real, verificável), **não** para migrar research morto. Supabase e cold storage seguem como passos dedicados posteriores. Decisão do Cris sobre qual bloco abrir a seguir.
