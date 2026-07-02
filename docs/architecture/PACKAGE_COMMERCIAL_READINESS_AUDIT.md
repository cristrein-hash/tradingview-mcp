# PACKAGE / COMMERCIAL READINESS AUDIT — Trading System Agentic OS

**Data:** 2026-07-02 · **Modo:** read-only / doc-only. **Nada movido/alterado; sem código; sem product_core físico; produção/runtime/RAW intocados.**
**Base:** `AGENTIC_OS_PORTABILITY_CHECKPOINT_20260702.md`, `PRODUCT_PRIVATE_SPLIT_PLAN.md`, `CONFIG_ENV_CONTRACT.md`, `SAFETY_LAYER_USAGE.md`.

## 1. Executive verdict
- **`READY_FOR_INTERNAL_ENGINE_PACKAGE`** (uso próprio / demo privada controlada): SIM, com trabalho leve.
- **`NOT_READY_FOR_EXTERNAL_COMMERCIAL_RELEASE`**: correto — **não maquiar**. Blockers principais:
  1. **Compliance/legal (o maior):** o README declara explicitamente *"for personal, educational, and research purposes only"* e proíbe *"redistributing, reselling, or commercially exploiting TradingView's market data"*. O produto interage com o TradingView Desktop via CDP → **vender/redistribuir esbarra na ToS do TradingView + licenciamento de market-data**. Isto é um blocker jurídico, não técnico.
  2. Fronteira produto/privado **documentada mas não aplicada fisicamente** (risco de vazar alpha/IP num pacote).
  3. Sem onboarding/instalação/security docs para terceiros.
  4. Safety layer ainda report-only.
- **Veredito honesto:** o **engine é tecnicamente empacotável** (package.json, MIT, 2 deps limpas, testes, `src/` portável), mas a **comercialização externa está bloqueada por compliance + fronteira física + docs**, não por qualidade de código.

## 2. Produto vendável — escopo
`src/` (MCP server + tools) · `config/` (env/path resolver) · `scripts/safety/` (report-only) · `external_factors_v2/{collectors,config,agents}` (EF context engine + contracts) · `docs/project_authority` + `docs/strategy_governance` (governance/validation contracts) · `skills/` (Agentic OS skills) · docs de uso · package skeleton futuro.

## 3. Privado / não vendável (comprador leva motor, não edge)
Estratégias do Cris · rulers · RTSE · research · RAW/source · logs/backtests · backups · private runtime (alert-bridge, EF v2 daemon) · LaunchAgents/plists · EF v2 `.venv-agents` · Telegram/live bridge · outputs privados · **qualquer edge/alpha**.

## 4. Readiness matrix
| Componente | Path | Status | Comm. value | IP risk | Portab. | Dep risk | Docs | Tests | Ação | Prio | Blocker? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MCP server | `src/` | maduro | ALTO | baixo | ✅ (0 hardcodes) | baixo (2 deps: mcp-sdk, chrome-remote-interface) | README pessoal | 5 tests ✅ | README comercial + separar | P1 | Não (técnico) |
| Config/env layer | `config/` | novo, testado | ALTO | baixo | ✅ byte-idêntico | nenhum | CONFIG_ENV_CONTRACT ✅ | test_paths ✅ | — | P1 | Não |
| Safety scanners | `scripts/safety/` | report-only | médio | baixo | ✅ stdlib | nenhum | USAGE ✅ | manual | maturar | P2 | Não |
| EF context engine | `external_factors_v2/collectors+config+agents` | operacional | ALTO | médio (keys) | ✅ relativo | keys externas | AGENTS_ENV_REGEN | — | separar de runtime + secrets policy | P2 | Parcial |
| Governance/validation contracts | `docs/project_authority`,`docs/strategy_governance` | maduro | ALTO | baixo | n/a | nenhum | próprios | n/a | curar p/ produto | P2 | Não |
| Skills | `skills/` | maduro | médio | baixo | ✅ | nenhum | próprios | — | curar produto vs privado | P3 | Não |
| Packaging | `package.json`+lock, LICENSE(MIT) | existe | — | — | ✅ | — | — | `npm test` | Docker/onboarding | P2 | Parcial |
| Fronteira física product/private | (só documental) | não aplicada | — | **ALTO** | — | — | plano ✅ | — | 4C quando embalar | P1 | **SIM** (p/ externo) |
| Compliance (TradingView ToS/market-data) | README disclaimer | restritivo | — | — | — | — | disclaimer ✅ | — | parecer legal | P0 | **SIM** (p/ externo) |

