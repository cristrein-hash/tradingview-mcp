# Signal Outcome Lab — MVP Contract

**Status:** design only. **Not implemented.** No code, no LaunchAgent, no data
movement, no production effect from this document.

**Date:** 2026-05-28.

**Parent design:** `docs/architecture/SIGNAL_OUTCOME_LAB.md` (architecture).
This document **concretizes** the MVP scope and adds operational decisions
beyond the parent. Where the two conflict on MVP scope, this document wins.

---

## 1. Objective and MVP scope

The Signal Outcome Lab MVP produces clean R-style outcome records for
PEPPERSTONE:XAUUSD signals only, using exclusively canonical slim/features data
already on the external drive, with no TradingView chart access, no
LaunchAgent, no scheduler, and no daemon. The MVP is a manual batch tool that
operators invoke explicitly.

The MVP supports two modes:

1. **`fresh_from_signal_journal`** — operates on new valid signals from
   `alert-bridge/logs/indicator_signals.jsonl` going forward.
2. **`backfill_from_quarantine`** — operates on the 330 records preserved in
   `alert-bridge/logs/indicator_signals_outcomes.jsonl.contaminated_pre_pepperstone_fix_2026-05-28`,
   to recover the **signals** behind the contaminated outcomes while never
   trusting the old outcomes as truth.

Both modes share the same evaluator, the same data source policy, and the
same output schema; they differ only in input and in the presence of
`legacy_outcome_ref` / `old_vs_new_diff` fields.

**In-scope for MVP:**

- Symbol: PEPPERSTONE:XAUUSD only.
- Data source: `/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD/` only.
- Execution: manual batch CLI, `--dry-run` default.
- Output: derived files under `alert-bridge/logs/signal_outcomes_lab/`.

**Out-of-scope for MVP** (see section 18).

---

## 2. Mode A — `fresh_from_signal_journal`

### Input

- File: `alert-bridge/logs/indicator_signals.jsonl` (read-only).
- Filter chain (a signal must pass ALL):
  - `payload_full.validation_status == "valid"`;
  - `payload_full.symbol` startswith `PEPPERSTONE:`;
  - `payload_full.provider == "PEPPERSTONE"`;
  - `payload_full.base_symbol == "XAUUSD"` (MVP scope);
  - `indicator_name` does NOT start with `TEST_`;
  - `signal_type` does NOT start with `TEST_`;
  - `payload_full.source` (if present) does NOT start with `synthetic_`;
  - signal `ts_signal` is mature for the chosen horizon (see section 7).
- Synthetic markers above are mandatory per `INDICATOR_SIGNAL_POLICY.md`
  section 8.

### Output

Records carry `signal_provenance = "signal_journal_v2"`. No `legacy_outcome_ref`
and no `old_vs_new_diff` fields in Mode A output.

### Behavior on filter failure

| Reason | Output |
|---|---|
| `validation_status != "valid"` | dropped silently (not in MVP universe) |
| Non-XAU base | `outcome_status = SKIPPED_UNSUPPORTED_SYMBOL` |
| Provider mismatch (defensive) | `outcome_status = SKIPPED_PROVIDER_MISMATCH` |
| TEST_/synthetic marker | dropped silently |
| Immature ts_signal | not picked up this batch (retry later) |
| Canonical coverage gap | `outcome_status = UNKNOWN` |

---

## 3. Mode B — `backfill_from_quarantine`

### Input

- File: `alert-bridge/logs/indicator_signals_outcomes.jsonl.contaminated_pre_pepperstone_fix_2026-05-28`.
- Access mode: read-only. The file is never modified, moved, or deleted.
- Classification: **QUARANTINED_LEGACY_REFERENCE.** The records inside provide
  signal provenance only; the legacy outcomes inside are not source of truth.

### Filter chain (Mode B)

A quarantined record is processed only when ALL hold:

- `base_symbol == "XAUUSD"` (MVP scope);
- `ts_signal` parseable to ISO8601 with timezone;
- `timeframe` in `{"15","30","60"}` (the set observed in the quarantine file);
- `atr_at_signal` present OR ATR recomputable from canonical (see section 6);
- `direction_classified` in `{"long","short","ambiguous"}` (any of the three;
  ambiguous is handled by section 5);
