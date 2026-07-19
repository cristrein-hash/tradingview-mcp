#!/bin/zsh
# LAYER1 LIVE SERVICE — regime macro 1D (BULL/BEAR/RANGE) causal p/ router 15M + E0/E2 (Cris 2026-07-19).
# Pura computação sobre ficheiros do bar-store (zero MCP/CDP/Telegram). Matemática congelada intocada.
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/core/layer1_service" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
exec /usr/bin/python3 layer1_cycle.py
