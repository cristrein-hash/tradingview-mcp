# XAU 15M — TRAP / FAILURE ENTRY FEATURES (Ring-2 proposals, lente: armadilhas)

Lens: failed-breakdown (spring) / failed-breakout (upthrust) / liquidity-grab-and-reverse / EQH-EQL fakeout.
Premise: the point where the MAJORITY stops out = where the institutional fills. Right-tail wall came from
basic triggers conditioned on NAS-in-zone + single-event geometry. These detect the TRAP independently of the
NAS universe, on raw swing/EQ/zone-edge geometry, with TWO-SIDED liquidity + absorption signatures.

All causal: events with t<=j (bar of confirmation), SMC/NAS/OB consumed SHIFT1 (repaint). Entry = close of
confirmation bar. Volume = raw tick-volume → used RELATIVELY (z-score / ratio vs local median), never as absolute.

## 1. STOP_RUN_VACUUM (spring with proof-of-thin-liquidity-below)
angle: A real spring sweeps a swing-low / EQL, but the TELL is that the breach happens on a VOLUME+RANGE EXPANSION
spike into a region that then refuses to follow through — price snaps back through the broken level on the very
next 1-2 bars (vacuum, no supply met). A continuation breakdown instead ACCEPTS below: it consolidates beyond the
level on flat/rising volume. So: classify the breach by what happens in the 2-3 bars AFTER it, not the breach itself.
raw_recipe: find prior swing-low SL (lowest low of a k=10..20 bar fractal, t<=j-2) OR latest EQL price.
breach = min(low) over window [j-4,j] < SL*(1-eps). reclaim = close[j] > SL. Then compute:
  vac_speed = bars from breach-low bar to first close-back-above SL (require <=2).
  thrust_vol_z = volume z-score (vs median vol of trailing 50 bars) on the breach bar (require >=1.0).
  followthru_fail = max(close) of the 2 bars after breach-low does NOT make a new low (no acceptance).
fire LONG only if reclaim AND vac_speed<=2 AND thrust_vol_z>=1.0 AND followthru_fail. Mirror for SHORT (swing-high/EQH).
lifts_wr_how: separates spring (snap-back through level on expansion = trapped sellers covering) from
"breakdown that holds" (the bulk of losers that fired the basic failed_breakdown=0). The vac_speed<=2 + vol-z gate
is the actual institutional signature; basic detector ignored speed and volume so it caught nothing.
cuts_streak_how: in a genuine downtrend, breaches ACCEPT (vac_speed never satisfied) → feature stays 0 across the
whole bear leg → no longs fired into the trend = no loss cluster.
novelty: never tested — prior failed_breakdown used close-beyond-edge with NO post-breach speed/volume confirmation
and was conditioned on NAS-in-zone (fired 0/791). This is universe-independent (any swept swing-low) + 2-bar reaction.
beats_right_tail_how: the right-tail trades in the corpus are exactly the snap-back springs; basic triggers diluted
them with accepting-breakdowns. Conditioning ON the snap-back speed concentrates the universe onto the right tail
instead of sampling around it.

## 2. DOUBLE_SWEEP_DIVERGENCE (two pokes, second on lower energy = exhausted stop hunt)
angle: The cleanest grab-and-reverse is the SECOND sweep of the same liquidity pool: price pokes a low, bounces,
pokes it again (equal-or-marginally-lower low) but the second poke arrives on LOWER volume / SMALLER range AND
with RSI making a higher low (momentum divergence). Two failed attempts to break = the pool is being defended;
the stops from the first poke are already gone, so the second poke is the institutional fill, not a fresh break.
raw_recipe: detect two local lows L1 (at t1) and L2 (at t2, t1<t2<=j) within band: L2 in [L1*(1-0.15ATR/px), L1].
require a bounce between them (a local high > both by >=0.5ATR). Then:
  vol2_lt_vol1 = vol(L2 bar) < vol(L1 bar).
  range2_lt_range1 = (h-l)(L2 bar) < (h-l)(L1 bar).
  rsi_div = rsi(L2 bar) > rsi(L1 bar) (higher low in RSI vs lower/equal price).
fire LONG at close[j] (j = first close back above L1 after L2) if vol2_lt_vol1 AND rsi_div AND (range2_lt_range1).
Mirror for SHORT with EQH/swing-highs + RSI lower-high.
lifts_wr_how: the volume+range+RSI triple-divergence is a hard separator of "exhausted hunt that reverses" vs
"momentum break that continues" — continuation has vol2>=vol1 and RSI confirming, so it's filtered out.
cuts_streak_how: requires a SECOND poke, which structurally cannot happen during a clean one-way leg → no fires in
strong trends against you (the chop-killer is built into the geometry).
novelty: prior sweep+reclaim used ONE breach. Two-sweep + cross-feature divergence (vol AND range AND RSI) on the
SAME pool has never been computed. RSI was only ever used as a context column, never as a divergence on swept lows.
beats_right_tail_how: double-sweeps are rarer (=fits the 1-5/wk frequency) AND have the highest reverse-probability
of any trap geometry; the right tail is built from a few high-conviction reversals, and this is the precise filter
that isolates them rather than averaging over all single sweeps.

