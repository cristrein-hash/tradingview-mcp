#!/bin/zsh
# ENTRY ROUTER 15M — ciclo LIVE em modo DRY (Cris 2026-07-19). Roteia camada de entry por regime macro
# (autoridade Layer1 1D). B em RANGE · Cp cobre BEAR · A1/A2 pendentes. SEM Telegram (dry, forward-ledger).
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_15m_long/ENTRY_ROUTER" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
exec /usr/bin/python3 run_router_cycle.py
