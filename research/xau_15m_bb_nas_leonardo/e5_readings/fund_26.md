# Fund 26 — DEEP READING (XAU 15M MON+FORTE bottom)

**Identity:** block 2024-11-25 · low at **2024-12-09 20:15 UTC** (LATE/Asia session, killzone=0) ·
tier **FORTE** · power_score 6.5 · leg_atr 29.9 · low price 2656.5 · MFE12 +2.22 ATR / MAE12 +0.22 ATR.

This is a **quiet, controlled pullback-in-uptrend bottom**, NOT a capitulation flush. It is the textbook
case for the "absorption-without-climax" thesis that the new-angle catalog inverts away from the climax model.

---

## (a) THE ENTRY MECHANIC — where/when to actually enter

**The raw bars (UTC) settle the question:** the leg in falls from ~2668 (17:15) on a steady, low-efficiency
grind into 2656.5 at 20:15, with **tick-volume DRAINING into and through the low**
(2836 → 2616 → 2218 → 1983 → 2370 → 2043 → 1892 → 1881 → 1990 → **1789 at the low** → 1853 → 1906 →
**1231 → 1132 → 1056**). There is **no climax bar, no big rejection wick, no deep sweep** — the low bar is
small (h-l = 3.0 = 1.3 ATR), closes mid-bar (low_closepos 0.46). Selling simply runs out of fuel.

The reclaim is **slow and quiet, not a V**. This is the load-bearing nuance vs the dossier's ATR-scaled
`reaction_seq` (which is normalized to a tiny ATR ~2.0 and so *looks* explosive in ATR units): in PRICE the
turn is a flat base that drifts up from 2657.9 → 2659.4 → 2660 over the Asia hours, then accepts above EMA21.

**Concrete causal entry — there are two valid triggers, both honest:**

1. **Micro-HL + first-thrust entry (early, aggressive):** bar +3 (21:00 UTC) is the first decisive green bar
   — it closes 2659.4 above the prior bar's high (2658.3) and posts a higher-low (2657.8 > the low's 2656.5),
   on a vol drop (1231). That is the first higher-low confirmation (`first_higher_low_bar=1` in the dossier).
   Entry on the close of +3 at ~2659.4, SL below 2656.5 (≈ 0.8 ATR / ~3 pts risk).
