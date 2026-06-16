# SKILL 06 — Cleanup Governance

**Purpose:** Clean architecture and files safely without deleting source-of-truth or useful history.

## Core Rule

```text
Inventory before delete.
Classify before action.
Approval before destructive cleanup.
```

## Classification

| Class | Action |
|---|---|
| SOURCE_OF_TRUTH | Keep |
| PRODUCTION | Keep / modify only with authorization |
| GOVERNANCE | Keep / patch carefully |
| RESEARCH_VALID | Keep |
| RESEARCH_EXPLORATORY | Keep or archive |
| SUSPECT_CONTAMINATED | Mark/quarantine |
| TEMP_LOCAL | Delete after approval |
| SUPERSEDED | Delete/archive after approval |
| UNKNOWN | Do not touch |

## Cleanup Steps

1. Read-only inventory.
2. Classify.
3. Propose action.
4. User approves.
5. Execute small batch.
6. Validate.
7. Report.

## Never Delete Blindly

Do not blindly delete:

- RAW replay
- manifests
- checksums
- dataset registry
- production code
- launch agents
- catalog/rules
- decision docs
- rejection records

## Cleanup Report Format

```text
inspected
classified
changed
deleted
not touched
validation
next action
```

No long essay unless requested.

## Contaminated Artifacts

Contaminated means:

```text
not validatory
do not use for promotion
may preserve lesson
```

Archive/mark before deleting unless user explicitly requests deletion.
