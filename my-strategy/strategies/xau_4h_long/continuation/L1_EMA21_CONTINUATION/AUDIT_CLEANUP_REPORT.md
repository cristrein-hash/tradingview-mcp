# AUDIT — XAU L1 system cleanup candidates (2026-06-16, read-only)

## 1. Executive summary
- **Sistema limpo? PARCIAL → operacionalmente SIM.** O caminho operacional (scheduler → runner → refresh → runtime → scanner/gate → telegram_notify) está **limpo, seguro e sem dependência legacy**. Restam poucos artefatos **não-operacionais** (tidiness), nenhum é risco.
- **Riscos reais:** **nenhum.** Sem ordem/broker ativo, sem scheduler duplicado, sem crash-loop, sem secret versionado, sem Telegram duplicável (dedup ok), XAU_60/15 inativos.
- **Ações recomendadas:** opcional — arquivar 1 pipeline de diagnóstico do regime morto + adicionar rotação de log. Nada urgente.

## 2. Inventory
**KEEP (essenciais operacionais):**
- `runtime_xau.py`, `run_l1_cycle.py`, `scanner.py`, `journal.py`, `outcome.py`, `telegram_notify.py`, `telegram_draft.py`
- `core/tv_read_adapter.py`, `core/group_model_xau.py`
- `core/regime_l1/` (regime_l1_v4.py, refresh_regime_l1_v4.py, xau_daily_l1v4.jsonl, .manifest.json, regime_l1_v4_classifications.jsonl)
- `core/regime/build_daily_features.py` (usado por regime_l1_v4)
- `com.cristrein.xau-l1-cycle.plist` (repo == instalada)

**Docs úteis (KEEP):** STRATEGY.md, MANIFEST.md, README.md (L1), OPERATING.md, core/regime_l1/README.md, core/regime/README.md.

**Estado vivo (KEEP, gitignored):** `.runtime_state/l1_cycle.log` (728B), `launchd_stdout/stderr.log`, dedup file (ainda não criado — sem candidato operacional).

## 3. Cleanup candidates
| Path | Categoria | Motivo | Risco remover | Validar antes |
|---|---|---|---|---|
| `core/regime/regime_pipeline.py` + `core/regime/README.md` | **KEEP_REFERENCE / ARCHIVE_CANDIDATE** | Reproduz o regime morto v2→v3 (diagnóstico do BLOCO 1). **Não-operacional** (regime_l1_v4 é a autoridade; não importa este). | Baixo (não usado em runtime) | confirmar que nada importa `regime_pipeline` |
| `core/input_normalization.py` + `core/live_input_adapter.py` + 2 testes | **KEEP (future-core) / CLEANUP_CANDIDATE** | Camada de **webhook live-input** (Production v2 futuro). **Não usada** pelo runtime atual (que usa `tv_read_adapter` MCP). Validada, limpa. | Baixo (mas é direção aprovada p/ futuro) | decidir se a ingestão futura será webhook (mantém) ou só MCP (arquiva) |
| `.runtime_state/*.log` | **CLEANUP_CANDIDATE (rotação)** | ~6 linhas/dia, sem rotação. Cresce devagar (~2KB/dia). | Baixo | adicionar rotação simples no futuro |
| `candidates/regime_classifier_v3/*` (regime_B_v3, v2/v3.py, xau_daily_with_features) | **RESEARCH_HISTORY (KEEP)** | Regime legacy morto + fonte OHLCV histórica usada uma vez p/ semear xau_daily_l1v4. Já classificado RESEARCH_HISTORY. | — (não tocar) | — |

**Nenhum** `.tmp/.bak/.old/.test/.debug`, nenhum pyc commitado, nenhum manifest/dataset duplicado no novo core.

## 4. Legacy contamination
**NENHUMA dependência legacy operacional.** Grep no caminho operacional (runtime/runner/adapter/regime_l1/refresh) → 0 refs a `regime_B_v3`/`strategy_rules`/`catalog`/`claude_recheck`/`monitor`/`enrich`/`raw_replay`/`combined_score`/`vol_entry_z` (exceto comentários documentando que NÃO se usa). A L1 não depende de: strategy_rules, catalog, recheck, monitor legacy, regime_B_v3 (autoridade), enrich/outcomes, RAW/v6, XAU daemon antigo, external factors. Receiver legacy só consultado para health (infra).

## 5. Scheduler audit
- **plist repo == instalada** (idênticas). **1 único** agente carregado (`com.cristrein.xau-l1-cycle`); sem duplicata.
- Horários (Lisboa local, DST-robusto): 03:05/07:05/11:05/15:05/19:05/23:05.
- `runs=1, last exit code=0` → **sem crash-loop**.
- **Dedup:** persistente em `.runtime_state/l1_dedup.txt` (1 linha/signal_hash) → ≤1 Telegram por barra. Sem risco de duplicata.
- **Conflito de chart:** o runner troca TF (240→D→240) a cada ciclo e restaura — pode atrapalhar uso manual do chart durante o ciclo (~15s, 6×/dia). Documentado no OPERATING.md. Mitigação futura = Python-puro (sem chart).

## 6. Security audit
- **Secrets:** nenhum `.env`/token/secret versionado; `alert-bridge/.env` IGNORED; nenhum token hardcoded.
- **Broker:** inativo; campos `broker`/`broker_order_id` no journal são só registro opcional (sem chamada de execução). Sem path de ordem.
- **Telegram:** só `telegram_notify` envia; allowlist = L1_EMA21_CONTINUATION; guard de frases proibidas; dedup. XAU_60/15 `telegram_allowed=[]`.
- **MCP:** só leitura (chart_get_state/ohlcv/study_values/pine_boxes) + set_timeframe com restauração. Sem trade management.
- **pause flag:** PRESENTE (intacta). **Produção:** receiver ok, cloudflared vivo, XAU legacy dormant.

## 7. Recommended next cleanup block (NÃO executar agora)
**Bloco único proposto:** "Archive dead-regime diagnostic + add L1 log rotation" —
(a) mover `core/regime/regime_pipeline.py`+README para um sub-balde de referência (ou marcar ARCHIVE no doc) já que reproduz o regime morto não-operacional;
(b) adicionar rotação simples ao `.runtime_state/l1_cycle.log` (truncar/rotacionar > N KB);
(c) decidir o destino de `input_normalization`/`live_input_adapter` (manter como future-core webhook OU arquivar se a ingestão for só-MCP).
Tudo gated, read-confirm antes de mover, sem tocar runtime/scheduler/produção.
