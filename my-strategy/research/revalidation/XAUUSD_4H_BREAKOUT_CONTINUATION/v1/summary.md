# XAUUSD 4H BREAKOUT_CONTINUATION v1 — Revalidation Summary

- Generated: 2026-05-29T00:10:54.936206+00:00
- git: 5c34af217284
- Data: canonical 4H slim · 15187 bars · 2016-05-24 → 2026-05-22
- Method: replay_real_rt_canonical_slim
- Config: S_full_trend_htf
- Primary target: 4R · max_hold: 24 bars

## Aggregate

| Metric | Value |
|---|---:|
| signals | 261 |
| trades | 115 |
| win_rate | 0.3043 |
| avg_R | +0.2198 |
| total_R | +25.2778 |
| PF | 1.479 |
| BE moves | 57 |
| right-censored | 29 |

## Exit reasons

- `stop_be`: 25
- `stop`: 52
- `time_limit`: 29
- `target`: 9

## By regime

| regime | n | win_rate | avg_R | total_R |
|---|---:|---:|---:|---:|
| pre_covid | 22 | 0.3182 | +0.0951 | +2.0931 |
| bull_pre_covid | 14 | 0.3571 | +0.5329 | +7.4608 |
| covid_rally | 10 | 0.2000 | +0.3634 | +3.6343 |
| chop_post_covid | 8 | 0.1250 | -0.1250 | -1.0000 |
| chop_inflation_bear | 11 | 0.1818 | -0.4684 | -5.1522 |
| chop_macro | 10 | 0.3000 | +0.1822 | +1.8222 |
| bull_recent | 40 | 0.3750 | +0.4105 | +16.4196 |

## Legacy aggregate comparison (informational)

- legacy: n=234, pf=1.64, win=0.286, total_net_r=64.57
- canonical v1: n=115, pf=1.479, win=0.3043, total_R=+25.2778
- _note_: Aggregate-vs-aggregate informational comparison only — legacy lacks trade-level dump.

## Current research conclusion — D1a

Concluded: 2026-06-01. Read-only research over the 115-trade `trades.jsonl`. No
operational change, no Pine/monitor/catalog edit, no promotion.

### Baseline (recap)

| Metric | Value |
|---|---:|
| n | 115 |
| win_rate | 0.304 |
| avg_R | +0.220 |
| total_R | +25.28 |
| PF | 1.479 |
| targets | 9 / 115 |

### D1a — macro 1D regime filter

**Definition:** keep long only if, at signal_iso, the most recent completed 1D
bar (no lookahead) satisfies `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D`.
EMAs computed from 1D close series (slim does not pre-publish them).

**Result vs baseline:**

| Metric | Baseline | D1a | Δ |
|---|---:|---:|---:|
| n | 115 | 90 | −25 |
| win_rate | 0.304 | 0.333 | +0.029 |
| avg_R | +0.220 | +0.358 | +0.138 |
| total_R | +25.28 | +32.20 | **+6.93** |
| PF | 1.479 | 1.862 | +0.383 |
| targets kept | 9 | 8 | −1 |

D1a removes 25 trades worth −6.93 R net. Only 1 target removed, ~8.48 R lost
inside removed winners — net of all losses, still strongly positive.

### Walk-forward stability

Windows split by `entry_iso`. D1a vs baseline per window:

| Window | n base / D1a | totR base | totR D1a | ΔtotR |
|---|---|---:|---:|---:|
| W1 2016-2020 | 36 / 23 | +9.55 | +13.15 | **+3.60** |
| W2 2020-2023 | 29 / 18 | −2.52 | +0.81 | **+3.33** (PF crosses 1.0) |
| W3 2023-2026 | 50 / 49 | +18.24 | +18.24 | 0 (no-op) |

W1+W2 carry the full +6.93 R gain (≈50/50). W3 untouched — D1a does not
degrade the most recent / strongest window. Improvement is distributed, not
concentrated in one regime or one window.

### Visual review of 25 D1a-rejected trades

Operator manually reviewed the 25 trades D1a rejects (`PEPPERSTONE:XAUUSD`
4H). Conclusion: ~20/25 are visually correct rejections (top/exhaustion/
inadequate context). ~5 are "false positives" with positive R (#3 +0.76,
#8 +2.08, #10 +0.96, #20 +4.00, #21 +0.67 — total +8.48 R left on the table).

Decision: do NOT add an exception rule. Only trade #10 (close_1D > EMA200_1D
but EMA50_1D still below) is a replicable candidate; the others are
event-driven (Fed pivot Nov-2021, CPI surprise Nov-2022) or non-replicable
slow drifts. The exception's `acceptance ≥ 2/3` requirement would introduce
a 12h delay that erases the +0.96 R it could recover.

### H1c OR H2b — local 4H filter

- `H1c` = ≥3 NAS SHORT/TOP labels in last 15 bars 4H
- `H2b` = RSI bear divergence event in last 10 bars 4H

