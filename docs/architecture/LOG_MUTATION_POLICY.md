# Log Mutation Policy

**Effective:** 2026-05-28
**Scope:** all append-only operational logs under `alert-bridge/logs/` and any future
log file with the same access pattern.

## 1. Definition — `ACTIVE_APPEND_ONLY`

An `ACTIVE_APPEND_ONLY` file satisfies **all** of:

1. It is opened in **append mode (`"a"`)** by one or more production writers.
2. Writers may append at **any time** while the system is running (event-driven
   or scheduled), with no application-level lock protecting the file against
   external readers/rewriters.
3. The file is the **operational source of truth** for downstream consumers
   (monitor, enrich, analytics, weekly reviews, audits) or an **audit trail**
   for security/compliance purposes (provider rejections, dedup state).
4. Loss of a single appended record between read and rewrite is **detectable
   only by external means** (no record of how many writes happened during a
   maintenance window).

If any of those four conditions fails, the file is **not** `ACTIVE_APPEND_ONLY`
and this policy does not bind it (e.g. files inside a tempdir; files in
`backups/`; files behind a paused writer).

## 2. Known `ACTIVE_APPEND_ONLY` files (non-exhaustive)

| Path | Writer | Append mode | Audit value |
|---|---|---|---|
| `alert-bridge/logs/indicator_signals.jsonl` | `tv_webhook_receiver.py` (`write_indicator_signal`) | `"a"` | operational signal journal |
| `alert-bridge/logs/indicator_signals_quarantined.jsonl` | `tv_webhook_receiver.py` (`_write_indicator_quarantine`) | `"a"` | rejected signals audit |
| `alert-bridge/logs/watchlist_rejections.jsonl` | `tv_webhook_receiver.py` (watchlist gate) | `"a"` | symbol-watchlist rejections |
| `alert-bridge/logs/indicator_signals_outcomes.jsonl` | (decommissioned `enrich_indicator_outcomes.py`; flagged `contaminated_pre_pepperstone_fix`) | `"a"` | outcome history |
| `alert-bridge/logs/indicator_signals_dedup_index.json` | `tv_webhook_receiver.py` (`_persist_indicator_dedup_set`) | `"w"` (rewrite of in-memory cache) | dedup state |
| `alert-bridge/logs/tradingview_alerts.jsonl` | `tv_webhook_receiver.py` (`run_claude_recheck_background`) | `"a"` | raw TV alert archive |
| `alert-bridge/logs/strategy_eval_log.jsonl` | `monitor_xau_4h_strategies.py` | `"a"` | strategy evaluation history |
| `alert-bridge/logs/strategy_signals.jsonl` | `monitor_xau_4h_strategies.py` | `"a"` | matched strategy signals |
| `alert-bridge/logs/schema_warnings.jsonl` | `tv_webhook_receiver.py` | `"a"` | schema validation shadow |
| `alert-bridge/logs/launchd_*_stdout.log` / `*_stderr.log` | various LaunchAgents | `"a"` (launchd) | process stdio |

Treat any newly introduced `*.jsonl` / `*.log` under `alert-bridge/logs/` as
`ACTIVE_APPEND_ONLY` unless explicitly documented otherwise.

The `indicator_signals_dedup_index.json` rewrite is operated by the writer
itself (atomic from its perspective). External rewriters must coordinate as
with append-only files — never rewrite while the receiver is running.

## 3. Prohibition

While a writer is **running** (process alive, LaunchAgent loaded and not
paused), the following are **prohibited** against an `ACTIVE_APPEND_ONLY` file:

- **Filter-and-rewrite** (read all → filter in memory → write to `.tmp` →
  `os.replace`/`mv` over the original). This pattern carries an inherent race
  window between the read and the replace; appended records during that window
  are **silently lost**.
- **In-place line removal** (`sed -i`, `ed`, etc.).
- **Truncation** (`> file`, `truncate`, `: > file`).
- **Move/rename** of the active file (writers re-open by path on next append
  in some setups; in others they keep an open FD pointing to the inode
  underneath — either way, behaviour becomes implementation-dependent and
  unsafe).
