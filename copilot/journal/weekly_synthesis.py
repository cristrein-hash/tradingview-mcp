#!/usr/bin/env python3
"""COPILOT/JOURNAL — síntese SEMANAL (P3, domingo). Junta os journals diários da semana + trades resolvidos
+ lições, e corre `claude -p` (Opus, Max) -> weekly/AAAA-Www.md + weekly.jsonl. Reusa run_claude do
daily_journal (não duplica). Read-only sobre dados. py3.9.
Uso: python3 weekly_synthesis.py [AAAA-MM-DD]  (default: hoje; usa a semana ISO que o contém)."""
import sys, json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import daily_journal as DJ
LX = ZoneInfo("Europe/Lisbon")
WEEKLY = HERE / "weekly"; WEEKLY.mkdir(parents=True, exist_ok=True)


def _jl(f):
    try: return [json.loads(x) for x in Path(f).read_text().splitlines() if x.strip()]
    except Exception: return []


def build_week_material(date_str):
    d0 = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=LX)
    monday = d0 - dt.timedelta(days=d0.weekday())
    days = {(monday + dt.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)}
    iso = d0.isocalendar()
    week = f"{iso[0]}-W{iso[1]:02d}"
    entries = [e for e in _jl(HERE / "entries.jsonl") if e.get("date") in days]
    trades = [t for t in _jl(HERE / "trades.jsonl")
              if str(t.get("detected_ts", "")).startswith(tuple(days)) or (t.get("resolved_ts") or "")[:10] in days]
    lessons = [l for l in _jl(HERE / "lessons.jsonl") if l.get("date") in days]
    return {"week": week, "days": sorted(days), "daily_entries": entries,
            "trades_this_week": trades, "lessons_this_week": lessons}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    date_str = args[0] if args else dt.datetime.now(LX).strftime("%Y-%m-%d")
    M = build_week_material(date_str)
    body, err = DJ.run_claude(M, instr_file="weekly_instruction.md")
    if err or not body:
        s = M["week"]
        body = (f"# Síntese semanal — {s} (Lisboa)\n\n_(fallback — claude -p indisponível: {err})_\n\n"
                f"- entries: {len(M['daily_entries'])} · trades: {len(M['trades_this_week'])} · "
                f"lições: {len(M['lessons_this_week'])}")
    (WEEKLY / f"{M['week']}.md").write_text(body)
    print(f"weekly {M['week']}: {len(body)} chars -> weekly/{M['week']}.md"
          + (f" | ERRO: {err}" if err else "") + f" · entries={len(M['daily_entries'])}")


if __name__ == "__main__":
    main()
