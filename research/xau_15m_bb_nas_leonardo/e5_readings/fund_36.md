# Fund 36 — DEEP READING (XAU 15M MON+FORTE bottom)

**Block:** 2024-08-25 collection · **Bottom bar:** 2024-10-25 09:30 (UTC stamp t=1729848600)
**Tier:** FORTE · **power_score 3.5** · **leg_atr 24.23** (large clean leg) · year 2024
**Session:** LONDON · **killzone = 1**

---

## TL;DR

This is a **deep-flush LONDON-killzone reversal that grinds, sweeps hard, then locks into a no-look-back staircase** — the OPPOSITE archetype to the "quiet Asia off-killzone" MON+FORTE template the angle agents grounded on. It still earns FORTE because the absorption shows up in *trajectory* (grindy down-leg eff 0.17 + monotone reclaim) and in *HTF context* (Daily strongly bullish, fresh virgin 4H demand defended). The cleanest entry is a **demand-zone retest + micro higher-low confirmation a few bars after the flush low**, not at the flush bar itself.

---

## (a) THE ENTRY MECHANIC — where/when I would actually enter

`reaction_seq` (bars +1..+12 post-low, in ATR off the low) tells the whole story:

| bar | l_atr | c_atr | green | read |
|---|---|---|---|---|
| 1 | 0.89 | 1.41 | ✓ | thrust off low (+1.41 ATR close) — engulf bar |
| 2 | 0.50 | 0.83 | ✗ | gives back — first retest of demand |
| 3 | **0.06** | 0.33 | ✗ | **deep retest, comes back to within 0.06 ATR of the low** |
| 4 | 0.24 | 1.36 | ✓ | rejection of the retest — higher low forms (0.24 > 0.06) |
| 5 | 0.98 | 1.74 | ✓ | no-look-back begins |
| 6 | 1.37 | 1.87 | ✓ | floor keeps climbing |
| 7 | 1.79 | 2.70 | ✓ | EMA21 reclaimed (reclaim_ema_bars=7) |
| 8 | 2.72 | 3.78 | ✓ | displacement / leg confirmed |
| 9–12 | 2.06→2.76 | 2.36→3.84 | mostly ✓ | runs to mfe12 4.10 ATR |

