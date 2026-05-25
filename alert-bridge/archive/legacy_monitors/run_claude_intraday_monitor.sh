#!/bin/zsh

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

BASE="$HOME/tradingview-mcp/alert-bridge"
LOG="$BASE/logs/launchd_intraday_monitor.log"
LOCK="$BASE/logs/claude_intraday_monitor.lock"

mkdir -p "$BASE/logs"

now_stamp=$(date '+%Y-%m-%d %H:%M:%S')
weekday=$(date '+%u')      # 1=segunda ... 7=domingo
hour=$(date '+%H')
minute=$(date '+%M')
total_minutes=$((10#$hour * 60 + 10#$minute))

# Janela operacional local:
# Segunda a sexta, de 00:00 até 22:15.
# Fora disso, o monitor pula a rodada.
session_start=$((0 * 60 + 0))
session_end=$((22 * 60 + 15))

if [ "${CLAUDE_INTRADAY_MONITOR_FORCE:-0}" != "1" ]; then
  if [ "$weekday" -ge 6 ]; then
    echo "---- $now_stamp intraday monitor skipped: weekend ----" >> "$LOG"
    exit 0
  fi

  if [ "$total_minutes" -lt "$session_start" ] || [ "$total_minutes" -gt "$session_end" ]; then
    echo "---- $now_stamp intraday monitor skipped: outside trading session ----" >> "$LOG"
    exit 0
  fi
fi

# Trava anti-overlap: não deixa duas rodadas intraday rodarem ao mesmo tempo.
if [ -f "$LOCK" ]; then
  OLD_PID=$(cat "$LOCK")

  if ps -p "$OLD_PID" > /dev/null 2>&1; then
    echo "---- $now_stamp intraday monitor skipped: previous run still active pid=$OLD_PID ----" >> "$LOG"
    exit 0
  else
    echo "---- $now_stamp stale intraday lock removed pid=$OLD_PID ----" >> "$LOG"
    rm -f "$LOCK"
  fi
fi

echo $$ > "$LOCK"

echo "---- $now_stamp intraday monitor start ----" >> "$LOG"

python3 "$BASE/claude_intraday_monitor.py" >> "$LOG" 2>&1

echo "---- $(date '+%Y-%m-%d %H:%M:%S') intraday monitor end ----" >> "$LOG"
echo "" >> "$LOG"

rm -f "$LOCK"
