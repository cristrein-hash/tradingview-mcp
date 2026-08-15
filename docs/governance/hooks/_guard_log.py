#!/usr/bin/env python3
"""Telemetria mínima partilhada das guardas de comportamento (Cris 2026-08-15).
Uma linha por DISPARO (bloqueio exit 2) em ~/.claude/hooks/logs/guard_fires.jsonl,
para deixarmos de auditar às cegas (antes só o G7 registava). FAIL-OPEN absoluto:
qualquer erro no log NUNCA pode impedir a guarda de bloquear."""
import json, time
from pathlib import Path


def fire(guard, action="block", detail=""):
    try:
        L = Path.home() / ".claude/hooks/logs"
        L.mkdir(parents=True, exist_ok=True)
        with open(L / "guard_fires.jsonl", "a") as f:
            f.write(json.dumps({"ts": int(time.time()), "guard": guard,
                                "action": action, "detail": str(detail)[:200]}) + "\n")
    except Exception:
        pass
