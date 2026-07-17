#!/bin/zsh
# L1 EMA21 cycle wrapper — PRODUÇÃO (go-live Cris 2026-07-17; tab-pinning Cris 2026-07-17).
# (1) L1_PRODUCTION_AUTHORIZED=1 destrava o hard-lock de Telegram (runtime_xau.notify + telegram_notify).
# (2) --pin-tabs: refresh lê a tab 1D pinada e o runtime a tab 4H pinada (TVMCP_TARGET_CHART_ID) —
#     recurso geral de coexistência (Cris): ZERO troca de chart, ZERO pausa dos daemons E0/E1/E2.
#     Se as tabs 1D/4H não existirem, o run_l1_cycle cai sozinho no modo manage-chart antigo
#     (troca+restaura) e nesse caso ELE cria/remove a pausa dos daemons.
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export L1_PRODUCTION_AUTHORIZED=1

exec /usr/bin/python3 run_l1_cycle.py --pin-tabs --send-telegram
