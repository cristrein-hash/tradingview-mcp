# 00 — Project Overview

**Project:** Trading System  
**Purpose:** Provide a concise orientation file for any new GPT/Claude chat inside this project.  
**Primary rule:** Preserve source truth, reduce complexity, and operate with minimum safe execution.

---

## 1. What This Project Is

This is a trader-assist system for research, alert triage, validation, and operational review.

It is **not** an auto-trading system.

Core flow:

```text
TradingView / RAW market data
→ research and validation
→ webhook / alert receiver
→ Claude/GPT recheck
→ selective Telegram / human review
→ user decision
```

The user remains the final decision-maker.

---

## 2. Core Operating Philosophy

The project must prioritize:

```text
truth over speed
RAW/source data over convenience
simplicity over architecture
small corrective actions over broad remediation
explicit gates over assumptions
visual Auction Theory over indicator stacking
```

The project exists to build a clean, reliable, auditable trading system — not to generate impressive but unverified backtests.

---

## 3. Current Strategic Direction

Current priority:

```text
Clean the project architecture.
Separate useful knowledge from contaminated artifacts.
Rebuild validation workflow around RAW/source truth.
Avoid further complexity until the foundation is reliable.
```

Before new strategy promotion:

1. Clean documentation.
2. Classify current strategy work.
3. Identify contaminated/proxy-based artifacts.
4. Preserve RAW and validated source references.
5. Rebuild candidates one at a time from RAW.

---

## 4. Source of Truth Hierarchy

Use this hierarchy in all work:

```text
1. RAW replay/source payload
2. TradingView visual evidence
3. Indicator source fields verified against RAW
4. Faithful extractor output verified per field
5. Derived features / SLIM / proxy artifacts
```

Only levels 1–3 can support serious validation directly.

Derived/SLIM/proxy artifacts cannot validate strategies unless explicitly re-authorized for non-validatory screening.

---

## 5. Key Current Rule

```text
All serious strategy validation, backtesting, recalibration, and threshold work must use RAW/source data.
```

Do not validate from SLIM features.

Do not treat proxy fields as market truth.

---

## 6. Current System Components

Known active or relevant areas:

```text
alert-bridge/
my-strategy/
docs/
research/
TradingData RAW replay archive
dataset registry
TradingView MCP/chart interaction
receiver / cloudflared / xau daemon
Telegram human-review channel
```

Known decommissioned or deprecated:

```text
External Factors iMac bridge
old enrich / outcome evaluator
old d2r daily outcome flow
```

Do not restart decommissioned systems unless explicitly requested.

---

## 7. Current Strategy Status Summary

| Area | Status |
|---|---|
| XAU 4H Breakout Continuation | Research candidate; D1a promising; needs RAW-traced v2. |
| XAU 1H Demand Reclaim/Reentry | Promising concept but suspect until RAW rebuilt. |
| BB Confluence / Auction Labs | Exploratory; not validation. |
| Demand Breakout 4H | Rejected. |
| Capitulation 4H | Rejected under R-real. |
| Body60 1H | Rejected. |
| Caminho A / Caminho B recent official paths | Critical contamination due to SLIM/proxy features. |

---

## 8. Non-Negotiable Working Rules

1. No serious backtest without gate manifest.
2. No validation without RAW/source trace.
3. No strategy promotion without visual review.
4. No production change without explicit authorization.
5. No broad cleanup without inventory.
6. No trust in variant names without checking actual gates.
7. No PDF/plot/report unless requested.
8. No recommendation to stop the project because of assistant/process error.
9. Ask before acting if ambiguity can cause damage.
10. Keep outputs concise unless the user requests depth.

---

## 9. How Assistants Should Work Here

Default behavior:

```text
direct
critical
concise
scope-controlled
source-conscious
RAW-first
minimum safe execution
```

When uncertain:

```text
say uncertain
ask
do not invent
do not continue on assumption
```

When an error is found:

```text
acknowledge
state impact
correct immediate scope
wait for direction
```

---

## 10. Current Project Setup Files

Core MASTER files:

```text
00_PROJECT_OVERVIEW.md
01_ASSISTANT_OPERATING_SYSTEM.md
02_DATA_SOURCE_POLICY_RAW_FIRST.md
03_BACKTEST_VALIDATION_PROTOCOL.md
04_STRATEGY_STATUS_MASTER.md
05_SYSTEM_ARCHITECTURE_CURRENT.md
06_CLEANUP_AND_RESTRUCTURE_PLAN.md
07_INCIDENTS_AND_PROCESS_LESSONS.md
08_PROMPT_AND_TASK_TEMPLATES.md
09_SKILLS_INDEX.md
10_DO_NOT_DO_RULES.md
```

Skills:

```text
SKILL_01_MINIMUM_SAFE_EXECUTION.md
SKILL_02_RAW_BACKTEST_PROTOCOL.md
SKILL_03_VISUAL_REVIEW_AUCTION_THEORY.md
SKILL_04_STRATEGY_GOVERNANCE.md
SKILL_05_PRODUCTION_SAFETY.md
SKILL_06_CLEANUP_GOVERNANCE.md
SKILL_07_PROMPT_DISCIPLINE.md
```

---

## 11. Immediate Use

Any new chat inside this project should first follow:

```text
Read project instructions.
Respect MASTER files.
Apply relevant skill.
Use RAW-first rule.
Ask if ambiguous.
Do only requested task.
```

