#!/usr/bin/env python3
from pathlib import Path
import json

BASE = Path.home() / "tradingview-mcp"
LOGS = BASE / "alert-bridge/logs"

RESEARCH_LOG = LOGS / "setup_research_log.jsonl"
OUTCOME_LOG = LOGS / "setup_outcome_log.jsonl"

HORIZONS = [5, 10, 20, 50]


def load_jsonl(path):
    if not path.exists():
        return []

    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def main():
    research = load_jsonl(RESEARCH_LOG)
    outcomes = load_jsonl(OUTCOME_LOG)

    outcome_keys = {
        (row.get("event_id"), int(row.get("bars_after", -1)))
        for row in outcomes
        if row.get("event_id")
    }

    pending_events = []
    for event in research:
        event_id = event.get("event_id")
        if not event_id:
            continue

        missing = [h for h in HORIZONS if (event_id, h) not in outcome_keys]
        if missing:
            pending_events.append((event, missing))

    print("=== Research Status ===")
    print(f"Setup research events: {len(research)}")
    print(f"Outcome evaluations:   {len(outcomes)}")
    print(f"Pending events D2:     {len(pending_events)}")
    print()

    if research:
        last = research[-1]
        print("Last research event:")
        print(f"- event_id:       {last.get('event_id')}")
        print(f"- received_at:    {last.get('received_at')}")
        print(f"- symbol:         {last.get('symbol')}")
        print(f"- timeframe:      {last.get('timeframe')}")
        print(f"- alert_type:     {last.get('alert_type')}")
        print(f"- drawing_name:   {last.get('drawing_name')}")
        print(f"- classification: {last.get('classification')}")
        print(f"- telegram_sent:  {last.get('telegram_sent')}")
        print(f"- telegram_reason:{last.get('telegram_reason')}")
        print()

    if outcomes:
        last = outcomes[-1]
        print("Last outcome:")
        print(f"- event_id:       {last.get('event_id')}")
        print(f"- bars_after:     {last.get('bars_after')}")
        print(f"- outcome_label:  {last.get('outcome_label')}")
        print(f"- symbol:         {last.get('symbol')}")
        print()

    if pending_events:
        print("Pending examples:")
        for event, missing in pending_events[:5]:
            print(f"- {event.get('symbol')} {event.get('timeframe')} {event.get('alert_type')} | missing horizons: {missing}")


if __name__ == "__main__":
    main()