2. **EMA21-reclaim acceptance entry (the strategy's canonical trigger):** the dossier's `reclaim_ema_bars=9`
   matches the raw — first 15M close back above EMA21 is bar **+9 (23:30 UTC, c2661.2 vs ema2661.1)**. This
   is later and pays ~2 ATR less, but is the "acceptance confirmed" version.

**Recommended read:** enter at the **micro-HL/first-green-thrust (+3)** because the bottom is so quiet that
waiting for the EMA reclaim (+9) surrenders most of a small-ATR leg. The trigger is **not** a sweep+reclaim
or a CHoCH (none prints — `choch_15m_after=0`, `nas_long_after=0`); it is a **failed-supply absorption →
shallow local-low undercut → immediate higher-low**. `swept_prior_low=1` but only of a *local* pool
(low 2656.5 undercut prior bar's 2657.6 by 1.1 pts; NOT lowest-of-50 = 2646.0). The sweep is cosmetic; the
real signal is the volume-drain + higher-low, not the grab.

---

## (b) Lenses PRESENT / STRONG here (old E1/htf + NEW angles)

**STRONG (the spine of this read):**
- **Angle 1 · Lens 1 — QUIET RECLAIM (off-killzone × non-headline low):** killzone=0, session LATE/Asia,
  low NOT lowest-of-50. This is the single highest-lift lens (8.1×) and it fires cleanly here. The textbook
  match.
- **Angle 3 · Time/Session — Asia off-peak bottom:** 20:15 UTC, mid-Asia, off all kill windows; mid-week
  (Monday→Tuesday boundary, exhausted intraday leg). Matches the 2.3×–4.7× Asia/off-killzone enrichment.
- **Angle 0 · L8 / Angle 2 · L1-L2 — VOL DRAIN + ATR DECEL INTO LOW:** tick-vol falls monotonically into and
  past the low; ATR contracts 4.24 → 2.33 across the leg (`atr_regime 0.76` = calm regime, well below the
  MON median 0.94, deep in the "drained/coiled" zone). `atr_compression_pre 1.74` is very high. Coil-launch.
- **Angle 0 · L2 — QUIET CLIMAX (anti-capitulation):** vol_climax 0.6 (tiny), sweep_depth_atr 4.0 but the
  *price* sweep is shallow/local, lower_wick_ratio 0.46. Modest-everything = the absence-of-theatrics
  fingerprint.
- **Angle 0 · L10 / E1 — RSI HOLDS ABOVE FLOOR:** rsi_low/rsi_min8 = 38.2 (NOT deeply oversold; well above
  control's ~28). Momentum absorbed, not confirmed-down.
- **Angle 1 · Lens 7 — STOP-RUN / NAS-SHORT EXHAUSTION:** the only NAS prints nearby are SHORT (08:15, 10:45,
  11:30, 15:30); the last short fired ~18 bars BEFORE the low and then went stale. Sell-initiative stopped
  advertising into the bottom — `sell_bub_w=0` at the low (sellers gone), `buy_bub_w=15`/`buy_bub_L=4` present.
- **Angle 5 · L5.4 / L5.6 — COMPRESSED REGIME + NESTED DEMAND:** `in_demand=1`, `demand_fresh=1`,
  `demand_virgin=1`, dist_demand −0.17 ATR (sitting on a fresh virgin 4H demand), htf4_native.in_demand=1,
  htf1_native.in_demand=1 — a **stacked multi-TF virgin-demand floor** in a compressed regime.
- **Angle 1 · Lens 2/5 — ENGINEERED EQL:** an EQL printed earlier the same day (13:30, 2653.34) plus a BOS at
  13:45 (2660.45) — resting equal-low liquidity below and a structural break above = the raid/reclaim geometry.

**PRESENT / supportive:**
- E1 `buy_bub_w=15, buy_bub_L=4` with `sell_bub_w=0` — demand footprint with zero opposing sell bubbles
  (Angle 0 L3 sell-exhaustion gap + L9 buy-bubble print).
- htf1_native.trend=+1, htf4_native.trend=+1 (both up) — this is a *with-trend pullback*, the cleanest context.
- `legpos30=0.137` (deep within the 30-bar leg = near the extreme), `flush_v_ratio 0.2` (sharp local V on the
  geometry side).

**ABSENT / counter-signals (honesty):**
- **NO CHoCH after, NO 15M NAS-LONG trigger, NO buy-side NAS** (`nas_long_16=0`, `choch_15m_after=0`). The
  turn is a quiet absorption, not a signal-confirmed reversal. Angle-4 reclaim-velocity lenses (monotone
  staircase, reclaim_jerk, hard slope-flip) are **WEAK** here — the recovery is a flat grind, not the
  front-loaded staircase seen in the MONSTRO archetype.
- `h1_eff 0.13` is LOW (consistent with the chop-base nature) — note the memory's `h1_eff≥0.15` anti-range
  filter would **borderline-reject** this trade; it is a slow base, not an impulsive launch.

---

## (c) What is DISTINCTIVE about this bottom

It is a **maximally quiet bottom**: vol_climax 0.6 and atr_regime 0.76 are *below* the already-quiet MON
medians (1.23 / 0.94). There is **zero capitulation theater** — no climax bar, no deep flush, no rejection
wick, no oversold RSI, no CHoCH, no NAS-long. The entire edge is carried by the **convergence of absences**
(no sellers left: sell_bub_w=0, NAS-short stale, vol drained) layered on a **fresh virgin multi-TF demand
floor in an uptrend**. The leg it produces is small in ATR-normalized terms (MFE 2.22 ATR) and the reaction
is a flat Asia-hours base, not a thrust — so this is a FORTE (not MONSTRO) by virtue of *clean structure +
low risk* rather than *explosive displacement*. The risk is tiny (MAE 0.22 ATR — price essentially never
went against the entry), making it a high-quality, low-noise entry even though it lacks fireworks.

The discriminating contrast: a naive "find the climax / oversold / CHoCH" detector would **miss this entirely**.
Only the inverted absorption lenses (quiet-reclaim, off-killzone, vol-drain, sell-exhaustion, stacked-virgin-
demand) catch it. That is exactly the angle-catalog thesis in its purest form.

---

## (d) Macro / HTF context

December 2024, gold consolidating after the post-US-election pullback, mid-2660s. On the native HTF:
**1H trend +1 and 4H trend +1 (both bullish), htf1 RSI 46.9 / htf4 RSI 67.2** — a healthy uptrend taking a
breather. The 15M flush lands on a **fresh, virgin, un-mitigated demand zone** that coincides on both 4H and
1H (`in_demand=1` on all frames, dist_demand −0.17 ATR 15M / −0.27 4H / +0.11 1H), with
`htf4_native.choch_rec=1` (a recent 4H bullish structure shift already on the books) and
`htf4_native.clean_sky_atr 0.15` / `htf1 clean_sky 0.93` (some overhead supply nearby on 4H — modest run-room,
consistent with the small leg). The bottom forms in the **quiet Asia window** as the intraday down-auction
exhausts into that stacked demand floor — a with-trend, low-volatility re-accumulation pullback. Not a regime
turn; a continuation-pullback entry inside an established bull leg.
