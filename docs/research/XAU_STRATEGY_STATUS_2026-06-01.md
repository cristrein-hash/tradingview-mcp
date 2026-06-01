# XAU Strategy Status — 2026-06-01

Single-page consolidated map of XAUUSD strategies after the recent
rejection/research cycle. **Read-only snapshot.** No promotion, no new
strategy, no operational change. Intended for navigation, not to drive
behaviour.

## 1. Map of XAU strategies

| strategy_id | TF | Status (catalog) | Visual review | Operational route | Telegram | Pine | Decision (date) |
|---|---|---|---|---|---|---|---|
| `XAU_4H_DEMAND_BREAKOUT` | 4H | **REJECTED** / DISABLED | ✅ done 2026-05-29 (52 trades) | monitor computes + logs only | **suppressed** (in `NO_TELEGRAM_DISPATCH`) | none | Rejected by visual auction-theory review |
| `XAU_4H_REVERSAL_CAPITULATION` | 4H | **REJECTED** / DISABLED | n/a (rejected by R-real revalidation) | monitor computes + logs only | **suppressed** (in `NO_TELEGRAM_DISPATCH`) | none | Rejected 2026-05-28 — canonical revalidation v2 showed no edge (PF 0.47, avg_R −0.31) |
| `XAU_4H_REVERSAL_DISCRETIONARY` | 4H | **RESEARCH** / WATCH_ONLY (recommended) | partial visual (Family C) | monitor evaluates SWEEP + BASE separately | **suppressed** (both `discr_sweep` and `discr_base` in `NO_TELEGRAM_DISPATCH`) | none | n=6 SWEEP, ~60% BASE — sample minúsculo, mantido como pesquisa |
| `XAUUSD_4H_BREAKOUT_CONTINUATION` | 4H | **ACTIVE_CANDIDATE** / LIVE_DORMANT | not visually reviewed yet (research-only) | recheck classifier (channel dormant) | not dispatched (channel dormant) | `pine_alerts/01_*.pine` | D1a documented as research-stage candidate (no promotion) |
| `XAUUSD_1H_DECISIVE_BODY60` | 1H | **REJECTED** / DISABLED | ✅ done 2026-06-01 (25 trades) | recheck prompt: DESATIVADO block | not dispatched (channel was already dormant) | `pine_alerts/05_*.pine` (kept for history) | Rejected by visual auction-theory review |
| `XAUUSD_INTRADAY_BB_CONFLUENCE` | 15M | RESEARCH / NOT_DEPLOYED | n/a | none active | not dispatched | none | Forward test stopped 2026-04-30 |
| `XAUUSD_4H_LONG_REJECTION_SWING` | 4H | REJECTED (legacy) / DISABLED | n/a | none active | not dispatched | none | Deactivated 2026-05-12 — superseded by BREAKOUT_CONTINUATION (predecessor) |
| `XAUUSD_1H_LONG_REJECTION_EXECUTION` | 1H | REJECTED (legacy) / DISABLED | n/a | recheck prompt: DESATIVADO block | not dispatched | none | Deactivated 2026-05-12 — original successor (BODY60) also rejected; no LONG 1H active |

## 2. Groups

### REJECTED / closed (5)

- `XAU_4H_DEMAND_BREAKOUT` (auction-theory visual)
- `XAU_4H_REVERSAL_CAPITULATION` (canonical revalidation R-real)
- `XAUUSD_1H_DECISIVE_BODY60` (auction-theory visual)
- `XAUUSD_4H_LONG_REJECTION_SWING` (legacy backtest negative)
- `XAUUSD_1H_LONG_REJECTION_EXECUTION` (legacy backtest no edge)

### RESEARCH-STAGE CANDIDATE (1)

- `XAUUSD_4H_BREAKOUT_CONTINUATION` — D1a (close_1D > EMA200_1D AND
  EMA50_1D > EMA200_1D) is the candidate filter. Walk-forward distributed
  W1/W2 (~50/50), W3 no-op. PF 1.479 → 1.862. **No operational
  promotion.** See revalidation v1 summary.md.

### WATCH_ONLY / RESEARCH (1)

- `XAU_4H_REVERSAL_DISCRETIONARY` — Family C, two triggers (SWEEP n=6,
  BASE ~60%). Telegram already suppressed; recommended deployment
  WATCH_ONLY.