- canonical slim coverage exists for `[ts_signal, ts_signal + max_horizon]`.

### Behavior on filter failure (Mode B)

| Reason | Output |
|---|---|
| Non-XAU base (ETHUSD / EURUSD / US500 / XAGUSD / USOUSD) | `outcome_status = PENDING_NO_CANONICAL_DATA`; record listed in `skipped_signals.jsonl` |
| Unrecognized timeframe | listed in `skipped_signals.jsonl` with reason |
| ATR absent AND not recomputable | listed in `skipped_signals.jsonl` |
| Canonical coverage gap | `outcome_status = UNKNOWN` |

### Output

Records carry `signal_provenance = "quarantine_legacy_2026-05-28"`. Each
record MUST include `legacy_outcome_ref` and `old_vs_new_diff`.

### Quarantined record use policy

Permitted:
- Read fields as signal provenance.
- Cite `outcome_R`, `outcome_label`, `snapshots` as **legacy reference**.

Forbidden:
- Use legacy R/label as ground truth.
- Promote a legacy outcome into `outcomes_current.jsonl` without recomputation.
- Modify, move, or delete the quarantine file.

---

## 4. Schema reference — quarantine file

Established by read-only audit on 2026-05-28. Source path:
`alert-bridge/logs/indicator_signals_outcomes.jsonl.contaminated_pre_pepperstone_fix_2026-05-28`.

### Top-level fields (presence over 330 records)

| Field | Presence | Notes |
|---|---|---|
| `signal_hash` | 330/330 | 16-char hex; link to Signal Journal |
| `ts_signal` | 330/330 | ISO8601 with timezone |
| `base_symbol` | 330/330 | NO provider prefix (root of contamination) |
| `timeframe` | 330/330 | string "15" / "30" / "60" |
| `indicator_name` | 330/330 | Custom_OB_Detector (218), Market_Bubbles (61), RSI (29), NAS_TopBottom_Detector (22) |
| `signal_type` | 330/330 | semantic string |
| `direction_classified` | 330/330 | long (108), short (114), ambiguous (108) |
| `entry_price` | 330/330 | price at signal bar |
| `atr_at_signal` | 330/330 | ATR(14); used to derive legacy stops |
| `snapshots` | 330/330 | dict: close_plus_1/5/10/20 |
| `long_outcome` | 224/330 | R-multiple dict; null when not computed |
| `short_outcome` | 231/330 | R-multiple dict; null when not computed |
| `bars_evaluated` | 330/330 | always 20 (legacy horizon was fixed H20) |
| `enrichment_notes` | 330/330 | free text |
| `enriched_at` | 316/330 | when legacy enrich ran |
| `outcomes_by_atr_mult` | 164/330 | extended schema (later records) |
| `potential_direction` | 164/330 | extended schema (later records) |
| `outcome_structural` | 164/330 | extended schema (later records) |

### Fields ABSENT (significant)

- `symbol` (with `PEPPERSTONE:` prefix): 0/330 — confirms `chart_set_symbol(base_only)` contamination path.
- `provider`: 0/330.
- `payload_full` (original alert payload): 0/330.

### Linkage to Signal Journal

- 330/330 signal_hashes match records in `indicator_signals.jsonl`.
- 0/330 match `validation_status == "valid"` because the matching SJ entries
  predate the receiver hardening (2026-05-28).
- Implication: in Mode B, the quarantine record is the canonical signal source;
  cross-referencing to SJ is informational only.

### Recoverability summary

| base_symbol | total | TF=15 | TF=30 | TF=60 | recoverable in MVP |
|---|---|---|---|---|---|
| XAUUSD | 54 | 23 | 16 | 15 | 54 (100% of XAU) |
| ETHUSD | 94 | 56 | 27 | 11 | 0 (no canonical) |
| EURUSD | 62 | 26 | 20 | 16 | 0 (no canonical) |
| US500  | 61 | 23 | 22 | 16 | 0 (no canonical) |
| XAGUSD | 59 | 23 | 23 | 13 | 0 (no canonical) |
| **TOTAL** | **330** |  |  |  | **54** |

