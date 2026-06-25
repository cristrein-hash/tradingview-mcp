#!/usr/bin/env python3
"""Validate _readings_batch_08.jsonl (episodes 0-indexed 140-159 of the 276 input).

Checks:
  - every line is valid JSON
  - exactly 20 episodes
  - episode_ids match the expected slice of the input file
  - required fields present per episode
  - tallies provisional_decision and episode_type distributions

verified at: 2026-06-23
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
READINGS = HERE / "_readings_batch_08.jsonl"
INPUT = HERE / "l2_bpt_episode_reading_input_276.jsonl"

REQUIRED_FIELDS = [
    "episode_id", "bar_idx", "timestamp", "episode_type", "trade_role",
    "narrative", "conditioning_principal", "factors_meaning_changed",
    "provisional_decision", "qualitative_confidence", "invalidation_triggers",
    "uncertainty_notes",
]
VALID_DECISIONS = {"TAKE", "SKIP", "REVIEW", "TRANSFORM"}
SLICE_START, SLICE_END = 140, 160  # 0-indexed [140, 160) -> 20 episodes


def expected_ids():
    ids = []
    with INPUT.open() as f:
        for i, line in enumerate(f):
            if SLICE_START <= i < SLICE_END:
                ids.append(json.loads(line)["episode_id"])
    return ids


def main() -> int:
    rows = []
    with READINGS.open() as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"FAIL: line {n} invalid JSON: {e}")
                return 1

    ok = True

    if len(rows) != 20:
        print(f"FAIL: expected 20 episodes, got {len(rows)}")
        ok = False
    else:
        print("PASS: 20 valid JSON lines")

    for r in rows:
        missing = [k for k in REQUIRED_FIELDS if k not in r]
        if missing:
            print(f"FAIL: episode {r.get('episode_id')} missing {missing}")
            ok = False
        if r.get("provisional_decision") not in VALID_DECISIONS:
            print(f"FAIL: episode {r.get('episode_id')} bad decision "
                  f"{r.get('provisional_decision')}")
            ok = False

    got_ids = [r["episode_id"] for r in rows]
    exp_ids = expected_ids()
    if got_ids == exp_ids:
        print("PASS: episode_ids match input slice [140,160)")
    else:
        print(f"FAIL: id mismatch\n  expected {exp_ids}\n  got      {got_ids}")
        ok = False

    print("decisions:", dict(Counter(r["provisional_decision"] for r in rows)))
    print("types:", dict(Counter(r["episode_type"] for r in rows)))
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
