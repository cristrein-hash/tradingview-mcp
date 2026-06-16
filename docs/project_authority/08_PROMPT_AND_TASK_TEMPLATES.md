# 08 — Prompt and Task Templates

**Project:** Trading System  
**Purpose:** Provide concise, reusable task templates for Claude/GPT work.  
**Rule:** Use templates to prevent missing gates, scope creep, and accidental production changes.

---

## 1. Read-Only Audit Template

```text
Run a read-only audit.

Objective:
[one sentence]

Scope:
[paths/files/modules]

Do not:
- modify files
- touch production
- commit
- push
- call TradingView/MCP unless explicitly needed

Output:
- findings
- risks
- exact files inspected
- recommended next smallest action

Keep concise.
```

---

## 2. RAW Backtest Template

```text
Run a RAW-source backtest.

Strategy:
[name]

Objective:
[test one hypothesis only]

Source:
RAW replay files only.
Do not use SLIM/proxy fields as validation input.

Gate manifest:
1. [gate]
2. [gate]
3. [gate]

For each gate, report:
- RAW/source field
- predicate
- timing convention
- sanity example pass/fail

Do not:
- alter repo
- alter production
- generate PDF
- plot chart
- commit
- push

Output:
- n trades
- date range
- win rate
- total_R
- PF
- avg_R
- MFE/MAE
- hit 1R/2R/5R/10R/20R
- noTop1/3/5/10
- caveats
- conclusion in <=10 lines

Stop after report.
```

---

## 3. Gate Manifest Template

```text
Before running any test, print the gate manifest.

Strategy name:
[exact name]

Required gates:
1. [gate]
2. [gate]
3. [gate]

Actual code predicates:
1. [predicate]
2. [predicate]
3. [predicate]

Source fields:
1. [RAW/source field]
2. [RAW/source field]
3. [RAW/source field]

Sanity checks:
- example that should pass
- example that should fail
- known edge/borderline

If any mismatch exists between strategy name and gate definition, stop and report.
```

---

## 4. Visual Review Plot Template

```text
Plot selected trades for manual visual review.

Objective:
[what to inspect]

Input:
[path to trades or list]

Selection:
[exact sample rule]

TradingView:
- Symbol: PEPPERSTONE:XAUUSD
- Timeframe: [1H/4H]
- Drawing: Long Position or Short Position
- Use absolute price levels for entry/stop/target
- Follow canonical drawing format from alert-bridge/draw_xau_4h_trades.py

Safety:
- pause daemon if needed
- pause cron if needed
- create pause flag
- confirm symbol/timeframe
- plot only requested sample
- leave drawings for review
- do not restore until user confirms if review ongoing

Do not:
- run backtest
- generate PDF
- commit
- push

Output:
PASS/FAIL
n plotted
symbol/timeframe
daemon/cron status
pause flag status
drawings left yes/no
```

---

## 5. Production Sanity Template

```text
Run production sanity check only.

Do not change anything.

Check:
- receiver /health local
- public /health HTTP 200
- xau daemon loaded + PID
- cron status if relevant
- pause flag
- enrich absent
- d2r_daily absent
- server.js child/orphan status

Output:
short table only.
```

---

## 6. Safe Cleanup Inventory Template

```text
Run cleanup inventory read-only.

Scope:
[path/folder]

Classify each item:
- SOURCE_OF_TRUTH
- PRODUCTION
- GOVERNANCE
- RESEARCH_VALID
- RESEARCH_EXPLORATORY
- SUSPECT_CONTAMINATED
- TEMP_LOCAL
- SUPERSEDED
- UNKNOWN

Do not delete.
Do not move.
Do not modify.

Output:
table with path, class, reason, recommendation, approval_needed.
```

---

## 7. Safe Delete Template

```text
Delete only the explicitly approved items below.

Approved delete list:
1. [path]
2. [path]

Before delete:
- confirm each path exists
- confirm not RAW/source/prod/governance
- show count/size

After delete:
- show removed count
- show remaining warnings
- git status if repo touched

Do not delete anything else.
```

---

## 8. Strategy Status Update Template

```text
Update strategy status only.

Strategy:
[name]

Current status:
[status]

New status:
[status]

Reason:
[short reason]

Allowed files:
[exact files]

Do not:
- alter production behavior unless explicitly requested
- touch unrelated strategies
- push without approval

Validate:
- JSON if catalog/rules changed
- py_compile if Python changed
- diff check
- secret scan

Output:
changed files
before/after
validations
commit hash if committed
no push unless authorized
```

---

## 9. Incident Note Template

```text
Record process incident.

Incident:
[short name]

What happened:
[factual]

Impact:
[what is invalid/suspect]

Root cause:
[one sentence]

Correction:
[future rule]

Do not:
- over-explain
- blame-shift
- create broad remediation

Output:
short incident note only.
```

---

## 10. Claude Prompt Hygiene Checklist

Before sending any prompt:

```text
Is the task read-only or write?
Are gates explicit?
Are data sources explicit?
Are forbidden actions listed?
Is output length constrained?
Is there a stop condition?
Could ambiguity cause damage?
```

If yes, ask before sending.

---

## 11. Short Response Standard

For routine operational reports:

```text
PASS/FAIL
what changed
what did not change
risk
next action
```

No long narrative unless user requests it.

---

## 12. Forbidden Prompt Patterns

Avoid prompts that say:

```text
explore everything
optimize broadly
try all combinations
improve the strategy
clean up whatever is unnecessary
fix architecture
```

Unless user explicitly requested broad work.

Use narrow prompts instead:

```text
test only this hypothesis
inspect only this folder
plot only these trades
update only this file
```

