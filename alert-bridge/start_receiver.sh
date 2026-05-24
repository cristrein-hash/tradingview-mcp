#!/usr/bin/env bash
set -euo pipefail

FOREGROUND=0
if [ "${1:-}" = "--foreground" ]; then
    FOREGROUND=1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
    echo "ERROR: .env nao encontrado em $SCRIPT_DIR" >&2
    exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

if [ -z "${TV_WEBHOOK_SECRET:-}" ]; then
    echo "ERROR: TV_WEBHOOK_SECRET nao esta set ou esta vazio" >&2
    exit 1
fi
SECRET_LEN=${#TV_WEBHOOK_SECRET}
if [ "$SECRET_LEN" -lt 20 ]; then
    echo "ERROR: TV_WEBHOOK_SECRET muito curto (length=$SECRET_LEN). Esperado >=20." >&2
    exit 1
fi
echo "OK: TV_WEBHOOK_SECRET set (length=$SECRET_LEN)"

mkdir -p logs

TS=$(date +%Y%m%d_%H%M%S)
for log in logs/tv_webhook_receiver_stdout.log logs/tv_webhook_receiver_stderr.log; do
    if [ -f "$log" ]; then
        mv "$log" "${log}.${TS}.bak"
        echo "Archived: ${log} -> ${log}.${TS}.bak"
    fi
done

OLD_PIDS=$(pgrep -f "tv_webhook_receiver.py" || true)
if [ -n "$OLD_PIDS" ]; then
    echo "Stopping previous receiver (PIDs: $OLD_PIDS)"
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
fi

if [ "$FOREGROUND" = "1" ]; then
    echo "Starting in foreground mode (exec) - launchd-friendly"
    exec python3 -u tv_webhook_receiver.py
fi

nohup python3 -u tv_webhook_receiver.py \
    > logs/tv_webhook_receiver_stdout.log \
    2> logs/tv_webhook_receiver_stderr.log &

sleep 2

NEW_PID=$(pgrep -f "tv_webhook_receiver.py" || true)
if [ -z "$NEW_PID" ]; then
    echo "ERROR: Receiver nao iniciou" >&2
    exit 1
fi
echo "Receiver started: PID=$NEW_PID"

HEALTH_HOST="${TV_WEBHOOK_HOST:-127.0.0.1}"
HEALTH_PORT="${TV_WEBHOOK_PORT:-8787}"
HEALTH=$(curl -s -m 5 "http://${HEALTH_HOST}:${HEALTH_PORT}/health" || true)
if [ -z "$HEALTH" ]; then
    echo "WARNING: /health nao respondeu" >&2
else
    echo "Health: $HEALTH"
fi

STDERR_SIZE=$(wc -c < logs/tv_webhook_receiver_stderr.log | tr -d ' ')
echo "stderr size: $STDERR_SIZE bytes"
