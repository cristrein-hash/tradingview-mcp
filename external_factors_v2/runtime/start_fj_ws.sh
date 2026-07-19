#!/bin/zsh
# FINANCIAL JUICE WEBSOCKET — lane de contexto/curadoria (10min atraso). Daemon persistente (KeepAlive).
set -u
cd "/Users/cristrein/tradingview-mcp/external_factors_v2" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
set -a; [ -f ../.env ] && source ../.env; set +a   # FJ_API_KEY do .env (durável a restart do launchd)
exec /usr/bin/python3 collectors/fj_stream_ws.py
