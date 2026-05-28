# Indicator Signal Policy

**Status:** active policy.
**Effective:** 2026-05-28 (Phase 1 of the post-decommission roadmap; see
`SIGNAL_OUTCOME_LAB.md` §12).
**Scope:** the `Indicator Signal Journal` — how TradingView indicator alerts
enter the system, how symbols are normalized, what the whitelist allows, where
records live, and how this layer feeds future tools (notably the Signal
Outcome Lab).

This is the operator-facing reference. Material changes require a fresh
authorized commit (see §14).

## 1. Objective

The Indicator Signal Journal is the **canonical, authoritative entry point**
for indicator-generated alerts emitted by TradingView (via webhook) into this
system.

Its responsibilities, in order:

1. **Receive** every TV webhook payload routed at `alert_type ==
   "indicator_signal"`.
2. **Normalize** the symbol to canonical `PEPPERSTONE:<BASE>` form, preserving
   the original payload alongside the normalized fields.
3. **Validate** against the active operational whitelist.
4. **Persist** valid signals (operational stream) and rejected signals
   (quarantine/watchlist-rejection streams) in append-only JSONL files,
   subject to `LOG_MUTATION_POLICY`.
5. **Dedup** valid signals by deterministic hash.
6. **Feed** downstream consumers: revalidation lab, research analytics, and
   the future Signal Outcome Lab.

The Journal is **read-only from a write-back perspective**: nothing downstream
edits its files. New events are always appended via the writer
(`tv_webhook_receiver.py`).

## 2. Scope

### Included (governed by this policy)

| Artifact | Path | Role |
|---|---|---|
| Operational signal log | `alert-bridge/logs/indicator_signals.jsonl` | valid signals stream |
| Quarantine log | `alert-bridge/logs/indicator_signals_quarantined.jsonl` | hard-whitelist-rejected (post-validation) |
| Watchlist rejection log | `alert-bridge/logs/watchlist_rejections.jsonl` | early-gate rejections (pre-validation) |
| Dedup index | `alert-bridge/logs/indicator_signals_dedup_index.json` | dedup hash set persisted by writer |
| Schema warnings | `alert-bridge/logs/schema_warnings.jsonl` | shadow validation log |
| Raw payload preservation | inside `payload_full` on each operational record + `raw_event` on each quarantined record | audit / regen capability |
| Normalization fields | `raw_symbol`, `base_symbol`, `symbol`, `provider`, `normalization_method`, `validation_status`, `_normalize_warning` | injected by `_normalize_indicator_parsed` |

### Out of scope (governed elsewhere)

| Artifact | Governed by |
|---|---|
| Outcome computation | `SIGNAL_OUTCOME_LAB.md` |
| Backtest engines and revalidation lab | revalidation lab READMEs + decision flow |
| Strategy catalog / status | `my-strategy/strategies/catalog.json` + `catalog.schema.json` |
| TradingView drawings / Pine code | not policy-governed in this document |
| Signal Outcome Lab outputs | `SIGNAL_OUTCOME_LAB.md` §4 |
| Cold-storage data (RAW / manifests / slim features) | `DATA_STORAGE_POLICY.md` |

## 3. Active whitelist (frozen 2026-05-28)

The **only** symbols admitted to the operational signal stream:

| Base symbol | Operational `symbol` | Notes |
|---|---|---|
| `XAUUSD` | `PEPPERSTONE:XAUUSD` | gold spot — primary focus instrument |
| `XAGUSD` | `PEPPERSTONE:XAGUSD` | silver spot |
| `ETHUSD` | `PEPPERSTONE:ETHUSD` | ETH/USD spot |
| `US500` | `PEPPERSTONE:US500` | S&P 500 index CFD |
| `EURUSD` | `PEPPERSTONE:EURUSD` | EUR/USD spot |
| `USOUSD` | `PEPPERSTONE:USOUSD` | WTI crude oil — kept for petroleum macro/geopolitical context |

**Provider obligation:** `PEPPERSTONE` and only `PEPPERSTONE`.

### Explicitly excluded

The following base symbols are **not** accepted (any incoming alert carrying
them — regardless of provider prefix — is rejected and recorded for audit):

- `BTCUSD`
- `XPTUSD`
- `USDJPY`
- any other base symbol not listed in §3 above

