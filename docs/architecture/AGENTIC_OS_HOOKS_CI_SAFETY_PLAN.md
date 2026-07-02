# AGENTIC OS — HOOKS / CI SAFETY LAYER PLAN (Etapa 1, doc-only)

**Data:** 2026-07-02 · **Natureza:** planeamento. **Sem código, sem hooks instalados, sem produção/runtime tocado.** Referência de estado: `AGENTIC_OS_PORTABILITY_CHECKPOINT_20260702.md`.
**Princípio:** começar **report-only**, nunca bloqueio agressivo. Guardrails para impedir regressões numa futura sessão/agent.

## Contexto (o que já existe — NÃO duplicar)
Hooks **pessoais** em `~/.claude/hooks/` (fora do repo, prompt-level): `post_backtest_devils_advocate.py`, `pre_analysis_myopia_guard.py`, `pre_approval_guard.py`, `systematic_error_guards.py` (+ `GUARDS.md`). São guardas de comportamento do Claude, ligados à máquina do Cris.
**Gap:** não há camada **repo-level, portável e versionada** que um CI ou outra máquina/comprador possa correr. Esta camada preenche isso, **complementando** (não substituindo) os hooks pessoais. Sem `.github/workflows`, `scripts/safety/`, `docs/governance/` hoje.

## 1. Objetivo
Proteger produção · reforçar RAW/source-first · impedir regressões SLIM/derived · exigir manifest p/ backtests sérios · garantir rastreabilidade · preparar o Agentic OS para automação segura. **Tudo report-only na 1ª fase.**

## 2. Camadas de proteção
| Camada | Papel | Fase |
|---|---|---|
| Repo scanners (`scripts/safety/*.py`) | leem árvore/diff, geram relatório | Etapa 2 (report-only) |
| Claude Code hooks (pessoais, já existem) | prompt-level DA/myopia/approval | já ativo (não tocar) |
| pre-commit (opcional) | correr scanners em report-only | futuro, opt-in |
| GitHub Actions (report-only) | `workflow_dispatch`, sem secrets, não bloqueia PR | Etapa 2 opcional |
| Forbidden-paths / input / product-write scanners | ver §6 | Etapa 2 |
| Manifest/report checker | backtest sem manifest, resultado sem sanity | Etapa 2 (check_backtest_manifest) |

## 3. Paths proibidos ou gated (BLOCKER/gated no scanner)
`alert-bridge/` (receiver/webhook/evaluator/monitors + logs raiz vivos) · `strategy_rules` · `catalog` · `monitor` · `Telegram/receiver` · `runtime` · LaunchAgents/`*.plist` · `external_factors_v2/runtime` + `.venv-agents` + snapshots · RAW/source (`/Volumes/GUTS_ LACIE/TradingData`, rulers) · D1A/Breakout Continuation live inputs · quaisquer ficheiros de broker/write/execução.

## 4. Patterns proibidos ou suspeitos
- SLIM como **validação** (BLOCKER) — exceto docs históricos autorizados (`docs/cleanup/*`, incidentes) = INFO/HISTORICAL.
- derived/proxy como source of truth (BLOCKER).
- `/Users/cristrein`, `/Volumes`, `/tmp`-persistente **em paths de produto** (`src/`, `config/`, EF collectors/config/contracts) (WARNING/BLOCKER). **Research/private NÃO é blocker.**
- `rm -rf`, `git clean`, moves destrutivos, writes a live inputs (WARNING → gated).
- backtest sem manifest; resultado reportado sem sanity checks (WARNING).

## 5. Política de severidade
`BLOCKER` (nunca sem aprovação) · `WARNING` (revisar) · `INFO` (contexto/histórico) · `ALLOWED_WITH_APPROVAL` (gated). Na Etapa 2 **nada bloqueia** — severidade é só rótulo no relatório.

## 6. Modo inicial
**Report-only.** Sem blocking · sem alterar produção · **nenhum hook instalado no runtime vivo sem aprovação** · GitHub Action (se criada) = `workflow_dispatch` report-only, sem secrets, não gate de PR/push.

## 7. Critérios para passar de report-only → blocking
scanner estável · false positives revistos e allowlist documentada · aprovação explícita do Cris · nunca automático.

## 8. Artefactos propostos (Etapa 2, aditivos)
- `scripts/safety/check_forbidden_paths.py`
- `scripts/safety/check_slim_policy.py`
- `scripts/safety/check_hardcoded_product_paths.py`
- `scripts/safety/run_safety_report.py` (agrega + tabela)
- `docs/governance/SAFETY_LAYER_USAGE.md`
- (opcional) `.github/workflows/safety-report.yml` — só se seguro/aditivo, `workflow_dispatch`, sem secrets, não-bloqueante.
- `check_backtest_manifest.py` / `check_raw_source_policy.py` = fase posterior (após os 3 base estabilizarem).

## 9. Riscos
falso positivo · bloquear research legítimo · confundir private alpha com product core · quebrar CI por deps locais (mitigar: scanners stdlib-only, sem deps) · scan pesado (mitigar: só ler texto tracked, excluir node_modules/venv/logs) · **expor paths privados em logs públicos** (mitigar: relatório fica local/`reports/`, Action não imprime conteúdo sensível).

## 10. Rollback
Apagar `scripts/safety/` + `docs/governance/` + workflow · desativar Action · **nenhum runtime/produção afetado** (tudo aditivo, report-only).

---

## Implementação mínima proposta (Etapa 2, se plano aprovado)
Começar só com **A + B + C + agregador D**, todos report-only, stdlib-only:
- **A. `check_forbidden_paths.py`** — reporta ficheiros/mudanças que toquem paths perigosos (§3).
- **B. `check_slim_policy.py`** — reporta SLIM em contexto de validação; docs/cleanup + incidentes = INFO/HISTORICAL (não erro).
- **C. `check_hardcoded_product_paths.py`** — reporta `/Users/cristrein`,`/Volumes`,`/tmp` só em **product-core** (`src/`, `config/`, EF collectors/config/contracts); research/private ≠ blocker.
- **D. `run_safety_report.py`** — agrega e imprime tabela `SEVERIDADE | file | line/pattern | reason | recommended action`; exit code **sempre 0** (report-only).

## Pré-análise obrigatória antes da Etapa 2 (a apresentar)
1. lista dos checks · 2. ficheiros lidos · 3. dirs escaneados · 4. dirs excluídos · 5. runtime esperado · 6. risco de false positive · 7. formato do relatório · 8. Action sim/não · 9. como desativar · 10. rollback. **Se houver risco de tocar produção/runtime → parar.**

## Critérios de aceitação (Etapa 2)
scripts aditivos · report-only (exit 0) · zero produção/runtime/RAW tocado · relatório útil · false positives classificados · rollback simples.
