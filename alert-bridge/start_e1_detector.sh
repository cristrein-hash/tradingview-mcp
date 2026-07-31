#!/bin/zsh
set -u
cd "/Users/cristrein/tradingview-mcp/alert-bridge" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
# gap #1 stacked zones (Cris 2026-07-27): flag ON nos DOIS daemons (context constrói, e1 consome)
export E1_STACKED_ZONES=1
export E1_BOS_CONTINUATION=1   # 2ª quebra = confirmação (Cris 2026-07-31); shadow, E2 julga cada candidato
exec python3 -u e1_detector.py
