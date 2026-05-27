# Feature Extraction Policy — Canonical Feature Extraction Layer (CFEL)

> Status: **CANONICAL** — `scripts/extract_replay_features.py` is the single official extractor (promoted 2026-05-28; rename + v1 removal done; full re-extraction + v1 cleanup pending). Last updated 2026-05-28.
> Authoritative policy for turning RAW TradingView replay dumps into operational features for strategy
> revalidation, new-strategy validation, analytical datasets and backtests. Read this before adding an
> asset, changing the extractor, or using any feature in a backtest.

Related: [`dataset_registry.json`](./dataset_registry.json) · [`DATA_STORAGE_POLICY.md`](../architecture/DATA_STORAGE_POLICY.md) · `scripts/extract_replay_features.py`

---

## 1. Layer principle

- **RAW replay (`raw_replay/.../*.jsonl.gz`) is the source-of-truth.** Never altered. Integrity via per-file manifests (gzip + SHA256 + roundtrip).
- **The Dataset Registry (`docs/data/dataset_registry.json`) is the official inventory** of RAW datasets (symbol/timeframe/window/status/integrity). The extractor consumes it.
- **Slim features are DERIVED and regenerable.** They are not source-of-truth; they can be re-extracted from RAW at any time.
- **`scripts/extract_replay_features.py` is the Canonical Feature Extraction Layer** — the single official interpreter of indicators (schema v2). After full re-extraction of all active datasets, **the canonical slims are the ONLY source of features**.
- **v1 (`extract_replay_features_v1.py` / `slim_features/`) is DEPRECATED — NOT permanent legacy.** Its slim semantics are known-wrong (the NAS/SMC/Custom-OB/Bubbles misinterpretations this layer fixes). v1 is **scheduled for deletion** after v2 promotion + full re-extraction (see §8-§9). **No future backtest may use v1.** v1 is not an operational or alternative feature source. The v1 extractor leaves the active path (removed, or archived only if a concrete audit need arises).
- **No backtest may use a feature without a defined class + confidence** (see §3). Ambiguous fields are never `official_for_backtest`.

## 2. Input / Output contract

**Input:**
- `dataset_registry.json` entry with `status: active` (symbol, timeframe, window, `raw_gz_path`).
- The RAW `.jsonl.gz` (read-only, streamed). No hardcoded asset.

**Output (per block, to `slim_features/<SYMBOL>/<TF>/`):**
- `<SYMBOL>_<tf>_features[_v2]_<start>_to_<end>.jsonl` — 1 row per bar.
- `.report.json` with: `schema_version`, `provenance` (raw_gz_path, registry_entry), `feature_quality` (parse_errors, labels_capped, sources_missing, …), **`field_classes`**, **`indicator_fidelity`/validation counts**, `warnings`.

**Row conventions:** decision bar = last **closed** bar (`ohlcv[-2]`); `ts` = `replay_current_dt`; provenance carries `raw_gz_path` + `bar_index`. Drawing coordinates (`x`, `x1/x2`) are **relative to the snapshot** — never used as absolute timestamps.

## 3. Field classes

Every feature carries one class (recorded in `report.field_classes`):

| Class | Meaning | Backtest use |
|---|---|---|
| **official_for_backtest** | Source + mapping verified; confidence HIGH | ✅ allowed |
| **low_confidence** | Source verified but mapping/semantics not fully proven (e.g. needs visual) | ⚠️ only with explicit per-strategy justification |
| **diagnostic_only** | Auxiliary/derived state, or superseded by a better field | ❌ not for signal |
| **deprecated** | Replaced by a correct field; kept for transition | ❌ |
| **do_not_use** | Not reliably extractable from current RAW | ❌ |

## 4. Per-indicator policy (source · mapping · confidence · official fields)

