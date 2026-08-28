#!/bin/zsh
# AMD LIVE F1+F2 — detetor H4 sweep + candidatos 1H, Ping-1/Ping-2 Telegram (Cris 2026-07-19, PRODUÇÃO).
# Alert-only, nunca negoceia, read-only (store-first). Baixa-frequência (raro).
set -u
cd "/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_amd/amd_live" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export AMD_PRODUCTION_AUTHORIZED=0   # SHADOW (Cris 28/08: valida em que regime funciona; nunca envia)   # LIVE — Ping-1/Ping-2 enviam Telegram (Cris autorizou produção já)
export L1_PRODUCTION_AUTHORIZED=1    # hard-lock do telegram_notify (defensivo)
exec /usr/bin/python3 run_amd_cycle.py
