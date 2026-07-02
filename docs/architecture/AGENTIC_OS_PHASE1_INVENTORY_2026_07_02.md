# AGENTIC OS — FASE 1: INVENTÁRIO READ-ONLY + CLASSIFICAÇÃO

**Data:** 2026-07-02
**Proveniência:** varredura read-only automatizada do repo (ferramenta de fan-out do Claude Code, general-purpose). **Nada foi editado, movido ou apagado.** Serve para aprovar (ou não) cortes numa fase posterior. Todos os candidatos a limpeza = `needs_user_approval`.
**Contexto:** ver `TRADING_SYSTEM_AGENTIC_OS_MEMORY_v1.md` (direção + DECISÃO A).

## Resumo executivo
- Repo total: **2,7 GB**, **2.323 ficheiros git-tracked**, só 2 untracked-não-ignorados.
- **~95% dos bytes já são gitignored** (logs, `.venv`, backups, snapshots, node_modules). Footprint de código versionado é modesto.
- **Conclusão:** limpeza ≈ **cold-storage de dumps de dados**, NÃO deleção de código. O "primeira fase a sujar" é menor do que o receio.
- **Bloqueador #1 de comercialização = portabilidade:** 248 ficheiros `.py` hardcodam `/Users/cristrein/`, 193 `/tmp/`, 63 `/Volumes/`. Espalhado (sem ficheiro-choke) → precisa camada de config/env repo-wide.
- **Ativos VIVOS confirmados (NÃO tocar):** `regime_turnstate_engine/` (RTSE aprovado), `external_factors_v2/` (EF v2 operacional), `docs/project_authority/`+`docs/strategy_governance/` (governança), `my-strategy/research/revalidation/*/results/` (rulers RAW).

## A) Mapa top-level
| Área | Tamanho | Ficheiros (tracked) | Papel |
|---|---|---|---|
| `alert-bridge/` | 2,2 G | 299 (135) | PRODUÇÃO receiver/webhook/evaluator; 2,2G = `logs/backtests/` (gitignored) |
| `external_factors_v2/` | 265 M | 2765 (39) | PRODUÇÃO EF v2 daemon; 259M = `.venv-agents` (gitignored) |
| `my-strategy/` | 130 M | 1195 (1080) | Código + `research/revalidation` rulers RAW (120M) |
| `research/` | 47 M | 648 | Lab `xau_15m_bb_nas_leonardo` (kickoff) |
| `backups/` | 32 M | 150 (0) | Snapshots backup — untracked/gitignored |
| `node_modules/` | 26 M | — | Deps JS do MCP (regeneráveis) |
| `screenshots/` | 6,9 M | 31 (0) | Screenshots (gitignored) |
| `regime_turnstate_engine/` | 2,5 M | 126 | RTSE aprovado + ground_truth + validation |
| `docs/` | 1,9 M | 198 | Governança + reports |
| `eval_tmp/` `.tmp_enrich/` `.cache_eval/` | <1,2 M | 0 tracked | Temp stale (~5 semanas), gitignored |

