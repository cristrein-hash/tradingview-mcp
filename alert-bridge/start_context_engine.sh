#!/bin/zsh
# Wrapper launchd do E0 Context Engine (Camada 2 P3). Produz market_context.json (0 tokens, não emite
# sinais). caffeinate independente (robusto se o P1 parar). Instância única = pidfile + launchd KeepAlive.
set -u
DIR="/Users/cristrein/tradingview-mcp/alert-bridge"
cd "$DIR" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
exec /usr/bin/caffeinate -dimsu python3 -u context_engine.py