The following providers are **never** accepted as the operational `provider`
field (TV may use them as the default resolver for bare tickers; the Journal
must override or reject):

- `OANDA`
- `VANTAGE`
- `FOREXCOM`
- `FX`
- `FX_IDC`
- any other broker prefix not equal to `PEPPERSTONE`

When an unauthorized provider arrives **paired with a whitelisted base**
(e.g. `OANDA:XAUUSD`), the receiver **normalizes** the operational `symbol` to
`PEPPERSTONE:<BASE>` and logs a `replaced_provider:<X>->PEPPERSTONE` warning
(see §4). When an unauthorized provider arrives **paired with a non-whitelisted
base** (e.g. `OANDA:BTCUSD`), the entire signal is **rejected** — never
silently normalized to PEPPERSTONE:BTCUSD.

## 4. Provider policy

Hard rules enforced by `tv_webhook_receiver.py::_normalize_indicator_parsed`
on every incoming indicator_signal payload:

1. **No bare ticker propagates as `symbol`.** The operational `symbol` field
   must always be `PEPPERSTONE:<BASE>` for valid signals, or empty `""` for
   rejected signals — never just `XAUUSD` or `BTCUSD`.
2. **`base_symbol` is provider-free.** The internal-only `base_symbol` field
   carries the uppercase base ticker without prefix. Dedup hash and downstream
   grouping use `base_symbol`.
3. **Provider replacement requires authorized base.** If the incoming payload
   carries a non-PEPPERSTONE provider AND the base is in the whitelist (§3),
   the operational `symbol` is rewritten to `PEPPERSTONE:<BASE>` and a
   `replaced_provider:<X>->PEPPERSTONE` warning is emitted. This is the only
   silent normalization permitted.
4. **Non-whitelisted base = full rejection.** Any base outside §3, regardless
   of incoming provider, sets `validation_status =
   rejected_unauthorized_symbol`, blank `symbol` + `provider`, and the signal
   is diverted to the quarantine log. **Never** silently invent a
   PEPPERSTONE:BASE for unauthorized BASE.
5. **Empty payload = empty rejection.** Missing or empty `symbol/ticker` →
   `validation_status = rejected_empty_symbol`; same diversion to quarantine.
6. **No silent whitelist expansion.** Adding a new base requires the §9
   process — code change + this doc change + explicit authorization.

The same rules apply at the watchlist gate (earlier in the request flow) by
reading `strategy_rules.json::allowed_symbols`; see §7.

## 5. Required fields on a valid operational signal

A record appended to `indicator_signals.jsonl` has at minimum:

```json
{
  "schema_version":         "1.0",
  "ts_received":            "<ISO8601 with microseconds + tz, server clock>",
  "ts_signal":              "<ISO8601 from indicator payload>",
  "symbol":                 "PEPPERSTONE:<BASE>",
  "base_symbol":            "<BASE>",
  "timeframe":              "<e.g. 15 | 60 | 240 | D>",
  "indicator_name":         "<e.g. Custom_OB_Detector | NAS_TopBottom_Detector | RSI | Market_Bubbles>",
  "indicator_version":      "<e.g. custom_ob_v12 | unversioned>",
  "signal_type":            "<indicator-defined event identifier>",
  "alert_type":             "indicator_signal",
  "price":                  <float>,
  "priority":               "<A | B | C>",
  "signal_hash":            "<sha256(ts_signal|base_symbol|timeframe|indicator_name|signal_type)[:16]>",
  "payload_full":           { "<entire normalized parsed payload>": "..." }
}
```

`payload_full` MUST also contain (set by the normalizer):

```json
{
  "raw_symbol":              "<exact symbol/ticker string as received from TV>",
  "provider":                "PEPPERSTONE",
  "normalization_method":    "added_pepperstone_prefix | kept_pepperstone | replaced_<provider>_with_pepperstone | rejected | empty_symbol",
  "validation_status":       "valid",
  "_normalize_warning":      "<optional, only when applicable, e.g. replaced_provider:OANDA->PEPPERSTONE>"
}
```

Synthetic test signals (see §8) MUST additionally carry:

