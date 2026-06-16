# INVENTÁRIO READ-ONLY DOS UNTRACKED (Trading System)

**Gerado:** 2026-06-16 · **Natureza:** auditoria read-only. **Nada foi alterado, movido, deletado, adicionado ao git ou gitignored.**
**Base:** `git status --untracked-files=all` após commit `4f5df26`. Recomendações são **propostas para bloco futuro**, não ações.

## Resumo executivo
- **6 grupos, ~14,5 MB no total** de arquivos untracked (o "1,4 G" de `alert-bridge/logs` é a pasta inteira, dominada por logs vivos **gitignored** — não por estes untracked). Maior arquivo untracked = 2,9 MB. **Nenhum grande demais para git.**
- **Nenhum secret/token/credencial real.** Único match foi a string de **teste** `"test_new_secret"` (payload de teste, benigno) e a palavra `broker` em **texto de nota de enriquecimento** ("Broker/source mismatch"). Campo `provider:PEPPERSTONE` é metadado de roteamento, não credencial.
- **Nenhum processo vivo com handle aberto** em qualquer untracked (`lsof` limpo). Nenhum é escrito por daemon/scheduler.
- **Nenhum é o RAW source-of-truth** (RAW de replay vive no HD externo `/Volumes/GUTS_ LACIE/`). Nenhum hard stop disparado.
- `.gitignore:14` = `alert-bridge/logs/*.jsonl` ignora a store viva (extensão `.jsonl`), mas **não** pega os snapshots (sufixo `.before_synthetic_cleanup…`) nem a subpasta `signal_outcomes_lab/` — por isso aparecem untracked.
- `candidates/` e `research/` **não** são gitignored (tracking possível sem `-f`). `research/` já tem 175 arquivos tracked; `candidates/` só 2 stubs `.md` tracked.

## Classificação por grupo

### 1. `alert-bridge/logs/` — snapshots de backup + Signal Outcome Lab (~4,2 MB untracked)
| Arquivo | Tam | Data | Tipo | Recomendação |
|---|---|---|---|---|
| `indicator_signals.jsonl.before_synthetic_cleanup_2026-05-28` | 2,9M | 05-28 | backup pré-cleanup do event store | **ARCHIVE_CANDIDATE** → cold storage, depois GITIGNORE |
| `indicator_signals_outcomes.jsonl.contaminated_pre_pepperstone_fix_2026-05-28` | 412K | 05-26 | backup contaminado (pré-fix) | **ARCHIVE_CANDIDATE** |
| `indicator_signals_quarantined.jsonl.before_synthetic_cleanup_2026-05-28` | 4K | 05-28 | backup quarantine | **ARCHIVE_CANDIDATE** |
| `signal_outcomes_lab/outcomes_current.jsonl` (+manifest) | 200K | 05-28 | seed do outcome engine (72 CLEAN) | **KEEP_UNTRACKED** (forward seed, referenciado em memory) |
| `signal_outcomes_lab/backfill_*/` (3 dirs: handpick_3xau, xau_full, xau_full_v2) | ~600K | 05-28 | backfills + manifests + comparison reports | **ARCHIVE_CANDIDATE** (têm manifest; preservar como histórico) |
- **Logs vivos:** NÃO (snapshots datados 05-26/05-28, sem handle). São backups point-in-time dos eventos `before_synthetic_cleanup` / `pre_pepperstone_fix`.
- **Convenção:** a pasta `logs/` fica **fora do git** por design (dados). Não versionar. Forensicamente úteis → arquivar em cold storage; o Lab seed pode permanecer untracked vivo.
- **Risco se versionar:** bloat do repo com dados de backup que pertencem a cold storage.

### 2. `my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/` (~4,2 MB, 06-14/06-15)
| Conteúdo | Recomendação |
|---|---|
| `rebuild_v1/v2/v3`: README, config.json, `rebuild_*.py`, summary.json, candidates_pre_cooldown.jsonl | **TRACK_IN_REPO** |
- **Outputs de pesquisa:** SIM — é a **proveniência da L1 operacional** (decisão de remover R_CEIL, calibração do gate RSI). `summary.json` marcado `NOT_VALIDATION` / `DA_verdict: NEEDS_CAUSAL_FILTER` (honesto, in-sample).
- **Necessário para reavaliação futura:** SIM — documenta como a regra-base/SL da estratégia viva foi reconstruída.
- `research/` já é tracked (175 arquivos) → esta árvore é uma adição natural. Arquivos pequenos, reprodutíveis. **Versionar (código + summaries + config + READMEs + jsonl pequenos).**

