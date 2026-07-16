#!/bin/zsh
# Wrapper launchd da PONTE Telegram<->Claude. Valida .env, instância única, e exec do daemon em foreground
# (launchd supervisiona via KeepAlive). NÃO iniciar 2 instâncias (getUpdates conflita -> HTTP 409).
set -u
DIR="/Users/cristrein/tradingview-mcp/alert-bridge"
cd "$DIR" || exit 1
export PATH="$HOME/.local/bin:$PATH"

# valida chaves obrigatórias no .env (sem imprimir valores)
if ! grep -q '^TELEGRAM_BOT_TOKEN=' .env || ! grep -q '^AUTHORIZED_CHAT_ID=' .env; then
  echo "FATAL: .env sem TELEGRAM_BOT_TOKEN e/ou AUTHORIZED_CHAT_ID" >&2
  exit 1
fi

# Instância única = garantida pelo launchd (KeepAlive, um job) + pidfile com liveness no daemon python.
# (Não usar pgrep aqui: sob KeepAlive, apanharia a instância anterior a morrer e abortaria em loop.)
exec python3 -u telegram_assistant_bridge.py