- `source` = `"synthetic_<purpose>_test"`
- `test_run_id` = `<unique timestamp or UUID>`
- `indicator_name` / `signal_type` prefixed with `TEST_` (e.g.
  `TEST_PROVIDER_NORMALIZATION`).

## 6. Official logs — roles and append discipline

### 6.1 `indicator_signals.jsonl` — operational signal stream

- Contains **only** signals with `validation_status == "valid"`.
- Every record has `symbol = "PEPPERSTONE:<BASE>"` with `BASE` in §3
  whitelist.
- Dedup applies: identical `(ts_signal, base_symbol, timeframe, indicator_name,
  signal_type)` → same `signal_hash` → de-duplicated on second arrival.
- Writers: `tv_webhook_receiver.py::write_indicator_signal`. **No other
  writer.**
- Readers: revalidation tools, research analytics, future Signal Outcome Lab.
- Mutation: governed by `LOG_MUTATION_POLICY.md`. ACTIVE_APPEND_ONLY while the
  receiver is loaded.

### 6.2 `indicator_signals_quarantined.jsonl` — hard-gate rejections

- Contains signals that **reached** the write path but were rejected by the
  hard whitelist gate inside `write_indicator_signal` (i.e. base not in §3, or
  empty payload). Each record includes the full `raw_event` for audit.
- Schema (top-level): `ts_received`, `raw_symbol`, `base_symbol`,
  `validation_status` (`rejected_unauthorized_symbol` | `rejected_empty_symbol`),
  `validation_reason`, `_normalize_warning`, `raw_event` (full original event).
- Writer: `tv_webhook_receiver.py::_write_indicator_quarantine`.
- Readers: audits only. **Never operational input** for downstream consumers.
- Existence is also reported by patched consumers (see §10) as the
  `OUTCOMES_UNAVAILABLE_DECOMMISSIONED_ENRICH` banner context.

### 6.3 `watchlist_rejections.jsonl` — early-gate rejections

- Contains signals barred **before** `write_indicator_signal` by the watchlist
  gate (reads `strategy_rules.json::allowed_symbols`).
- Earlier in the request flow than the quarantine log — these signals never
  enter the write path.
- Schema: `received_at`, `symbol`, `base_symbol`, `allowed_symbols` (snapshot
  of the watchlist at decision time), `reason`, `payload` (full original
  payload).
- Writer: receiver's watchlist gate (`_validate_schema_shadow` + dispatch).
- Readers: audits only. Same defense-in-depth role as the quarantine log.

### 6.4 `indicator_signals_dedup_index.json` — operational dedup

- A persisted set of `signal_hash` values for **valid** signals only.
- Rejected signals (quarantine or watchlist) **must not** appear here.
- Writer: `tv_webhook_receiver.py::_persist_indicator_dedup_set` after every
  successful write.
- Trimming policy: capped at `_INDICATOR_DEDUP_MAX` (current: 10000), trimmed
  to `_INDICATOR_DEDUP_TRIM_TO` (current: 8000) when exceeded.
- Mutation: governed by `LOG_MUTATION_POLICY.md`. Modify only with the writer
  paused or via tombstone manifest.

## 7. Two-gate defense (watchlist + hard whitelist)

The Journal applies the symbol policy in **two layers**:

```
TV webhook POST
      ↓
[ Gate 1 — Watchlist gate ]   reads strategy_rules.json :: allowed_symbols
      ├── base ∈ allowed_symbols   → continue
      └── base ∉ allowed_symbols   → log to watchlist_rejections.jsonl ;
                                      respond 200 with rejected_by_watchlist=true ;
                                      DO NOT call write_indicator_signal
      ↓
[ write_indicator_signal ]
      ↓
[ Gate 2 — Hard whitelist gate ]   _normalize_indicator_parsed sets validation_status
      ├── validation_status == valid      → append to indicator_signals.jsonl + dedup
      └── validation_status startswith "rejected_"
                                          → _write_indicator_quarantine to
                                            indicator_signals_quarantined.jsonl ;
                                            DO NOT compute/persist dedup hash ;
                                            DO NOT append to indicator_signals.jsonl
```

**Invariant:** the two whitelists MUST be identical:
`{XAUUSD, XAGUSD, ETHUSD, US500, EURUSD, USOUSD}`.