### REFERENCE_ONLY (1, multi)

- `FAMILY_A_BIGBELUGA_ZONE_REVERSAL` — not symbol-specific; injected as
  prompt context. Out of XAU-only scope but worth noting it backs the
  recheck framework.

### Pendentes de inventário

- None at this date — all XAU-specific entries accounted for.

## 3. Operational verifications (confirmation)

- `XAU_4H_DEMAND_BREAKOUT` Telegram: **suppressed** —
  `monitor_xau_4h_strategies.py:52` includes `"demand_breakout"` in
  `NO_TELEGRAM_DISPATCH`.
- `XAU_4H_REVERSAL_CAPITULATION` Telegram: **suppressed** —
  `monitor_xau_4h_strategies.py:52` includes `"capitulation"` in
  `NO_TELEGRAM_DISPATCH`.
- `XAUUSD_1H_DECISIVE_BODY60_HTF` recheck/strategy_rules: **suppressed**
  — `claude_recheck.py:54,755,975` updated 2026-06-01 to mark module
  DESATIVADO and remove from `SETUP_CANDIDATO_FORTE` list;
  `strategy_rules.json:383` `module_backtest_n` set to DEACTIVATED
  string.
- `XAUUSD_4H_BREAKOUT_CONTINUATION` operational promotion: **none**.
  Catalog: `ACTIVE_CANDIDATE` / `LIVE_DORMANT`. Revalidation v1 summary
  explicitly states "no operational promotion yet; D1a is the
  research-stage candidate filter".
- `XAU_4H_REVERSAL_DISCRETIONARY` Telegram: **already suppressed** for
  both `discr_sweep` and `discr_base` via `NO_TELEGRAM_DISPATCH`.

## 4. Inconsistencies / loose ends (flagged, not patched)

These are misalignments worth a future cleanup patch but **not touched
in this session** because they do not change behaviour today (channels
dormant or Telegram already suppressed):

1. **`strategy_rules.json` line ~530 still has a structured
   `XAUUSD_1H_LONG_DECISIVE_BODY60_HTF` block with `"status": "active"`
   and full backtest metadata**, despite the `module_backtest_n` entry
   at line 383 being DEACTIVATED and `claude_recheck.py` prompt now
   marking the module as DESATIVADO. The structured block is consumed
   as JSON reference but not as a behaviour driver; the prompt block
   wins. Still: cleanup recommended for consistency.

2. **`claude_recheck.py:931` retains `Módulo ATIVO — XAUUSD_4H_LONG_
   BREAKOUT_CONTINUATION_REGIME_FILTERED`** with full SETUP_VALIDO
   instructions, while the catalog says ACTIVE_CANDIDATE /
   LIVE_DORMANT and the revalidation v1 summary explicitly states
   "no operational promotion yet". If the legacy recheck channel
   resumes any flow, the prompt would currently emit SETUP_VALIDO. No
   harm today because channel is dormant since 2026-05-17.

3. **Catalog `XAU_4H_REVERSAL_DISCRETIONARY` next_action references
   PATCH 2B as future work** ("stop SWEEP urgent Telegram dispatch"),
   but `NO_TELEGRAM_DISPATCH` already includes both `discr_sweep` and
   `discr_base`. Patch 2B is effectively done; the catalog text is
   stale.

4. **`XAUUSD_1H_LONG_REJECTION_EXECUTION` legacy structured block in
   `strategy_rules.json:408` lists `replacement_module:
   XAUUSD_1H_LONG_DECISIVE_BODY60_HTF`** — but BODY60 is now also
   rejected. The simpler `module_backtest_n` entry at line 385 was
   updated to mention this; the structured block was not.

## 5. State of D1a (as the only research-stage candidate filter)

- Defined in `my-strategy/research/revalidation/XAUUSD_4H_BREAKOUT_CONTINUATION/v1/summary.md` (committed 2026-06-01).
- Result: baseline +25.28 R → D1a +32.20 R; PF 1.479 → 1.862; only 1 target removed.
- Walk-forward W1+W2 carry the +6.93 R gain; W3 no-op.
- No operational promotion; preconditions documented (OOS data
  post-2026-06, then re-evaluate D1a_ext for chop_inflation_bear).