MVP rescues 54/330 (16.4%). The remaining 276/330 (83.6%) are recorded as
`PENDING_NO_CANONICAL_DATA` in `skipped_signals.jsonl` and remain dormant until
canonical data for their bases exists.

---

## 5. Direction policy

Per signal:

1. `direction_classified` in `{"long","short"}` — process as a single outcome.
2. `direction_classified == "ambiguous"` — emit **two** outcome records, one
   `direction = "long"` and one `direction = "short"`, each with its own
   `outcome_id`. This replicates the legacy enrich behavior (which computed both
   `long_outcome` and `short_outcome` for ambiguous cases) and preserves
   information without inference.
3. Direction inference from `indicator_name` / `signal_type` heuristics is
   **forbidden**. Ambiguous stays explicit.

In Mode A (fresh), the direction comes from `payload_full.direction`. If
absent, the signal yields `outcome_status = UNKNOWN` (no inference).

---

## 6. ATR fallback policy

- If `atr_at_signal` is present in the quarantine record, use it.
- If absent (Mode B) or never recorded (Mode A future), recompute ATR(14) from
  the same canonical slim feed used to evaluate the outcome:
  - Window: 14 closed bars ending at the signal bar.
  - Algorithm: standard Wilder ATR(14) (same as legacy).
- Record the source in `provenance`:
  - `atr_source: "legacy_quarantine"` (used as-is from quarantine), OR
  - `atr_source: "recomputed_from_canonical"` (computed by the Lab).
- If both fail (e.g. insufficient prior bars in canonical), the signal is
  listed in `skipped_signals.jsonl` with reason `ATR_UNAVAILABLE`.

ATR is only used to derive stop/target units for R-multiple computation. When
no stop is derivable, `R` fields stay `null` and the absolute/percent metrics
remain valid.

---

## 7. Data source policy

Priority order:

1. **Canonical slim** at `/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD/<TF>/`
   where `<TF>` is one of `15M`, `30M`, `1H`. The Lab maps the signal
   timeframe to the slim TF directory (15→15M, 30→30M, 60→1H).
   - Record: `data_source = "canonical_slim_v2"`, `data_source_ref = "<file>:rows[i..j]"`, `data_source_sha256 = <sha256 of file>`.
2. **Cross-TF** is not required by the MVP (horizons are intra-TF; see
   section 9). Cross-TF integration is deferred to a post-MVP version.
3. **TradingView chart fallback is NOT permitted in the MVP.** If canonical
   does not cover the window, emit `outcome_status = UNKNOWN` and proceed to
   the next signal.
4. **No fabrication.** The Lab never synthesizes prices.

### Pre-batch hard checks (drive / coverage)

Before any record is written:

- The external drive `/Volumes/GUTS_ LACIE/` MUST be mounted.
- The directory `slim_features/XAUUSD/` MUST exist on it.
- For each timeframe being processed, the relevant subdirectory MUST exist and
  contain at least one slim file.
- For each signal: there MUST exist a slim file whose covered range includes
  `[ts_signal, ts_signal + max_horizon_window]`.

Failure of the drive / dir checks → abort batch before any output is written.
Failure of the per-signal coverage → the signal goes to `UNKNOWN`.

---

## 8. Output structure

### Directory layout

```
alert-bridge/logs/signal_outcomes_lab/
  <run_dir>/
    outcomes_<run_id>.jsonl
    outcomes_<run_id>.manifest.json
    outcomes_<run_id>.log
    legacy_comparison_report.md     # Mode B only
    skipped_signals.jsonl           # Mode B only
  outcomes_current.jsonl            # rollup across runs
```

`<run_dir>` is a per-batch subdir named e.g. `backfill_2026-05-28` or
`fresh_2026-05-29`. This isolates each batch and prevents accidental
cross-contamination of run artifacts.

### Per-file role

