# Fund 35 — Deep Reading (XAU 15M MON+FORTE bottom)

**Identity:** block 2024-05-25 · date **2024-07-03 02:45 UTC** · tier **FORTE** · leg_atr 24.63 · power_score 11.3 · session **ASIA** · killzone **0** (off-killzone).
**Outcome shape:** mfe12 **5.77 ATR**, mae12 **0.76 ATR** — i.e. after the low, price gave back essentially nothing (0.76 ATR = the bottom bar's own low) and ran 5.77 ATR up. A "no-look-back" leg.

---

## (a) ENTRY MECHANIC — where/when I would actually enter

This is a **shallow-sweep + immediate-reclaim + clean-staircase** bottom, NOT a deep-flush capitulation. The reaction sequence is the most distinctive thing about this fund:

- bar-lows (`l_atr`): 0.76 → 1.34 → 1.39 → 2.37 → 3.12 → 3.55 → 3.82 → 4.27 → 4.59 — **9 consecutive higher bar-lows from w1**. The floor literally only goes up. (Angle 4 / L1 `reclaim_low_monotone_k` = max run, the canonical staircase.)
- close progression w1..6: **R² = 0.963, slope +0.573 ATR/bar** — a near-straight ramp (Angle 4 / L5 `close_progression_R2` `clean_launch`, R²>0.85 satisfied with room to spare).
- per-bar close velocity is front-loaded then sustained: +0.17, +0.87, +0.73, +0.62 … the thrust arrives in bars 1–2 and never reverses.

Entry mechanics fields confirm the trigger menu: `swept_prior_low=1`, `first_higher_low_bar=1`, `reclaim_ema_bars=3`, `choch_15m_after=1`, `nas_long_after=0`.

**My entry: at the close of reaction bar 1 (the first higher-low / EMA-reclaim onset), confirmed by the 15M CHoCH that prints shortly after.** Concretely:
- The bottom bar swept a prior fractal low (`swept_prior_low=1`) but only **shallowly** (`sweep_depth_atr=1.02`, far below the control's ~2.3) and closed strong (`low_closepos=0.82`, `lower_wick_ratio=0.82` — a big lower-wick rejection bar, buyers defended into the close).
- **Bar 1 (w=1) is the trigger**: it prints the first higher-low (`first_higher_low_bar=1`) and closes at c_atr 1.34 off a 0.76 low — a decisive thrust. This is the moment the sweep is reclaimed and the staircase begins.
- EMA21 is reclaimed by **bar 3** (`reclaim_ema_bars=3`) and a **15M bullish CHoCH** confirms (`choch_15m_after=1`). A more conservative entry takes the CHoCH/EMA-reclaim at bar 3 (c_atr ~2.38); even then there are 5.77−2.38 ≈ **3.4 ATR of leg left**, because the leg is large (leg_atr 24.63).

So: **entry = sweep+reclaim of the swept prior low → first higher-low (bar 1) → ride the monotone staircase, with the 15M CHoCH as confirmation by bar 3.** Risk sits just under the 0.76-ATR bottom (MAE never threatened it).

NOTE on `nas_long_after=0` and zero bubbles (`buy_bub_w/L=0`, `sell_bub_w=0`): this bottom has **no order-flow/NAS confirmation footprint at all** — it is read purely off price structure + HTF context. That is itself distinctive (see below).

## (b) Lenses PRESENT / STRONG here

**Strongest (multi-angle convergence — the staircase + quiet thesis):**
- **Angle 4 L1 `reclaim_low_monotone_k` = MAX (run 9)** and **L5 `close_progression_R2` (0.963)** — the textbook clean no-look-back launch. This is the single most dominant signature of fund 35.
- **Angle 4 L8 `reclaim_dip_depth` shallow_retest = TRUE** — mae12 0.76 ATR means the first pullback never returns toward the low; the higher-low quality is excellent.
- **Angle 0 / Angle 2 quiet-absorption thesis = PRESENT.** This bottom is the inverse-capitulation fingerprint: `sweep_depth_atr 1.02` (shallow), `vol_climax 1.23` (modest), `atr_regime 0.78` (calm, even below the MON median 0.94), `atr_compression_pre 0.69`, `downleg_eff 0.03` (extremely grindy descent). Angle 2 L1 `atr_decel_into_low` and the "drained, not climactic" reading apply — though note `consec_down=1` only (the bottom was not a long cascade; see distinctive).
- **Angle 3 time/session = STRONG.** Session=ASIA, **02:45 UTC** lands squarely in the Asia/late off-peak window (Angle 3's 2.3×–4.7× enriched zone), killzone=0 (off-killzone, the 80%-MON profile). L1 `asia_offpeak_flush` / L3 `time_since_session_open` (early-Asia reaction to prior-session excess) both fire. This is a quintessential off-killzone Asia reversal.
- **Angle 0 L4/L7 absorption-reclaim:** `low_closepos 0.82` + `lower_wick_ratio 0.82` = strong-close, big rejection wick = demand absorbing at the low; `liquidity_grab_no_followthrough` (shallow grab + fast reclaim) fires cleanly.

**Present but moderate:**
- **Angle 1 liquidity:** `in_demand=1`, `demand_fresh=1`, `demand_virgin=1`, `n_demand_near=78` — flushed into a FRESH, VIRGIN demand zone (Lens 3/6 defended-floor + discount). BUT `dealing_range_pos=−0.586` (discount third, not a range break → Lens 6 DISCOUNT-not-breakdown fires) AND `vpnode_dist_atr=−1.04` (a volume node nearby). Caveat: `n_supply_overhead=160` is HIGH (overhead is congested), so Angle 1 Lens 3 "thin overhead" does NOT fire and Angle 5 L5.6 "clean HTF sky" is only partial.
- **Angle 5 cross-TF — mixed/partial.** `h4_trend=+1` and `hd_trend=0` here (NOT the "4H-still-bearish / 1H-leads" phase-lag the angle expects). `htf1_native.trend=−1` while `htf4_native.trend=+1` — actually the SLOW frame (4H) is already up and the native-1H is still down: the *opposite* phase-lag from Angle 5's grounding. So L5.1/L5.8 (1H-leads-4H) do NOT fire in the textbook direction. What DOES fire: **macro_bull=1, macro_bear=0**, h4_trend +1, hd_slope +0.88 — the broader regime is constructively bullish, so the 15M flush is a dip inside an up-regime (a different, arguably stronger, alignment than the angle's lag thesis).

**Absent / not firing:**
- All bubble/NAS lenses (Angle 0 L3/L9, Angle 5 L5.7): `buy_bub/sell_bub=0`, `nas_long_16=0`, `nas_short_16=0`, `smc_bos=0`. No order-flow signal layer.
- `rsi_bull_div=0`; `rsi_low 49.6` / `rsi_min8 45.4` — **not oversold at all** (even less oversold than the MON median ~35). Angle 0 L10 / Angle 5 L5.3 fire in spirit (RSI refuses to confirm a panic low) but there is no classic divergence and no deep wash.
- Climax lenses (Angle 2 L8 flush_then_freeze, Angle 4 L7 velocity-spike): `consec_down=1`, modest `drop20_atr 3.4`, `flush_v_ratio 0.28` — there is no big terminal climax bar to freeze after. This bottom skips the puke entirely.

## (c) What is DISTINCTIVE about this bottom

1. **It is a structure-only reversal.** Zero bubbles, zero NAS, no SMC BOS, no RSI divergence, not oversold. Everything that "confirms" a bottom in the order-flow/momentum toolkit is silent. The edge is read entirely from (i) the shallow sweep + strong-close rejection bar, (ii) the fresh virgin demand zone, (iii) the perfect monotone staircase reclaim, and (iv) the off-killzone Asia timing inside a bullish macro. A pure price-action / Auction-Theory bottom.

2. **Almost no down-leg, yet a huge up-leg.** `consec_down=1`, `downleg_eff=0.03`, `drop20_atr=3.4` — this was barely a flush. There was no multi-session capitulation (Angle 3 L7 down-leg rhythm = short). The leg_atr 24.63 / mfe 5.77 came from the *up* side, not from snapping back a deep dump. This makes it an outlier vs the "exhausted multi-session decline" archetype — it is closer to a **continuation-dip-in-an-uptrend** that happened to print at a fresh demand floor.

3. **The cleanest possible reclaim.** Monotone-low run of 9, R²=0.963, MAE 0.76 ATR. Among MON+FORTE funds this is at the top end of "no-look-back" quality — the single most reliable post-low confirmation, and the reason an entry as early as bar 1 is safe.

4. **HTF phase-lag is INVERTED vs the angle's prior.** 4H trend already +1, 1H trend still −1. The bottom is not "fast-frame leads slow-frame turn"; it's "the slow frame already turned up and the 15M is buying the dip." Honest flag: Angle 5's marquee REGIME-ONSET TRIAD does not fire here in its designed direction — but the constructive macro (macro_bull=1) replaces it.

## (d) Macro / HTF context

- **Daily:** `hd_trend=0` (neutral/transitioning), `hd_rsi 50.9`, `hd_slope_atr +0.88` (slope turning up), `hd_pos 0.51` (mid-range), `hd_dist 1.59`. Daily is balanced-to-constructive, slope positive.
- **4H (E1 + native):** `h4_trend=+1`, `h4_rsi 53.6`, `h4_slope_atr +0.43`, `htf4_native.in_demand=1`, `htf4_native.dist_demand_atr −0.27`, `clean_sky_atr 0.22`. The 4H is up-trending and the 15M flush landed INTO 4H demand — a nested floor.
- **1H (E1 + native):** `h1_trend=+1` (E1) but `htf1_native.trend=−1` (native resample) — the 1H is the laggard, still working off the short-term dip; `h1_rsi 50.6`, `h1_eff 0.16` (note: above the anti-range floor 0.15 from memory), `htf1_native.in_demand=1`.
- **Regime:** `macro_bull=1`, `macro_bear=0`, `atr_regime 0.78` (compressed/calm). 
- **Read:** a calm, bullish-macro environment; price dips into a **fresh virgin 4H+15M demand confluence** in the quiet early-Asia window, sweeps a local low shallowly, rejects with a strong-close wick bar, and launches a clean monotone staircase. The one caution is heavy overhead supply (`n_supply_overhead 160`) — yet the leg ran 5.77 ATR anyway, so the demand-defense + macro-bull tailwind overpowered the congestion.

---

**Validation status:** all lens references are CALIBRATION-grade (per the 6 angle docs' own honesty notes — n=61/144, no OOS/cross-asset per canon). This is one fund's reading, not an edge claim.
