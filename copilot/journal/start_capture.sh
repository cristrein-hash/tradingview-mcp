#!/bin/zsh
# COPILOT/JOURNAL — captura de trades read-only (P1). Poller + resolve. NUNCA negoceia/alerta/pausa o chart.
set -u
cd "/Users/cristrein/tradingview-mcp/copilot/journal" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
exec /usr/bin/python3 capture_trades.py
