# E5 OPEN SYNTHESIS — Common Entry Pattern of the 61 MON+FORTE Bottoms (XAU 15M LONG)

**Inputs read:** 55 `fund_*.md` deep readings (6 of the 61 lack a file: #4,15,17,29,50,56), all 6 `angle_*.md`, `dossier_monforte.jsonl` (61: 20 MONSTRO + 41 FORTE), `dossier_control.jsonl` (144 MED/FRACO).
**Method:** deterministic aggregation of the as-of features in the JSONL (`features_E1`, `htf1/4_native`, `reaction_seq`, `entry_mechanics`) — script `e5_synthesis_analysis.py`. **CALIBRATION on the curated 61/144, NOT validation** (per canon: no OOS/cross-asset; validate later with per-year + leave-block + null-of-max INSIDE the 8 blocks).
**Honesty note up front:** the per-fund prose names many lenses as "present/absent" so text-grep counts are inflated by the template; the JSONL numbers below are the trustworthy measure.

---

## 1. COMMON PATTERN — what is shared (quantified X/61)

The single robust shared mechanic is **NOT a trajectory shape and NOT one trigger — it is a multi-factor CONVERGENCE of "quiet-absorption + cross-TF spring" sub-states**. Every angle independently arrived at the same thesis: **MON+FORTE bottoms are quiet, controlled, off-peak absorption lows where the 1H has already turned — NOT violent capitulation flushes.** The control set is the one full of dramatic capitulation.

### The shared as-of fingerprint (MON median vs CON median):
| factor | MON | CON | direction |
|---|---|---|---|
| `htf1_native.trend` (1H already turned) | **+1** | **−1** | cleanest cross-TF separator |
| `killzone` (off London/NY KZ) | **0** (80%) | 1 (44% off) | quiet timing |
| `sell_bub_w` (sell-bubble effort) | **1** | **8** | supply already thin |
| `atr_regime` (vol regime) | **0.94** | **1.29** | calm, not panic |
| `downleg_eff` (descent efficiency) | **0.25** | 0.39 | grindy, two-sided, not a clean crash |
| `h1_pos` (1H lifted off its floor) | **0.19** | 0.01 | 1H spring loaded |
| `sweep_depth_atr` | **1.26** | 2.02 | shallow grab, not deep flush |
| `dealing_range_pos` (no range break) | **−0.55** | −0.92 | discount pullback, not breakdown |
| `rsi_min8` (not deeply oversold) | **35** | 29 | momentum absorbed |
| `reclaim_ema_bars` | **3** | 5 | reclaims faster |
| `mfe12_atr` | **5.19** | 3.79 | (outcome, not entry) |

### Convergence is the actual common pattern (graded, 7 orthogonal core predicates):
Core = {calm `atr_regime<1.0`, `htf1_trend==+1`, `quiet_sell sell_bub_w≤2`, `grind_leg downleg_eff<0.30`, `h1_pos≥0.10`, `off_killzone`, `no_range_break drp>−1`}.

| convergence | MON recall | CON rate | lift |
|---|---|---|---|
| ≥2 / 7 | 57/61 = 93% | 67% | 1.40 |
| ≥3 / 7 | 48/61 = 79% | 44% | 1.80 |
| **≥4 / 7** | **39/61 = 64%** | **25%** | **2.56** |
| ≥5 / 7 | 27/61 = 44% | 14% | 3.19 |
| ≥6 / 7 | 19/61 = 31% | 3% | 11.2 |
| 7 / 7 | 11/61 = 18% | 1% | 26.0 |

**So the common pattern is: ≥4-of-7 quiet-absorption/cross-TF-spring sub-states co-fire (64% of the 61, lift 2.56×), and it sharpens monotonically as more converge.** This is well-distributed: ≥4/7 fires in all 8 blocks (7,7,7,7,2,4,3,2) and captures **17/20 MONSTRO (85%)** + 22/41 FORTE — the biggest legs are the most convergent.

### What is NOT shared / does NOT separate (important negatives):
- **Reclaim trajectory shape** (`monotone_run≥3` 39% vs 38% ctrl, lift 1.05; front-loaded jerk lift 0.89) — the bar-by-bar staircase that fund_0 made vivid is NOT a separator across the 61. It describes individual monsters but is just as common in control.
- `swept_prior_low` (92% vs 96%) — universal, no edge.
- `nas_long_after` (23% vs 49%) — actually INVERTED (more common in control).
- `h1_rsi_strong≥52` (67% vs 60%, lift 1.11) — weak.
- `buy_bub_w`, `nas_long_16`, `sell_decel` medians = 0 in both — rare/no edge alone.

---

## 2. ESSENTIAL DIFFERENCES — sub-families of MON+FORTE bottoms

The 61 are NOT one homogeneous setup. Three sub-families, with overlap:

**A. PULLBACK-INTO-FRESH-DEMAND inside an established HTF uptrend** (e.g. fund_0 / 2025-08-27 MONSTRO). HTF *already* bullish on BOTH frames, 15M flushes into virgin nested 4H demand with clean sky. NOT a regime reversal — a trend-continuation buy of a discount. Can be IN-killzone and deeply oversold (fund_0 is London, `rsi_min8` 21.9) — these defy the off-killzone/quiet priors and are caught by the demand-stack + cross-TF-bull factors instead.

**B. REGIME-ONSET phase-lag turn** (the canonical angle-5 monster). 1H just turned +1 while 4H still −1 (still room overhead), formed off-killzone in a compressed-vol regime, grindy inefficient descent. This is the median MON profile (`h4.trend` −1, `h1.trend` +1, calm, off-KZ).

**C. QUIET ENGINEERED-LIQUIDITY raid** (angle-1/3). Off-killzone Asia/late-hours, shallow sweep of a local pool (not the lowest-of-50), sell-bubble effort drying up, instant quiet reclaim. The "precision stop-run, not headline capitulation" family.

**What varies and matters for detection:** killzone/session (family A can be in-KZ + oversold; B/C are off-KZ + not-oversold), HTF-trend state (A = both bull; B = 1H-leads-4H), and oversold depth. **No single factor catches all three — which is exactly why a convergence vote (any-N-of-many), not a hard AND of any one signature, is required.** A hard AND of any one family's signature collapses recall to ~3% (angle-1 already observed this).

---

## 3. SPECIFICITY CHECK (honest)

- **Trajectory-shape lenses are GENERIC** — monotone staircase / front-loaded jerk fire equally in control (lift ~1.0). Do not gate on them. This is a clean refutation of the "no-look-back staircase = monster fingerprint" hypothesis at the population level.
- **Single best factors are real but moderate:** `atr_regime<1.0` (2.91×), `h1_pos≥0.10` (2.23×), `grind_leg` (1.98×), `fast_reclaim≤3` (1.97×), `quiet_sell≤2` (1.77×), `off_killzone` (1.81×). None is a standalone gate — each fires on 14–46% of control.
- **Convergence is where specificity lives:** ≥4/7 = 2.56×, ≥6/7 = 11×, 7/7 = 26×. The lift rises monotonically with agreement, and ≥6/7 fires on only 3% (4/144) of control — that is genuinely specific.
- **Honest cost:** specificity buys at the price of recall. ≥6/7 catches only 19/61 (31%). The "broad" common pattern (≥4/7) still admits 25% of control (36/144 false positives), spread across all years. So **the common pattern is real but not sharp until you demand high convergence**; at ≥4/7 it is a 2.5× enrichment, not a clean separator.
- The convergence ≥4 subset is NOT concentrated in one block/year (fires 2–7× in every one of the 8 blocks; control FPs also spread 2024/25/26) — so it is not a single-period beta artifact. **Still calibration; requires leave-block + null-of-max before any edge claim.**

---

## 4. CANDIDATE CAUSAL DETECTION RULES (for deterministic R/specificity testing)

All as-of entry (close of the reclaim/entry bar), SHIFT1 on repainting layers (bubbles/NAS/SMC/OB), computable from the 15M series + native HTF resample. Predicate definitions are in `e5_synthesis_analysis.py`.

| # | conditions (as-of) | rationale | exp. recall of 61 | exp. specificity (vs 144 ctrl) |
|---|---|---|---|---|
| **R-CONV4** (primary) | **≥4 of 7**: `atr_regime<1.0` · `htf1_native.trend==+1` · `sell_bub_w≤2` · `downleg_eff<0.30` · `h1_pos≥0.10` · `killzone==0` · `dealing_range_pos>−1` | the shared multi-factor convergence; orthogonal regime/cross-TF/liquidity/structure votes | **64% (39/61)** | 2.56× (ctrl 25%) — broad detector |
| **R-CONV6** (high-precision) | **≥6 of 7** same core | demand strong agreement; for high-conviction-only entries | 31% (19/61) | **11.2× (ctrl 3%)** |
| **R1 REGIME-ONSET** | `atr_regime<1.0` AND `htf1_native.trend==+1` AND `h1_pos≥0.10` | family B: calm regime + 1H already turned + 1H lifted off floor | 25% (15/61) | **5.90× (ctrl 4%)** |
| **R3 ABSORPTION** | `downleg_eff<0.30` AND `atr_regime<1.0` AND `sell_bub_w≤2` | family C: grindy two-sided descent + calm + supply dried up | 25% (15/61) | **7.08× (ctrl 3%)** |
| **R5 DISCOUNT-NOBREAK** | `dealing_range_pos>−1` AND `killzone==0` AND `rsi_min8≥30` | quiet off-KZ discount pullback that did NOT break the range and is not deeply oversold | 41% (25/61) | 3.47× (ctrl 12%) |
| **R7 2-of-3 SOFT** | 2 of {`atr_regime<1.0`, `killzone==0`, `downleg_eff<0.30`} | soft-vote balance: best single-rule recall while keeping ~2.6× lift | **64% (39/61)** | 2.63× (ctrl 24%) |

**Recommended test order:** R-CONV4 / R-CONV6 (the headline convergence detector at two operating points) first — they are the synthesis's core claim. Then R1 and R3 as the two cleanest narrow sub-family detectors (5.9× / 7.1×, ideal as high-precision confluence boosters). R5/R7 as broader-recall variants. **Do NOT include trajectory-shape lenses (monotone_run, front_loaded) — they are refuted as non-specific (lift ~1.0).** For each rule, run per-year + leave-block (8 blocks) + null-of-max + concentration check, and measure realized R on the entries it admits (using the reaction_seq / let-run exit), not just the binary recall/specificity here.

**Family-A probe result (tested):** R-DEMANDSTACK = `htf4_native.in_demand==1` AND `htf1_native.trend==+1` AND `htf4_native.clean_sky_atr<0.5` scores only MON 15/61=25% / CON 16% (**lift 1.54×, weak**), and of R-CONV4's 22 misses it recovers only **3**. The UNION (CONV4 OR DEMANDSTACK) raises recall to 69% but DILUTES specificity to 1.94× (ctrl 35%). **Conclusion: family A is NOT cleanly separable with the available native-HTF demand fields — it is the irreducible residual.** Do not add R-DEMANDSTACK as a gate; keep R-CONV4/CONV6 as the spine. The ~22/61 family-A/oversold-pullback misses are the honest recall ceiling of this synthesis given current features.
