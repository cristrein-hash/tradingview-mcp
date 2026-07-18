#!/bin/zsh
# STACK WATCHDOG — anti-cegueira-silenciosa (Cris 2026-07-18). Telegram na transição cego/recuperado.
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/core/stack_watchdog" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export L1_PRODUCTION_AUTHORIZED=1   # hard-lock do telegram_notify (reuso)
exec /usr/bin/python3 stack_watchdog.py