## 3. TRAPPED_BREAKOUT_FUEL (failed-breakout upthrust → the breakout buyers ARE the fuel)
angle: After an EQH/range-high breaks UP and FAILS (close back below within N bars), every breakout buyer is now
offside and will sell-stop below the range — a magnet. The institutional play is to SHORT the upthrust OR (the
bolder version) to wait for the offside-long flush and BUY the resulting spring at range-low. Quantify the trapped
cohort: how much volume transacted ABOVE the broken high before the failure (= size of the trapped book).
raw_recipe: range-high RH = recent EQH or k-bar swing-high (t<=j). breakout = max(high)[window]>RH*(1+eps) AND
some close>RH. failure = close[j]<RH. trapped_vol = sum(volume) of bars whose close>RH within the window
(proxy for trapped breakout longs). Normalize: trapped_vol_z vs trailing-50 median bar-vol.
  For SHORT entry: fire at close[j]<RH if failure AND trapped_vol_z>=2.0 (big trapped book) AND
    bars_above_RH<=4 (fast trap, not a real acceptance/base).
  For the contrarian LONG: arm a "flush target" = range-low RL; if within next M bars price sweeps RL and
    snaps back (feature 1 logic), the trapped-long flush is complete → highest-quality long.
lifts_wr_how: trapped_vol_z sizes the fuel — small trap = weak follow-through (skip); big trap = strong directional
flush (the WR lives here). The bars_above_RH<=4 gate removes real breakouts that based and held (those are longs,
not traps).
cuts_streak_how: a real sustained breakout produces bars_above_RH large → feature never fires → you don't fade a
genuine trend repeatedly (the classic streak-killer for fade strategies).
novelty: NO feature in the corpus measures the SIZE of the trapped cohort (volume transacted in the failed
excursion). All prior breakout logic was binary (broke / didn't). Quantifying the offside book as fuel is new.
beats_right_tail_how: the biggest 15M reversals are upthrust-failures with heavy trapped volume (blow-off topping
into a flush); right-tail magnitude correlates with cohort size, so sizing it directly targets the magnitude tail
the basic binary triggers couldn't see.

## 4. EQ_FAKEOUT_TIMEPOLARITY (EQH/EQL fakeout read by TIME-IN-EXCURSION, not just reclaim)
angle: SMC EQH/EQL are engineered liquidity. A fakeout that reverses spends MINIMAL time beyond the level (stop
sweep = instantaneous), whereas a true break spends time + closes accepting. The discriminator the basic detector
missed is the RATIO of time-beyond-level to reclaim, plus whether the wick (not body) did the sweep (wick-dominant
= rejection; body-dominant = acceptance).
raw_recipe: EQ level = nearest EQL (long) / EQH (short), t<=j. excursion_bars = count of bars in [j-6,j] whose
LOW<EQL (or HIGH>EQH). wick_sweep = on the deepest breach bar, the breach was via wick: (open & close both > EQL)
i.e. body stayed above, only the low pierced. body_accept_bars = count of bars that CLOSED beyond the level.
fire LONG if close[j]>EQL AND excursion_bars<=3 AND wick_sweep AND body_accept_bars<=1. Mirror SHORT.
Add fakeout_strength = (EQL - min_low)/ATR (depth of the grab, deeper grab into obvious liquidity = stronger).
lifts_wr_how: wick_sweep + body_accept<=1 is the exact separation of "swept the stops and rejected" vs "broke and
closed through" — the latter is the loser the EQH/EQL fade kept buying. Time-in-excursion is a continuous quality
score for the cut.
cuts_streak_how: when the level genuinely breaks, body_accept_bars climbs and the gate closes → no repeated fading
of a level that has actually given way. Caps consecutive losses at a broken EQ.
novelty: EQH/EQL were only used as price levels for room_to_run / sweep_reclaim. Reading them by WICK-vs-BODY and
TIME-beyond-level (the microstructure of the sweep) is unexplored. The candidate universe never used EQ as the
trigger itself with a polarity/time read.
beats_right_tail_how: institutional EQ sweeps that reverse hard are wick-dominant and fast; the right-tail reversals
share this microstructure. Filtering to wick+fast isolates the tail-producing fakeouts from the body-accept breaks
that produced the median-stop losers.

## 5. ABSORPTION_AT_EXTREME (climax volume + range-compression = supply/demand exhausted)
angle: The trap completes when the LAST push to a new extreme happens on the HIGHEST volume of the leg but the
SMALLEST net progress (effort >> result = absorption). This is the Wyckoff selling/buying climax. It is the
strongest non-geometric reversal tell and is invisible to swing/zone/EMA logic entirely.
raw_recipe: over the trailing K=20 bars find the bar making the leg extreme (lowest low for long). climax = that
bar's volume is the max of the K window (vol == rolling-max) AND its CLOSE-to-CLOSE progress |c-prev_c|/ATR is in
the bottom tercile of the window (high effort, low result). Confirm with next-bar reversal: close[j] > climax_bar
high (long). effort_result = volume_z / (abs(c-prev_c)/ATR + eps) → high score = strong absorption.
fire LONG if climax AND close[j]>climax_high AND effort_result above its trailing median. Mirror SHORT at highs.
lifts_wr_how: effort>>result is a direct read of absorption (the institutional side soaking supply); it separates
"capitulation that ends" from "momentum bar that continues" — the latter has result proportional to effort.
cuts_streak_how: trending legs show effort≈result (no absorption) → no fire → you sit out the trend instead of
catching falling knives, which is the #1 source of loss streaks in reversal trading.
novelty: NO corpus feature uses effort-vs-result (volume / price-progress). Volume was present in RAW but never
used analytically (warned as tick-volume → here used only RELATIVELY as a within-leg ratio, which is robust to the
tick-volume caveat). This is genuinely new signal extraction from an unused channel.
beats_right_tail_how: climaxes mark the exact bar the right-tail runners begin; the basic triggers fired mid-leg or
on geometry and missed the energetic turning point. Anchoring entry to the effort/result climax targets the origin
of the magnitude move, not a point along it.

## 6. LIQUIDITY_MAGNET_REJECTION (run to obvious pool → instant rejection = the reversal pivot)
angle: Price hunts the most obvious resting liquidity (a clean prior swing extreme, an EQH/EQL, or a round level),
takes it, and rejects within 1 bar. The bold edge: pre-identify the magnet (where stops MUST sit) and only trade
the rejection AT that magnet — entries elsewhere are noise. Combine with the OB-zone confluence as a SECONDARY
location filter, not the trigger.
raw_recipe: magnet candidates (t<=j-1): nearest untouched-since-creation swing-low (for long), latest EQL, and the
zone-edge of a virgin DEMAND OB. magnet_hit = bar low pierces a magnet within [j-2,j]. instant_reject = within 1
bar, close back above magnet AND the piercing bar closes in top 1/3 of its range (rejection candle). confluence =
how many distinct magnet types coincided within 0.5ATR (stacked liquidity = stronger). dist_to_next_magnet (room)
in the trade direction must be >= some R-multiple (else no room to pay).
fire LONG if instant_reject AND confluence>=1 AND room>=2.0 ATR. Mirror SHORT.
lifts_wr_how: "stacked magnets + instant rejection candle + room ahead" is a multi-factor convergence that the
single-event sweep_reclaim (fired 12/791, no lift) lacked. Each factor is orthogonal (location, reaction, payoff),
so convergence is a true quality gradient, not a re-labeling.
cuts_streak_how: requires a magnet to BE hit and rejected; in a one-way trend the magnet is run THROUGH (no
instant_reject) → no fire → the chop/trend that generated streaks is structurally excluded.
novelty: no prior feature pre-registered WHERE stops sit and demanded rejection AT that exact location with stacking.
Prior work detected sweeps reactively anywhere; this is location-pre-committed + multi-magnet stacking + room gate.
beats_right_tail_how: the rare high-R reversals in the corpus all pivot off obvious-liquidity rejections with room
to the opposite structure; gating on (location + rejection + room) jointly is the convergence that concentrates the
universe onto those pivots instead of averaging over all sweeps — directly attacking the right-tail concentration.

## Cross-cutting notes
- All six are ENTRY-quality / environment-detectors usable as a CONVERGENCE stack (count how many fire), echoing
  the L2/BPT 4H finding that convergence ELIMINATES bad environments (cut streak) even when no single feature
  selects the runner. Recommend testing both as individual lifts AND as conv>=2 elimination gate.
- Volume features (1,3,5) use tick-volume RELATIVELY (z-score / within-leg ratio) → robust to the tick-volume
  caveat in memory (never absolute Session-VP claims).
- Validation stays inside the 8 blocks: per-feature WR lift, sub-window/jackknife, leave-one-block-out, null
  permutation. No OOS / cross-asset (per standing locks).
- Trap features are universe-INDEPENDENT (computed on raw swing/EQ/zone geometry), fixing the root cause of
  failed_breakdown firing 0/791 (it was bolted onto the NAS-in-zone universe).
