#!/bin/zsh
set -u
cd "/Users/cristrein/tradingview-mcp/alert-bridge" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
# gap #1 stacked zones (Cris 2026-07-27): flag ON nos DOIS daemons (context constrói, e1 consome)
export E1_STACKED_ZONES=1
exec python3 -u e1_detector.py
