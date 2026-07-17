#!/bin/zsh
# L2/BPT cycle wrapper — PRODUÇÃO (go-live Cris 2026-07-17, DA causalidade PASS + paridades V-1..V-4).
# Destravas executadas 2026-07-17: (1) L2_PRODUCTION_AUTHORIZED=1; (2) --send-telegram;
# (3) L2_BPT_ZONE_TREND_EXIT registado no core/group_model_xau.py (XAU_240); (4) plist carregado.
# Tab-pinning only: run_l2_cycle pina a tab 4H via TVMCP_TARGET_CHART_ID; tab ausente = HARD_STOP.
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_4h_long/reversal/L2_BPT_ZONE_TREND_EXIT" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export L2_PRODUCTION_AUTHORIZED=1

exec /usr/bin/python3 run_l2_cycle.py --once --send-telegram
