#!/bin/zsh
# READER DE VELA CONSTANTE (Cris 2026-08-04, opção B): Opus lê cada vela 5M/15M/1H → log. Telegram OFF
# por defeito (só sinal confirmado, e só quando CANDLE_TG_AUTHORIZED=1 for explicitamente ligado).
set -u
DIR="/Users/cristrein/tradingview-mcp/alert-bridge"
cd "$DIR" || exit 1
set -a; source .env 2>/dev/null || true; source ../.env 2>/dev/null || true; set +a
unset ANTHROPIC_API_KEY          # sessão Max (subscrição), não API key
export CANDLE_TG_AUTHORIZED=1    # Telegram ON (ordem Cris 2026-08-04) — SÓ sinal confirmado (is_confirmed)
exec /usr/bin/python3 -u candle_reader.py
