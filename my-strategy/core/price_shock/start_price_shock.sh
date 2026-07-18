#!/bin/zsh
# DETETOR DE CHOQUE DE PREÇO — gatilho realtime mais rápido (Cris 2026-07-18). Telegram na hora do choque.
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/core/price_shock" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export L1_PRODUCTION_AUTHORIZED=1   # hard-lock do telegram_notify (reuso)
exec /usr/bin/python3 price_shock_cycle.py
