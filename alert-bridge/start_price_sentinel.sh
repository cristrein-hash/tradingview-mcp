#!/bin/zsh
# SENTINELA DE PREÇO (Cris 2026-08-04) — quote MCP ~15s, linha só em cruzamento de nível do mapa. 0 Fable.
set -u
DIR="/Users/cristrein/tradingview-mcp/alert-bridge"
cd "$DIR" || exit 1
set -a; source .env 2>/dev/null || true; source ../.env 2>/dev/null || true; set +a
export SENTINEL_TG_AUTHORIZED=1    # entrada realtime do break vai ao Telegram (ordem Cris 05/08)
exec /usr/bin/python3 -u price_sentinel.py