- **Manual edit** (vim/nano/anything that writes a new inode atomically and
  swaps).
- **Mass deletes of historical lines** even with strict marker filters — race
  remains regardless of selectivity.

These prohibitions apply **even with extremely specific markers** (e.g. unique
`test_run_id`). The race window does not depend on what you filter — it
depends on the read-then-replace pattern itself.

## 4. Allowed methods

Three methods, in order of decreasing intrusiveness:

### 4.1 Writer paused/stopped

Bring the writer to a state where it provably cannot append:

- `launchctl bootout gui/$UID/<label>` and verify `launchctl list | grep
  <label>` is empty AND `ps -ef | grep <writer>` is empty AND any chart/file
  lock the writer held is released.
- Or `kill -STOP <pid>` (SIGSTOP) — process stays loaded but frozen; SIGCONT
  to resume.
- Or rely on an explicit pause flag the writer honours (`touch
  /tmp/<writer>.paused`) — only when the writer's source code is known to
  check the flag before each append.

After confirmation of paused/stopped state, filter-and-rewrite is safe.
Restore the writer with `launchctl bootstrap` / `SIGCONT` / `rm` the flag
after the rewrite, in that order.

### 4.2 Shared lock, demonstrably honoured

If the writer and the cleanup tool **both** acquire the same OS-level lock
(e.g. `flock` on `/tmp/<writer>.lock`) around their respective write/rewrite,
filter-and-rewrite is safe under that lock. This is the highest-rigour option
but requires:

- The writer's source code explicitly acquires the lock around every append
  (this is the case for the `chart_lock` mutex but **not** generally for
  log appends — most JSONL writes today are unsynchronised).
- The cleanup tool acquires the same lock and holds it for the entire
  read+filter+replace transaction.

Today, **no `ACTIVE_APPEND_ONLY` log has a documented shared lock**. Until
one is introduced and documented, do not use this method.

### 4.3 Tombstone / quarantine manifest (preferred for production-running
systems)

Do **not** physically rewrite the JSONL. Instead, write a separate, small
**manifest** that downstream consumers consult to exclude entries logically:

- Manifest file (e.g. `alert-bridge/logs/<log>.tombstones.jsonl`,
  itself append-only).
- One entry per excluded line: `{tombstoned_at, reason, identifier_field,
  identifier_value, audit_note}`.
- Downstream readers join: `for line in log: if line[identifier] in
  tombstones: skip`.

Properties:
- No race (manifest is independent append; original log untouched).
- Auditable (every exclusion is recorded with reason + timestamp).
- Reversible (delete the manifest entry; the line returns to the active set).
- Compatible with running writers (zero coordination).

This is the **default method** for cleanup of test/contamination/erroneous
entries on a running production system.

## 5. Synthetic test policy

Synthetic tests against running writers (e.g. POST `/webhook/<SECRET>` with a
test payload) are allowed when:

1. The payload carries a **unique `test_run_id`** (high-resolution timestamp
   to microseconds or a UUID).
2. The payload carries explicit synthetic markers:
   - `source = synthetic_<purpose>_test`
   - `indicator_name = TEST_<PURPOSE>`
   - `signal_type = TEST_<PURPOSE>`
3. The resulting entries are reported in the test deliverable (path, line,
   identifying fields).
4. **No automatic post-test cleanup** of the appended entries. If cleanup is
   desired, it follows section 4 and requires explicit authorization.
5. The entries are documented as test residuals — operational consumers must
   not action them (monitor filters, enrich filters, etc. should already
   exclude `TEST_*` indicator/signal names by design).

## 6. Cleanup policy

Cleanup of unwanted entries (test residuals, contamination, errors) on an
`ACTIVE_APPEND_ONLY` log requires:

