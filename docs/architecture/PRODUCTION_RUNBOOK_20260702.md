# PRODUCTION RUNBOOK — 2026-07-02

**Modo:** doc-only. Referência operacional do runtime vivo. **Não altera comportamento.** Base: `PRODUCTION_LOGIC_REAUDIT_20260702.md`.
**Regra-mãe:** não iniciar/parar serviços, editar plists ou tocar runtime sem autorização explícita do Cris.

## 1. Current live runtime
| Serviço | LaunchAgent / processo | Estado | Nota |
|---|---|---|---|
| Receiver | `com.cristrein.tv-webhook-receiver` (py3.9, `tv_webhook_receiver.py`) | **LIVE** | `/health` ok; ingest webhooks TV; logs raiz vivos |
| Tunnel | `com.cristrein.cloudflared-tunnel` | **LIVE** | webhook público |
| External Factors v2 | `com.cristrein.external-factors-v2` | **LIVE (passivo)** | ciclo ~30min; snapshots frescos; NÃO ligado a trade |
| MCP server | `node src/server.js` | LIVE (ferramenta on-demand) | ponte CDP↔TradingView |
| Weekly archive | `com.cristrein.archive-weekly` | LIVE (weekly) | arquivamento |
| L1 cycle | `com.cristrein.xau-l1-cycle` | **PAUSED** (plist existe, não carregado) | não religar sem autorização |
| XAU 4H monitor | `monitor_xau_4h_strategies.py` | **DORMANT** (não a correr) | — |
| cron | — | **inexistente** (vazio) | — |

## 2. What is NOT live
- **NO auto-trading. NO broker execution. NO active strategy auto-execution.**
- L1 / camada 4H = **dormant/paused**.
- L2/BPT = **research / APPROVED_NOT_PRODUCTION**.
- XAU 15M swept-runner = **APPROVED_NOT_PRODUCTION** (research).
- D1A/Breakout Continuation = **ACTIVE_CANDIDATE / LIVE_DORMANT**.

## 3. Start/stop safety rules
- **Não iniciar/parar daemon sem autorização explícita.**
- Antes de tocar chart/produção: seguir production safety + `feedback_pause_daemon_and_cron` (pausar daemon **e** cron/scheduler).
- `alert-bridge/logs/` **raiz = logs vivos** (não apagar).
- `alert-bridge/logs/backtests/` está **cold-stored** (`COLD_STORAGE_MANIFEST_20260702.md`) — não confundir com logs vivos.
- EF v2 `.venv-agents` = **runtime dependency**; não apagar enquanto o daemon estiver ativo (regen: `AGENTS_ENV_REGEN.md`).

## 4. Read-only checks (seguros)
```bash
launchctl list | grep cristrein
ps aux | grep -E "tv_webhook|external_factor|cloudflared|server.js" | grep -v grep
curl -s http://127.0.0.1:8787/health        # receiver (GET, read-only)
ls -lt alert-bridge/logs/*.jsonl | head
ls -lt external_factors_v2/snapshots/*.json | head
git status --short
python scripts/safety/run_safety_report.py
```

## 5. Forbidden actions (sem autorização)
kill/unload/load de daemon · rm/mv em runtime · editar plists · editar Telegram/receiver · editar monitor · editar strategy runtime · apagar EF v2 venv · sobrescrever RAW/source/live inputs · backtest sério sem manifest.

## 6. Telegram / receiver notes
- Podem emitir Telegram (capacidade): `auto_d2r_daily`, `claude_recheck`, `evaluate_setup_outcomes`, `research_status`, `monitor_xau_4h_strategies`, `setup_watch_manager`, `tv_webhook_receiver`, `weekly_review`.
- **Emissores principais (monitor/recheck/d2r) = DORMANT** → risco de notificação automática baixo agora; dispatch default-deny.
- **Não tocar** logs vivos nem o receiver. Restart manual (se autorizado): `./start_receiver.sh` — **nunca** `python3 tv_webhook_receiver.py` direto (SECRET→403).

## 7. EF v2 notes
Daemon passivo/logging; collectors 7 (keyless + Alpha Vantage key no `.env`); snapshots `external_context.json`/`latest.json`/`theory_*`; env/keys em `.env` do módulo (gitignored); venv **mantido**. Não integrado ao trading.

## 8. Strategy state summary
| Módulo | Status | Runtime live? | Telegram? | Produção? | Próxima ação permitida |
|---|---|---|---|---|---|
| Receiver/Tunnel/MCP | LIVE infra | sim | receiver bridge | infra | manter; não tocar |
| External Factors v2 | LIVE passivo | sim | não (passivo) | não (contexto) | manter; não integrar sem gate |
| L1 EMA21 | APPROVED_NOT_PRODUCTION / PAUSED | não | não | não | não religar sem autorização |
| L2/BPT V2 | APPROVED_NOT_PRODUCTION | não | não | não | research; slippage+2024 p/ OFICIAL_FN |
| XAU 15M swept-runner | APPROVED_NOT_PRODUCTION | não | não | não | **próximo: 15M regime re-adaptation** |
| D1A/Breakout Cont. | ACTIVE_CANDIDATE / LIVE_DORMANT | não | não | não | rebuild RAW-traced (status master §4.1) |
| V1.4g / Caminho B / Regime v3 | DORMANT / SUPERSEDED / (Caminho B CONTAMINATED) | não | não | não | não usar; historical |

## 9. Recovery / rollback
- Reverter docs: `git checkout <doc>` ou reverter o commit.
- Restaurar cold storage: `COLD_STORAGE_MANIFEST_20260702.md` (SHA256 + `zstd -dc | tar -xf`).
- **Não confundir** logs vivos (`alert-bridge/logs/*.jsonl`) com backtests cold-stored (arquivados fora do repo).

## 10. Next governance actions
- Status master reconciliado (§3.1 + linhas EF v2 / XAU 15M) — feito.
- **XAU 15M LONG Regime Detector Re-Adaptation = próximo bloco** (research, read-only first).
- XAU SHORT research = **PENDING_AFTER_XAU_15M_LONG_REGIME_READAPTATION**.
- Supabase schema = após produção/research boundary (agora claro) + memory/dados.
