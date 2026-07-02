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

## Baseline
- **Antes da calibração** (HEAD a05c177): `BLOCKER=0 · WARNING=12 · INFO=33 · total=45`.
- **Depois da calibração** (2026-07-02): `BLOCKER=0 · WARNING=1 · INFO=44 · total=45`.
- **Único WARNING remanescente = TRUE_RISK, mantido de propósito:** `my-strategy/strategies/candidates/xau_4h_caminho_b_long/reentry/reentry_agent_A_targetstop.py` lê `slim_features/*.jsonl` (Caminho B = `SUSPECT/CRITICAL` SLIM-contaminated no status master). Deve permanecer visível até revalidação RAW.

## Calibração aplicada (2026-07-02)
- **Scanner `.md`**: documentação que *descreve* SLIM = INFO; só WARNING se *prescrever* SLIM como validação (heurística `DANGEROUS_MD`) **e** sem contexto de negação (`NEG_MD` — "PROIBIDO/não usar/NÃO é validação/never"). Elimina falsos-positivos de docs que declaram a política anti-SLIM.
- **Allowlist D1A RAW-in-memory**: `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/*.py` = INFO (reutilizam o interpretador auditado sobre RAW; SLIM-file mode NÃO usado; D1A não é tocado).
- **Banner** adicionado a `scripts/backtest_xau_4h_demand_breakout_v2.py` (cluster histórico) → classificado INFO. (`breakout_continuation_v1.py` é D1A ACTIVE_CANDIDATE, não tocado; não dispara o scanner.)
- **Não escondido:** o Caminho B SLIM-contaminated permanece WARNING (TRUE_RISK).

## Critérios para passar report-only → blocking (NÃO agora)
scanner estável · falsos-positivos acima revistos + allowlist documentada · aprovação explícita do Cris. Só então considerar exit-code não-zero / pre-commit / gate de CI.

## Desativar / rollback
Não correr; ou `rm -rf scripts/safety docs/governance`. Nenhum runtime/produção afetado (tudo aditivo, report-only, sem instalação em hooks vivos).

## Fora de escopo (por agora)
GitHub Action (proposta no plano, não criada) · pre-commit global · blocking · `check_backtest_manifest`/`check_raw_source_policy` (fase posterior).
