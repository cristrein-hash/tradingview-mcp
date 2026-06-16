# SKILL 04 — Strategy Governance

**Purpose:** Keep strategy status honest and prevent unvalidated research from becoming operational.

## Core Rule

```text
Research is not validation.
A candidate is not operational.
A file existing is not a deployment.
```

## Status Ladder

```text
RESEARCH
SUSPECT
ACTIVE_CANDIDATE
WATCH_ONLY
LIVE_DORMANT
VALIDATED
REJECTED
DISABLED
```

## Promotion Requirements

A strategy can move toward validation only after:

1. RAW/source validation.
2. Gate manifest.
3. Visual review.
4. Walk-forward.
5. Sensitivity.
6. Costs/slippage.
7. OOS/shadow.
8. User approval.

## Status Update Rules

When changing status:

- update only relevant files;
- do not touch unrelated strategies;
- state before/after status;
- validate JSON if catalog/rules changed;
- py_compile if Python changed;
- no push without approval.

## Live Alert Safety

A strategy must not emit live/urgent entries unless explicitly validated and approved.

Research modules may only be:

```text
observation
watch-only
review humana
no_trade
```

## Rejected Strategy Handling

Rejected does not always mean delete.

It means:

```text
do not trade
do not promote
preserve reason
avoid repeating failure
```

## Suspect Strategy Handling

If contaminated by SLIM/proxy/unverified fields:

```text
SUSPECT / NOT VALIDATED
```

Never treat as performance proof.
