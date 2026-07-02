# PRODUCTION LOGIC RE-AUDIT — 2026-07-02

**Modo:** read-only / doc-only. **Nada tocado:** sem kill/load/unload/rm/mv/edit/backtest/Telegram. Só `launchctl list`, `ps`, `ls/stat`, `grep`, `curl /health` (GET), safety report.
**Base:** `AGENTIC_OS_PORTABILITY_CHECKPOINT_20260702.md`, `04_STRATEGY_STATUS_MASTER.md`, memória.

## 1. Executive verdict
**`PRODUCTION_LOGIC_PARTIALLY_CLEAR`** (honesto, sem maquiar).
- O **runtime vivo é estreito e claro**: receiver + cloudflared tunnel + EF v2 (passive-logging) + MCP server. **Nada executa trades; não há auto-trading.**
- A **camada de estratégias está largamente DORMANT/SUPERSEDED**: `xau-l1-cycle` PAUSADO, `monitor_xau_4h` não a correr, cron vazio, logs XAU 4H stale (10 jun). As estratégias que a memória antiga chamava "coração do sistema hoje" (2026-06-03) **não estão vivas em runtime**.
- **Risco principal = drift docs/memória vs runtime** (docs afirmam produção onde o runtime mostra dormência). Não é risco de execução; é risco de *interpretação*.

## 2. Live runtime inventory
| Item | Serviço/processo | Função | Última atividade | Status | DO_NOT_TOUCH |
|---|---|---|---|---|---|
| Receiver | `com.cristrein.tv-webhook-receiver` (PID 841, py3.9) | ingest webhooks TV; `/health` ok (`claude_recheck:true`, `secret_configured:true`, `legacy_endpoint_enabled:false`) | vivo agora; logs `indicator_signals`/`tradingview_alerts` 24 jun | **LIVE** | **SIM** |
| Tunnel | `com.cristrein.cloudflared-tunnel` (PID 1033) | webhook público | vivo | **LIVE** | **SIM** |
| EF v2 daemon | `com.cristrein.external-factors-v2` (loaded) | coleta contexto externo (30min) | **snapshots 2 jul 14:36 — HOJE** | **LIVE** (passive) | **SIM** |
| MCP server | `node src/server.js` (PID) | ponte CDP↔TradingView (esta sessão) | vivo | LIVE (ferramenta) | cuidado |
| Weekly archive | `com.cristrein.archive-weekly` (loaded) | arquivamento semanal | periódico | LIVE (weekly) | SIM |
| L1 cycle | `com.cristrein.xau-l1-cycle.plist` (**NÃO carregado**) | scanner L1 XAU 4H | **PAUSADO** (logs 10 jun) | **DORMANT** | SIM (não religar sem autorização) |
| XAU 4H monitor | `monitor_xau_4h_strategies.py` (não em `ps`) | monitor 4 estratégias | código 15 jun; não a correr | **DORMANT** | SIM |
| cron | (vazio) | — | — | **inexistente** | — |

