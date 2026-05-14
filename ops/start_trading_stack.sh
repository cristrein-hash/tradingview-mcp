#!/usr/bin/env bash
set -euo pipefail

BASE="$HOME/tradingview-mcp"
OPS="$BASE/ops"
LOGS="$OPS/logs"

RECEIVER="$BASE/alert-bridge/tv_webhook_receiver.py"
RECEIVER_LOG="$LOGS/receiver.log"
TUNNEL_LOG="$LOGS/cloudflared.log"

WEBHOOK_URL="https://webhook.tdwclaudestrategy.org/webhook/local-test"

mkdir -p "$LOGS"

echo "=== Trading Stack Start/Check ==="
date
echo ""

echo "1) Checking receiver on 127.0.0.1:8787..."

if lsof -nP -iTCP:8787 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Receiver already running."
else
  echo "Receiver not running. Starting..."
  nohup env \
    TV_WEBHOOK_HOST="127.0.0.1" \
    TV_WEBHOOK_PORT="8787" \
    TV_WEBHOOK_SECRET="local-test" \
    python3 -u "$RECEIVER" >> "$RECEIVER_LOG" 2>&1 &
  sleep 3
fi

echo ""
echo "2) Checking receiver health..."

if curl -s http://127.0.0.1:8787/health | grep -q '"ok": true'; then
  echo "Receiver health: OK"
else
  echo "Receiver health: FAILED"
  echo "Last receiver log:"
  tail -n 40 "$RECEIVER_LOG" || true
  exit 1
fi

echo ""
echo "3) Checking cloudflared named tunnel..."

if pgrep -f "cloudflared tunnel run tradingview-webhook" >/dev/null 2>&1; then
  echo "Cloudflared tunnel already running."
else
  echo "Cloudflared tunnel not running. Starting..."
  CLOUDFLARED="$(command -v cloudflared || true)"
  if [ -z "$CLOUDFLARED" ]; then
    echo "cloudflared not found in PATH."
    exit 1
  fi
  nohup "$CLOUDFLARED" tunnel run tradingview-webhook >> "$TUNNEL_LOG" 2>&1 &
  sleep 6
fi

echo ""
echo "4) Checking cloudflared process..."

if pgrep -f "cloudflared tunnel run tradingview-webhook" >/dev/null 2>&1; then
  echo "Cloudflared process: OK"
else
  echo "Cloudflared process: FAILED"
  echo "Last tunnel log:"
  tail -n 60 "$TUNNEL_LOG" || true
  exit 1
fi

echo ""
echo "5) Public webhook test..."

RESP="$(curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "PEPPERSTONE:XAUUSD",
    "base_symbol": "XAUUSD",
    "timeframe": "30",
    "alert_type": "test_connectivity",
    "event": "stack_start_public_webhook_check",
    "reason": "automatic stack start public webhook check",
    "is_system_test": true
  }')"

echo "$RESP"

if echo "$RESP" | grep -q '"ok": true'; then
  echo "Public webhook: OK"
else
  echo "Public webhook: FAILED"
  exit 1
fi

echo ""
echo "6) Last raw alert log:"
tail -n 1 "$BASE/alert-bridge/logs/tradingview_alerts.jsonl" | python3 -m json.tool || true

echo ""
echo "=== STACK READY ==="
echo "Receiver: OK"
echo "Cloudflared: OK"
echo "Public webhook: OK"
