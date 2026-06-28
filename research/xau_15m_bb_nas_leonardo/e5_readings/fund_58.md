# Fund 58 — DEEP READING (XAU 15M MON+FORTE bottom)

**Date:** 2024-10-15 05:30 UTC (ASIA, off-killzone) · **Tier:** FORTE · **Block:** 2024-08-25→11-25 · **leg_atr 16.78 · power 4.6**
**Low bar (idx 3337):** O2639.38 H2643.06 L2638.10 C2640.80 v4933 rsi26.4 atr2.81 ema2645.82
**Outcome (causal, post-entry):** mfe12 6.25 ATR · mae12 0.79 ATR — clean monotone runner, almost no give-back.

---

## (a) THE ENTRY MECHANIC — where/when I actually enter

This is a **sweep + reclaim + NAS-LONG demand-trigger** bottom, entered on a *micro-HL confirmation*, NOT a CHoCH/EMA-reclaim entry (those come too late here).

Causal sequence (only info ≤ each bar):
1. **Bar 0 (05:30, the low):** a 12-bar grind-down from 2652 (02:30) terminates in a single climactic bar — v4933 (≈2× the preceding bars, the leg's volume peak), RSI 26.4 (the leg's RSI floor), range 4.96 (1.76 ATR). Its low **2638.10 undercuts the immediately-prior bar's low (2639.26 @05:15) by ~0.4 ATR — a shallow stop-run** — and **closes back ABOVE that swept level (C 2640.80 > 2639.26): reclaim WITHIN the bar.** Close-in-bar 0.54 (mid-upper). This is the absorption print. Aggressive entry = on the close of bar 0 (the sweep-reclaim bar itself), stop just below 2638.
2. **Bar +1 (05:45):** prints the **first higher-low (l 2640.31 > 2638.10)** AND a **NAS LONG fires at 2637.58** — the demand/algorithmic trigger lands exactly one bar after the low. This is my **primary, confirmed entry**: enter on bar +1 close (2641.94), the HL + NAS-LONG confluence confirms the sweep held. `first_higher_low_bar=1`, `nas_long_after=1`.
3. **Bars +2..+4:** monotone staircase up (closes 2644.1 → 2644.9 → 2647.2; lows climb every bar 2641.4 → 2642.5 → 2644.8 — no re-test of the low). **EMA21 reclaimed at bar +4 (06:30).** A patient entry on the EMA reclaim still captures ~5+ ATR of the leg.
4. **Bar +11 (08:15):** bullish CHoCH prints — this is *structural confirmation*, far too late to be the trigger (it's the let-run/add signal, not entry).

**Verdict on trigger:** the decisive, earliest causal trigger is the **shallow-sweep-of-prior-low + same-bar reclaim, confirmed by bar+1 micro-HL and a NAS-LONG**. Entry bar +1. Risk = below 2638.10 (sub-1 ATR; mae12 was only 0.79 ATR — the low was never revisited).

---

## (b) LENSES PRESENT / STRONG here

### Old E1 / HTF features that ARE firing
- **`swept_prior_low=1`** + **`sweep_depth_atr=3.25`** — swept, BUT note: the *structural* sweep of the immediate prior low was shallow (0.4 ATR); the 3.25 figure is depth vs a further-back reference. The reclaim-within-bar is the key.
- **`in_demand=1`, `dist_demand_atr=−0.02`, `demand_virgin=1`** — flushed into a FRESH/virgin 4H demand zone, sitting right on it.
- **`nas_long_after`** (entry_mechanics) + NAS-LONG @05:45 confirmed in RAW.
- **`choch_15m_after=1`** — structural confirmation (late).
- **`rsi_low=rsi_min8=26.4`** — washed 15M momentum (lens-relevant: see L5.3 below — 15M washed while HTF strong).
- **`vol_climax=2.55`** — single climactic volume bar AT the low (v4933).
- **`hd_trend=+1, hd_rsi=58.3, h4_trend=+1`** — daily and 4H both already bullish; this is a pullback-in-uptrend bottom, not a downtrend reversal.

### NEW-ANGLE lenses PRESENT/STRONG

**Angle 4 (Inter-bar Geometry) — STRONGEST fit:**
- **L1 `reclaim_low_monotone_k` = 4/4 (MAX):** l_atr 0.79→1.17→1.55→2.39 — the floor climbs every single bar, no-look-back launch. Textbook MON staircase.
- **L5 `close_progression_R2`:** c_atr 1.37→2.14→2.43→3.26→3.77→4.09 is a near-straight rising ramp — high R², one-directional control.
- **L8 `reclaim_dip_depth`:** shallow_retest — deepest post-thrust dip (bars 4-8) barely sags (mae12 0.79 ATR); the HL holds far above the low.
- **L9 `velocity_regime_flip` / L4 `flush_then_snap`:** down-velocity into the low was a grind, up-velocity off it is faster — hard up-flip; the V snaps.
- L6 `pivot_engulf_thrust`: bar+1 is green and closes above bar-0 high (2642.85>2643.06 ~ borderline); the thrust is steady rather than one giant engulf — present but moderate.

**Angle 5 (Cross-TF Momentum / Regime-Onset) — STRONG, the macro spine:**
- **L5.3 HTF-RSI Hook:** 15M RSI washed (26.4) WHILE **htf1_native.rsi=60.0 and hd_rsi=58.3** — the slower frames never broke; classic cross-TF momentum divergence. Strong fit.
- **L5.6 Multi-TF Demand Stack:** 15M flush lands ON 4H demand (`htf4_native.in_demand=1`) which sits under 1H also in_demand — nested value floor.
- L5.2 1H Room-Above: **PARTIAL/INVERTED** — here `htf1_native.in_demand=1` (1H still at its demand, not lifted off). So the "1H already reclaimed" half is NOT present; the strength comes from the daily/4H uptrend instead.
- L5.1 phase-lag (1H>4H disagreement): NOT the mechanism here — both h4 and hd trend are +1 (aligned UP). This is a **dip-in-uptrend**, not a regime-onset turn.

**Angle 3 (Time/Session) — STRONG textbook fit:**
- **L1 `asia_offpeak_flush`:** ASIA session, **05:30 UTC, killzone=0** — exactly the off-killzone Asia profile (the angle's headline enrichment 8.1× lift). Large climactic candle in thin liquidity.
- **L3 `time_since_session_open`:** late-Asia, a reaction to the prior session's excess; sweep-and-reverse in the quiet window.

**Angle 0 / Angle 1 (Order-flow / Liquidity Absorption) — MIXED:**
- **L4 `absorption_reload` (A0) / L7 `liquidity_grab_no_followthrough`:** the low bar is high-volume (v4933) closing in the upper half (closepos 0.54) AND swept the prior low + reclaimed within ≤2 bars → **absorption_reload + shallow-grab-fast-reclaim PRESENT.**
- **CAVEAT — anti-capitulation thesis is PARTIALLY VIOLATED here:** Angle 0/1/2 argue MON bottoms are *quiet* (low vol_climax ~1.23, RSI ~37, no climax). This fund is the **opposite of that fingerprint**: vol_climax 2.55 (high), rsi_low 26.4 (deeply oversold), a real climactic volume bar. So the "quiet absorption" lenses (A0-L2 quiet_climax, A2-L1 atr_decel, A2 vol-drain) would mostly NOT fire / fire against it. This bottom is a **climactic-flush-then-instant-reclaim** type, captured better by the *geometry* (A4) and *cross-TF* (A5) lenses than by the quiet-absorption family. Honest flag: it is a MON via a DIFFERENT route than the curated median.

---

## (c) WHAT IS DISTINCTIVE about this bottom

1. **It is a CLIMACTIC flush, not a quiet grind** — contradicts the dossier-median MON profile (which is calm/shallow). The leg is real (16.78 ATR) and the reclaim is pristine (monotone 4/4, mfe 6.25 / mae 0.79), so MON-ness here comes from **the cleanliness of the REACTION, not the calmness of the FLUSH.** A "quiet_climax" detector would MISS this fund — a cautionary data point against over-fitting the anti-capitulation thesis.
2. **The trigger is a textbook single-bar sweep+reclaim** (undercut prior low by 0.4 ATR, close back above, RSI 26.4 floor, volume peak) immediately followed by a **NAS-LONG one bar later** — exceptionally clean, time-aligned confluence.
3. **Off-killzone ASIA 05:30** — fits the strongest session lens (Angle 3 / Angle 1 killzone-polarity).
4. **No-look-back launch:** mae12 of just 0.79 ATR means a stop a hair under the low was never threatened — among the highest-quality risk profiles a bottom can offer.

---

## (d) MACRO / HTF CONTEXT

- **Daily: bullish & healthy** — `hd_trend=+1, hd_rsi=58.3, hd_slope_atr=2.09, hd_pos=0.47, dist_demand_atr 3.12 (above its demand, room).** Gold in an established daily uptrend (Oct-2024 leg).
- **4H: bullish** — `h4_trend=+1, h4_rsi=51.4, h4_slope_atr=1.0, h4_pos=0.6`; native 4H `in_demand=1, clean_sky 0.56` — pulled back INTO 4H demand with a fairly clean ceiling near-term.
- **1H: corrective/washed** — `h1_trend=0, h1_rsi=42.1, h1_pos=−0.1, h1_slope −0.51`; native 1H `in_demand=1, rsi 60.0`. The 1H is the frame that absorbed the dip (still at demand) while daily/4H momentum stayed up.
- **macro_bull=1, macro_bear=0.** **Read: a healthy pullback-in-uptrend** — daily/4H trend UP, a 15M Asia liquidity-flush into a fresh nested 4H+1H demand floor, swept and reclaimed with a NAS-LONG, launching a clean continuation leg. The leg has fuel (uptrend + virgin demand) and a target overhead. This is a *continuation-of-uptrend* bottom, NOT a downtrend reversal — which is why the geometry (clean reclaim) and HTF-trend lenses fire while the regime-onset / phase-lag lenses (which need a slow-frame turn) do not.
