#!/bin/zsh
# Wrapper launchd do DAEMON de monitoração realtime XAU (P1). caffeinate -dimsu = Mac/tela não dormem
# ENQUANTO o daemon vive (autorizado Cris 2026-07-16). Valida .env sem imprimir. Instância única = pidfile
# no daemon + launchd KeepAlive. NÃO toca produção existente.
set -u
DIR="/Users/cristrein/tradingview-mcp/alert-bridge"
cd "$DIR" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

if ! grep -q '^TELEGRAM_BOT_TOKEN=' .env || ! grep -q '^TELEGRAM_CHAT_ID=' .env; then
  echo "FATAL: .env sem TELEGRAM_BOT_TOKEN e/ou TELEGRAM_CHAT_ID" >&2
  exit 1
fi

# caffeinate ligado ao ciclo de vida: -d tela, -i idle, -m disco, -s sistema, -u user-active
exec /usr/bin/caffeinate -dimsu python3 -u realtime_monitor.py