Walk-forward of D1a vs H1c OR H2b vs combo:

| Filter | n | total_R | PF | targets |
|---|---:|---:|---:|---:|
| BASELINE | 115 | +25.28 | 1.479 | 9 |
| D1a only | 90 | **+32.20** | 1.862 | 8 |
| H1c OR H2b only | 87 | +24.27 | 1.649 | 8 |
| D1a + H1c OR H2b | 68 | +30.19 | 2.118 | 8 |

Adding H1c OR H2b on top of D1a costs **−2.01 R** total (W1 −0.86, W2 +1.19,
W3 −2.34) in exchange for +0.256 PF — cosmetic PF gain at real R cost. H1c OR
H2b alone catastrophically degrades W2 (PF 0.667, totR −4.33), proving it is
not robust as a standalone filter.

**Conclusion:** H1/H2 stays as **visual diagnostic only** (see
`docs/research/AUCTION_THEORY_VISUAL_REVIEW_RUBRIC.md`), not as a mechanical
filter. D1a sozinho wins on total_R, stability, target preservation,
and simplicity. PF (where combo wins) is the lowest-priority criterion.

### Bubbles (H5) — current state

Slim 4H exposes `bubble_buy_current`, `bubble_sell_current`, `bubble_large_
current`, `bubble_size_rank`, `bubble_buy_recent`, `bubble_sell_recent`,
`bubble_activations_window` — sufficient coverage for naive proxies.

Three proxies tested (H5a large_buy at signal; H5b buy_recent + activations≥3;
H5c = H5a OR H5b). H5b/H5c trigger on 47-48% of trades and remove **4
targets** worth ~+16 R. Combo `D1a + H1c OR H2b + H5c` drops total_R from
+24.27 to +18.06, while PF rises to 1.903 (again cosmetic). Visual signal
"BUY climax cluster at top of extension" is real, but cannot be mechanized
without structural location — `bubble_event_price`, `bubble_poc_current`,
`bubble_poc_recent` are **all zeroed by the extractor**.

Structural proxy B5_loc1 (`bubble_buy_recent + close ≥ HH(20) − 1×ATR`) does
work standalone (totR +32.39, PF 2.088) but has Jaccard 20% with D1a and adds
−0.92 R when combined with D1a (incremental removes net winners). **Not
worth the complexity.**

**Conclusion:** H5 not pursued as mechanical filter at this time. Reopen only
if extractor populates `bubble_event_price` (currently zeroed) and walk-
forward D1a starts failing in an OOS regime.

### chop_inflation_bear — residual cost

This is the only regime still negative after D1a (n=7 kept, totR −2.82, win
0.143). Diagnostic of all 11 trades:

- 0 targets hit across 11 trades — best outcome was time_limit positive.
- The 7 D1a-KEEP trades are concentrated in Feb-Apr 2022 (Russia/Ukraine +
  inflation parabolic from $1800 to $2070).
- Average `(close_1D − EMA200_1D) / ATR_1D = +3.18` — entries occur with the
  1D close ~3.2 daily-ATR units above EMA200, i.e. **blow-off territory**.
- Average distance from entry to swing_high_10 = +9.5 ATR_4H — chasing late
  breakouts of an already extended trend.
- 4 of 7 have BUY bubbles (climax markers); 0 SELL bubbles.
- Stop = 0.5×ATR_4H is structurally too small for the post-entry volatility
  expansion (ATR_4H 8-10).

**Hypothesis (archived, NOT promoted):**
`D1a_ext = D1a AND (close_1D − EMA200_1D) / ATR_1D < 2.5`

Would mitigate chop_inflation_bear from −2.82 to ~−1.82 R but **risks
degrading bull_recent** (40 trades, +16.42 R), where XAUUSD also runs
extended for long stretches (2024-2025 rally to $4500+ also has high
EMA200_1D stretch). Walk-forward by window required before any adoption.

**Decision:** accept chop_inflation_bear as residual cost.
- Cost: ~0.29 R/year over 9.8-year sample, regime is rare (once per decade).
- D1a globally still nets +32.20 R / PF 1.862.
- Solving CIB mechanically risks bleeding the regime that actually drives
  the strategy's edge (bull_recent).

### Current decision

- **D1a is the research-stage candidate filter for BREAKOUT_CONTINUATION
  v1.** Macro 1D direction-only, no extension component, no local 4H filter,
  no Bubbles.
- **No operational promotion yet.** No Pine, monitor, catalog, or
  strategy_rules change is sanctioned by this conclusion.
- Next preconditions before any promotion:
  1. Real OOS data (post-2026-06) covering at least one new directional
     regime change.
  2. If D1a OOS holds, re-evaluate whether `D1a_ext` (extension cap) helps
     without hurting bull_recent.
- H1/H2 remain available as **visual diagnostic** via the rubric.
- Bubbles remain blocked on extractor populating `bubble_event_price` and
  `bubble_poc_*`.