| Indicator | RAW source | Mapping rule | Confidence | Official fields |
|---|---|---|---|---|
| **NAS Top Bottom** | `pine_labels` "NAS TOP BOTTOM DETECTOR" | text LONG/SHORT; recent if `max_x − x ≤ 5` (legacy monitor); events via id-diff + price-match | **HIGH** (2026≈18/19 = visual) | `nas_label_long/short_recent`, `nas_label_recent_long/short_bars`, `nas_label_long/short_event`, `nas_label_event_type/price/id` |
| **Market Order Bubbles** | `pine_shapes_bubbles.activations` (absolute `time`) | BUY=plot_0/2/4, SELL=plot_6/8/10, POC=plot_12; size by plot order | direction **HIGH** · size **MEDIUM-HIGH** · POC HIGH · price **unavailable** | `bubble_buy/sell_current+recent`, `bubble_poc_current/recent`, `bubble_active`, `bubble_raw_plot_ids` (+ `bubble_size_current/rank` low-conf) |
| **RSI** | `study_values` "Relative Strength Index" (RSI, RSI-based MA) | numeric + crosses | **HIGH** | `rsi`, `rsi_ma`, `rsi_above/below_ma`, `rsi_cross_above/below_ma` |
| **RSI divergences** | `study_values` Regular Bullish/Bearish (+ `*_Label`) | `_Label` = discrete visible event; raw = aux RSI level | **HIGH** (Bull/Bear labels visually confirmed) for events | `rsi_div_bullish/bearish_event` (raw/label = diagnostic) |
| **LuxAlgo SMC** | `pine_labels` (CHoCH/BOS/EQH/EQL/Strong) + `pine_boxes` (OB) + `pine_lines` (levels) | direction via **textColor** (green=bull/blue=bear, anchored EQH=bear/EQL=bull); internal/swing via **size** (tiny=internal); event_new via id-diff; OB bull/bear via **bgColor** | **HIGH** (color/size visually confirmed) | `smc_structure_event_new/type/direction/kind/price`, `smc_last_structure_event/bars_ago`, `smc_last_swing_bos/choch_direction`, `smc_recent_eqh/eql`, `smc_strong_high/low_price`, `smc_nearest_bullish/bearish_ob_*` |
| **Custom OB** | `pine_boxes` "Custom OB Detector v11" | text DEMAND/SUPPLY; **presence = active** (Pine v11 deletes violated/aged); state via **bgColor alpha** (77 fresh / 51 touched / 25 mitigated); `x2` ignored (extend.right) | **HIGH** (Pine v11 audited) | `custom_ob_demand/supply_active`, `inside_demand/supply_zone`, `nearest_demand/supply_*`, `custom_ob_nearest_demand/supply_state`, `custom_ob_n_demand/supply_zones`, `custom_ob_nearest_zone_type` |
| **OHLCV-derived** | `ohlcv` | ATR legacy SMA; swing/body/range computed on the bar series | **HIGH** | `atr14_sma_tr`, `atr14_sma30_ratio`, `swing_high/low_10`, `body_pct`, `candle_range`, `range_atr_ratio`, `close_above/below_swing_high/low_10`, OHLCV |

## 5. Specific decisions (locked)

**NAS:** LONG/SHORT from `pine_labels`; **BOTTOM=LONG, TOP=SHORT** (not separate operational concepts — no bottom/top fields); `study_values` NAS_*_SIGNAL are **deprecated/diagnostic** (proven inadequate: ~1 fire/block vs ~18 visible labels).

**Bubbles:** `BUY=plot_0/2/4`, `SELL=plot_6/8/10`, `POC=plot_12`; size by plot order within direction (small/medium/large). Direction confidence **HIGH** (stat bull% 60-78 vs 38-19 + visual green-below/red-above). Size confidence **MEDIUM-HIGH** (3 tiers visually confirmed; exact plot→size order is inference — the chart does not expose plot_ids; definitive only via the Leviathan Pine source). **price/y = unavailable** (not captured in activations).

**RSI divergence:** `Regular Bullish/Bearish Label` = the discrete visible Bull/Bear marker = **event** (confidence **HIGH**, visually confirmed on RSI subpane). `Regular Bullish/Bearish` (continuous) = auxiliary RSI level (diagnostic).

**SMC:** **textColor defines direction** (green=bull, blue=bear; anchored by EQH=bear-color / EQL=bull-color). **size defines internal vs swing** (tiny=internal/high-frequency, small=swing/significant). `smc_structure_event_new` (id-diff) is the discriminative event. `smc_has_recent_bos/choch` **saturate (~always true) → diagnostic_only**. EQH/EQL, `smc_last_structure_event` and swing-direction are official.

**Custom OB:** **Pine v11 (`11_custom_ob_detector_v11.pine`) is the semantic source.** **Presence of a box = active zone** (v11 with `obshowbb=false` deletes violated + aged + overlapping; FIFO over 40/dir; auto-delete after 800 bars). `x2` is the creation coord (boxes use `extend.right`) → **NOT used for active status**. DEMAND=bull/green, SUPPLY=bear/orange (by `text`). **State via bgColor alpha**: 77=fresh, 51=touched, 25=mitigated. `inside_demand/supply`, `nearest_*`, `*_state`, counts are official. `demand/supply_zone_active` (x2-based) is **deprecated**.

