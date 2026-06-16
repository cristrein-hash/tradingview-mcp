# SKILL 02 — RAW Backtest Protocol

**Purpose:** Ensure strategy validation uses RAW/source data, not proxy/SLIM assumptions.

## Core Rule

```text
RAW / source payload / TradingView visual = source of truth.
SLIM/proxy = not validatory.
```

## Required Before Any Serious Backtest

### 1. Gate Manifest

Declare:

```text
strategy name
timeframe
direction
all gates
exact timing
entry
stop
target
exit
dedup/event policy
```

### 2. Source Mapping

For every gate:

```text
gate
RAW/source field
indicator source
field semantics
timing convention
known limitations
```

### 3. Predicate Check

Show exact code predicate.

Do not trust strategy/variant names.

### 4. Sanity Examples

At minimum:

```text
one example that should pass
one example that should fail
one borderline example
```

### 5. RAW/Visual Spot-Check

Required if strategy depends on:

- NAS
- Bubbles
- SMC
- CHoCH/BOS
- BigBeluga/Custom OB zones
- supply/demand
- auction context
- absorption/exhaustion
- any derived threshold

## Backtest Output

Required:

```text
n
date range
win rate
total R
PF
avg R
MFE/MAE
hit 1R/2R/5R/10R/20R
no-top-N robustness
regime/window split
sample caveats
```

## Not Allowed

Do not validate strategy from:

```text
SLIM-only
proxy-only
derived zones
unverified extracted labels
synthetic swing proxies
unmapped feature names
```

## If RAW Trace Is Missing

Status must be:

```text
EXPLORATORY / NOT VALIDATED
```

Never:

```text
VALIDATED
OFFICIAL
READY
PROMOTABLE
```

## After Backtest

Before any promotion:

1. Visual review.
2. Walk-forward.
3. Sensitivity.
4. Costs/slippage/stops.
5. OOS/shadow.
6. Explicit user approval.