## B) Classificação (resumo — conservador; dúvida = NO_TOUCH)
| Área | Classe | Ação | Aprovação |
|---|---|---|---|
| `regime_turnstate_engine/` (core, ground_truth, docs) | RESEARCH_VALID | NO_TOUCH | — |
| `regime_turnstate_engine/validation/*` (phaseNN, _DA_) | RESEARCH_EXPLORATORY | KEEP | N |
| `external_factors_v2/` (collectors/runtime/config) | PRODUCTION | NO_TOUCH | — |
| `external_factors_v2/.venv-agents` (259M) | TEMP_LOCAL | DELETE_CANDIDATE (regen) | Y |
| `alert-bridge/` (receiver/recheck/evaluator/monitors) | PRODUCTION | NO_TOUCH | — |
| `alert-bridge/logs/backtests/` (2,2G) | COLD_STORAGE | mover p/ cold storage (gzip+SHA256+manifest) | Y |
| `alert-bridge/logs/*.before_* / *.contaminated_* / *_synthetic_cleanup*` | SUPERSEDED | ARCHIVE | Y |
| `alert-bridge/alert_templates.backup.20260523-*` | SUPERSEDED | ARCHIVE (dup) | Y |
| `alert-bridge/archive/legacy_monitors` | DECOMMISSIONED | ARCHIVE | N |
| `docs/project_authority/` + `docs/strategy_governance/` | GOVERNANCE | NO_TOUCH | — |
| `my-strategy/research/revalidation/*/results/` | SOURCE_OF_TRUTH | NO_TOUCH | — |
| `my-strategy/strategies/candidates/` | RESEARCH_VALID | KEEP | N |
| `docs/XAU_4H_BREAKOUT_D1A_*` (~15) | RESEARCH_EXPLORATORY | KEEP (rever) | N |
| `docs/BOOTSTRAP_REARCHITECTURE_CANONICAL_CONTEXT*` (2 quase-dup) | SUPERSEDED? | KEEP (dedupe rever) | N |
| `scripts/` slim producers/consumers (`extract_replay_features.py`, `build_crosstf_dataset.py`, slim backtests) | SUSPECT_CONTAMINATED | QUARANTINE (rever vs trava SLIM) | Y |
| `research/xau_15m_bb_nas_leonardo/` (47M) | RESEARCH_EXPLORATORY | KEEP (gate proveniência aberto; `_source_guard.py` já bloqueia slim) | N |
| `backups/` (dated snapshots) | SUPERSEDED | COLD_STORAGE | Y |
| `eval_tmp/` `.tmp_enrich/` `.cache_eval/` | TEMP_LOCAL | DELETE_CANDIDATE (stale) | Y |
| `archive/one_off_migrations` | DECOMMISSIONED | ARCHIVE | N |
| `screenshots/` (6,9M) | TEMP_LOCAL | COLD_STORAGE/prune | Y |
| `src/` `tests/` `skills/` `ops/` (+ `.claude/` runtime dirs) | PRODUCTION/GOVERNANCE | NO_TOUCH | — |

## C) Portabilidade (bloqueador de comercialização)
Paths absolutos hardcoded em `.py` (excl. node_modules): **`/Users/cristrein/` = 248 ficheiros · `/tmp/` = 193 · `/Volumes/` = 63.** Espalhado (pior ofensor só 8 ocorrências) → precisa refactor repo-wide para camada de config/env (`paths.py`/resolução por env). A maioria dos `/Volumes/` e `/tmp/` vive em `scripts/` e `my-strategy/research/backtests/` (tier de pesquisa), NÃO nos daemons de produção (`alert-bridge`/`external_factors_v2`, que usam mais paths relativos/config).

## D) Top 10 candidatos a limpeza (TODOS needs_user_approval=Y — nada apagado agora)
| # | Candidato | Recupera | Ação sugerida |
|---|---|---|---|
| 1 | `alert-bridge/logs/backtests/` | ~2,2 G | Cold storage (gzip+SHA256+manifest, política) |
| 2 | `external_factors_v2/.venv-agents` | 259 M | Delete + documentar comando de regen |
| 3 | `backups/` (snapshots dated) | 32 M | Cold-storage archive |
| 4 | `research/xau_15m_bb_nas_leonardo/` dumps | ~40 M | Cold-storage se gate proveniência ficar aberto |
| 5 | `screenshots/` | 6,9 M | Cold-storage/prune |
| 6 | `alert-bridge/logs/*.before_*/*.contaminated_*/*_synthetic_cleanup*` | ~6 M | Archive |
| 7 | `eval_tmp/`+`.tmp_enrich/`+`.cache_eval/` | ~1,2 M | Delete (stale ~5 sem, gitignored) |
| 8 | `alert-bridge/alert_templates.backup.20260523-*` | 264 K | Archive (dup) |
| 9 | slim-pipeline scripts | pequeno | Quarentena + rever vs "NUNCA USAR SLIM" |
| 10 | `archive/one_off_migrations` + `alert-bridge/archive/legacy_monitors` | ~64 K | Confirmar morto → archive |

## Cautelas
- `research/.../_source_guard.py` **proíbe** slim (governança) → KEEP. Só os `scripts/` que escrevem/leem `slim_features/` = SUSPECT; verificar antes de qualquer ação.
- Onde incerto (D1A docs, bootstrap dup, snapshots a envelhecer) → KEEP/UNKNOWN, NO_TOUCH.
- **Nenhuma ação git/produção/backtest tomada.**
