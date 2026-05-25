#!/usr/bin/env bash
#
# start_trading_stack.sh — health-check + start controlado (supervisionado) do ingress.
#
# Arquitetura (2026-05-25):
#   Receiver    -> LaunchAgent com.cristrein.tv-webhook-receiver  (roda start_receiver.sh, carrega .env)
#   Cloudflared -> LaunchAgent com.cristrein.cloudflared-tunnel   (KeepAlive)
#   Público     -> https://webhook.tdwclaudestrategy.org -> 127.0.0.1:8787
#
# SEGURANÇA:
#   - Default = --check (read-only; NÃO inicia nada).
#   - --start reinicia um serviço DOWN via `launchctl kickstart` (caminho SUPERVISIONADO).
#   - NUNCA inicia o receiver via python direto e NUNCA usa o secret "local-test".
#     O TV_WEBHOOK_SECRET real vive em alert-bridge/.env e é carregado pelo start_receiver.sh
#     (acionado pela LaunchAgent). Por isso usamos kickstart, não chamada direta — evita
#     receiver paralelo/não-supervisionado e conflito de porta 8787.
#
set -uo pipefail

BASE="$HOME/tradingview-mcp"
OPS="$BASE/ops"
LOGS="$OPS/logs"

RECEIVER_HOST="127.0.0.1"
RECEIVER_PORT="8787"
PUBLIC_HOST="webhook.tdwclaudestrategy.org"

RECEIVER_LABEL="com.cristrein.tv-webhook-receiver"
TUNNEL_LABEL="com.cristrein.cloudflared-tunnel"
GUI="gui/$(id -u)"

mkdir -p "$LOGS"

MODE="check"
case "${1:-}" in
  --start) MODE="start" ;;
  --check|"") MODE="check" ;;
  -h|--help)
    echo "uso: $0 [--check|--start]"
    echo "  --check (default): health-check read-only; não inicia nada"
    echo "  --start          : reinicia serviço DOWN via launchctl kickstart (supervisionado)"
    exit 0 ;;
  *) echo "uso: $0 [--check|--start]" >&2; exit 2 ;;
esac

log() { echo "[$(date '+%H:%M:%S')] $*"; }
FAIL=0

agent_running() { launchctl print "$GUI/$1" 2>/dev/null | grep -q "state = running"; }

echo "=== Trading Stack — modo: $MODE ==="
date
echo

# 1) Receiver local
log "1) Receiver local ($RECEIVER_HOST:$RECEIVER_PORT)"
RH=$(curl -s -m5 "http://$RECEIVER_HOST:$RECEIVER_PORT/health" 2>/dev/null || true)
if printf '%s' "$RH" | grep -qE '"ok":[[:space:]]*true'; then
  LM=$(printf '%s' "$RH" | python3 -c "import sys,json;print(json.load(sys.stdin).get('logs',{}).get('tradingview_alerts_last_modified',''))" 2>/dev/null || true)
  log "   OK (último alerta ingerido: ${LM:-?})"
else
  log "   DOWN"
  FAIL=1
  if [ "$MODE" = "start" ]; then
    log "   kickstart $RECEIVER_LABEL (supervisionado; carrega .env, secret real)..."
    launchctl kickstart -k "$GUI/$RECEIVER_LABEL" 2>/dev/null || launchctl kickstart "$GUI/$RECEIVER_LABEL" 2>/dev/null || true
  else
    log "   AÇÃO: launchctl kickstart $GUI/$RECEIVER_LABEL   (NUNCA rodar tv_webhook_receiver.py direto)"
  fi
fi

# 2) Cloudflared (LaunchAgent)
log "2) Cloudflared ($TUNNEL_LABEL)"
if agent_running "$TUNNEL_LABEL"; then
  log "   OK (running)"
else
  log "   DOWN"
  FAIL=1
  if [ "$MODE" = "start" ]; then
    log "   kickstart $TUNNEL_LABEL..."
    launchctl kickstart "$GUI/$TUNNEL_LABEL" 2>/dev/null || true
  else
    log "   AÇÃO: launchctl kickstart $GUI/$TUNNEL_LABEL"
  fi
fi

# 3) URL pública /health = 200 (em --start, dá tempo ao kickstart via retry do curl)
log "3) Público https://$PUBLIC_HOST/health"
if [ "$MODE" = "start" ]; then RETRIES=8; else RETRIES=0; fi
PCODE=$(curl -s --retry "$RETRIES" --retry-delay 2 --retry-all-errors -m8 -o /dev/null -w "%{http_code}" "https://$PUBLIC_HOST/health" 2>/dev/null || echo "000")
if [ "$PCODE" = "200" ]; then log "   200 OK"; else log "   !! $PCODE (esperado 200)"; FAIL=1; fi

# 4) Endpoint legado /webhook/local-test DEVE ser 403 (desativado)
log "4) Legado /webhook/local-test (deve ser 403)"
LCODE=$(curl -s -m5 -o /dev/null -w "%{http_code}" -X POST \
  "http://$RECEIVER_HOST:$RECEIVER_PORT/webhook/local-test" \
  -H "Content-Type: application/json" -d '{"is_system_test":true}' 2>/dev/null || echo "000")
if [ "$LCODE" = "403" ]; then log "   403 OK (legado desativado)"; else log "   !! $LCODE (esperado 403)"; FAIL=1; fi

echo
if [ "$FAIL" = "0" ]; then
  log "=== STACK OK === (receiver=$RECEIVER_LABEL | cloudflared=$TUNNEL_LABEL)"
  exit 0
else
  log "=== STACK COM PROBLEMAS — ver AÇÃO acima ==="
  exit 1
fi
