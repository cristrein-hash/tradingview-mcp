# 07 — Incidents and Process Lessons

**Project:** Trading System  
**Purpose:** Preserve hard lessons so they are not repeated.  
**Tone:** Direct, operational, non-dramatic.

---

## 1. Core Lesson

The main failure pattern was allowing fast analysis to outrun source fidelity.

Correct hierarchy:

```text
RAW / TradingView visual / source payload
> faithful extractor
> derived dataset
> proxy / heuristic
> exploratory model
```

A proxy is not a fact. A SLIM feature is not automatically source truth.

---

## 2. Major Incidents

### Incident 1 — SLIM / Proxy Feature Contamination

**Summary:**  
Recent strategy work used SLIM-derived and proxy features as if they were source-truth representations of zones, absorption, structure, and Auction Theory context.

**Affected examples:**

- `Caminho A V1.4g-RWS-A6-A7`
- `Caminho B FINAL`
- XAU 1H intraday labs using zone/proxy logic
- Any recent backtest relying on unverified:
  - `inside_demand`
  - `inside_supply`
  - `nearest_demand_atr`
  - `demand_state`
  - `inside_demand_zone`
  - `inside_supply_zone`
  - `n_demand_zones`
  - `n_supply_zones`
  - `absorption_depth_atr_5b`
  - synthetic swing-low proxy

**Impact:**  
These results cannot be treated as validation.

**Correction:**  
All serious validation must use RAW/source fields and visual spot-checks.

---

### Incident 2 — Invented/Overtrusted SLIM Features

**Summary:**  
Derived features were created or accepted as if they represented real market/indicator states.

**Problem:**  
A feature like `inside_demand` can appear objective but may encode assumptions, proxy logic, or extractor interpretation.

**Correction:**  
Every derived feature must declare:

1. Source field.
2. Transformation.
3. Semantics.
4. Known limitations.
5. Whether it is validatory or exploratory.

Default classification for proxy features: **non-validatory**.

---

### Incident 3 — Name vs Definition Mismatch

**Summary:**  
A named variant was reused (`OLD_ANY_CHOCH_AGGRESSIVE`) while the user-listed components still included NAS LONG >= 2 sequential. The implementation followed the name, not the intended gates.

**Impact:**  
Downstream artifacts became suspect:

- 134 trades
- 22 events
- reentry analysis
- discriminator analysis
- plots
- PDF
- candidate selection audit

**Correction:**  
Before any backtest or plot, use a minimal gate check:

```text
Strategy name:
Required gates:
Actual code predicates:
Expected sample sanity:
Accepted examples:
Rejected examples:
```

If name and requested gates conflict, stop and ask.

---

### Incident 4 — NAS Timing Misinterpretation

**Summary:**  
NAS was incorrectly forced into a pre-entry boolean gate in some tests.

**User intent:**  
NAS/BOTTOM was part of visual bottom/capitulation context, not necessarily a strict pre-entry boolean.

**Finding:**  
`nas_label_long_event` correctly maps from `pine_labels:NAS TOP BOTTOM DETECTOR`, but its timing/anchor semantics matter.

**Correction:**  
For NAS:

- Check event timestamp.
- Check `nas_label_event_price`.
- Check anchor relative to cluster low.
- Distinguish visual anchor from executable trigger.
- Do not impose timing semantics not requested.

---

### Incident 5 — CHoCH Internal vs Swing Confusion

**Summary:**  
CHoCH was first treated as a single generic event.

**Finding:**  
The SLIM preserved `smc_structure_event_kind`:

- `swing` = structural / continuous-line CHoCH.
- `internal` = smaller / serrilhado/internal CHoCH.

**Correction:**  
Any CHoCH/BOS strategy must explicitly declare:

```text
event_type
event_kind
direction
timing window
whether internal is allowed
whether swing is required
```

---

### Incident 6 — Plotting Format Error

