#!/bin/zsh
# Wrapper do VELA-NO-NÍVEL (copiloto 🕯️) — corrido pela LaunchAgent com.cristrein.vela-no-nivel (KeepAlive).
# Telegram AUTORIZADO pelo Cris 2026-08-04 (após a 1ª sessão chat-only + aceitação PASS 5/5).
set -u
DIR="/Users/cristrein/tradingview-mcp/alert-bridge"
cd "$DIR" || exit 1
set -a; source .env 2>/dev/null || true; source ../.env 2>/dev/null || true; set +a
export VELA_PRODUCTION_AUTHORIZED=1    # Telegram ON (ordem Cris 2026-08-04)
export VELA_READER_CONSULT=1           # consulta o reader após cada alerta (1 read/alerta, cooldown 2h/zona)
exec /usr/bin/python3 -u vela_no_nivel.py
