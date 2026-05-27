#!/usr/bin/env python3
"""validate_strategy_catalog.py — read-only validator for my-strategy/strategies/catalog.json.

Enforces the Strategy Catalog v1 invariants (Patch 1). Does NOT modify anything.
Exit 0 = all checks PASS; exit 1 = at least one FAIL.

Checks:
  1. JSON valid
  2. Schema valid (jsonschema if available; manual structural checks always)
  3. ids unique
  4. enums valid (validation_status, deployment current/recommended, archetype,
     family_origin, direction, deployment_confidence, risk_level, evidence.method)
  5. no duplicate (archetype, symbol, timeframe, direction) among non-REJECTED/non-LEGACY entries
  6. deployment_evidence required if current_deployment_status in
     {LIVE, LIVE_CONTEXT, LIVE_DORMANT, SHADOW, WATCH_ONLY}
  7. validation_status=VALIDATED forbidden if evidence.method in {close_only_d2r, none}
  8. close_only_d2r => validation_status ceiling = ACTIVE_CANDIDATE (never VALIDATED)
  9. requires_human_decision=true => next_action non-empty

Usage: python3 scripts/validate_strategy_catalog.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CATALOG = REPO / "my-strategy" / "strategies" / "catalog.json"
SCHEMA = REPO / "my-strategy" / "strategies" / "catalog.schema.json"

VALIDATION_ENUM = {"VALIDATED", "ACTIVE_CANDIDATE", "RESEARCH", "REFERENCE_ONLY",
                   "REJECTED", "LEGACY_ARCHIVE", "UNKNOWN_NEEDS_DECISION"}
DEPLOY_ENUM = {"LIVE", "LIVE_CONTEXT", "LIVE_DORMANT", "SHADOW", "WATCH_ONLY",
               "DISABLED", "NOT_DEPLOYED"}
ARCHETYPE_ENUM = {"DECISIVE_BREAKOUT_CONTINUATION", "LIQUIDITY_SWEEP_REVERSAL",
                  "PULLBACK_RECLAIM", "REVERSAL_CAPITULATION", "ZONE_REJECTION"}
FAMILY_ENUM = {"A", "B", "C"}
DIRECTION_ENUM = {"LONG", "SHORT", "BOTH"}
CONFIDENCE_ENUM = {"confirmed", "inferred", "unknown"}
RISK_ENUM = {"LOW", "MEDIUM", "HIGH"}
METHOD_ENUM = {"close_only_d2r", "replay_real_rt", "forward", "none"}

DEPLOY_REQUIRES_EVIDENCE = {"LIVE", "LIVE_CONTEXT", "LIVE_DORMANT", "SHADOW", "WATCH_ONLY"}
NON_UNIQUE_EXEMPT = {"REJECTED", "LEGACY_ARCHIVE"}  # historical predecessors exempt from uniqueness

REQUIRED_FIELDS = ["id", "archetype", "family_origin", "symbol", "timeframe", "direction",
                   "validation_status", "current_deployment_status", "recommended_deployment_status",
                   "deployment_confidence", "risk_level", "requires_human_decision", "evidence"]


def main() -> int:
    failures: list[str] = []

    def check(cond: bool, msg: str):
        if not cond:
            failures.append(msg)

    # 1. JSON valid
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL [1] catalog.json invalid JSON: {e}")
        return 1
    print("PASS [1] catalog.json is valid JSON")

    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL [2] catalog.schema.json invalid JSON: {e}")
        return 1

    # 2. Schema validation (jsonschema if available)
    try:
        import jsonschema  # type: ignore
        try:
            jsonschema.validate(catalog, schema)
            print("PASS [2] catalog validates against schema (jsonschema)")
        except jsonschema.ValidationError as e:
            failures.append(f"[2] schema validation: {e.message} at {list(e.path)}")
    except ImportError:
        print("INFO [2] jsonschema not installed — running manual structural checks only")

    entries = catalog.get("strategies", [])
    check(isinstance(entries, list) and len(entries) > 0, "[2] 'strategies' must be a non-empty array")

    ids = []
    unique_keys = {}
    for e in entries:
        eid = e.get("id", "<no-id>")
        # required fields
        for f in REQUIRED_FIELDS:
            check(f in e, f"[2] {eid}: missing required field '{f}'")
        # 4. enums
        check(e.get("validation_status") in VALIDATION_ENUM, f"[4] {eid}: bad validation_status {e.get('validation_status')!r}")
        check(e.get("current_deployment_status") in DEPLOY_ENUM, f"[4] {eid}: bad current_deployment_status")
        check(e.get("recommended_deployment_status") in DEPLOY_ENUM, f"[4] {eid}: bad recommended_deployment_status")
        check(e.get("archetype") in ARCHETYPE_ENUM, f"[4] {eid}: bad archetype {e.get('archetype')!r}")
        check(e.get("family_origin") in FAMILY_ENUM, f"[4] {eid}: bad family_origin")
        check(e.get("direction") in DIRECTION_ENUM, f"[4] {eid}: bad direction")
        check(e.get("deployment_confidence") in CONFIDENCE_ENUM, f"[4] {eid}: bad deployment_confidence")
        check(e.get("risk_level") in RISK_ENUM, f"[4] {eid}: bad risk_level")
        ev = e.get("evidence") or {}
        method = ev.get("method")
        check(method in METHOD_ENUM, f"[4] {eid}: bad evidence.method {method!r}")
        check(isinstance(e.get("requires_human_decision"), bool), f"[2] {eid}: requires_human_decision must be bool")

        ids.append(eid)

        # 6. deployment_evidence required for live-ish current deployment
        if e.get("current_deployment_status") in DEPLOY_REQUIRES_EVIDENCE:
            check(bool(str(e.get("deployment_evidence", "")).strip()),
                  f"[6] {eid}: deployment_evidence required when current_deployment_status={e.get('current_deployment_status')}")

        # 7 + 8. close-only / none never VALIDATED (ceiling = ACTIVE_CANDIDATE)
        if method in {"close_only_d2r", "none"}:
            check(e.get("validation_status") != "VALIDATED",
                  f"[7] {eid}: validation_status=VALIDATED forbidden with evidence.method={method}")

        # 9. human decision requires next_action
        if e.get("requires_human_decision") is True:
            check(bool(str(e.get("next_action", "")).strip()),
                  f"[9] {eid}: requires_human_decision=true needs non-empty next_action")

        # 5. uniqueness among non-rejected/non-legacy
        if e.get("validation_status") not in NON_UNIQUE_EXEMPT:
            key = (e.get("archetype"), e.get("symbol"), e.get("timeframe"), e.get("direction"))
            if key in unique_keys:
                failures.append(f"[5] duplicate (archetype,symbol,tf,dir)={key}: {unique_keys[key]} and {eid}")
            else:
                unique_keys[key] = eid

    # 3. ids unique
    dupe_ids = {i for i in ids if ids.count(i) > 1}
    check(not dupe_ids, f"[3] duplicate ids: {sorted(dupe_ids)}")
    if not dupe_ids:
        print(f"PASS [3] {len(ids)} ids unique")

    if failures:
        print(f"\nFAIL — {len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        return 1

    # summary
    from collections import Counter
    vc = Counter(e["validation_status"] for e in entries)
    dc = Counter(e["current_deployment_status"] for e in entries)
    hd = [e["id"] for e in entries if e.get("requires_human_decision")]
    print("\nPASS — all checks OK")
    print(f"  strategies: {len(entries)}")
    print(f"  validation_status: {dict(vc)}")
    print(f"  current_deployment_status: {dict(dc)}")
    print(f"  requires_human_decision ({len(hd)}): {hd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
