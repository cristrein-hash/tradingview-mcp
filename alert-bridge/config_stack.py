#!/usr/bin/env python3
"""CONFIG ÚNICA do stack (Fase 4 arquitetura realtime, Cris 2026-07-18) — constantes partilhadas entre
daemons. Fonte única: acabou o "manter em sincronia com..." por comentário. py3.9."""
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path("/Users/cristrein/tradingview-mcp")
STORE_DIR = REPO / "my-strategy/core/bar_store/store"

# Sessões "mortas" do mapa ANTIGO de volatilidade. Desde 2026-07-17 NÃO vetam nada (session_vacuum
# observacional) — servem só de rótulo até o mapa forward (e2_outcome_backfill --map) dar base real.
DEAD_SESSIONS = {"dead_zone", "asia", "other"}

# Timezone humano (feedback_timezone_lisboa_always): TODA hora mostrada a humanos = Lisboa.
LX = ZoneInfo("Europe/Lisbon")


def iso_lx(t):
    import datetime as dt
    return dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")