**Summary:**  
TradingView long-position plotting was initially attempted with wrong parameters/offsets.

**Correction:**  
Use canonical drawing format from:

```text
alert-bridge/draw_xau_4h_trades.py
```

Key rule:

```text
point2 / stopLevel / profitLevel must be absolute price levels,
not R-offsets.
```

---

### Incident 7 — Overengineering After Simple Errors

**Summary:**  
Some elementary errors triggered overly complex remediation plans.

**Correction:**  
For simple errors:

1. Acknowledge.
2. Correct immediate scope.
3. Keep next action small.
4. Do not create architecture unless explicitly requested.

---

### Incident 8 — Forward / Outcome Pipeline Weakness

**Summary:**  
Some forward logs captured observations but not completed outcomes.

**Problem:**  
Observation logs without structured entry/stop/target/outcome are not validation datasets.

**Correction:**  
Any forward test requires:

- entry_price
- stop_price
- target(s)
- exit_price
- exit_iso
- outcome_R
- MFE_R
- MAE_R
- bars_held

---

### Incident 9 — External Factors Decommission

**Summary:**  
External Factors on iMac were decommissioned intentionally.

**Current state:**  
Treat External Factors as offline unless explicitly reactivated.

**Correction:**  
Do not assume iMac External Factors bridge is available.

---

### Incident 10 — Deprecated Enrich / Outcome Evaluator

**Summary:**  
Old enrich/outcome evaluator flow was deprecated/decommissioned.

**Correction:**  
Do not restart or depend on old enrich logic. Future outcome enrichment must be redesigned as a clean Signal Outcome Lab.

---

## 3. Non-Negotiable Process Rules

### 3.1 Before Backtest

Require:

```text
Gate manifest
RAW/source mapping
Predicate check
Sanity examples
Read-only first
```

### 3.2 Before Visual Plot

Require:

```text
Correct dataset
Correct symbol/timeframe
Correct drawing format
Pause daemon + cron if needed
Pause flag
Leave drawings unless user asks cleanup
```

### 3.3 Before Promotion

Require:

```text
RAW validation
Visual review
Walk-forward
Sensitivity
Slippage/costs
OOS/shadow
Explicit user approval
```

---

## 4. Do Not Repeat

Do not:

- use SLIM as validation source;
- treat proxy as truth;
- trust named variants without checking gates;
- add filters after the user asked for a simple test;
- produce long reports for elementary corrections;
- recommend stopping the project because of an assistant/process error;
- change production without explicit authorization;
- push without authorization;
- assume chart state;
- assume External Factors is running;
- assume old enrich is valid;
- assume a strategy is operational because it exists in a file.

---

## 5. Preserved Lessons

Some lessons remain valuable despite contaminated tests:

1. High R/R strategies must be evaluated by MFE, fat-tail robustness, and no-top-N, not only win rate.
2. BE@2R often matters for reducing damage after initial favorable movement.
3. Multiple entries in one event must be handled carefully: candidates must not be blindly discarded.
4. Event-level analysis is useful, but candidate-level detail must be preserved.
5. Visual Auction Theory cannot be replaced by generic indicator stacking.
6. RAW/source validation must come before confidence.

---

## 6. Current Incident Classification

| Area | Status |
|---|---|
| SLIM-derived strategy validation | Invalid / suspect |
| RAW replay datasets | Source-of-truth, subject to per-field checks |
| Extractor | Must be audited per field before validation use |
| Recent XAU 1H labs | Exploratory only |
| XAU 4H D1a work | Research candidate; requires RAW-traced revalidation |
| Production system | Must be validated separately; not changed by research labs |

---

## 7. Assistant Behavior After Incidents

When an error is found:

1. Do not defend the error.
2. Do not create a large remediation plan automatically.
3. Do not recommend stopping the project.
4. State what is invalid/suspect.
5. Ask for or wait for the user's chosen direction.
6. Use the smallest corrective action.