- Watchlist gate set: `strategy_rules.json::allowed_symbols`.
- Hard gate set: `tv_webhook_receiver.py::KNOWN_BASE_SYMBOLS`.

Divergence is an **incident** to investigate. The hard gate is the
last-resort defense; it should not actively fire (because gate 1 already
filtered). If hard-gate quarantine entries appear without corresponding
watchlist alignment changes, audit which gate fired and why.

## 8. Synthetic test policy

Any synthetic test against the Journal — manual or scripted — must obey:

1. **Unique `test_run_id`** in the payload (high-resolution timestamp or UUID).
2. **Explicit markers** in the payload:
   - `source = "synthetic_<purpose>_test"`
   - `indicator_name = "TEST_<PURPOSE>"`
   - `signal_type = "TEST_<PURPOSE>"`
3. **No automatic post-test cleanup.** Resulting JSONL lines remain as test
   residuals.
4. **Cleanup, if ever, follows `LOG_MUTATION_POLICY.md`** (writer paused, or
   shared lock, or tombstone — default tombstone). The default disposition is
   "leave as documented residual"; no log surgery without explicit
   authorization.
5. **Markers + receiver patches must make test signals operationally inert:**
   the monitor filters by specific `signal_type` patterns (e.g. `NAS_LONG`)
   and would not act on `TEST_*`; future consumers must follow the same
   pattern. If a future consumer would action a `TEST_*` signal, that
   consumer is broken — fix the consumer, not the test policy.

## 9. Whitelist expansion process

Adding a new base symbol to the operational stream requires, in order:

1. **Human decision** — an explicit operator authorization stating the new
   base, the rationale, and any concerns (data availability, broker support,
   strategy fit).
2. **Code update** — add the base to
   `tv_webhook_receiver.py::KNOWN_BASE_SYMBOLS`. The same code commit may also
   touch any downstream that needs awareness.
3. **strategy_rules.json update** — add to `allowed_symbols`. Keep gates 1
   and 2 aligned (§7).
4. **Doc update** — this document's §3 table, plus any cross-reference
   (`OPERATIONAL_INVENTORY.md`, `SIGNAL_OUTCOME_LAB.md` if affected).
5. **End-to-end test** — a synthetic POST per §8 with the new base, verifying:
   acceptance, normalization to `PEPPERSTONE:<NEW_BASE>`, no warning, journal
   write, dedup hash present.
6. **Provider verification** — confirm Pepperstone offers the symbol at the
   expected timeframe(s); test a manual `chart_set_symbol("PEPPERSTONE:<NEW>")`
   under safe window.
7. **Downstream confirmation** — verify the monitor, revalidation lab, future
   Signal Outcome Lab handle the new base, or document why they don't
   (intentional limitation).

Without all of these, a new base **is rejected** by the gates and any
incoming alert is quarantined. There is no "trial mode" that bypasses §7.

Removing a base follows the same rigor: explicit decision, code update,
strategy_rules update, doc update, and migration plan for any in-flight data
referencing the removed base.

## 10. Relation to Signal Outcome Lab

The future Signal Outcome Lab (`SIGNAL_OUTCOME_LAB.md`) reads from this
Journal under strict invariants:

- **Only** operational records (`indicator_signals.jsonl` with
  `validation_status == "valid"`).
- **Only** records whose `symbol` starts with `PEPPERSTONE:`.
- **Only** records whose `base_symbol` is in the active whitelist (§3).
- `signal_hash` is the traceability key from signal to outcome.

Quarantined and watchlist-rejected records are visible to the Lab **for audit
purposes only** (statistical view of what was rejected over time, distribution
of rejection reasons, etc.). They never produce a clean operational outcome.

The legacy contaminated outcomes file
(`indicator_signals_outcomes.jsonl.contaminated_pre_pepperstone_fix_2026-05-28`)
is **not an input** to the Lab nor to this Journal. It is preserved for
forensic comparison only (see `SIGNAL_OUTCOME_LAB.md` §10).

## 11. Relation to `LOG_MUTATION_POLICY`

Every file enumerated in §2 (Included) is `ACTIVE_APPEND_ONLY` per
`LOG_MUTATION_POLICY.md`:

- The receiver is the writer; it appends in `"a"` mode while loaded.
- Filter-and-rewrite of any of these files **while the receiver is loaded** is
  prohibited (race window risk).
