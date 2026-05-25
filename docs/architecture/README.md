# Architecture

Documentation of the live trading system's operational architecture.

> Snapshot as-of **2026-05-25**. See [OPERATIONAL_INVENTORY.md](./OPERATIONAL_INVENTORY.md)
> for the full script/LaunchAgent inventory.

## Hosts

- **MacBook — primary host.** Runs everything operational: the webhook **receiver**, the
  **cloudflared** tunnel, **TradingView Desktop** + the **MCP server**, the **monitors**, the
  data **pipeline**, and **all LaunchAgents**.
- **iMac — auxiliary only.** Runs the **External Factors bridge** (HTTP server logging external
  factors). Nothing else operational depends on it.

## Ingress flow (external TradingView alerts)

```
TradingView alert
   │  (webhook POST)
   ▼
https://webhook.tdwclaudestrategy.org/webhook/<secret>
   │  cloudflared named tunnel  (LaunchAgent com.cristrein.cloudflared-tunnel, KeepAlive)
   ▼
127.0.0.1:8787  tv_webhook_receiver.py   (LaunchAgent com.cristrein.tv-webhook-receiver)
   │  spawns
   ▼
claude_recheck.py   →  Telegram / logs / setup tracking
```

- The real `TV_WEBHOOK_SECRET` lives in `alert-bridge/.env` (loaded by `start_receiver.sh`).
- The legacy `/webhook/local-test` endpoint is **disabled** (returns 403).

## MCP / TradingView automation

```
Claude / monitors / backtests  ←→  src/server.js (MCP, stdio)  ←→  CDP :9222  ←→  TradingView Desktop
```

- MCP server is hardened with per-operation CDP timeouts (no infinite hangs).
- `tv_launch` performs a real hard restart (kills a wedged instance before relaunch).

## Operational runbooks

- **Backtest maintenance window:** `alert-bridge/safe_backtest_window.sh --smoke`
  (pause production → restart TradingView → smoke → always restore).
- **Stack health-check:** `ops/start_trading_stack.sh --check` (read-only);
  `--start` restarts a down service via supervised `launchctl kickstart`.

## Scheduled jobs (LaunchAgents)

| Job | When |
|---|---|
| `enrich-indicator-outcomes` | daily 03:00 |
| `d2r-daily` | daily 04:00 |
| `archive-weekly` | Sun 04:00 |
| `weekly-review` | Sun 09:00 |

Resident: `tv-webhook-receiver`, `cloudflared-tunnel`, `xau-4h-monitor-daemon`.
