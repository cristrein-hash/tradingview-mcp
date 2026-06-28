# Angle 5 — Cross-TF Momentum & Regime-Onset Lenses (XAU 15M MON+FORTE bottom detection)

Dimension: **cross-timeframe momentum & regime-onset** — 4H/1D trend alignment, regime-turn detection,
HTF RSI turning, multi-TF demand confluence, NAS/SMC cross-TF. RAW-only, as-of bottom bar / SHIFT1.
Goal: NEW angles BEYOND the FEATURE_MAP (A–G) that flag, at entry time, that a fractal low is a
MONSTER/FORTE bottom (big clean reversal leg). Specificity (rare on weak/none) is the gate, not presence.

## Grounding (calibration on curated study/control, NOT validation)
Strong-vs-control medians on the 61 MON+FORTE vs 144 MED/FRACO dossiers exposed a real cross-TF gap
that the current map only touches as "HTF = contexto, não gate":
- `htf1_native.trend` (as-of bottom, native 1H resample): **MON med = +1 vs CON med = −1** — the single
  cleanest cross-TF separator seen. The 1H frame is ALREADY turning bullish at the strong bottom while
  the 1H is still bearish at weak ones.
- `htf1_native.in_demand`: MON = 0 vs CON = 1 (strong bottoms are 1H ABOVE demand → room overhead, not
  pinned inside it).
- `htf1_native.dist_demand_atr`: MON 1.05 vs CON 0.64 ; `features_E1.h1_pos`: MON 0.19 vs CON 0.01.
- `features_E1.atr_regime`: MON **0.94** vs CON 1.28 — strong bottoms form in a COMPRESSED-vol HTF regime,
  weak ones in expanded/panic vol.
- `htf4_native.trend` med = −1 for both (4H still bearish) → the turn is a 1H-leads-4H **phase lag**, not
  4H confirmation. This is the novel structural insight the lenses below exploit.

Note: all HTF here is NATIVE resample of the 15M series (no separate 4H/1D RAW). Every lens is computable
as-of the bottom bar from the 15M series + native HTF resample, SHIFT1 on repainting NAS/SMC/OB.

---

## NOVEL LENSES (6–10)

### L5.1 — HTF Phase-Lag Turn (1H-leads-4H regime onset)
**Definition (as-of):** Compute native 1H trend state (sign of 1H EMA21 slope over last 2 closed 1H bars)
and native 4H trend state. Fire when **1H_trend just flipped to +1 within last K≤2 closed 1H bars WHILE
4H_trend is still −1 (or flat)**. "Just flipped" = sign change vs the prior closed 1H bar (trajectory, not
snapshot). Optionally require 1H EMA21 slope crossing from negative to ≥0.
**Why MON+FORTE-specific:** strong bottoms showed `h1nat.trend=+1` while `h4nat.trend=−1` — the fast frame
turns first; weak bottoms are still 1H-bearish (−1). A still-falling 4H means the leg has ROOM (no overhead
4H supply mitigated yet), and a 1H that already turned means initiative arrived. The *disagreement* (fast up,
slow down) is rare in chop — chop has both frames flat/aligned-down. This captures regime ONSET, not regime.
**Combo:** {L5.1 phase-lag} × {h1_above_demand (L5.2)} × {compressed atr_regime (L5.6)}.

