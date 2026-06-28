# Angle 3 — TIME / SESSION / CYCLICAL lenses for MON+FORTE bottom detection

*New-angle DISCOVERY (Engine 5). Dimension: time-of-day, session, day/week phase, killzone, time-since-event, duration rhythm. All causal as-of the bottom bar / SHIFT1, RAW-only (`primitives/*.json`: series `t,o,h,l,c,v,rsi,atr,ema21`, `nas_events`, `smc_events`, `zones`). Tier label used ONLY to define study/control, never as feature.*

## Grounding (what the dossiers already show — motivates the new lenses)

Quick empirical scan of the 61 strong vs 144 control dossiers (descriptive, calibration not validation):

| signal | STRONG | CONTROL | direction |
|---|---|---|---|
| session = ASIA | 48% (29/61) | 25% (36/144) | **enriched in strong** |
| session = NY | 15% (9/61) | 46% (66/144) | depleted in strong |
| killzone flag = 0 (outside London/NY KZ) | 80% (49/61) | 47% (64/144) | **enriched in strong** |
| Asia clock-hours 22:00–03:00 UTC | **49%** | 22% | **2.3x enriched** |
| week-open (Sun+Mon) | 13% | 28% | depleted in strong |
| hour 01:00 UTC (Asia ramp) | 23% (14/61) | 5% | **4.7x enriched** |

So the *existing* session/killzone features (FEATURE_MAP §G, "secondary") are already carrying real signal in the WRONG direction from the usual killzone dogma: MON+FORTE bottoms form in the **quiet, off-killzone, Asia/late hours**, NOT in the high-volume London/NY killzones (which dominate the MED/FRACO control). The plain `session`/`killzone` flags are coarse. The lenses below are sharper, novel angles that exploit this and add time-since / rhythm structure nobody has mapped.

---

## The 9 novel lenses

### L1 — `asia_offpeak_flush` (off-hours capitulation timestamp)
**Definition (as-of):** Boolean/continuous. From bar `t`, compute UTC hour-of-day. Flag = bar formed in the low-liquidity Asia/late window (22:00–04:00 UTC) AND the bar's range/ATR (`(h-l)/atr`) is in the top tercile of the trailing 96-bar (1-day) range distribution. I.e. an *outsized* candle occurring when liquidity is thin.
**Why specific to MON+FORTE:** Big legs that bottom in thin Asia liquidity are stop-runs / forced liquidation into a vacuum — they overshoot and snap back hard (the monster reversal). The control set's mediocre lows cluster in NY where two-sided liquidity absorbs and grinds (no clean snap). A *large* candle in a *thin* window is the rare combination — most thin-window bars are small, most large bars are in NY. Empirically Asia-hours already 2.3x enriched; gating on "large-for-thin-window" should sharpen further and stay rare on control.
**Combo:** {asia_offpeak_flush, flush_v_ratio (E1), sweep_depth_atr} — thin-window + V-shape flush + sweep = forced-liquidation bottom.

### L2 — `session_volume_anomaly` (relative-to-session-normal volume spike)
**Definition (as-of):** Bucket each bar by its session (ASIA / LONDON / NY / LATE) using `t`. For the entry bar, compute its `v` as a z-score (or ratio) against the **trailing 20 same-session bars** (e.g. last 20 Asia bars for an Asia bottom). Flag if z ≥ +2. This normalizes the well-known fact that Asia volume is structurally low — a *within-session* climax is what matters, not raw volume.
**Why specific to MON+FORTE:** `vol_climax` (E1) uses an absolute/global ATR-ish measure, so genuine Asia climaxes get washed out by NY's baseline. A within-session climax during the Asia bottom is the institutional footprint of capitulation in a low-participation window — rare, because most Asia bars are quiet and most volume spikes happen in NY (where they DON'T predict strong bottoms). Directly attacks the under-detection of Asia capitulation.
**Combo:** {session_volume_anomaly, asia_offpeak_flush, lower_wick_ratio (E1)}.

### L3 — `time_since_session_open` (bottom-in-the-first-hour vs grind-bottom)
**Definition (as-of):** Minutes elapsed from the bar's session open (Asia ≈ 22:00 UTC, London ≈ 07:00, NY ≈ 12:30) to bar `t`. Feature = the elapsed-minutes value, plus a flag for "first-90-min-of-session". Hour-01-UTC enrichment (4.7x) hints the *Asia ramp* (first ~1–3h after Asia open) is where monsters bottom.
**Why specific to MON+FORTE:** A bottom that prints in the first session-hour is a *reaction to the prior session's excess* (the new session opens, sweeps the overnight low, reverses) — that's the classic liquidity-grab reversal. Grind-down bottoms deep into a session (control profile) are continuation lows, not reversals. The phase-within-session is orthogonal to raw clock-hour and to `killzone`.
**Combo:** {time_since_session_open, swept_prior_low (entry_mechanics), reclaim_ema_bars}.

