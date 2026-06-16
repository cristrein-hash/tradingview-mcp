# 09 — Skills Index

**Project:** Trading System  
**Purpose:** Index the operational skills uploaded to this project.

---

## Installed Skills

### SKILL 01 — Minimum Safe Execution

Use for:

- any operational task;
- error correction;
- cleanup;
- chart work;
- backtest prompt generation;
- preventing scope creep.

Core idea:

```text
smallest safe useful action
```

---

### SKILL 02 — RAW Backtest Protocol

Use for:

- strategy validation;
- recalibration;
- indicator-dependent tests;
- threshold work;
- RAW/source trace.

Core idea:

```text
RAW/source truth before backtest confidence
```

---

### SKILL 03 — Visual Review / Auction Theory

Use for:

- chart validation;
- winner/loser review;
- trade plausibility;
- Auction Theory classification.

Core idea:

```text
indicator confluence is not auction confluence
```

---

### SKILL 04 — Strategy Governance

Use for:

- updating status;
- rejecting/promoting;
- catalog/rules work;
- keeping research separate from live.

Core idea:

```text
research is not operational
```

---

### SKILL 05 — Production Safety

Use for:

- daemon/cron work;
- chart plotting;
- receiver/cloudflared checks;
- launchd safety;
- pause flag.

Core idea:

```text
research must not damage production
```

---

### SKILL 06 — Cleanup Governance

Use for:

- file cleanup;
- architecture restructure;
- deleting/archive decisions;
- classifying artifacts.

Core idea:

```text
inventory before delete
```

---

### SKILL 07 — Prompt Discipline

Use for:

- writing Claude prompts;
- preventing assumption;
- resolving name/definition mismatches;
- keeping tasks small.

Core idea:

```text
do exactly the task, ask if ambiguous
```

---

## Invocation Guidance

When a task starts, identify which skill applies.

Examples:

```text
Backtest strategy → SKILL 02 + SKILL 07
Plot trades → SKILL 05 + SKILL 01
Clean artifacts → SKILL 06 + SKILL 01
Update catalog → SKILL 04 + SKILL 05
Review chart → SKILL 03
Write Claude prompt → SKILL 07
```

---

## Priority Order

If skills conflict, priority is:

```text
1. User's current instruction
2. Production safety
3. RAW/source truth
4. Minimum safe execution
5. Strategy governance
6. Cleanup preference
```