## 3. Production strategy inventory
| Estratégia | Classificação | Evidência |
|---|---|---|
| L2/BPT XAU 4H V2 zona-pura | **APPROVED_NOT_PRODUCTION** | §4.4 status master; OK final Cris 2026-07-02; não wired |
| XAU 15M swept-runner (+ #4, 8ATR, regime-v5) | **APPROVED_NOT_PRODUCTION / RESEARCH** | memória; research, não em runtime |
| XAUUSD_4H_BREAKOUT_CONTINUATION (D1A) | **ACTIVE_CANDIDATE / LIVE_DORMANT** | status master §3; runtime dormant |
| V1.4g-RWS-A6-A7 REVERSAL_LONG | **SUPERSEDED / DORMANT** | "OFICIAL 2026-06-03" na memória MAS xau-l1 pausado + monitor off |
| Caminho B LONG (bottom catcher) | **SUPERSEDED / CONTAMINATED** | status master SUSPECT/CRITICAL (SLIM); dormant |
| Regime Classifier B v3 | **DORMANT (context only)** | informa contexto; LONG não usa gate |
| L1 EMA21 Continuation | **APPROVED_NOT_PRODUCTION / PAUSED** | xau-l1-cycle pausado |
| External Factors v2 | **LIVE (passive-logging, NÃO integrado ao trading)** | daemon cycling; gate Fase 4 |
| Legacy Pines / REVERSAL_CAPITULATION / DEMAND_BREAKOUT | **REJECTED / DEPRECATED** | status master §3 |

## 4. Production dataflow map (vivo)
```
TradingView (chart) --webhook--> cloudflared tunnel --> tv-webhook-receiver (LIVE)
   --> logs/ (indicator_signals, tradingview_alerts)  [ingest passivo]
EF v2 daemon (LIVE) --> external_factors_v2/snapshots/{external_context,latest,theory_*}.json  [contexto passivo, NÃO ligado a trade]
MCP server (src/server.js) <-> CDP <-> TradingView Desktop  [ferramenta on-demand]
```
DORMANT (não no fluxo vivo): monitor_xau_4h, xau-l1 scanner, claude_recheck (logs 1 jun), backtests, Telegram auto-dispatch.
Separação: **live runtime** (receiver/tunnel/EF/MCP) · **research** (regime_turnstate_engine, my-strategy, research) · **validation** (RAW rulers) · **private alpha** (estratégias/RTSE).

## 5. Files/path safety map
- `DO_NOT_TOUCH_PRODUCTION`: `alert-bridge/tv_webhook_receiver.py`, `start_receiver.sh`, `alert-bridge/logs/` raiz (vivos), plists (`tv-webhook-receiver`, `cloudflared-tunnel`, `external-factors-v2`, `archive-weekly`, `xau-l1-cycle`).
- `DO_NOT_TOUCH_RUNTIME`: `external_factors_v2/runtime/` + `.venv-agents` + `snapshots/`.
- `DO_NOT_TOUCH_RAW`: `/Volumes/GUTS_ LACIE/TradingData`, rulers `my-strategy/research/revalidation/*/results/`.
- `PRIVATE_ALPHA`: `regime_turnstate_engine/`, `my-strategy/strategies|research/`.
- `RESEARCH_ONLY`: `research/`, phase scripts.
- `HISTORICAL_ONLY`: SLIM cluster (banners), Caminho A/B docs.
- `SAFE_DOC_ONLY`: `docs/architecture`, `docs/governance`, `docs/cleanup`.
- `COLD_STORED`: `alert-bridge/logs/backtests` (arquivado), `backups/` (arquivado).

## 6. Telegram / receiver audit
- Receiver **vivo** (`/health` ok). Logs vivos `indicator_signals.jsonl`, `tradingview_alerts.jsonl` (24 jun).
- Telegram: 8 scripts referenciam telegram (`auto_d2r_daily`, `claude_recheck`, `evaluate_setup_outcomes`, `research_status`, `monitor_xau_4h_strategies`, `setup_watch_manager`, `tv_webhook_receiver`, `weekly_review`) → **capacidade de envio presente, mas os emissores (monitor/recheck/d2r) estão DORMANT** (não a correr). Risco de notificação automática = baixo agora (dispatch default-deny + monitor off).
- **Não alterado.** Não remover logs vivos. Confirmar comportamento exato de dispatch fica para runbook (fora deste read-only).

## 7. EF v2 audit
- Daemon **vivo** (`com.cristrein.external-factors-v2`), venv mantido (`.venv-agents`, KEEP_RUNTIME_DEPENDENCY), collectors 7, snapshots frescos (2 jul 14:36), `external_context.json` + `latest.json` + `theory_*`.
- Ciclo ~30min; inputs keyless + keys em `.env` do módulo; output = contexto passivo.
- Status: **product/private hybrid** (engine=collectors/contracts=produto; runtime/daemon/snapshots=privado). **NÃO integrado ao trading** (passive-logging).
- Riscos: chaves em `.env` (ok, gitignored); não redistribuir. **Não alterado.**

## 8. L1 production audit
- `L1 EMA21 Continuation` — **APPROVED_NOT_PRODUCTION**; `xau-l1-cycle` **PAUSADO** (plist não carregado; logs 10 jun). Memória `xau_l1_paused_2026_06_23`: "não religar sem autorização".
- Scanner/candidate/Telegram/journal: **dormant** (não a correr). Ficheiros ativos = scripts em `alert-bridge/` (dormant). Forbidden: religar sem autorização; editar estratégia. **Backtest NÃO revalidado (fora de escopo).**

## 9. L2/BPT / Reader audit
- **RESEARCH / APPROVED_NOT_PRODUCTION.** Reader Vivo = research; **sem Telegram, sem produção, sem runtime.** Sem policy/backtest exceto sob protocolo. Próximos blocos lógicos: slippage+2024 antes de OFICIAL_FN; relação com **XAU SHORT** (espelho, pendente). Estratégia estrutural V2 = OK final mas NOT_PRODUCTION.

## 10. Contaminated / deprecated audit
| Item | Estado | Ação recomendada |
|---|---|---|
| SLIM cluster (`extract_replay_features`, `build_crosstf`, 2 backtests) | HISTORICAL_COMPATIBILITY (RAW-in-memory p/ D1A) | keep + banner; DELETE se D1A abandonado |
| `caminho_b/reentry_agent_A_targetstop.py` | CONTAMINATED (lê slim_features) — **WARNING no safety report** | quarentena/historical; revalidar RAW se reativado; **fora do produto** |
| Caminho A/B iterations | SUPERSEDED | historical-only (arquivadas na memória) |
| REVERSAL_CAPITULATION / DEMAND_BREAKOUT / legacy Pines | REJECTED/DEPRECATED | manter registo, não usar |
| DEACTIVATED (Oracle, SMC-BTC, bubbles-nas shadow, ZONE_TOUCH) | DEAD | não usar |

## 11. Safety layer alignment
`python scripts/safety/run_safety_report.py` → **BLOCKER=0 · WARNING=1 · INFO=45 · exit 0.**
- Único WARNING = `caminho_b/reentry_agent_A_targetstop.py` (SLIM) = **research contaminado, FORA do produto e do runtime vivo** → NÃO impacta produção.
- Paths de produção protegidos pelo `check_forbidden_paths` (0 findings). Safety alinhado com este audit; sem updates necessários agora.

## 12. Gaps / risks
1. **Docs/memória vs runtime drift** — memória antiga chamava V1.4g/Caminho B/Regime v3 "coração do sistema" mas estão DORMANT. (Mitigado parcialmente pelo tiering do MEMORY.md + este audit.)
2. **Status master parcialmente desatualizado** — não reflete que a camada de estratégia 4H está dormant nem o OK-final do L2/BPT em runtime terms.
3. **"catalog"/"strategy_rules"** referenciados em guards/CLAUDE.md **não existem como ficheiro** localizável (só `claude_recheck.py`) → guard aponta para conceito, não ficheiro vivo. Verificar.
4. **Telegram dispatch** — capacidade em 8 scripts, emissores dormant; comportamento exato não documentado num runbook.
5. **Sem production manifest / runbook** de start/stop dos serviços vivos.
6. Paths hardcoded ainda em código research (não produção) — não bloqueia.

## 13. Recommendations
- **A. Governança imediata (no-code):** anotar no `04_STRATEGY_STATUS_MASTER.md` que a camada de estratégia 4H está DORMANT e o runtime vivo = receiver+tunnel+EF v2+MCP (só sob tua ordem).
- **B. Production runbook/safety docs:** start/stop dos 5 serviços + regra receiver + "não religar xau-l1 sem autorização" (doc-only).
- **C. Status master corrections:** L2/BPT §4.4 (feito) + marcar V1.4g/Caminho B/Regime v3 como DORMANT/SUPERSEDED.
- **D. Runtime cleanup candidates:** nenhum urgente (logs pesados já em cold storage).
- **E. XAU SHORT prereqs:** boundary produção/research agora claro → SHORT é research puro (não toca runtime); pode começar como research quando autorizares.
- **F. Supabase prereqs:** eventos reais = receiver logs + EF snapshots + decisions/checkpoints → schema `external_factor_events`/`task_runs`/`decisions` mapeável; RAW fica fonte.
- **G. Package prereqs:** engine (MCP+EF collectors+config+safety) separável do runtime privado; compliance P0 pendente.

## 14. Go / No-Go próxima fase
| Ação | Decisão |
|---|---|
| Criar **XAU SHORT research** | **GO** (research puro; não toca runtime; boundary claro) |
| Mexer em produção | **NO-GO sem runbook + autorização** (receiver/EF/tunnel vivos) |
| Supabase implementation | **GO para `schema.sql` draft (doc)**; setup real depois |
| Fase 4C (move físico) | **NO-GO agora** (organizacional; adiado) |
| Commercial package | **NO-GO** (compliance P0) |

## 15. Evidence appendix (comandos read-only usados)
`launchctl list | grep cristrein` · `crontab -l` (vazio) · `ls ~/Library/LaunchAgents` · `ps aux | grep …` · `ls -lt alert-bridge/logs` + `external_factors_v2/snapshots` · `find alert-bridge -iname catalog/strategy_rules/recheck` · `grep -l telegram alert-bridge/*.py` · `curl -s /health` (GET) · `python scripts/safety/run_safety_report.py`. **Nenhum comando de escrita; nenhum serviço alterado.**

---
**Conclusão:** runtime vivo = receiver + tunnel + EF v2 (passivo) + MCP; **nada auto-negocia**. Estratégias 4H antigas = DORMANT/SUPERSEDED; L2/BPT + 15M = APPROVED_NOT_PRODUCTION; D1A = ACTIVE_CANDIDATE dormant. **XAU SHORT research = GO** (não toca produção). Antes de mexer em produção: runbook + autorização.