### L4 — `overnight_low_sweep_clock` (sweep of the PRIOR session's extreme, time-stamped)
**Definition (as-of):** Identify the low of the *previous completed session* (e.g. for an Asia bottom, the prior NY/London session low) from `series`. Flag if the entry bar's low pierced that prior-session low (swept) AND reclaimed (close back above it). Tag the *clock distance* (bars) since that prior-session extreme was set.
**Why specific to MON+FORTE:** A *cross-session* liquidity sweep (this session takes out last session's low then reverses) is the signature of a stop-hunt that resets the auction — the engine of a big reversal leg. `swept_prior_low` (entry_mechanics) only checks a generic prior fractal low; anchoring the sweep to the *session boundary* makes it rarer and more causal (session lows are the liquidity pools institutions target). Control's continuation lows mostly extend the trend without a clean cross-session reclaim.
**Combo:** {overnight_low_sweep_clock, session_volume_anomaly, displacement_struct (post-entry, exit-side)}.

### L5 — `weekly_phase_position` (mid-week vs week-open/Friday-late)
**Definition (as-of):** From `t`, compute weekday + intraday fraction → a 0..1 position within the trading week (Sun-open=0, Fri-close=1). Feature = the continuous week-phase, with flags for {week-open (Sun+Mon-early), mid-week (Tue–Thu), Friday-late}.
**Why specific to MON+FORTE:** Strong bottoms are **depleted at week-open** (13% vs 28% control) and concentrate mid-week (Tue–Thu carry ~66% of strong). Week-open lows are often gap-driven noise / news-repricing that grinds (control), whereas mid-week monster bottoms come after a multi-day down-leg has exhausted — a trend that has *run long enough to reverse*. Week-phase is a pure cyclical axis nobody has used as a discriminator (only raw DOW counts exist).
**Combo:** {weekly_phase_position, downleg_eff (E1), drop20_atr}.

### L6 — `time_since_last_nas` and `nas_off_killzone` (event-clock, not event-count)
**Definition (as-of):** From `nas_events`, compute bars elapsed since the last directionally-matched (LONG) NAS event before entry. Feature = that latency, plus a flag for "NAS fired in a low-liquidity window (Asia/late) within ≤k bars". Existing features count NAS in-zone but never timestamp the *latency* nor the *session* of the NAS.
**Why specific to MON+FORTE:** A LONG NAS that fires **in the quiet Asia window** is rarer and more meaningful than one fired in NY chop (control). And a *recent* NAS (short latency) means the reversal trigger and the bottom are time-aligned (immediate reaction), vs a stale NAS that fired long ago and is decoupled. The latency × session combination is a new event-clock lens orthogonal to `nas_count_in_zone`/`nas_long_16`.
**Combo:** {time_since_last_nas, nas_off_killzone, recent_choch_dir}.

### L7 — `downleg_duration_rhythm` (how many SESSIONS the down-leg lasted)
**Definition (as-of):** Measure the down-leg not in bars but in **distinct session-crossings**: count how many session boundaries the leg from the swing-high to the entry low traversed. Feature = session-count of the leg + a "multi-day, accelerating-into-close" flag (leg spanned ≥2 sessions AND the steepest segment was the last session before the low).
**Why specific to MON+FORTE:** Monster reversals follow *exhausted* multi-session declines that capitulate on the final push — the leg has "earned" the reversal. A leg measured in raw bars (`drop20_atr`, `legpos*`) misses the *session rhythm*: a one-session quick dip (control) vs a 2–3-session grind that finally flushes are structurally different even at equal bar-count. Session-rhythm of the leg is an unmapped temporal axis.
**Combo:** {downleg_duration_rhythm, atr_compression_pre (E1), rsi_min8}.

### L8 — `low_revisit_clock` (time-spread of the equal-lows that built the base)
**Definition (as-of):** `low_revisit` (E1) counts how many times price revisited the low. New lens: measure the **time-span** over which those revisits occurred (bars between first and last touch of the low ±0.1ATR) and whether the touches straddle a session boundary. Feature = revisit-span-in-bars + cross-session-base flag.
**Why specific to MON+FORTE:** A base that holds the same low *across a session boundary* (e.g. defended through Asia into London) is a level being actively defended by a real participant base — a durable floor that launches a big leg. Quick same-session double-taps (control) are weaker. Distinguishes a *time-tested* floor from a fleeting one; orthogonal to the raw revisit count.
**Combo:** {low_revisit_clock, demand_virgin (E1), zone_age_bars}.

### L9 — `htf_clock_alignment` (bottom prints at an HTF candle boundary)
**Definition (as-of):** Flag if the 15M entry bar coincides with (or is the first bar after) a **4H or Daily candle open/close boundary** (derivable from `t` modulo 4h / 1d). Also: is the bottom forming in the *first 15M bar of a fresh HTF candle* (a new HTF auction opening) vs deep inside an HTF candle.
**Why specific to MON+FORTE:** Reversals that align with a fresh HTF candle open are HTF-level decisions (a new 4H/Daily auction rejecting lower prices) — institutional timeframe turns, which produce big legs. Mid-HTF-candle 15M lows are intrabar noise (control). This is a *temporal confluence* between the 15M trigger and the HTF clock — a new angle on top of the existing `htf4_native`/`htf1_native` snapshots (which give state, never *boundary timing*).
**Combo:** {htf_clock_alignment, htf4_native.in_demand, time_since_session_open}.

---

## Specificity priorities & honesty notes
- Highest-conviction (already empirically enriched, sharpen-and-test first): **L1, L3, L4** (Asia off-peak flush + first-session-hour + cross-session sweep). These directly exploit the 2.3x–4.7x Asia-hour enrichment and the off-killzone profile.
- The session/killzone axis is *counter-intuitive* (monsters bottom OFF killzone, in Asia) — this is itself the novelty: prior framing treated killzone as secondary and likely assumed London/NY were where reversals live. The data says the opposite for clean reversal legs.
- Gate every lens on **specificity** (fire-rate on control), not recall — per FEATURE_MAP §"seleção". n=61 is low: require per-year + leave-block + null-of-max before trusting any single lens.
- Risk: clock features can encode a regime/seasonality artifact (e.g. a 2025 Asia-session gold regime). Validate within the 8 blocks (sub-windows), not as a global average. Asia-enrichment must hold per-block or it's a beta/seasonality artifact, not a causal bottom signature.
