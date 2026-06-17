# RAW Field Mapping — XAU 4H L2/BPT BOS-CHoCH (census v1)

**Data:** 2026-06-17 · **Fonte = RAW replay `.gz` ONLY** (extractor auditado `extract_replay_features.py` in-memory via `build_entry_anatomy.extract_raw_rows()`; **zero slim**). · NOT_VALIDATION.

| Gate/feature | Fonte | Causal? | Notas |
|---|---|---|---|
| OHLCV 4H | RAW `ohlcv` (extractor base) | sim (bar fechado) | open/high/low/close/volume |
| ATR(14) | `atr14_wilder` (extractor post_pass) | sim | Wilder; usado em buffers 0.2/0.1/0.15·ATR e R-bounds |
| Pivots Williams 5/5 | computado de high/low | **sim — SHIFT5** | só pivots `j≤i-5` no bar i |
| protected_LH | derivado dos pivots confirmados | sim | PH antes do PL recente (não max) |
| CHoCH | `close>protected_LH+0.2ATR` | sim | bar fechado i |
| BOS | `close>PH_HH+0.2ATR` | sim | contado/tag |
| retest | `low≤polaridade+0.15ATR` | sim | janela ≤24 bars pós-CHoCH |
| reclaim | `close>open ∧ body_pct≥0.5 ∧ close>polaridade+0.1ATR` | sim | entry=close do reclaim |
| swing low / structure low | PL confirmado (5/5 SHIFT5) | sim | base do SL estrutural |
| `inside_demand/supply`, `nearest_supply_dist`, `custom_ob_*` | extractor (Custom OB v11, `pine_boxes`) | sim (snapshot) | TAG |
| NAS LONG/SHORT | `nas_label_long/short_*` (first-appearance) | sim | TAG; nunca TOP/BOTTOM nem `*_SIGNAL` |
| Bubbles | `bubble_buy/sell/large_*` | sim | TAG |
| RSI / divergência | `rsi`, `rsi_ma`, `rsi_div_*` | sim | TAG (exhaustion) |
| `at_D1_demand` | exige extração 1D (BPT v2) | sim (quando feito) | **DEFERIDO no census v1** (`tag_pending`) — evita re-extração 1D pesada agora |
| outcome | simulado (stop-first, +2/3/4R, time 24) | sim | gross R, sem custos |

**Hard stops (RAW mapping):** se protected_LH não reconstruível, CHoCH/BOS/retest/reclaim usarem futuro, SL estrutural não R-viável, ou cobertura RAW 2019+ insuficiente → parar. RAW 4H 2016-2026 já confirmado no registry (cobre 2019+).
