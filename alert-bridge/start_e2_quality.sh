#!/bin/zsh
set -u
cd "/Users/cristrein/tradingview-mcp/alert-bridge" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
# GO-LIVE E2 (ordem Cris 2026-07-26): hard-lock de producao destravado aqui, auditavel e reversivel
export E2_PRODUCTION_AUTHORIZED=1
exec python3 -u e2_quality.py
