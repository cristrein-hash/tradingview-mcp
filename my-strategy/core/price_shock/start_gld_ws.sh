#!/bin/zsh
# FINNHUB GLD WEBSOCKET — 2ª fonte de choque sub-segundo (horas US). Daemon persistente (KeepAlive).
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/core/price_shock" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export L1_PRODUCTION_AUTHORIZED=1   # hard-lock do telegram_notify (só wrapper autoriza)
set -a; source /Users/cristrein/tradingview-mcp/.env 2>/dev/null || true; set +a   # FINNHUB_API_KEY durável a restart
exec /usr/bin/python3 finnhub_gld_ws.py