**OHLCV-derived:** **ATR legacy** = `TR=max(h−l, |h−prev_close|, |l−prev_close|)`; `ATR14=SMA(TR,14)`; `ATR_MA30=SMA(ATR14,30)`; `ATR_RATIO=ATR14/ATR_MA30` (matches `monitor_xau_4h_strategies.py`). `atr14_wilder` = comparison/diagnostic. swing(10 prior)/body_pct/range/range_atr_ratio are official.

## 6. Mandatory validations (extraction gate)

A block PASSES only if all hold (recorded in `.report.json`):
- `rows == registry bars`;
- `parse_errors == 0`;
- spot-check vs RAW (independent re-read);
- **no lookahead** (features from the snapshot only; `x` relative; bubbles matched by absolute time; entry/decision on closed bars);
- duplicate timestamps **marked** (replay-stall, kept 1:1);
- feature coverage (null-rate per field);
- `.report.json` generated;
- indicator-specific checks (e.g. NAS LONG 2026 ≈ 17-19; `nas_signal_study_long` stays rare; Custom OB demand≠supply both=0; SMC swing rare vs internal; RSI div labels present);
- **visual validation** required before promoting new/sensitive fields (bubbles size, RSI div labels, SMC colors — done 2026-05-27).

## 7. New-asset policy

- **Never hardcode XAU.** Symbol/timeframe/window come from the registry.
- **Declare an indicator baseline per asset** (e.g. XAU = NAS + SMC + Custom OB + Bubbles + RSI).
- **If an expected indicator group is absent** in the asset's RAW, record it in `feature_quality.sources_missing`/`indicators_missing` and emit the affected fields as `null` — **never invent values**.
- **Divergent layout** (different indicators/settings) → flagged in the report, not a silent failure.

## 8. Promotion process (gate to canonical)

1. **Technical patch** (per-indicator mapping in the extractor).
2. **Minimal validation** (one block, all §6 gates).
3. **Visual validation** (sensitive new fields vs chart).
4. **Documentation** (this file).
5. **Canonical promotion** — rename `extract_replay_features_v2.py` → `extract_replay_features.py`; output to `slim_features/` (canonical). The **v1 extractor leaves the active path** (removed, or archived only if a concrete audit need arises — NOT a permanent operational option). v1 slims are flagged **DELETE_CANDIDATE** (NOT moved to a permanent legacy folder).
6. **Full re-extraction** of all active datasets to the canonical folder.
7. **Cleanup (deletion)** of v1 + superseded derivatives (see §9) — only after step 6 validates.
8. **Only then**: backtests on the canonical slims.

> Current state: steps 1-5 done (validated + documented + **canonical promotion**: `extract_replay_features.py`, v1 removed). Steps 6-8 (full re-extraction → cleanup → backtests) pending explicit authorization.

## 9. Mandatory cleanup after v2 promotion (deferred, gated)

v1 is DEPRECATED (§1) — **not kept as permanent legacy.** After canonical promotion + full re-extraction + validation (steps 5-6), the following derived/regenerable artifacts are **DELETE targets**. Each deletion uses the standard gate (gitignored/untracked or repo-tracked derivative · no live consumer · regenerable from RAW via v2 · NOT source-of-truth/manifest/registry):
- **v1 slims** (`slim_features/` v1 output) — DELETE;
- **v1 cross-TF** datasets (built on v1 slims) — DELETE + regenerate with v2;
- **v1 reports** + any v1 outputs — DELETE;
- **backtest v1 outputs** (`research/backtests/xau_4h_capitulation_v1/`) — superseded/diagnostic, DELETE if not useful;
- **v2 staging** (`slim_features_v2/`) once the canonical `slim_features/` exists — DELETE;
- intermediate `.report.json` of superseded runs — DELETE;
- local WIP commits (backtest v1 engine, intermediate extractor commits) — squash/resolve.

RAW `.gz` + manifests + registry are **NEVER** cleanup candidates.

---

## Open / non-blocking items
- **Bubble exact plot→size label** (small/medium/large per plot): MEDIUM-HIGH inference; chart never labels plot_ids → definitive only via Leviathan Pine source (third-party/protected). Direction + 3-tier existence are HIGH.
- **Bubble price/y**: not in RAW activations → `do_not_use` unless collection is changed to capture shape y.