### 3. `my-strategy/strategies/candidates/regime_classifier_v3/` (2,6 MB, 06-03)
| Arquivo | Tam | Recomendação |
|---|---|---|
| `regime_classifier_B_v2.py`, `regime_classifier_B_v3.py` | 8K cada | **TRACK_IN_REPO** (referência; regime_B_v3 morto como autoridade mas KEEP_REFERENCE) |
| `regime_B_v3_runs_2024plus.jsonl` | 8K | TRACK_IN_REPO |
| `regime_B_v3_classifications.jsonl` (1,7M), `xau_daily_with_features.jsonl` (760K), `xau_weekly_with_features.jsonl` (152K) | grandes/regeneráveis | **ARCHIVE_CANDIDATE** ou GITIGNORE (regeneráveis a partir do código) |
- **Estratégia útil?** Conhecimento de referência: regime_B_v3 foi **substituído** por `regime_L1_v4` como autoridade operacional; código preservado como caso-escola (índice legacy = KEEP_REFERENCE / `dead_regime_B_v3`).
- **Risco:** versionar os `.jsonl` grandes regeneráveis = bloat. Versionar só o código.

### 4. `my-strategy/strategies/candidates/xau_4h_caminho_b_long/` (1,5 MB, 06-03)
| Conteúdo | Recomendação |
|---|---|
| `caminho_b_*.jsonl` (251_full, FINAL_anti_demand_rsi30, with_dead_hours, +sweet_spot, OPTIMIZED, monumentais), `reentry/` (losers, summary.json, `reentry_agent_A_targetstop.py`) | **TRACK_IN_REPO** |
- **Candidato/estratégia XAU útil?** SIM — Caminho B (BOTTOM CATCHER) é **OFICIAL em memory** (KEEP_FOR_REVALIDATION), ainda **não migrado** ao novo core. São candidate packets (input canônico do strategy-research-analyst). Pequenos. **Versionar.**

### 5. `my-strategy/strategies/candidates/xau_4h_reversal_v1_4g_rws_a6/` (2,0 MB) + `…_a6_a7/` (180 K), 06-03
| Conteúdo | Recomendação |
|---|---|
| `README.md`, `plot_script.py`, `v14g_rws_2023plus_with_a6_flag.jsonl`, `v14g_rws_enriched_2016_2026.jsonl`, `v14g_rws_a6_a7_2016_2026.jsonl` | **TRACK_IN_REPO** |
| `v1_base_trades_2016_2026.jsonl` (1,8M) | TRACK_IN_REPO ou ARCHIVE (regenerável; aceitável p/ git) |
- **Útil?** SIM — `v1_4g_rws_a6_a7` é a **OFICIAL ATUAL do Caminho A LONG (REVERSAL)** em memory. Candidate packet de alto valor. **Versionar** (o base_trades 1,8M é o único candidato a arquivar se quiser enxugar).

## Maiores riscos
1. **Bloat de repo** se os backups de `logs/` e os `.jsonl` grandes regeneráveis (regime_B_v3) forem versionados — pertencem a cold storage, não a git.
2. **Falso-positivo de secret:** a string `test_new_secret` pode assustar scans futuros. **Não é credencial** — é payload de teste. Documentado aqui para evitar pânico.
3. **Perda de proveniência** se a research L1 (grupo 2) ou os candidate packets oficiais (grupos 4/5) forem deixados untracked indefinidamente e perdidos num cleanup — estão **fora do git** e **fora de cold storage** hoje (só no disco local). É o risco real mais alto: conhecimento oficial sem backup versionado.

## Recomendações consolidadas (para bloco futuro — NÃO executadas)
| Ação | Grupos |
|---|---|
| **TRACK_IN_REPO** (alto valor, pequeno, proveniência) | research/revalidation L1 (g2); caminho_b code+jsonl (g4); reversal a6/a6_a7 code+flags (g5); regime_v3 `.py` (g3) |
| **ARCHIVE_CANDIDATE** (cold storage, depois remover/ignorar) | snapshots de backup do event store (g1); `.jsonl` grandes regeneráveis do regime_B_v3 (g3); base_trades 1,8M (g5, opcional) |
| **KEEP_UNTRACKED** (seed forward vivo) | `signal_outcomes_lab/outcomes_current.*` (g1) |
| **GITIGNORE** (após arquivar, p/ limpar `git status`) | padrão p/ `alert-bridge/logs/*.before_*`, `*.contaminated_*`, `signal_outcomes_lab/` (g1) |
| **HARD_STOP_DO_NOT_TOUCH** | nenhum encontrado neste conjunto (a store viva `indicator_signals.jsonl` já é gitignored e NÃO está neste inventário) |

## O que NÃO deve ser tocado (mesmo fora deste inventário)
Event store vivo `alert-bridge/logs/indicator_signals.jsonl` (gitignored, HARD_STOP), RAW externo, manifests/checksums, receiver, scheduler. Nenhum desses está entre os untracked auditados.

**Nenhum arquivo foi removido, movido ou modificado neste bloco.**
