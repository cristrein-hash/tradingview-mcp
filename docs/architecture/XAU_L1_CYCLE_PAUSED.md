# XAU L1 CYCLE — PAUSADO INTENCIONALMENTE

**Data:** 2026-06-23
**Motivo:** sessão de plotagem/leitura do Reader Vivo (Cluster 2 — macro negativo runner vs trap). L1 não é necessária agora; mantê-la ativa enquanto mexemos no chart via CDP/MCP é risco operacional gratuito (colisão daemon×chart).

## Estado
- `com.cristrein.xau-l1-cycle` → **PAUSADO** via `launchctl bootout gui/$UID ~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist`.
- **NÃO tocados (seguem ativos):** `com.cristrein.tv-webhook-receiver` (pid 841), `com.cristrein.cloudflared-tunnel` (pid 1033).
- MCP `src/server.js` vivo (necessário p/ plotagem desta sessão).

## ⚠️ NÃO RELIGAR sem autorização do Cris
Para religar (somente com autorização explícita):
```
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist
```
Verificar: `launchctl list | grep com.cristrein.xau-l1-cycle`.