- Allowed mutation methods, in order of preference: tombstone manifest
  (default) → shared lock (none deployed today) → writer paused/stopped.
- Cleanup of test residuals or accidentally-written entries follows the
  `LOG_MUTATION_POLICY` cleanup checklist; default to tombstone unless the
  operator explicitly authorizes a writer-paused rewrite.

The 2026-05-28 incident (synthetic test residuals accidentally rewritten
while the receiver was running, with an acknowledged race window) is the
motivating example for the cleanup discipline; see
`LOG_MUTATION_POLICY.md` §8 (Incident registry).

## 12. Incidents and history

Brief timeline up to and including the establishment of this policy.

| Date | Event |
|---|---|
| pre-2026-05-28 | Signals were written without provider prefix (`symbol = "XAUUSD"`, bare ticker). |
| pre-2026-05-28 | The decommissioned `enrich_indicator_outcomes.py` called `chart_set_symbol` with these bare tickers; TradingView resolved them to OANDA (default provider) instead of PEPPERSTONE — outcomes contaminated. |
| 2026-05-28 | Decommission of `com.cristrein.enrich-indicator-outcomes` (`f69a8ac`, see `OPERATIONAL_INVENTORY.md` §12). |
| 2026-05-28 | `_normalize_indicator_parsed` inverted in the receiver: instead of stripping broker prefixes, now ADDS `PEPPERSTONE:`. New fields `raw_symbol`, `provider`, `normalization_method`, `_normalize_warning` introduced. |
| 2026-05-28 | Hard whitelist gate (`a6cf65a`) added: bases outside `{XAUUSD, XAGUSD, ETHUSD, US500, EURUSD, USOUSD}` are rejected and quarantined; `BTCUSD / XPTUSD / USDJPY` explicitly removed from any prior implicit list. |
| 2026-05-28 | Receiver restarted (`kickstart -k`); new code in production. End-to-end test (`test_run_id 2026-05-28T12:33:16.6NZ`) validated: `XAUUSD` accepted as `PEPPERSTONE:XAUUSD` (valid); `USDJPY` rejected by the watchlist gate (already aligned; hard gate did not need to fire). |
| 2026-05-28 | `LOG_MUTATION_POLICY.md` codified the prohibition against filter-and-rewrite of active append-only logs (motivated by an acknowledged race window during smoke-test cleanup). |
| 2026-05-28 | `SIGNAL_OUTCOME_LAB.md` codified the architecture for the clean replacement of the decommissioned outcome layer. |
| 2026-05-28 | This document (Phase 1 of the roadmap) — formalizes the Indicator Signal Journal as the canonical entry layer. |

## 13. Out of scope

This policy does **not** cover:

- Outcome calculation logic (`SIGNAL_OUTCOME_LAB.md`).
- The old enrich pipeline (decommissioned; `OPERATIONAL_INVENTORY.md` §12).
- Backtests (`my-strategy/research/` per its own decision flow).
- Visual audit of strategies (separate workstream + safe window).
- Signal performance analysis / edge reports (downstream consumers; this
  policy only governs the input layer).
- TradingView alert (alarme) definitions on the TV side. The Journal accepts
  bare tickers and normalizes internally; TV-side alarm authorship is
  unconstrained by this policy.
- Strategy catalog / status (`catalog.json` per its own schema and validator).
- Cold-storage data (`DATA_STORAGE_POLICY.md`).

## 14. Change control

Any material change to this policy — whitelist expansion, provider policy
change, addition or removal of a log, gate logic change, schema change —
requires:

1. **Own commit.** No mixing with unrelated changes.
2. **Validations** equivalent to those in §9 (code change + e2e test +
   provider verification + downstream confirmation if applicable).
3. **`OPERATIONAL_INVENTORY.md` update** in the same commit when the change
   affects operational state (writers, gates, files, LaunchAgents).
4. **Explicit operator authorization**, recorded in the conversation/issue
   that triggers the change.
5. **No silent expansion or relaxation.** Gates default to rejection on
   ambiguity; expansion is an explicit, audited act.

Routine refinements (clarification, examples, cross-references) may be made
in smaller commits without invoking the full §14 chain, but still require
explicit authorization for the commit itself.

End of policy.
