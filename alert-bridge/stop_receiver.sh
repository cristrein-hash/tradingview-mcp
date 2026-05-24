#!/usr/bin/env bash
set -euo pipefail

OLD_PIDS=$(pgrep -f "tv_webhook_receiver.py" || true)
if [ -z "$OLD_PIDS" ]; then
    echo "No receiver running"
    exit 0
fi

echo "Stopping receiver (PIDs: $OLD_PIDS)"
# shellcheck disable=SC2086
kill $OLD_PIDS 2>/dev/null || true
sleep 2

REMAINING=$(pgrep -f "tv_webhook_receiver.py" || true)
if [ -n "$REMAINING" ]; then
    echo "Force-killing leftover (PIDs: $REMAINING)"
    # shellcheck disable=SC2086
    kill -9 $REMAINING 2>/dev/null || true
    sleep 1
fi

FINAL=$(pgrep -f "tv_webhook_receiver.py" || true)
if [ -n "$FINAL" ]; then
    echo "ERROR: Receiver ainda ativo (PIDs: $FINAL)" >&2
    exit 1
fi
echo "Receiver stopped"
