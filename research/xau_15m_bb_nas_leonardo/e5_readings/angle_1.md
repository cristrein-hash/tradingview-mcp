# ANGLE 1 — Liquidity & Auction Theory NEW-ANGLE Lenses (XAU 15M MON+FORTE bottom detection)

*Discovery agent, dimension = liquidity / auction theory (sweeps, stop-runs, equal-highs/lows, dealing-range, value migration, untested liquidity). RAW-only, as-of bottom bar / SHIFT1. n=61 strong (MON+FORTE) vs 144 control (MED/FRACO). Grounding probes were quick SANITY scans for discovery, not validation — every lens is framed inside a multi-factorial trajectory combo, to be validated later with null/sub-window/leave-block on the 8 blocks.*

## Headline grounding finding (drives the whole angle)
The EXISTING FEATURE_MAP liquidity features all measure **magnitude/depth of the flush** (`sweep_depth_atr`, `drop20_atr`, `vol_climax`, `flush_v_ratio`, `lower_wick_ratio`). On the dossiers these ALL point the SAME way: strong bottoms are **shallower, less climactic, less dramatic** than control (sweep_depth S med 1.26 vs C 2.02; vol_climax S 1.23 vs C 1.33; lowest-of-50+reject S 31% vs C 59%). The "obvious capitulation flush" is a control-set / weak-bottom signature, not a strong-bottom one.

So the new angle is NOT "find a bigger sweep". It is: **strong bottoms are QUIET, PRECISION liquidity events (engineered stop-runs that reclaim quietly), not headline capitulation.** The single best raw probe found: **off-killzone AND not-lowest-of-50 → S 39.3% vs C 4.9% (lift 8.1×)**. Killzone alone is strongly INVERTED (S 16.9% vs C 54.3%, lift 0.31) — strong bottoms form OUTSIDE London/NY kill windows. Nobody mapped this polarity; FEATURE_MAP lists killzone as neutral context.

---

## Lens 1 — QUIET RECLAIM (off-killzone × non-headline low)
**Causal def (as-of):** `killzone==0` (bottom bar time outside London/NY open windows, from bar `time`) **AND** bottom-bar low is NOT the lowest of the trailing 50 bars (`low > min(low[i-50..i-1])`), i.e. it undercuts only a *local* pool, not the obvious chart low. Computed from `series` OHLC + bar timestamp; SHIFT-safe (uses only bar i and prior 50).
**Why specific to MON+FORTE:** measured S 39.3% / C 4.9% (lift 8.1×). Captures the auction principle that *engineered* reversals (smart-money accumulation) happen away from the liquidity-grab windows where the crowd flushes; control "bottoms" are the crowd's capitulation low inside the killzone that then continues. Rare on weak/none because those ARE the headline flushes.
**Combo:** Lens 1 × Lens 4 (up-vol absorption) × `rsi_bull_div` — quiet timing + absorption + momentum turn.

