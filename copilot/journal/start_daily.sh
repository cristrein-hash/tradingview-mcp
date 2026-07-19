#!/bin/zsh
# COPILOT/JOURNAL — cron do journal (P3). Roteia por dia da semana (hora local = Lisboa):
#   Sáb = skip · Dom = síntese semanal · Seg-Sex = journal diário. claude -p Max (custo zero), read-only.
set -u
cd "/Users/cristrein/tradingview-mcp/copilot/journal" || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
DOW=$(date +%u)                                  # 1=Seg .. 7=Dom (hora local do Mac = Lisboa)
if [ "$DOW" = "6" ]; then echo "sábado — sem journal"; exit 0; fi
if [ "$DOW" = "7" ]; then exec /usr/bin/python3 weekly_synthesis.py; fi
exec /usr/bin/python3 daily_journal.py
