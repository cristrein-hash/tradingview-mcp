#!/usr/bin/env python3
"""Validate _readings_batch_05.jsonl: 20 valid JSON lines, summarize decisions/types.
Episode reader output for XAU 4H L2/BPT lines 80-99 (episodes 3011-3622, Dec2021-May2022)."""
import json
from collections import Counter

PATH = "results/_readings_batch_05.jsonl"

def main():
    rows = [json.loads(l) for l in open(PATH)]
    assert len(rows) == 20, f"expected 20 readings, got {len(rows)}"
    required = ["episode_id", "bar_idx", "timestamp", "episode_type", "trade_role",
                "narrative", "conditioning_principal", "factors_meaning_changed",
                "provisional_decision", "qualitative_confidence",
                "invalidation_triggers", "uncertainty_notes"]
    for r in rows:
        for k in required:
            assert k in r and r[k], f"episode {r.get('episode_id')} missing/empty {k}"
    print("all 20 lines valid JSON, all required fields present")
    print("decisions:", dict(Counter(r["provisional_decision"] for r in rows)))
    print("types:", dict(Counter(r["episode_type"] for r in rows)))

if __name__ == "__main__":
    main()
