# 04 — Strategy Status Master

**Project:** Trading System  
**Purpose:** Maintain one canonical, conservative strategy-status map.  
**Rule:** Nothing is considered validated unless it has RAW/source-field trace, visual sanity checks, and explicit user approval.

---

## 1. Status Definitions

| Status | Meaning |
|---|---|
| `VALIDATED` | Passed RAW/source validation, visual review, walk-forward/sensitivity, and explicit approval. |
| `ACTIVE_CANDIDATE` | Promising research candidate, not operationally promoted. |
| `RESEARCH` | Hypothesis under study; may have useful insight but not validated. |
| `SUSPECT` | Results depend on contaminated/proxy/slim-only features, missing gate trace, or unverified semantics. |
| `REJECTED` | Rejected by R-real, visual review, methodology failure, or invalid premise. |
| `WATCH_ONLY` | May be observed/logged but must not issue live/urgent entries. |
| `DISABLED` | Must not participate in live classification or Telegram entry routing. |
| `LIVE_DORMANT` | Historically wired or present but dormant; must not be assumed active. |

---

## 2. Canonical Data Rule

All serious validation now requires:

1. RAW replay/source data as source of truth.
2. Exact source-field trace for every gate.
3. Visual/RAW spot-checks for accepted and rejected examples.
4. No SLIM/proxy-derived validation.
5. No promotion from exploratory/lab results alone.

SLIM/proxy results are historical artifacts only unless explicitly re-authorized for non-validatory screening.

---

## 3. Current XAU Strategy Map

| Strategy / Path | TF | Current Status | Operational Status | Main Decision |
|---|---:|---|---|---|
| `XAU_4H_DEMAND_BREAKOUT` | 4H | `REJECTED` | Suppressed / disabled | Rejected after visual/R-real review. |
| `XAU_4H_REVERSAL_CAPITULATION` | 4H | `REJECTED` | Suppressed / disabled | Legacy close-only edge failed R-real canonical revalidation. |
| `XAU_4H_REVERSAL_DISCRETIONARY` | 4H | `RESEARCH` / `WATCH_ONLY` | Telegram suppressed | May be observed only; not validated. |
| `XAUUSD_4H_BREAKOUT_CONTINUATION` | 4H | `ACTIVE_CANDIDATE` | `LIVE_DORMANT`, not promoted | D1a research-stage candidate. Needs official RAW-traced v2, visual review of kept trades, walk-forward, sensitivity, and OOS. |
| `XAUUSD_1H_DECISIVE_BODY60` | 1H | `REJECTED` | Disabled in recheck/rules/catalog | Rejected by visual review: too mechanical, late entries, similar weaknesses to 4H continuation. |
| `XAUUSD_INTRADAY_BB_CONFLUENCE` | 15M/MTF | `RESEARCH` / `NOT_DEPLOYED` | Recheck capped to observation only | BigBeluga/zone confluence thesis remains qualitative; old forward had no outcomes; labs are not validation. |
| `XAU_1H_DEMAND_RECLAIM_REENTRY_LONG v1.1` | 1H | `SUSPECT / REQUIRES RAW VALIDATION` | Not promoted | Promising concept from recent cycle, but must be treated as suspect until rebuilt/validated from RAW/source fields. |
| `Caminho A V1.4g-RWS-A6-A7` | 1H | `SUSPECT / CRITICAL` | Do not use for promotion | Contaminated by SLIM 4H/1D zone/proxy features. |
| `Caminho B FINAL` | 1H | `SUSPECT / CRITICAL` | Do not use for promotion | Contaminated by SLIM 4H/proxy features and synthetic swing-low proxy. |
| Legacy `XAUUSD_4H_LONG_REJECTION_SWING` | 4H | `REJECTED` | Disabled/dormant | Legacy rejected path. |
| Legacy `XAUUSD_1H_LONG_REJECTION_EXECUTION` | 1H | `REJECTED` | Disabled/dormant | Replaced then superseded; no active use. |

---

## 4. Detailed Notes

### 4.1 XAUUSD_4H_BREAKOUT_CONTINUATION

Current best 4H candidate.

Known research finding:

- Baseline: positive but noisy.
- D1a filter improved the strategy historically:
  - `close_1D > EMA200_1D`
  - `EMA50_1D > EMA200_1D`
- D1a rejected many visually bad top/exhaustion trades.
- D1a false rejections existed but were accepted as cost of simplicity.

Current rule:

> Do not promote. Rebuild as RAW-traced official revalidation before any operational movement.

Required next steps:

1. Rebuild official v2 from RAW/source trace.
2. Gate manifest.
3. Visual review kept trades, not only rejected trades.
4. Walk-forward and regime split.
5. Cost/slippage/stops.
6. OOS/shadow validation.

---

### 4.2 XAU_1H_DEMAND_RECLAIM_REENTRY_LONG v1.1

Promising concept, but status is not validation.

Known current concept:

- Two-path structure:
  - Path A: aggressive capitulation/reclaim.
  - Path B: confirmed bottom/NAS-trigger secondary.
- BE@2R looked useful.
- Lowest-risk intra-event picker looked useful.
- Large tail trade justified the thesis conceptually.
- However, strategy work was affected by serious process errors and reliance on derived/proxy/slim logic.

Current rule:

> Treat as suspect exploratory work. It can guide hypotheses, but must not be used as a validated system until rebuilt from RAW/source fields.

Required next steps:

1. Rebuild from RAW, not SLIM.
2. Validate every indicator gate against RAW/visual:
   - Bubbles side/size/timing.
   - NAS label event/anchor.
   - SMC CHoCH/BOS kind/direction.
   - Demand/supply zones.
   - RSI thresholds.
3. Recreate trades only after gate manifest.
4. Visual review.
5. Walk-forward/sensitivity/OOS.

---

### 4.3 BB Confluence / Auction Labs

Current value:

- Useful as conceptual exploration.
- Not valid as strategy proof.
- Several labs relied on slim/proxy-derived fields.
- Any findings must be rechecked through RAW before reuse.

---

## 5. Current Promotion Policy

No strategy may be promoted unless all conditions are true:

1. RAW/source-field validation complete.
2. Gate manifest matches actual code.
3. Visual review completed.
4. Walk-forward and sensitivity passed.
5. Cost/slippage model considered.
6. Production path explicitly reviewed.
7. User explicitly approves.

---

## 6. Immediate Project Direction

Before strategy promotion:

1. Clean architecture.
2. Remove/mark contaminated artifacts.
3. Establish RAW-first workflow.
4. Preserve only useful lessons.
5. Rebuild candidates one at a time.
6. Use the simplest safe action at every step.
