# Runbook — Realtime Monitor P1 (Camada 1-A: alertas de nível)

**Estado:** ATIVO (LaunchAgent `com.cristrein.realtime-monitor`, 2026-07-16). Daemon 24h, determinístico,
0 tokens, alerta-only, ZERO auto-trade. Lê preço via MCP (`quote_get`) a cada 5s e alerta no Telegram
quando o `last` cruza um nível armado. Ver spec `docs/superpowers/specs/2026-07-16-realtime-monitoring-architecture-design.md`.

## Armar / desarmar níveis
Via terminal OU via ponte Telegram (o `claude -p` chama o helper):
```
python3 alert-bridge/arm_level.py arm 4012 cross_below --note "break-and-run"   # one_shot por defeito
python3 alert-bridge/arm_level.py arm 4050 cross_above --no-oneshot --cooldown 600
python3 alert-bridge/arm_level.py list
python3 alert-bridge/arm_level.py disarm 4012        # por preço ou por id
```
Estado em `alert-bridge/logs/levels.json` (hot-reload por mtime; escrita atómica). Histerese default 10 ticks.

## Pausar / retomar / matar (kill-switch 3 camadas)
1. `touch alert-bridge/logs/monitor.pause` → log-only imediato (não compara, não alerta). Retomar: `rm`.
2. O daemon também honra `/tmp/claude_recheck.paused` (as ferramentas de chart-work pausam-no de graça).
3. Paragem total: `launchctl unload -w ~/Library/LaunchAgents/com.cristrein.realtime-monitor.plist`.

## Coexistência com chart-work (IMPORTANTE)
`quote_get` lê o preço do **gráfico ativo**. Antes de plotar/replay/trocar símbolo: `touch logs/monitor.pause`
(ou usar as ferramentas que já tocam `/tmp/claude_recheck.paused`). Guarda automática: se o gráfico sair de
XAUUSD ou entrar em replay, o daemon vai a `CHART_HIJACKED` (não dispara) até normalizar — nunca gera lixo.

## Watchdog
- `🔴 MONITOR CEGO` (Telegram 3×) se o CDP morrer após respawns → nunca falha em silêncio.
- `⚠️ degradado` / `🟢 recuperado` nas transições. Heartbeat em `logs/launchd_realtime_monitor_stdout.log`.
- `caffeinate -dimsu` no wrapper mantém o Mac/tela acordados enquanto o daemon vive.

## Verificação / rollback
- Saúde: `launchctl list | grep realtime-monitor` (status 0) · heartbeats no stdout log · `--selftest-mcp`.
- Rollback: `monitor.pause` (parar alertas) → `launchctl unload` (parar daemon) → apagar ficheiros (isolados, zero impacto).
- Auditoria de disparos: `alert-bridge/logs/realtime_monitor_alerts.jsonl`.

## Âmbito P1 vs futuro
P1 = só níveis estáticos (preço absoluto). Condições de engine (Cp/A1/A2/L1/L2) = P2. Dossiê MTF + detetor
Camada 2 = P3-P6. Shorts = quando construídos.