1. **Explicit authorization** stating which entries and by what method.
2. Method choice per section 4 (writer paused / shared lock / tombstone).
3. **Tombstone is the default.** Do not bring a writer down just to remove a
   handful of identifiable entries unless the manifest approach is genuinely
   inadequate.
4. **Backup before any physical rewrite** (writer-paused method only) to a
   `*.before_<reason>_<date>` sibling. Do not delete backups.
5. Cleanup post-conditions reported: counts before/after, exact lines removed,
   greps showing markers gone, sanity of writer/production state.

If a cleanup must touch dedup state (e.g. `*_dedup_index.json`), note that
the writer's in-memory cache will likely have the same data; a restart may
be required for full consistency, and that restart needs its own
authorization.

## 7. Mandatory checklist

### Before any cleanup or maintenance touching an `ACTIVE_APPEND_ONLY` file

- [ ] Identify the writer process and LaunchAgent label.
- [ ] Confirm the file is in scope of this policy.
- [ ] Choose method per section 4 (default: tombstone).
- [ ] If physical rewrite: confirm writer paused/stopped (3-way check:
      `launchctl list`, `ps`, lock holder).
- [ ] Take backup (`*.before_<reason>_<date>`).
- [ ] Capture line count + identifying snapshot of last N lines.
- [ ] State the exact filter criteria (multiple AND'd markers).
- [ ] Get explicit authorization quoting the criteria and method.

### After

- [ ] Re-verify writer state (paused or running as expected).
- [ ] If writer was paused: restore + verify with new pid + clean stderr.
- [ ] Count lines, count removals, confirm = expected.
- [ ] Greps for markers return 0.
- [ ] If tombstone manifest: verify downstream consumer reads it correctly
      (or document that consumers will pick it up on next run).
- [ ] Production sanity: receiver `/health`, public `/health`, dependent
      daemons, orphan processes, pause flags.
- [ ] Report deliverable per project conventions.

## 8. Incident registry — motivation for this policy (2026-05-28)

On 2026-05-28, during validation of the PEPPERSTONE hard whitelist gate, a
smoke test inadvertently wrote 9 synthetic entries to operational logs (3 to
`indicator_signals.jsonl`, 6 to `indicator_signals_quarantined.jsonl`).
A first cleanup attempt used the **filter-and-rewrite** pattern (read +
filter + `os.replace`) **while the receiver was running and appending real
alerts**. The race window was on the order of milliseconds; in this case the
counts before/after suggest no real alert was actually lost, but the
**possibility** was real and acknowledged in the deliverable.

This policy formalises the lesson: a small-but-non-zero probability of
silently dropping a production record is **never acceptable** as a default
posture for cleanup, regardless of how identifiable the unwanted entries
are. The tombstone manifest pattern is the safe default; physical rewrite is
the exception, gated by writer pause.

Cleanup of the 2 test entries from the e2e validation in the same session
(test_run_id `2026-05-28T12:33:16.6NZ`) was **deferred** under this policy and
remains pending — to be resolved with a method aligned to section 4 on a
later, explicitly authorised step.

## 9. Out of scope

- Files outside `alert-bridge/logs/` (e.g. canonical slim features under
  `slim_features/`, RAW replay archive) — those have their own immutability
  guarantees (cold storage, manifests, SHA256).
- Files inside `backups/` — by definition not active.
- LaunchAgent plists — governed by separate decommission/maintenance flow.
- Pure metric/state files written wholesale by a single owner with no
  external readers (rare; document case-by-case if introduced).

## 10. Cross-references

- `docs/architecture/OPERATIONAL_INVENTORY.md` — catalog of LaunchAgents,
  writers, decommissioned components.
- `docs/architecture/DATA_STORAGE_POLICY.md` — cold storage / RAW / manifests.
- `alert-bridge/tv_webhook_receiver.py::_normalize_indicator_parsed` and
  `::write_indicator_signal` — current writer behaviour for signals.
- `alert-bridge/tv_webhook_receiver.py::_write_indicator_quarantine` — current
  writer behaviour for rejections.