### L5.2 — 1H Room-Above (above-demand, supply-thin) at the 15M flush
**Definition (as-of):** At the bottom bar, `htf1_native.in_demand == 0` (1H price NOT pinned inside its
demand) AND `htf1_native.dist_demand_atr ≥ ~0.8` (1H sits a clear ATR above its demand) AND `h1_pos` (1H
position in its recent range) > ~0.1. Meanwhile the 15M itself is flushed INTO 4H demand (`htf4_native.in_demand==1`).
So: 15M is at the floor, but the 1H structure has already lifted off its own floor.
**Why specific:** MON in_demand=0 / dist 1.05 / h1_pos 0.19 vs CON in_demand=1 / dist 0.64 / h1_pos 0.01.
Weak bottoms are 1H STILL inside/at demand (price grinding the floor on both frames = absorption/continuation
down). Strong bottoms are a 15M-deep-flush against a 1H that has already reclaimed — a multi-TF spring, not a
trend-down. This is a *cross-TF position divergence* nobody mapped (the map's `in_demand` is single-TF).
**Combo:** {L5.2 1H room} × {15M-in-4H-demand} × {L5.1 phase-lag turn}.

### L5.3 — HTF RSI Hook (1H RSI turning up from a non-oversold base while 15M RSI is washed)
**Definition (as-of):** 15M RSI deeply washed (`rsi_min8 ≤ ~25`, present in MON med 21.9) AND
`htf1_native.rsi` is turning UP — i.e. 1H RSI now > 1H RSI of the prior closed 1H bar (positive 1H RSI delta)
AND 1H RSI ≥ ~52 (MON h1nat.rsi med 57.7 vs CON 54.6; the 1H is NOT oversold). The divergence: 15M momentum
capitulated but 1H momentum never broke and is hooking up.
**Why specific:** a washed 15M RSI is common to ALL fractal lows (no edge alone). What's RARE is a 1H RSI that
stayed strong (≥52) and is hooking up at the same instant — that is the 1H refusing to confirm the 15M panic.
Weak bottoms have both frames' RSI sagging together. This is a cross-TF RSI-divergence trajectory feature, not
the single-frame `rsi_bull_div`/`rsi_head` already in the map.
**Combo:** {L5.3 HTF-RSI hook} × {15M rsi_bull_div} × {L5.1 phase-lag}.

### L5.4 — Compressed-Regime Onset (low HTF vol BEFORE the flush)
**Definition (as-of):** `atr_regime` (current ATR vs longer-window baseline) < ~1.0 AND `atr_compression_pre`
elevated (≥ ~0.85). I.e. the bottom forms in a quiet, coiled HTF vol regime — the flush is a sharp local spike
inside an otherwise compressed market, not a leg of a high-vol downtrend.
**Why specific:** MON atr_regime 0.94 vs CON 1.28 — a 27% vol-regime gap. Weak/none bottoms cluster in
expanded-vol (panic/trend-down) regimes where ATR is high and every flush looks the same and reversals fail.
A compressed regime + a single sharp flush = a stop-run inside accumulation → the setup for a clean reversal
leg. This reframes ATR as a *regime gate*, not the per-bar `range_exp`/`vol_climax` in the map.
**Combo:** {L5.4 compressed regime} × {L5.5 flush-spike isolation} × {L5.1 phase-lag}.

### L5.5 — Cross-TF Flush-Spike Isolation (15M panic NOT echoed on 1H body)
**Definition (as-of):** The terminal down-move is a 15M-only spike: 15M `drop20_atr` large (MON ~4.5) and
`flush_v_ratio` low (sharp V, MON 0.22) BUT the corresponding closed 1H bar's body is small relative to its
ATR (1H did NOT print a large bearish marubozu) — i.e. the panic lives in the 15M wick, the 1H absorbed it
into a single small/lower-wick bar. Compute: 1H_body_atr = |1H close − 1H open|/1H_atr at the flush; fire when
1H_body_atr < ~0.8 while 15M drop20_atr > 3.
**Why specific:** strong bottoms are stop-runs the 1H *swallows* (the 1H bar closes back near its open with a
lower wick — absorption visible on the slower frame). Weak/continuation flushes print a real 1H bearish body
(the move is "real" on both frames → it keeps going). The 15M-spike-without-1H-body is a fingerprint of
liquidity-grab-then-reversal that no single-TF velocity feature (`arrival_velocity_atr`, `flush_v_ratio`) sees.
**Combo:** {L5.5 1H-absorbs-spike} × {15M flush_v_ratio low} × {sweep_depth (sweep+reclaim)}.

### L5.6 — Multi-TF Demand Stack (15M flush lands ON aligned 4H demand, supply-clear above)
**Definition (as-of):** 15M is inside a Custom-OB DEMAND zone AND `htf4_native.in_demand==1` (the 15M demand
sits within / coincident with a 4H demand) AND overhead supply is thin on BOTH frames:
`htf4_native.clean_sky_atr` and 15M `n_supply_overhead` low / `dist_supply_atr` large. So price flushes into a
*stacked* multi-TF demand with a clear runway up.
**Why specific:** the map has single-TF `in_demand`, `dist_demand_atr`, `clean_sky`. The NOVEL angle is the
*coincidence* of 15M-demand inside 4H-demand (a nested value floor) PLUS clear sky above on the HTF — a leg
needs both a floor to bounce from and air to run into. Weak bottoms bounce off a 15M demand that has 4H supply
just overhead (capped → small bounce → fail). Stacked-demand + clean-HTF-sky is rare and is the structural
precondition for a MONSTER leg.
**Combo:** {L5.6 nested 4H+15M demand} × {h4 clean_sky} × {15M penetration_pct low (rejection)}.

### L5.7 — Cross-TF NAS Hand-off (1H/4H NAS-LONG context arming the 15M NAS trigger)
**Definition (as-of, SHIFT1):** Beyond the 15M `nas_long_16` cluster, check native-HTF NAS context:
`htf1_native.nas_long_rec` or `htf4_native.nas_long_rec` flips to 1 within the last few closed HTF bars (a
recent HTF NAS-LONG print), so the 15M NAS-LONG that fires at the bottom is *confirmed by an HTF NAS in the
same direction*. Fire when 15M NAS-LONG present AND (h1 or h4 nas_long_rec recently set).
**Why specific:** 15M NAS clusters fire at many lows (per map: cluster ↑prob but NOT magnitude). The
magnitude/cleanliness comes when the SLOWER frame's NAS agrees — a multi-TF NAS hand-off means the same
institutional signal is printing across resolutions, which is rare and aligns with the biggest legs.
NOTE: grounding showed h1/h4 nas_long_rec med=0 for both groups → this is a RARE-event lens (low base rate);
it must be tested as a *booster within a combo*, not standalone (low recall expected, but high precision when on).
**Combo:** {L5.7 HTF NAS hand-off} × {15M nas_long_16 cluster} × {L5.1 phase-lag}.

### L5.8 — Slope-Curvature Onset (1H EMA21 slope inflecting up — 2nd-derivative turn)
**Definition (as-of):** Track native 1H EMA21 slope over the last 3 closed 1H bars; fire when the slope is
still negative but its **rate of change turned positive** (slope_t > slope_{t−1} > slope_{t−2}, i.e. the 1H
downtrend is DECELERATING / curling) AND 15M ema21 reclaimed within ≤2 bars (`entry_mechanics.reclaim_ema_bars`
small). This is the curvature (2nd derivative) of HTF momentum, capturing the *inflection* before the trend
sign even flips — earlier and finer than L5.1's sign-flip.
**Why specific:** MON `h1_slope_atr` −0.77 vs CON −0.95 — strong bottoms have a 1H slope that is already LESS
negative (decelerating) than weak ones, even when both are technically still down. The curvature turn is the
true regime-onset moment. Weak bottoms have a 1H slope still accelerating down (no inflection). A 2nd-derivative
feature is genuinely unmapped (the map only has slope level `h1_slope_atr`).
**Combo:** {L5.8 1H slope curl-up} × {15M reclaim ≤2 bars} × {L5.4 compressed regime}.

### L5.9 — Cross-TF Structure Hand-off (15M CHoCH-up confirmed against an un-broken 1H higher-low)
**Definition (as-of, SHIFT1):** A 15M bullish CHoCH prints just after the low (`entry_mechanics.choch_15m_after==1`)
AND the most recent native-1H swing low is a HIGHER-LOW vs the prior 1H swing low (1H made HL — structural
support intact on the slow frame). So 15M structure flips up INTO an intact 1H HL structure.
**Why specific:** a 15M CHoCH alone fires constantly (map: choch base-rate high, weak signal). The discriminator
is whether the 1H structure underneath is an HL (constructive) vs an LL (still distributing). Strong bottoms =
15M turn nested in a 1H HL; weak bottoms = 15M wiggle inside a 1H LL sequence (the slow frame still breaking
down → the 15M CHoCH gets overrun). Cross-TF structure-nesting is a new lens vs single-TF `op_flow`/`recent_choch_dir`.
**Combo:** {L5.9 15M CHoCH in 1H-HL} × {L5.2 1H room-above} × {L5.6 nested demand}.

---

## Priority combos (convergence, for Fase 1/2 specificity test)
1. **REGIME-ONSET TRIAD** = L5.1 (1H-leads-4H turn) × L5.2 (1H room-above) × L5.4 (compressed regime).
   This is the highest-conviction, best-grounded cross-TF convergence (every leg showed a clean MON/CON gap).
2. **ABSORPTION-ONSET** = L5.5 (1H swallows the 15M spike) × L5.8 (1H slope curl-up) × L5.3 (HTF RSI hook).
   Captures the stop-run-then-reversal fingerprint across frames.
3. **STACKED-FLOOR LAUNCH** = L5.6 (nested 4H+15M demand, clean HTF sky) × L5.9 (15M CHoCH in 1H-HL) × L5.7 (HTF NAS hand-off).
   The structural launchpad: floor below + air above + multi-TF agreement.

## Honesty / caveats
- Grounding numbers are CALIBRATION on the curated 61/144 dossiers, NOT validation. Per-year + leave-block +
  null-of-max + no-concentration tests required in Fase 2 before any claim of edge.
- L5.7 is a rare-event booster (base rate ~0); expect low recall — use only inside a combo, never standalone.
- The whole angle rests on NATIVE HTF resample (no separate 4H/1D RAW). If finer HTF needed, gate provenance first.
- Specificity is the gate: any lens that also fires broadly on control is the "wall" (report honestly), not a win.
