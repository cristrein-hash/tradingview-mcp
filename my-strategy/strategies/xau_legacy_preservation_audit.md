# AUDIT — Preservação do conhecimento XAU legacy + prontidão p/ decommission (2026-06-16, read-only)

## 1. Veredito
- **Preservação suficiente? PARCIAL → SUFICIENTE para arquivar/desconectar legacy sem perder conhecimento**, com 1 ressalva: a captura mais rica vive na **memória da sessão** (`~/.claude/.../memory/`, 27 arquivos), **não versionada no repo**. Para permanência repo-side antes de DELETAR pesquisa, consolidar um índice (1º bloco abaixo).
- **Podemos começar a limpar legacies? PARCIAL — SIM para o já-neutralizado; NÃO para deletar pesquisa/RAW.** O legacy perigoso JÁ está neutralizado nesta sessão (recheck:931, catalog reconciliado, Telegram default-deny, daemons dormant). Não há legacy operacional inseguro restante. O que sobra é majoritariamente KEEP_REFERENCE + HARD_STOP.

## 2. O que já está preservado (knowledge capture)
- **27 memory files** (`project_xau_4h_*`, `project_caminho_*`, etc.) — hipótese, gates reais, razão de aprovação/rejeição, erros aprendidos, métricas, status. **Mais rico, mas em `~/.claude` (não repo).**
- **`catalog.json`** (21 estratégias) — validation_status × deployment_status + evidence/candidate_packet (21) + notes (5, incl. razões de rejeição de DEMAND/CAPITULATION).
- **`docs/LEGACY_KNOWLEDGE_REGISTER.md`** + **`docs/FUTURE_CORE_BOUNDARY.md`** — features/métricas/processos reusáveis + hipóteses-a-não-repetir + 4 baldes.
- **`candidates/`** packets (caminho_b, reversal a6/a7, regime_classifier_v3) + **`research/revalidation/`** (rebuilds) + **safety pack** `~/Desktop/TRADING/L2_REBOOT_SAFETY_PACK_2026-06-09`.

## 3. Classificação por família XAU antiga
| Família | Preservação | Categoria | Nota |
|---|---|---|---|
| XAU 4H LONG continuation (antiga) | memory + L1 STRATEGY/MANIFEST | **PRESERVED_OK** | superseded pela nova L1 |
| DEMAND_BREAKOUT | memory + catalog notes (razão rejeição) | **PRESERVED_OK / ARCHIVE_AFTER_CAPTURE** | REJECTED |
| REVERSAL_CAPITULATION | memory + catalog (PF 0.47) | **PRESERVED_OK / ARCHIVE_AFTER_CAPTURE** | REJECTED |
| SWEEP / reversal discretionary | memory + monitor (dormant) | **PRESERVED_PARTIAL / KEEP_REFERENCE** | lógica no monitor dormant |
| BB confluence (INTRADAY) | revalidation + catalog | **PRESERVED_PARTIAL / KEEP_FOR_REVALIDATION** | RESEARCH |
| L2 / BPT / Reason Atlas | safety pack 366 + memory | **PRESERVED_OK / KEEP_REFERENCE** | |
| regime_B v1/v2/v3 (morto) | archive `dead_regime_B_v3/` + regime_l1 README | **PRESERVED_OK (arquivado)** | já arquivado |
| Family A/B/C (Caminho A/B/C) | memory (B v1.5/v1.6 detalhado) + candidates | **PRESERVED_OK / KEEP_REFERENCE** | |
| XAU 1H (DEMAND_RECLAIM) | memory + revalidation | **KEEP_FOR_REVALIDATION** | frente pausada |
| XAU 15M/30M (pending) | md stubs + replay datasets | **KEEP_FOR_REVALIDATION** | potencial futuro |

→ Nenhuma família em **NEEDS_KNOWLEDGE_CAPTURE urgente** (todas têm memory + catalog/candidates). Risco real só se a memória `~/.claude` for perdida sem índice repo-side.

## 4. Legacy operacional — estado e classificação
| Componente | Estado | Categoria |
|---|---|---|
| `tv_webhook_receiver.py` (PID 841) + cloudflared (1033) | **VIVO** (ingestão + event store) | **KEEP_OPERATIONAL** (infra/`indicator_signals.jsonl`) |
| `weekly-review` + `archive-weekly` LaunchAgents | **carregados** (manutenção) | **KEEP_REFERENCE** (verificar se enviam Telegram — não-estratégia) |
| `claude_recheck.py` (recheck:931 neutralizado) | dormant/pausado | **KEEP_REFERENCE / DECOMMISSION_CANDIDATE futuro** |
| `monitor_xau_4h_strategies.py` | dormant (Telegram default-deny) | **KEEP_REFERENCE** |
| `strategy_rules.json` / `catalog.json` (runtime) | descritivo/referência | **KEEP_REFERENCE** |
| XAU daemon/cron · d2r · external-factors plists | dormant/arquivados (backups/launchagents_archive) | **ARCHIVE (feito) / DO_NOT_REACTIVATE** |
| old regime_B_v3 pipeline | arquivado last block | **ARCHIVE (feito)** |

## 5. Source-of-truth — HARD_STOP_DO_NOT_TOUCH
- **RAW externo** (`/Volumes/GUTS_ LACIE/TradingData/`) + **8 v6 dumps** + **manifests/checksums** + **dataset_registry**.
- **`indicator_signals.jsonl`** (event store) + **`tradingview_alerts.jsonl`** (journal vivo).
- **Novo:** `regime_l1/xau_daily_l1v4.jsonl` + classifications + journal/outcome novos + `.runtime_state/`.

## 6. Dependências do novo sistema (confirmado isolado)
A nova L1 **NÃO depende** de strategy_rules / catalog / claude_recheck / monitor legacy / regime_B_v3 / enrich-outcomes / RAW-via-runtime / XAU daemon / external-factors (grep operacional = 0 refs, exceto comentários). Scheduler novo (`com.cristrein.xau-l1-cycle`) **isolado e único**. Telegram novo usa `telegram_notify` (allowlist + dedup), **não** o fluxo recheck/receiver.

## 7. Riscos de limpar cedo demais
- **Perder a memória `~/.claude`** sem índice repo-side → perda da captura mais rica. **Mitigar antes de deletar pesquisa.**
- **Deletar candidates/research** antes de inventariar o que será reavaliado (XAU 1H/15M/30M são KEEP_FOR_REVALIDATION).
- **Desligar receiver/cloudflared** quebraria o event store `indicator_signals.jsonl` (ainda alimentado).
- **Apagar RAW/manifests** = irreversível, quebra reprodutibilidade.

## 8. Primeiro bloco seguro recomendado (NÃO executar aqui)
**"Consolidar índice repo-side de preservação XAU legacy"** — bloco read-mostly, reversível:
1. Criar **1 doc no repo** (`docs/XAU_LEGACY_KNOWLEDGE_INDEX.md`) que **aponta**, por estratégia/família: o memory file fonte, a entrada no catalog, o packet em candidates, o status (PRESERVED/REVALIDATION) e a razão de aprovação/rejeição — **copiando o essencial** da memória `~/.claude` para o repo (permanência).
2. **Auditar weekly-review/archive-weekly** (read-only): confirmar que não enviam Telegram de estratégia nem tocam o novo fluxo.
**Só depois** disso (com knowledge no repo) faz sentido um bloco de **archive** de scripts legacy mortos não-operacionais. **Nada de deletar research/RAW.**
