# 06 — Cleanup and Restructure Plan

**Project:** Trading System  
**Purpose:** Guide cleanup of architecture, files, artifacts, and workflows.  
**Rule:** Cleanup must be safe, reversible where needed, and explicitly authorized before destructive actions.

---

## 1. Cleanup Goal

Build a cleaner Trading System architecture:

```text
simpler
safer
RAW-first
less fragmented
less proxy-dependent
easier to operate
easier to audit
```

The goal is not to delete aggressively. The goal is to remove confusion and restore source fidelity.

---

## 2. Cleanup Principles

### 2.1 Minimum Safe Execution

For every cleanup task:

```text
one objective
smallest safe action
read-only inventory first
explicit delete list
no broad rm commands
no unrelated refactors
```

### 2.2 Source-of-Truth Preservation

Never delete before confirming source status.

Preserve:

```text
RAW replay data
manifests
checksums
dataset registry source references
production code
LaunchAgent references
catalog/rules history
```

### 2.3 Contaminated Does Not Always Mean Delete Immediately

Some contaminated artifacts may still preserve lessons.

Default handling:

```text
mark suspect
quarantine/archive
do not use for validation
delete only after explicit approval
```

---

## 3. Classification System

Every file/artifact should be classified before action.

| Class | Meaning | Default Action |
|---|---|---|
| `SOURCE_OF_TRUTH` | RAW/source/manifests/production-critical files | Keep |
| `PRODUCTION` | Active runtime code/config | Keep; modify only with explicit plan |
| `GOVERNANCE` | Catalog, rules, strategy status, policy docs | Keep; update carefully |
| `RESEARCH_VALID` | RAW-traced, documented research | Keep |
| `RESEARCH_EXPLORATORY` | Useful hypothesis but not validation | Keep or archive |
| `SUSPECT_CONTAMINATED` | Depends on SLIM/proxy/unverified semantics | Quarantine/mark; no validation use |
| `TEMP_LOCAL` | `/tmp`, scratch scripts, one-off outputs | Delete/archive after review |
| `SUPERSEDED` | Replaced by better source/version | Delete/archive with approval |
| `DECOMMISSIONED` | Old external/enrich processes | Keep disabled record; do not restart |
| `UNKNOWN` | Not yet classified | Do not delete |

---

## 4. Immediate Cleanup Targets

### 4.1 Strategy Research Artifacts

Targets:

```text
recent XAU 1H SLIM/proxy-based labs
Caminho A contaminated outputs
Caminho B contaminated outputs
temporary scripts from failed strategy paths
PDFs generated from invalid premises
```

Default action:

```text
mark as SUSPECT_CONTAMINATED or RESEARCH_EXPLORATORY
do not use for validation
do not delete until inventory reviewed
```

---

### 4.2 SLIM / Proxy Artifacts

Policy:

```text
SLIM cannot validate strategy.
Proxy features cannot validate strategy.
```

Possible actions:

1. Mark as deprecated/contaminated.
2. Move to archive if not needed.
3. Delete only with explicit user approval.
4. Do not use for thresholds or gates.

---

### 4.3 `/tmp` Research Scripts

Many scripts are useful only as scratch outputs.

Default action:

```text
inventory filename + purpose + keep/delete recommendation
delete only after user approval
```

---

### 4.4 Chart Drawings

Chart drawings from wrong/contaminated bases must not mislead future review.

Before deleting:

```text
ask user if review is complete
confirm chart symbol/timeframe
remove only requested drawings
restore production if paused
```

---

### 4.5 Stale Governance Inconsistencies

Known examples:

```text
stale notes in strategy_rules
old replacement_module references
catalog text that references already-completed patches
dormant modules still described as active in old docs
```

Action:

```text
low-risk patch only after inventory and explicit authorization
```

---

## 5. What Must Not Be Deleted Blindly

Do not blindly delete:

```text
RAW replay files
manifests/checksums
dataset registry
production receiver
cloudflared launch agent
xau monitor daemon
strategy catalog
strategy_rules.json
claude_recheck.py
research docs that record decisions
official rejection docs
```

---

## 6. Proposed Cleanup Phases

### Phase 1 — Inventory

Read-only.

Produce table:

```text
path
type
class
reason
risk
recommended action
needs user approval?
```

No deletion.

---

### Phase 2 — Mark / Quarantine

For suspect files:

```text
add note
move to archive
or document as contaminated
```

No production behavior change unless explicitly authorized.

---

### Phase 3 — Delete Obvious Junk

Only after inventory.

Candidates:

```text
failed temporary outputs
duplicate PDFs
obsolete scratch scripts
known superseded artifacts
old wrong plots if no longer needed
```

---

### Phase 4 — Governance Cleanup

Patch stale docs/configs:

```text
catalog text
strategy_rules stale fields
research status docs
operational inventory
```

One patch at a time.

---

### Phase 5 — Architecture Simplification

Only after contaminated artifacts are separated.

Targets:

```text
single RAW-first backtest workflow
single strategy status source
single production safety checklist
single visual review workflow
single outcome lab design
```

---

## 7. RAW-First Rebuild Path

For any strategy worth revisiting:

```text
1. Concept statement
2. Gate manifest
3. RAW/source-field map
4. Spot-check RAW/visual examples
5. Backtest from RAW
6. Event/trade outputs
7. Visual review
8. Walk-forward/sensitivity
9. Status update
```

No shortcut through SLIM validation.

---

## 8. Cleanup Output Format

Every cleanup action should report:

```text
what was inspected
what was changed
what was not changed
what was deleted
what remains
production health
next smallest action
```

---

## 9. Safety Checks After Cleanup

After any file or production-adjacent change:

```text
git status
diff check if tracked files changed
secret scan if commit-ready
receiver health if production touched
public health if webhook/tunnel touched
daemon state if monitor touched
pause flag state
orphan server.js check
```

---

## 10. Current Recommended Next Cleanup Step

Start with a read-only inventory of recent strategy research artifacts:

```text
XAU 1H Demand Reclaim/Reentry
BB Confluence labs
Auction Confluence labs
Caminho A / Caminho B artifacts
temporary PDFs and scripts
```

Output only a classification table.

No deletion until user approves.