- H1/H2 archived as visual diagnostic in `docs/research/AUCTION_THEORY_VISUAL_REVIEW_RUBRIC.md`.
- Bubbles blocked on extractor populating `bubble_event_price` and
  `bubble_poc_*` (currently zeroed).
- chop_inflation_bear accepted as residual cost (~0.29 R/year).

## 6. Pine alerts on disk (XAU only)

| File | Status |
|---|---|
| `pine_alerts/01_xauusd_4h_breakout_continuation.pine` | kept (BREAKOUT_CONTINUATION 4H — research-stage candidate; not promoted) |
| `pine_alerts/05_xauusd_1h_decisive_body60_htf.pine` | kept for history (REJECTED; not for new alerts) |

No other Pine for XAU. Strategies in the monitor (`XAU_4H_DEMAND_BREAKOUT`, `CAPITULATION`, `DISCRETIONARY_SWEEP/BASE`) live in Python, not Pine.

## 7. Revalidation directories on disk (XAU only)

| Path | Strategy | Status |
|---|---|---|
| `my-strategy/research/revalidation/XAU_4H_DEMAND_BREAKOUT/v2/` | DEMAND_BREAKOUT | rejected source-of-truth |
| `my-strategy/research/revalidation/XAU_4H_REVERSAL_CAPITULATION/v2/` | CAPITULATION | rejected source-of-truth |
| `my-strategy/research/revalidation/XAUUSD_4H_BREAKOUT_CONTINUATION/v1/` | BREAKOUT_CONTINUATION | active research; D1a documented |

No revalidation dir for BODY60 (rejected before creation), DISCRETIONARY (still research; n too small), INTRADAY_BB (forward test stopped).

## 8. Next XAU frontier — recommendation

**No immediate new frontier.** All low-cost research frontiers on
mechanical strategies have been explored on the 4H and 1H sides:

- BREAKOUT_CONTINUATION 4H: D1a research closed; awaiting OOS data.
- BODY60 1H: rejected.
- DEMAND_BREAKOUT 4H, CAPITULATION 4H: rejected.
- DISCRETIONARY 4H: n too small (SWEEP=6) to meaningfully audit.
- INTRADAY_BB 15M: forward test stopped, deliberate pause.

**Three plausible directions, ranked by cost/value:**

1. **Wait for OOS data on D1a (2026-06+)** — lowest cost, highest
   value. Re-run walk-forward in 1-3 months on real new trades and
   confirm stability or trigger D1a_ext (extension cap) experiment for
   chop_inflation_bear residual cost.
2. **Visual audit of `XAU_4H_REVERSAL_DISCRETIONARY`** (SWEEP + BASE) —
   already auction-style by construction (Family C, sweep + reclaim),
   so auction-theory alignment is more likely than the mechanical
   strategies just rejected. Risk: n=6 SWEEP is too small for any
   statistical claim; only useful as setup-quality screening.
3. **Design a new auction-first XAU 1H strategy** — explicit
   precondition per the rubric: must state its auction thesis BEFORE
   any backtest. High effort; only worth doing if a clear visual
   pattern is identified first (e.g., off the BODY60 visual review's
   "what would actually look auction-aligned").

**Suggested:** start with (1) by simply waiting. If pressure to keep
moving exists, (2) is the safer next step — visual audit of
DISCRETIONARY trades to decide whether to invest in deeper data
collection or close it too. Do **not** open new strategy design (3)
without explicit human approval; that is high-cost work and the rubric
demands a stated thesis first.

## 9. What this document is NOT

- Not a deployment patch — no behaviour changes.
- Not a complete inventory of the recheck prompt — only XAU strategies
  are mapped.
- Not authoritative for non-XAU strategies (ETH, EUR, US500, XAG).
- Not a substitute for the catalog or the revalidation summaries —
  it is a navigation snapshot pointing at them.

---

**Snapshot date:** 2026-06-01
**Last related commits on `main`:** `1d761cb` (Reject XAU 1H DECISIVE_BODY60), `3fdb1c5` (Document BREAKOUT_CONTINUATION D1a research conclusion), `41cee27` (Document Auction Theory visual review rubric).
