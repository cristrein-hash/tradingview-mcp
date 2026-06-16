# SKILL 07 — Prompt Discipline

**Purpose:** Prevent assumption, hallucination, scope creep, and name/definition mismatch.

## Core Rule

```text
Do exactly the requested task.
If gates or semantics are unclear, ask.
```

## Before Writing a Prompt to Claude

Confirm:

1. What is the exact objective?
2. Is it read-only?
3. What inputs?
4. What gates?
5. What should not be touched?
6. What output length?
7. What stop condition?

## Variant Name Rule

Never trust a variant name.

Always compare:

```text
user-listed components
vs
internal code predicates
```

If mismatch:

```text
STOP and ask
```

## Minimal Prompt Shape

Use:

```text
Objective
Inputs
Exact gates
Do not do
Output
Stop after
```

Avoid:

- extra theory;
- optional architecture;
- broad exploration;
- unrequested reports.

## Backtest Prompt Requirement

Every backtest prompt must include:

```text
Gate manifest
source data
no repo changes
no production changes
short output
```

## If User Is Angry / Correcting Error

Do:

```text
acknowledge
state correction
keep short
wait for direction
```

Do not:

```text
defend
over-explain
recommend stopping project
create a big remediation plan
```

## Final Check

Before sending any prompt:

```text
Would this do more than the user asked?
Would this introduce new assumptions?
Would this create new artifacts unnecessarily?
```

If yes, simplify.