| File | Mode A | Mode B | Lifetime |
|---|---|---|---|
| `outcomes_<run_id>.jsonl` | yes | yes | append-only within the run; immutable after |
| `outcomes_<run_id>.manifest.json` | yes | yes | write-once at batch end |
| `outcomes_<run_id>.log` | yes | yes | append-only within the run |
| `legacy_comparison_report.md` | — | yes | write-once at batch end |
| `skipped_signals.jsonl` | — | yes | append-only within the run |
| `outcomes_current.jsonl` | shared | shared | atomic replace (`*.tmp` + `mv`) |

The Lab is the **only** writer of any file under `signal_outcomes_lab/`. No
process writes there concurrently, by design.

---

## 9. `outcomes_current.jsonl` policy

- Contains exclusively records with `outcome_status == "CLEAN"`.
- Dedup by `outcome_id`: when multiple runs produced the same outcome_id, the
  latest run's record wins.
- Sole writer: the Lab. Read-only for all consumers.
- Update mechanism: write `outcomes_current.jsonl.tmp`, then atomic
  `mv outcomes_current.jsonl.tmp outcomes_current.jsonl`. Allowed because no
  other process writes this file (unlike `indicator_signals.jsonl`, which is
  ACTIVE_APPEND_ONLY with a live receiver writer).
- Cross-reference: `LOG_MUTATION_POLICY.md`. The atomic-replace pattern is
  permitted here because the writer-paused condition is structural (the Lab
  is the only writer at all).
- Consumer reactivation (auto_d2r_daily, weekly_review, report_indicator_edge
  reading this file) is **out of scope** for the MVP. See section 18.

---

## 10. `old_vs_new_diff` verdict enum (Mode B only)

Each Mode B record carries a `verdict` field comparing the legacy outcome to
the newly computed outcome:

| Verdict | Condition |
|---|---|
| `OUTCOME_AGREES` | direction matches AND `outcome_label` matches AND `\|close_plus_20_diff_pct\| < 0.5%` |
| `OUTCOME_DIVERGES_MAGNITUDE` | direction matches BUT R-multiple differs beyond tolerance |
| `OUTCOME_DIVERGES_SIGN` | direction matches BUT win became loss or vice versa |
| `LEGACY_INCOMPLETE` | legacy `<direction>_outcome` was null for the relevant direction |
| `NEW_INCOMPLETE` | new outcome could not be computed (data gap, ATR unavailable) |
| `NOT_COMPARABLE` | legacy `direction_classified == "ambiguous"` AND both directions are split — comparison is structural-only |

Tolerance thresholds (initial; adjustable in a future version):

- close_plus_N agreement: absolute price diff < 0.5% of entry_price.
- R-multiple agreement: |R_new - R_legacy| < 0.25.

The aggregated counts of these verdicts populate
`legacy_comparison_report.md`.

---

## 11. Outcome schema v0.1.0

Each record is a single JSON-line. Fields marked `[backfill only]` appear only
in Mode B output.