The bar-1 thrust is a trap: bars 2–3 retest almost all the way back to the low (l_atr 0.06). A naive "enter on the first green bar" entry sits through a full retest. **The real, defensible entry is at bar 4** — the bar that *rejects the retest and prints the confirmed higher low* (l_atr 0.24 > bar-3's 0.06). That is the **retest-of-demand-holds + micro higher-low** trigger. `entry_mechanics` confirms: `first_higher_low_bar = 1` (HL structure available early), `swept_prior_low = 1` (the low was a sweep), and critically **`mae12_atr = 0.06`** — after the bottom, the maximum adverse excursion over 12 bars is essentially zero. The low is never meaningfully revisited, so an entry on the bar-4 HL-confirmation captures ~3.5 ATR of the 4.10 ATR mfe with near-zero heat.

Entry trigger classification: **sweep + reclaim → deep retest holds → confirmed higher-low at bar 4** (a demand-retest entry). NOT a CHoCH entry: `choch_15m_after = 0` and `nas_long_after = 0` — no post-low structure-break or NAS print confirms it, so the trade rests on demand-defense + HL, not on a CHoCH/NAS hand-off.

---

## (b) Which lenses are PRESENT / STRONG here

### STRONG / PRESENT
- **Angle 4 L1 `reclaim_low_monotone_k` (climbing floor):** PRESENT from bar 3 onward. Floor: 0.06→0.24→0.98→1.37→1.79→2.72 — a clean 5-bar monotone-low run after the retest. This is the signature that earns the FORTE label.
- **Angle 4 L8 `reclaim_dip_depth` (shallow-retest-holds):** the bar-2/3 dip retraces ~deep then the bar-4 HL holds; post-HL the dip never returns → `shallow_retest` confirmed by mae12 0.06.
- **Angle 4 L5 `close_progression_R2` (clean ramp):** c_atr 1.41→…→3.84 is a near-monotone rising ramp (only bar-3 dip + bar-9 pause) — high R² reclaim.
- **Angle 4 L9 `velocity_regime_flip` / L4 `flush_then_snap`:** steep down-leg (drop20_atr 5.16) inverts into a fast up-leg (c_atr 3.78 by bar 8) — hard V flip.
- **Angle 0 L1 `effort_vs_result_failure` / downleg absorption:** `downleg_eff = 0.17` (extremely grindy — far below MON median 0.28 and control 0.39). High effort, poor downward result = textbook absorption. **This is the dominant absorption tell here.**
- **Angle 0 L7 `liquidity_grab_no_followthrough`:** `swept_prior_low = 1`, sweep taken out then reclaimed; the grab does not extend (mae12 0.06).
- **Angle 1 L6 `discount-not-breakdown`:** borderline — `dealing_range_pos = -1.051` is *just past* the −1 range-break line. Reads as a marginal range-break flush rather than a clean in-discount accumulation (a control-leaning value here).
- **Angle 5 L5.6 `multi-TF demand stack`:** `in_demand=1` AND `htf4_native.in_demand=1` (15M flush lands inside a 4H demand), `demand_virgin=1`, `demand_fresh=0` — a virgin (never-tested) 4H demand floor. `htf4_native.clean_sky_atr = 0.62` is thin overhead on 4H though, capping run-room (a mixed tell).
- **Angle 5 / HTF regime — DAILY BULL BACKBONE:** `hd_trend=+1`, `hd_pos=0.76`, `hd_slope_atr=+10.24`, `hd_rsi=68.2`. The Daily is in a strong uptrend at value-high. The 15M flush is a pullback within a powerful Daily bull — the highest-conviction context lens for this fund.
- **Angle 0 / sell-bubble fade:** `sell_bub_w=6`, `buy_bub_w=1`, `sell_decel=-6` (sell-bubble effort decelerating into the low) + `nas_long_16=1` (a NAS LONG cluster present). Demand footprint emerging as sell pressure fades.
- **rsi_bull / momentum:** `rsi_low=30.4`, `rsi_min8=29.4`, `rsi_head=0.99` (RSI at its washed low at the print, no held-above-floor divergence) — washed but not extreme; `rsi_bull_div=0`.

### ABSENT / WEAK / CONTRARY (this is where fund 36 breaks the template)
- **Angle 1/3 off-killzone & Asia thesis — CONTRARY.** This bottom is `session=LONDON`, `killzone=1`. It directly violates the "strong bottoms form off-killzone in Asia" grounding. Fund 36 is the counter-example: a London-killzone reversal that still ran. Whatever edge exists here is NOT the quiet-timing lens.
- **Angle 0/2 quiet-climax / shallow-sweep thesis — CONTRARY.** `sweep_depth_atr=2.64` (DEEP, > control median 2.34), `drop20_atr=5.16` (deep), `vol_climax=1.32`, `atr_regime=1.27` (EXPANDED vol, not the calm 0.94–0.99 MON regime), `atr_compression_pre=0.84` (low). This is a *climactic / expanded-vol* low, the control-leaning archetype — yet it reversed. So the quiet-absorption lenses do NOT explain this fund.
- **Angle 5 L5.1 phase-lag / 1H-leads-4H — CONTRARY.** Here `h1_trend=-1` AND `h4_trend=+1` — the FAST frame (1H) is still bearish while the 4H is already bullish. That is the *opposite* of the L5.1 "1H leads 4H up" template. `htf1_native.trend=+1` (native resample) disagrees with the E1 `h1_trend=-1`; the E1 1H is still down. The real HTF backbone is the 4H+Daily uptrend, not a 1H-leads turn.
- **Angle 5 L5.2 1H room-above — WEAK.** E1 `h1_pos=0.06`, `h1_dist=-3.12`, `h1_rsi=33.6` (1H pinned low, oversold) — the 1H is washed, NOT lifted off. htf1_native says dist_demand 2.2 / rsi 67.5 but that is the coarser native resample; the finer E1 1H is still at the floor.
- **CHoCH / NAS-after confirmation — ABSENT.** `choch_15m_after=0`, `nas_long_after=0`. No structure-break or NAS confirmation after the low.
- **clean_sky overhead — MIXED/CAPPED.** `n_supply_overhead=39`, `dist_supply_atr=-0.06` (price is right at overhead supply), `htf4_native.clean_sky_atr=0.62` — overhead is congested. The leg ran *despite* a capped sky, pointing to the Daily-bull draw as the fuel.

---

## (c) What is DISTINCTIVE about this bottom

1. **It is the anti-template MON+FORTE.** It violates the three headline angle theses simultaneously — off-killzone (it's London/KZ), quiet-shallow-sweep (it's a deep 2.64-ATR sweep in expanded 1.27 vol), and 1H-leads-4H (here 1H is still down, 4H already up). It teaches that the curated "quiet Asia" signature is *one* path to FORTE, not the only one.
2. **The edge lives in the DAILY BULL + virgin 4H demand, not in the microstructure of the low.** `hd_slope +10.24`, `hd_rsi 68.2`, `hd_pos 0.76` + `demand_virgin=1` inside `htf4 in_demand=1`. This is a **buy-the-dip in a roaring Daily uptrend onto a fresh higher-TF demand** — a fundamentally different (and arguably more robust) bottom type than a counter-trend exhaustion reversal.
3. **The grindy down-leg (`downleg_eff 0.17`, `consec_down 0`) is the only "absorption" tell that survives** — the descent was inefficient/two-sided even though it was deep and in expanded vol. Effort-vs-result divergence (Angle 0 L1) is the microstructure lens that *does* apply here.
4. **Near-zero post-entry heat (`mae12 0.06`)** with a deep retest first (bar 3 back to l_atr 0.06) — the demand floor was tested to the tick and held, which is *why* the retest-HL entry at bar 4 is so clean.
5. **dealing_range_pos −1.05** = a marginal range-break low (slight overshoot of the discount band) that immediately reclaimed — a stop-run below the range that failed, consistent with the deep-sweep-then-reclaim read.

---

## (d) MACRO / HTF context (as-of entry)

- **Daily (hd):** strong uptrend — trend +1, pos 0.76 (upper range), slope +10.24 ATR, RSI 68.2. Bull backbone fully intact; the 15M low is a pullback inside it. **Primary justification for the long.**
- **4H (h4 / htf4_native):** trend +1 (E1) / −1 (native, conflicting resample), pos 0.24, RSI 50.3, **in a virgin (untested) demand zone** the price has flushed into (`in_demand=1`, `demand_virgin=1`, `dist_demand_atr ≈ -0.25`). 4H clean_sky thin (0.62) = some overhead resistance, but a fresh demand floor to bounce from.
- **1H (h1):** still bearish/washed — trend −1, pos 0.06, RSI 33.6, slope −0.77, dist −3.12. The fast frame has NOT turned at entry; this is a dip *into* the higher-TF bull, caught before the 1H confirmed. (Adds risk vs the L5.1 template but the 4H/Daily carry it.)
- **Timing:** London killzone, 09:30 — a London-session sweep of the prior low that reversed. Standard liquidity-grab-at-session-open mechanic (Angle 3 L3/L4 in spirit), just inside the killzone rather than the off-peak Asia window.
- **Order-flow context:** sell-bubble effort fading (`sell_decel -6`), a lone buy bubble (`buy_bub_w 1`) and a NAS LONG cluster (`nas_long_16 1`) emerging at the low — demand footprint appearing as supply decelerates.

**Net:** a **Daily-bull buy-the-dip onto fresh 4H demand**, entered on the **demand-retest + bar-4 higher-low** after a deep London sweep, carried by HTF trend rather than by quiet-absorption microstructure. Honest caveat: the curated-set lifts (Angles 0/1/3/5) are calibration on 61/144, and this fund is an *exception* to most of them — its causal story is HTF-trend continuation, so it should be read as a different sub-type, not as evidence for the quiet-Asia template.
