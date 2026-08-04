#!/bin/zsh
# VALIDADOR DE ENTRADA (Cris 2026-08-04) — fulltime/realtime/paralelo. GO/ESPERA/INVALIDOU nos niveis do Cris.
set -u
DIR="/Users/cristrein/tradingview-mcp/alert-bridge"
cd "$DIR" || exit 1
set -a; source .env 2>/dev/null || true; source ../.env 2>/dev/null || true; set +a
unset ANTHROPIC_API_KEY
export EV_TG_AUTHORIZED=1     # GO da validacao vai ao Telegram (ordem Cris: apoio realtime)
exec /usr/bin/python3 -u entry_validator.py
