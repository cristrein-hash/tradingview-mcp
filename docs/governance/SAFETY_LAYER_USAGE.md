# AGENTIC OS — SAFETY LAYER USAGE (report-only)

**Data:** 2026-07-02 · **Modo:** REPORT-ONLY (nunca bloqueia; exit 0 sempre). Plano: `docs/architecture/AGENTIC_OS_HOOKS_CI_SAFETY_PLAN.md`.
**Natureza:** scanners aditivos, stdlib-only, read-only (só lêem ficheiros **tracked** via `git ls-files`; gitignored — logs vivos/venv/backups/node_modules — ficam fora automaticamente).

## Como correr
```bash
python scripts/safety/run_safety_report.py     # relatório agregado (recomendado)
# ou individualmente:
python scripts/safety/check_forbidden_paths.py
python scripts/safety/check_slim_policy.py
python scripts/safety/check_hardcoded_product_paths.py
```
Saída: tabela `SEVERITY | check | file:line | reason` + sumário. **Exit 0 sempre.** Nada é bloqueado, nada é escrito fora do stdout.

## Checks
- **check_forbidden_paths** — write/destructive ops (`open(...,'w')`, `.write`, `json.dump`, `rm -rf`, `git clean`, `launchctl`, `shutil/os.remove`) que referenciam alvos proibidos (`strategy_rules`, `catalog`, `receiver`, `telegram`, `.plist`, `raw_replay`, `/Volumes/GUTS`, `alert-bridge/logs`, `external_factors_v2/runtime`, `.venv-agents`). BLOCKER p/ os mais críticos, senão WARNING.
- **check_slim_policy** — SLIM consumido como dado/validação. Historical/guard/docs autorizados = **INFO** (docs/cleanup, incidentes, banner `HISTORICAL_COMPATIBILITY`/`SLIM_MODE_FORBIDDEN`, `_source_guard`, `never_use_slim`). Código que consome slim sem banner = WARNING.
- **check_hardcoded_product_paths** — `/Users/cristrein`,`/Volumes`,`/tmp` **só** em product-core (`src/`,`config/`,`skills/`,`tests/`,`external_factors_v2/{collectors,config,agents}`). Research/private NÃO é alvo. `config/paths.py`/`.env.example`/teste = INFO (defaults by-design).

## Baseline (2026-07-02, HEAD a05c177)
`BLOCKER=0 · WARNING=12 · INFO=33 · total=45`.
- WARNINGs = maioritariamente **docs/rulers de research** (README/methodology/SKILL.md) que descrevem a antiga pipeline SLIM, + 1 script do cluster histórico sem banner (`scripts/backtest_xau_4h_demand_breakout_v2.py`). Nenhum é produção/runtime.
- INFOs = defaults do resolver + docs + cluster histórico bannerizado + `_source_guard`.

## Falsos-positivos conhecidos (calibrar antes de promover a blocking)
1. `.md` de research fora de `docs/` (ex.: `my-strategy/research/**/README.md`, `methodology.md`) são classificados WARNING; são **documentação histórica** → deveriam ser INFO. Refinamento: tratar todos os `.md` como doc-INFO, ou allowlistar `my-strategy/research/**/*.md`.
2. `scripts/backtest_xau_4h_demand_breakout_v2.py` + `backtest_xau_4h_breakout_continuation_v1.py` pertencem ao **cluster HISTORICAL** (sustentam D1A) mas não têm banner → aparecem WARNING. Opções: adicionar banner (como nos 2 core) ou allowlist.

## Critérios para passar report-only → blocking (NÃO agora)
scanner estável · falsos-positivos acima revistos + allowlist documentada · aprovação explícita do Cris. Só então considerar exit-code não-zero / pre-commit / gate de CI.

## Desativar / rollback
Não correr; ou `rm -rf scripts/safety docs/governance`. Nenhum runtime/produção afetado (tudo aditivo, report-only, sem instalação em hooks vivos).

## Fora de escopo (por agora)
GitHub Action (proposta no plano, não criada) · pre-commit global · blocking · `check_backtest_manifest`/`check_raw_source_policy` (fase posterior).