```json
{
  "outcome_id":             "sha256(signal_hash|evaluator_version|horizon_spec_id|data_source_resolution)[:16]",
  "signal_hash":            "e5ce5e83e7f053db",
  "signal_provenance":      "signal_journal_v2 | quarantine_legacy_2026-05-28",
  "run_id":                 "fresh-2026-05-29T14-00Z-a1b2 | backfill-2026-05-28T18-00Z-c3d4",
  "evaluator_version":      "v0.1.0",
  "evaluated_at":           "<ISO8601 microseconds with timezone>",

  "base_symbol":            "XAUUSD",
  "symbol":                 "PEPPERSTONE:XAUUSD",
  "provider":               "PEPPERSTONE",
  "timeframe":              "15 | 30 | 60",

  "ts_signal":              "<ISO8601 with timezone>",
  "indicator_name":         "Market_Bubbles",
  "signal_type":            "Small_Sell",
  "direction":              "long | short",
  "horizon":                {"bars": 20, "tf": "15", "spec_id": "H20@15M"},

  "data_source":            "canonical_slim_v2",
  "data_source_ref":        "/Volumes/.../slim_features/XAUUSD/15M/<file>:rows[i..j]",
  "data_source_sha256":     "<sha256 of slim file>",

  "provider_status":        "ok",
  "legacy_provider_status": "contaminated_pre_pepperstone_fix",   // backfill only
  "outcome_status":         "CLEAN | UNKNOWN | SKIPPED_UNSUPPORTED_SYMBOL | SKIPPED_PROVIDER_MISMATCH | PENDING_NO_CANONICAL_DATA",

  "entry_price":            2181.34,
  "stop_price":             null,
  "target_price":           null,
  "close_after_horizon":    2120.17,

  "mfe":                    {"price": 2169.14, "abs": -12.20, "pct": -0.0056, "R": null},
  "mae":                    {"price": 2185.10, "abs": 3.76,   "pct": 0.0017,  "R": null},
  "return_pct":             -0.028,
  "directional_result":     "short_close_below_entry",
  "hit_result":             "target | stop | time_limit | not_applicable",

  "legacy_outcome_ref": {                                            // backfill only
    "file":            "indicator_signals_outcomes.jsonl.contaminated_pre_pepperstone_fix_2026-05-28",
    "line_no":         1,
    "enriched_at":     "2026-05-18T13:15:17.171763+00:00",
    "bars_evaluated":  20,
    "snapshots":       {"close_plus_1": 2178.36, "close_plus_5": 2129.74, "close_plus_10": 2111.89, "close_plus_20": 2120.17},
    "outcome_for_direction": {"outcome_R": 2.0, "outcome_label": "win_2r", "max_favorable_R": 23.57, "max_adverse_R": -0.027}
  },

  "old_vs_new_diff": {                                               // backfill only
    "close_plus_20_diff_abs":   0.0,
    "close_plus_20_diff_pct":   0.0,
    "outcome_label_match":      true,
    "outcome_R_diff":           0.0,
    "verdict":                  "OUTCOME_AGREES"
  },

  "errors":                 [],
  "warnings":               [],

  "provenance": {
    "signal_source_path":      "<input file>",
    "signal_source_line_no":   1,
    "raw_symbol_observed":     "XAUUSD",
    "horizon_bars_used":       20,
    "data_window_from":        "<ISO8601>",
    "data_window_to":          "<ISO8601>",
    "data_bars_observed":      20,
    "data_bars_expected":      20,
    "atr_source":              "legacy_quarantine | recomputed_from_canonical | unavailable",
    "chart_lock_holder":       null
  }
}
```

Notes:

- `R` fields stay `null` when no stop is derivable. The MVP does not invent
  stop levels.
- `data_source_sha256` enables strong idempotence and external audit of which
  slim file produced each outcome.
- `chart_lock_holder` is always `null` in the MVP because the Lab never
  touches the chart.

---

## 12. Idempotency

```
outcome_id = sha256(
  signal_hash
  | evaluator_version
  | horizon_spec_id        # e.g. "H20@15M"
  | data_source_resolution # e.g. "canonical_slim_v2|<file_sha256>"
)[:16]
```

Invariants:

- Same inputs → same outcome_id → record deduped on rollup.
- Changed `evaluator_version` → new outcome_id → recomputation (intentional).
- Re-extracted slim file (different SHA256) → new outcome_id → recomputation
  (intentional; catches data regeneration).
- Different horizons of the same signal yield different outcome_ids (expected).
- For ambiguous signals (Mode B): the two split records carry the synthesized
  `direction` in `horizon_spec_id` to keep their outcome_ids distinct.

Skip logic: if `outcomes_current.jsonl` already has a CLEAN record with the
same `outcome_id`, the run skips it. Non-CLEAN records (UNKNOWN, etc.) are
re-attempted each run.

---

## 13. Pre-flight gates

Before any record is written, ALL must hold:

1. External drive `/Volumes/GUTS_ LACIE/` mounted.
2. `slim_features/XAUUSD/` exists on the drive.
3. For each timeframe in the batch's input: matching subdirectory exists and
   contains slim files.
4. Output directory `alert-bridge/logs/signal_outcomes_lab/<run_dir>/` is
   created and writable.
5. The Lab makes ZERO calls to TradingView MCP / CDP / chart APIs.
6. Input file readable (`indicator_signals.jsonl` for Mode A, quarantine file
   for Mode B).
7. No `TEST_*` / `synthetic_*` markers pass the filter chain.
8. Every signal that passes the chain carries `PEPPERSTONE:XAUUSD` (or has
   `base_symbol == XAUUSD` and the Lab synthesizes the prefixed `symbol` in
   the output — never silently for non-whitelist bases).