## Lens 2 — ENGINEERED DOUBLE-BOTTOM RAID (EQL undercut + reclaim)
**Causal def:** find an `EQL` (equal-low) smc_event with `t-50bars < e.t < t` whose price sits within 1.0 ATR above the bottom-bar low; require bottom bar `low < EQL.price < close` (undercut the resting equal-low pool, then close back above it). SHIFT1 on EQL (repaints) — only EQLs printed before bar i.
**Why specific:** S 4.9% / C 1.4% (lift 3.54×). This is the *classic* sell-side liquidity raid on an engineered double bottom — equal lows are advertised resting liquidity; sweeping them and instantly reclaiming = initiative absorption. Low recall but very clean polarity; designed to fire rare on weak (weak flushes blow through, don't reclaim within the bar).
**Combo:** Lens 2 × Lens 5 (dual-raid context) × `swept_prior_low` — the engineered-trap stack.

## Lens 3 — LIQUIDITY ASYMMETRY (support-closer-than-supply / thin overhead)
**Causal def:** from live `zones` (born_t < t ≤ last_t), nearest DEMAND-zone high below close → `dn_atr=(close−zhigh)/atr`; nearest SUPPLY-zone low above close → `up_atr=(zlow−close)/atr`. Lens = `dn_atr < up_atr` (floor is nearer than the ceiling) **AND** `n_supply_overhead < 70` (thin run-room). All as-of zone state.
**Why specific:** strong bottoms have support nearer & overhead thinner (asym up−dn med S 0.73 vs C 1.30; thin-overhead S 50.8% vs C 41.4%). Auction reading: a bottom backed by a close institutional floor with a clean path to higher value = the leg has fuel and a defended origin. Control bottoms float mid-air with overhead congestion (no defended floor, capped run-room).
**Combo:** Lens 3 × Lens 6 (dealing-range discount) × `demand_virgin` — defended-floor + discount + fresh value.

## Lens 4 — ABSORPTION EFFORT/RESULT (up-vol ≥ down-vol into the low)
**Causal def:** over the trailing 10 bars (incl. i), sum volume of up-bars (`c≥o`) vs down-bars (`c<o`); lens fires when `upvol/downvol > 1.0`. Pure RAW volume + OHLC, as-of.
**Why specific:** S 23.0% / C 11.8% (lift 1.94×). Effort/result divergence — price is at/near the low yet buyers are already transacting more volume than sellers = absorption of the down-auction before the bottom prints. Weak bottoms still show net sell-volume dominance into the low (no absorption yet → continuation).
**Combo:** Lens 4 × Lens 1 (quiet reclaim) × Lens 7 (NAS-short exhaustion).

## Lens 5 — DUAL-SIDED RAID CONTEXT (EQH then EQL within the swing)
**Causal def:** both an `EQH` and an `EQL` smc_event exist within the trailing 120 bars before i (buy-side liquidity taken on the prior high, then sell-side liquidity taken into this low). Counts as the "raid both pools" stop-hunt signature. SHIFT1 on events.
**Why specific:** S 34.4% / C 23.6% (lift 1.46×). Auction theory: a complete liquidity sweep cycle (highs raided → reversal down → lows raided → reversal up) marks a true range extreme where both crowd stops are gone, leaving a one-sided book = explosive reversal fuel. Control bottoms more often lack the prior EQH leg (incomplete cycle).
**Combo:** Lens 5 × Lens 2 (EQL reclaim) × Lens 8 (EQH magnet target).

## Lens 6 — DISCOUNT-NOT-BREAKDOWN (dealing-range lower band without range break)
**Causal def:** `dealing_range_pos` in (−1.0, −0.2) — price in the discount third of the dealing range but NOT flushed beyond it (pos ≤ −1 = range break = trend continuation, not reversal).
**Why specific:** S 50.0% / C 34.5% (lift 1.45×). The discount band is where institutions accumulate; a *break* of the range (control: more often beyond −1) is continuation, not reversal. This is the "buy the discount, fade the break" auction reading — a band, not a one-sided threshold.
**Combo:** Lens 6 × Lens 3 (asymmetry) × Lens 1 (quiet).

## Lens 7 — STOP-RUN EXHAUSTION (NAS-short staleness at the low)
**Causal def:** time (in bars) since the last NAS SHORT first-appearance before i, conditioned on ≥1 short existing in trailing 30 bars. Lens = a recent short cluster that has gone *stale* (last short ≥ ~15 bars ago) — the down-initiative fired and then stopped advertising. SHIFT1 on NAS.
**Why specific (hypothesis):** the down-auction's sell-signals dry up before a true reversal (no fresh shorts confirming = sellers exhausted) — distinct from control where shorts keep printing into the low (continuation). Probe was thin (few qualify) → keep strictly as a *confluence component*, never a gate.
**Combo:** Lens 7 × Lens 4 (absorption) × `sell_decel` (existing decel feature).

## Lens 8 — EQH MAGNET OVERHEAD (untested buy-side liquidity target)
**Causal def:** an `EQH` smc_event printed in trailing 150 bars sits above close within < 8 ATR — resting buy-side liquidity overhead acts as a draw/target that the reversal leg is incentivized to reach. SHIFT1 on EQH.
**Why specific:** S 47.5% / C 41.0% (lift 1.16×, weak alone) — included not for standalone power but because it supplies the *destination* half of the auction read (untested liquidity = where price wants to go). Pairs with Lens 5 (cycle) to define a measurable target distance for let-run, and explains why strong legs run (they have a magnet); control legs stall with no overhead draw.
**Combo:** Lens 8 × Lens 5 (dual raid) × Lens 3 (clean path / thin overhead) — the "fuel + target + path" let-run trio.

---

## What is genuinely NEW here (beyond FEATURE_MAP)
1. **Killzone POLARITY inverted** — mapped as neutral context; here it is the single strongest discriminator (off-killzone, lift 0.31 inverted → 8.1× in combo). Quiet > climactic.
2. **EQH/EQL events used as liquidity geometry** — FEATURE_MAP never uses the `EQH`/`EQL` smc_event types at all; they are raw engineered-liquidity markers (Lenses 2,5,8).
3. **Effort/result absorption from volume sign** (Lens 4) — FEATURE_MAP volume is only `vol_climax` magnitude; the directional up/down-volume split is new.
4. **Liquidity ASYMMETRY** (floor-nearer-than-ceiling, Lens 3) — distinct from the static `clean_sky`/`dist_demand`; it is the *ratio* of the two paths = defended-floor reading.
5. **Discount-as-band not break** (Lens 6) reframes dealing_range_pos as a reversal *band*, opposite to the existing magnitude reading.

## Honesty / cautions
- All lifts are calibration-grade on n=61/144 — discovery, not edge. Lens 1 (8.1×) is the candidate to carry forward; Lenses 2/4 next. The over-stacked COMBO already collapsed recall to 3% (S) — combos must be 2-of-3 soft votes, not hard AND.
- Lenses 7/8 are weak/thin standalone — keep as confluence/target components only, never gates.
- Validate with per-year + leave-block + null-of-max on the 8 blocks before any claim; no OOS/cross-asset (canon).
