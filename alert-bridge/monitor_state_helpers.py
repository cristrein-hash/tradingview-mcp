"""
monitor_state_helpers.py — shared helpers for claude_monitor.py + claude_intraday_monitor.py

Separates monitor target CONFIG (versionable, in monitor_targets[_intraday].json)
from RUNTIME STATE (volatile, in monitor_targets[_intraday]_state.json — gitignored).

Created 2026-05-18 to resolve monitor_targets git status leak.
"""
import json
from pathlib import Path
from typing import Optional


# Fields that are runtime state (updated by daemon every cycle).
# Anything in this set lives in <name>_state.json, never in config file.
RUNTIME_FIELDS = {
    "priority",
    "classification_last",
    "probability_label_last",
    "last_checked_at",
    "last_relevant_change",
    "last_change_reason",
    "last_event_types",
    "last_next_action",
    "last_notified_at",
}


def state_path_for(targets_path: Path) -> Path:
    """Derives state file path from config path:
    monitor_targets.json → monitor_targets_state.json
    """
    return targets_path.with_name(targets_path.stem + "_state.json")


def load_state(state_path: Path) -> dict:
    """Load state file; returns empty dict if missing.
    Schema: {"state_by_id": {target_id: {field: value, ...}}}
    """
    if not state_path.exists():
        return {}
    try:
        data = json.loads(state_path.read_text())
        return data.get("state_by_id", {}) or {}
    except (json.JSONDecodeError, OSError):
        return {}


def merge_state_into_targets(targets_list: list, state_by_id: dict) -> None:
    """In-place merge: copy state fields from state_by_id into each target by id.
    Targets without matching state get no runtime fields (clean start)."""
    for target in targets_list:
        tid = target.get("id")
        if not tid:
            continue
        state = state_by_id.get(tid, {})
        for field in RUNTIME_FIELDS:
            if field in state:
                target[field] = state[field]


def save_state(state_path: Path, targets_data: dict) -> None:
    """Extract runtime state from targets_data and write to state_path.
    Preserves any existing state fields not currently set on targets (defensive).
    """
    # Load existing state to preserve any extra fields
    existing = load_state(state_path)

    new_state_by_id = {}
    for target in targets_data.get("targets", []):
        tid = target.get("id")
        if not tid:
            continue
        new_state = {}
        for field in RUNTIME_FIELDS:
            if field in target:
                new_state[field] = target[field]
        if new_state:
            new_state_by_id[tid] = new_state

    # Preserve existing entries for targets no longer in config (don't lose history)
    for tid, st in existing.items():
        if tid not in new_state_by_id and st:
            new_state_by_id[tid] = st

    output = {
        "version": "0.1",
        "description": "Runtime state of monitor targets (auto-updated). DO NOT commit to git.",
        "state_by_id": new_state_by_id,
    }
    state_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