9. XAU-only enforcement: any non-XAU signal in Mode A → `SKIPPED_UNSUPPORTED_SYMBOL`;
   any non-XAU signal in Mode B → `PENDING_NO_CANONICAL_DATA` + listed in
   `skipped_signals.jsonl`.

Failure of any structural gate (1-5) → abort the batch without writing.

---

## 14. CLI shape (proposed; not implemented)

```
scripts/run_signal_outcome_lab.py \
  --mode {fresh_from_signal_journal | backfill_from_quarantine} \
  --symbol XAUUSD \
  --evaluator-version v0.1.0 \
  --run-id <unique> \
  [--max-signals N] \
  [--output-dir alert-bridge/logs/signal_outcomes_lab] \
  [--signals-from <ISO8601>] \
  [--signals-to <ISO8601>] \
  [--dry-run]                                # default ON until explicit --no-dry-run
```

Notes:

- `--dry-run` is the default. The script refuses to write output without an
  explicit `--no-dry-run`.
- `--symbol` is currently only `XAUUSD` (MVP scope). Other values rejected.
- `--mode backfill_from_quarantine` ignores `--signals-from/--signals-to`
  (the quarantine file already defines the range).
- `--run-id` is mandatory; the script never auto-invents one to keep manifest
  audit clean.

The CLI is documentation. Implementation lives in a separate authorized
patch.

---

## 15. Test plan

Before any bulk run, validate with **3 hand-picked XAUUSD signals from
quarantine** (one per TF):

| TF | Pick criterion | Expected verdict |
|---|---|---|
| 15 | record with `direction_classified == "long"` and ATR present | producible; verdict TBD by data |
| 30 | record with `direction_classified == "short"` and ATR present | producible; verdict TBD by data |
| 60 | record with `direction_classified == "ambiguous"` | split into 2 outcomes; one per direction |

Per pick:

1. Run `--dry-run` and verify the manifest projects exactly the expected
   number of outcomes.
2. Run `--no-dry-run` and verify:
   - `outcomes_<run_id>.jsonl` has the expected number of lines;
   - each record has all required schema fields;
   - `legacy_outcome_ref` matches the quarantine row;
   - `old_vs_new_diff.verdict` is one of the enum values;
   - `data_source_sha256` matches the actual slim file;
   - `outcomes_current.jsonl` was atomically updated;
   - the input file (`indicator_signals.jsonl`) and the quarantine file are
     bit-identical before and after (SHA256 unchanged).
3. Verify no chart-touching MCP call was made (audit log; manifest's
   `chart_lock_holder` is null).
4. Verify no LaunchAgent was created or modified.

Only after the 3-pick test passes is bulk backfill of the remaining XAU
records authorized in a separate step.

---

## 16. Acceptance criteria

The MVP is acceptable when ALL of the following are true:

- The TradingView chart was not touched during any batch.
- No production component (receiver, monitor daemon, cloudflared, external
  factors, LaunchAgents, secrets) was modified by Lab execution.
- All Lab outputs live under `alert-bridge/logs/signal_outcomes_lab/`.
- For XAUUSD backfill: each producible quarantine record yields a CLEAN
  outcome with `legacy_outcome_ref` and `old_vs_new_diff` populated.
- For non-XAU records in Mode B: each is listed in `skipped_signals.jsonl`
  with `outcome_status = PENDING_NO_CANONICAL_DATA`.
- The quarantine file's SHA256 is unchanged after every run.
- The Signal Journal's content is unchanged after every run.
- The 330 legacy outcomes are never used as truth — every Mode B record is a
  fresh computation from canonical, with the legacy outcome attached only as
  audit reference.
- `outcomes_current.jsonl` contains only CLEAN records, deduped by outcome_id.
- `legacy_comparison_report.md` enumerates all 6 verdicts and provides
  per-base aggregate counts (only XAUUSD will have non-zero clean counts in
  MVP).

---

## 17. Relation to `SIGNAL_OUTCOME_LAB.md`

