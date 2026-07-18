#!/bin/zsh
# BAR-STORE — único leitor MCP/CDP do stack (Fase 1, Cris 2026-07-18).
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
exec /usr/bin/python3 bar_store_cycle.py