## 5. Blockers reais para venda externa
- **[P0] Compliance/legal:** ToS TradingView + market-data + disclaimer atual "personal/educational/research only" e anti-reselling. **Sem parecer legal + reposicionamento, não há release externo.**
- **[P1] Fronteira física não aplicada:** product vs private ainda misturados no repo → risco de empacotar alpha/RAW/IP. (Fase 4C ou package manifest resolve.)
- **[P1] Sem pacote instalável limpo p/ terceiros** (só `npm` local; sem install guide/onboarding).
- **[P1] Sem docs comerciais:** README comercial, install, security model, data policy, risk/no-advice disclaimer dedicado.
- **[P2] Safety layer report-only** (sem gate); **secrets policy** não formalizada; sem Docker/devcontainer; sem testes do *package* (só do MCP).
- **[P2] EF v2 depende de venv/keys**; separar engine (collectors/contracts) do runtime (daemon/plist).
- **[P3] Paths privados remanescentes** fora do produto (research morto) — não bloqueia o engine, mas confirmar que nenhum entra no pacote.

## 6. Non-blockers (não impedem empacotar o engine)
Hardcodes em research morto · RAW privado (não empacotado) · RTSE privado · cold storage externo · scripts históricos · **o WARNING único do Caminho B** (SLIM-contaminated) — desde que fique FORA do produto (é private/research; ver Decisão 6 da sessão).

## 7. Package candidates (não mover agora)
`product_core/src` · `product_core/config` · `product_core/external_factors` (collectors+contracts) · `product_core/safety` · `product_core/docs` (governance/uso) · `product_core/skills`.

## 8. Minimal commercial package proposal — "Trading Agentic OS Engine Lite"
MCP server + config/env + EF **context** engine + safety scanners (report-only) + governance contracts + skills/templates. **Sem** strategy edge · **sem** RAW · **sem** broker automation (default off) · **sem** live execution. É o "motor sem edge" — o que se pode mostrar/licenciar sem revelar alpha, sujeito a resolução do blocker P0.

## 9. Commercial architecture target (plano, não execução)
```
product_core/        (src, config, external_factors[collectors+contracts], safety, skills, docs)
private_alpha/       (strategies, rulers, RTSE, research)
private_runtime/     (alert-bridge, EF v2 daemon, plists)
research_archive/    (historical/one-off)
data_private/        (RAW pointers, ground-truth)
docs/  scripts/safety/  config/
```

## 10. Required docs checklist (a criar)
README comercial · install guide · `.env.example` guide (já há `.env.example`) · security model · data policy (há `docs/architecture/DATA_STORAGE_POLICY.md` — adaptar) · risk/no-financial-advice disclaimer dedicado · MCP setup · External Factor setup · Supabase future plan · safety checks usage (já há) · product/private boundary (já há plano) · restore/cold storage note (já há manifest) · contribution/governance.

## 11. Security & compliance risks
- Trading system pode ser lido como **financial advice** → disclaimer forte obrigatório.
- **Broker automation deve estar explicitamente desativada** por default no pacote.
- Secrets **nunca no repo** (`.env` gitignored ✅; EF keys em `.env` do módulo ✅) — formalizar policy.
- RAW privado **fora do produto**.
- Logs podem conter dados sensíveis → não empacotar `logs/`.
- Supabase futuro precisa **RLS + secrets policy**.
- MCP tools = permissões mínimas; safety blocking gradual.
- **TradingView market-data**: não redistribuir dados; o produto é uma ponte de automação local, não um feed.

## 12. Recommended next phases
A. **Este audit** (agora). · B. README comercial + install/security docs. · C. Product skeleton plan (manifest, sem mover). · D. Fase 4C move físico **só quando embalar**. · E. CI report-only. · F. Supabase memory design. · G. (opcional) Docker/devcontainer. · H. (opcional) camada hosted/comercial.

## 13. Go / No-Go
| Nível | Estado | Falta |
|---|---|---|
| Empacotamento **interno** (uso próprio) | **GO** | nada crítico (README pessoal já serve) |
| **Demo privada** (mostrar engine a 1 parceiro, sem entregar) | **GO com cautela** | esconder private/alpha; usar Engine Lite conceptual |
| **Venda externa** (entregar pacote) | **NO-GO** | P0 compliance/legal + P1 fronteira física + docs comerciais |
| **Automação com cliente** (execução) | **NO-GO** | tudo acima + broker-off + security/RLS + safety blocking + parecer legal |

## 14. Riscos e rollback
Doc-only → rollback = apagar este doc; nenhum runtime afetado. Fronteira produto/privado respeitada (nada de alpha exposto aqui). Blockers claros; próximos passos mínimos definidos (secção 12).

---
**Conclusão:** o **engine está pronto para pacote interno/demonstração**; a **venda externa depende primeiro de resolver compliance (P0) e aplicar a fronteira física + docs comerciais**. Recomendação de ordem: primeiro **docs comerciais + parecer de compliance**, depois product skeleton, e só então 4C/Supabase.