This document concretizes **Phase 3 (Lab MVP)** of the parent design.

**Material amendment to the parent roadmap (proposed):**

The parent's **Phase 2** ("Audit OANDA vs PEPPERSTONE on stratified sample of
the 330 quarantined records → produce `audit_report_2026-05-28.md`") becomes
**a byproduct of Mode B** in the MVP rather than a separate prior step.
Specifically:

- The MVP's Mode B recomputes outcomes under PEPPERSTONE/canonical for every
  XAUUSD record in quarantine.
- The MVP's `legacy_comparison_report.md` is the artifact that fulfills the
  intent of the proposed `audit_report_2026-05-28.md`.
- For non-XAU records (276/330), no comparison is produced in the MVP — they
  are explicitly `PENDING_NO_CANONICAL_DATA`. The parent's Phase 2 is also
  preempted for these because no PEPPERSTONE canonical exists to compare
  against.

This amendment should be reflected in `SIGNAL_OUTCOME_LAB.md` in a separate
commit (Patch 2) after the MVP doc is approved. Until then, the
SIGNAL_OUTCOME_LAB.md text on Phase 2 stands as historical intent; this MVP
doc is the operative plan.

Other phases of the parent remain unchanged:

- Phase 4 (selective regeneration): possibly merged with bulk backfill or
  superseded by it; to be decided after Mode B results.
- Phase 5 (consumer reactivation): unchanged, deferred.
- Phase 6 (re-enable d2r-daily): unchanged, deferred.
- Phase 7 (optional schedule): unchanged, deferred.

---

## 18. Out of scope (MVP)

This document does NOT cover:

- Outcomes for non-XAU bases (XAGUSD, ETHUSD, US500, EURUSD, USOUSD). They
  remain `PENDING_NO_CANONICAL_DATA` until their canonical slim is built.
- TradingView chart fallback for missing canonical coverage. The MVP never
  touches the chart.
- LaunchAgent / scheduler / `StartCalendarInterval` invocation. Manual only.
- Reactivation of `auto_d2r_daily.py`, `report_indicator_edge.py`, or
  `weekly_review.py::check_enrich_v2` to read `outcomes_current.jsonl`.
  These remain on their decommissioned/paused state until a separate phase.
- Re-enabling `com.cristrein.d2r-daily` LaunchAgent.
- Visual audit of strategies (separate workstream).
- R-multiple computation when the signal carries no stop and ATR is
  unavailable. In that case R stays `null`; absolute/percent metrics suffice.
- Changes to `strategy_rules.json` or `catalog.json`.
- Changes to `tv_webhook_receiver.py`, the Indicator Signal Policy, or the
  PEPPERSTONE whitelist.
- Extending the active whitelist beyond
  `{XAUUSD, XAGUSD, ETHUSD, US500, EURUSD, USOUSD}`.
- Real-time / streaming outcome computation. MVP is post-hoc batch.
- Cross-TF integration. Deferred to post-MVP version.

---

## 19. Cross-references

- `docs/architecture/SIGNAL_OUTCOME_LAB.md` — parent architecture; this MVP
  doc concretizes Phase 3 and absorbs Phase 2 for XAU.
- `docs/architecture/INDICATOR_SIGNAL_POLICY.md` — provider whitelist,
  validation status, synthetic markers.
- `docs/architecture/LOG_MUTATION_POLICY.md` — append-only discipline;
  rollup atomic-replace permitted because Lab is sole writer.
- `docs/architecture/OPERATIONAL_INVENTORY.md` — section 12 (enrich
  decommissioned), section 13 (outcome automation moratorium).
- `alert-bridge/tv_webhook_receiver.py` — current Signal Journal writer; not
  modified by the MVP.
- `scripts/extract_replay_features.py` — canonical slim builder; the MVP
  reads its outputs.

---

## 20. Change control

This document is amended only by explicit operator authorization, in the same
commit that records the architectural change. Material changes that affect
the parent (e.g. Phase 2 merge into Phase 3) must update
`SIGNAL_OUTCOME_LAB.md` in a separate authorized commit. No silent expansion
of MVP scope (e.g. adding TV fallback or non-XAU support) is permitted.

End of MVP contract.
