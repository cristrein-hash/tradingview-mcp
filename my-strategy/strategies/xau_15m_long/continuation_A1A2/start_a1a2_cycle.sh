#!/bin/zsh
# A1/A2 PULLBACK 15M LONG — wrapper live (ordem Cris 2026-08-05: "DESTRAVA TUDO. FAZ A1 E A2")
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"
export A1A2_REGIME_GATE_OFF=1            # ordem Cris 05/08: rótulo macro errado (RANGE 1 mês rotulado BEAR); destravado
export A1A2_PRODUCTION_AUTHORIZED=1      # sinal qualificado "15M BULL" -> Telegram do GRUPO (ordem Cris 05/08)
cd "$(dirname "$0")"
exec /usr/bin/python3 -u a1a2_runtime.py
