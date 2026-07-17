#!/bin/zsh
# REGIME ENGINE — serviço de regime live permanente (Cris 2026-07-17).
# Corre 1 ciclo: append live 4H/1H -> detetor canónico -> regime atual + transições.
# REGIME_TELEGRAM=1 + L1_PRODUCTION_AUTHORIZED=1: alerta Telegram na VIRADA de regime.
# Tab-pinned (lê tabs 240/60 sem trocar chart, sem pausa). Coexiste com E0/E1/E2/L1/L2.
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/core/regime_engine" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export REGIME_TELEGRAM=1
export L1_PRODUCTION_AUTHORIZED=1
exec /usr/bin/python3 regime_engine_cycle.py --once
