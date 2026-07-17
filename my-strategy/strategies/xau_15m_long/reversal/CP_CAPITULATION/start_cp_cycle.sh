#!/bin/zsh
# Cp CAPITULATION — ciclo live alert-only (Cris autorizou produção 2026-07-17).
# CP_PRODUCTION_AUTHORIZED=1: envia Telegram nas entradas novas. Tab-pinned 15M, read-only,
# coexiste com E0/E1/E2 (não troca chart, não pausa). Baseline congelado; forward = árbitro.
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export CP_PRODUCTION_AUTHORIZED=1
export L1_PRODUCTION_AUTHORIZED=1   # hard-lock do telegram_notify (reuso, mesmo padrão do regime engine)
exec /usr/bin/python3 run_cp_cycle.py
