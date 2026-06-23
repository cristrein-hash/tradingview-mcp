# READER DOSSIER — Cluster 1 (RAW-CLEAN, CAUSAL POS-FIX) — FRESH BLIND READ

> Source: `reading_packet_RAW_CLEAN.md` (commit 1267c8d, as-of join, 19/19 causal+exato, no look-ahead).
> This is a SETUP read only. No outcome, no R, no TAKE/SKIP, no score. Volume VA (LuxAlgo POC/VAL/VAH)
> is UNKNOWN_BLOCKED throughout; the only acceptance signal is a TIME-based TPO proxy treated as WEAK context.
> Reasoning is multi-factorial: regime x form/trajectory x supply-geometry x indicators x volume-effort.

---

## METHOD NOTE — how the CAUSAL backbone shaped the read

Because the anchor window ends exactly at the entry bar (no future bars), I cannot let "what the move became"
leak into the read. So the backbone I trust most is the structural triad that is fully formed AT entry:
**(regime cascade + macro_broken) x (supply geometry: sup_cat / dist_supply / dist_demand / clean_sky) x
(the trajectory shape of the last 5 RAW bars)**. The volume effort (entry_up / last6_up) is a real per-bar
ratio and I weight it as corroboration, but the LuxAlgo VOLUME value area is BLOCKED — so I cannot tell whether
price sits cheap-below-value or rich-above-value in *volume* terms. Where that distinction is the crux, I flag it.

The single most important causal split in this cluster is **macro_broken / cascade sign**:
- macro_broken=True + negative cascade => the move into entry is a counter-trend event inside a broken/bear macro
  (4918, 1661, 5701). These are "is this a real change of character at a level, or a pullback that re-prices into supply?"
- macro_broken=False + positive cascade (+1..+3) => the move into entry is *with* an intact/bull macro
  (6887, 7426, 8878, 8923, 8940, 4926). These are "is this fuel/continuation, a wall rejection, or a late/extended chase?"

---

## EPISODE READS

### 4918 — 2023-03-08 — washout-with-change-of-character (compressed AT demand)
- Backbone: weekly +0.54 but cascade=-1, macro_broken=True, v3=TRANSITION. So a *transition* inside a recently
  broken macro — not a clean bull, not a deep bear. Price is **sitting on demand (dist_demand=0.02ATR)** with
  SUPPLY_FAR (4.01ATR) and clean_sky above. Form: four tiny-range coiling bars, last bar a doji
  (H=L=C=1814.12) — volatility collapse right at the demand floor. RSI=35 with **Regular Bullish divergence**,
  entry_up=0.919 (strong up-effort on the entry bar) against a weak last6_up=0.431 (prior bars sold). The
  bearish surface (NAS last flip to SHORT, bubbles sell_mL=6) is the look-alike trap signature, but it is
  contradicted by the *location* (on demand, not into supply) and the divergence.
- NATURE: washout/compression at demand with an emerging change-of-character — the bearish indicators describe
  the move that GOT it here, while geometry + RSI div + collapsing range describe absorption at the floor.
- EXPECTATION (if read right): hold/expand up off the demand shelf with the clean-sky runway above; the doji
  resolves upward and the 4.01ATR to supply is the room. **Falsifier:** a decisive close back below the demand
  shelf / the coil that breaks down instead of up (then it is just a pause in a bear leg, not a CHoCH bottom).
- Confidence: **med**. BLOCKED-limited: HIGH — without the volume VA I can't confirm price is cheap-below-value
  (which would harden the absorption read). The entry_up vs last6_up split is my best volume proxy and it is suggestive, not conclusive.

### 1661 — 2021-01-28 — bear-pullback-trap (into a supply wall, no buying effort)
- Backbone: weekly -0.22, cascade=-2, v3=BEAR, macro_broken=True. **SUPPLY_NEAR with dist_supply=0.27ATR** — price
  is pressed right under a wall, demand far away (2.74ATR). Form: bars rolling over off the highs (1849 high ->
  lower closes). NAS SHORT x4. The single contrary tell is bubbles buy_mL=6, but **entry_up=0.111 / last6_up=0.089**
  is the lowest up-effort in the entire cluster — essentially no buyers. close_fidelity=False (feed warning) so the
  exact price is slightly soft, but the structure is unambiguous.
- NATURE: a bounce/pullback inside a bear that stalls directly beneath near supply with no buying effort behind it —
  classic supply-as-wall / bear-pullback-trap.
- EXPECTATION (if read right): rejection at/under the 0.27ATR supply and resumption lower; the buy bubbles fail.
  **Falsifier:** a clean acceptance THROUGH the near supply on rising up-effort (entry_up climbing), which would
  flip it to a reclaim rather than a trap.
- Confidence: **high** (geometry + effort agree, regime agrees). BLOCKED-limited: LOW — the read does not hinge on
  the volume VA; the near-supply distance carries it.

### 5701 — 2023-09-07 — supply-as-wall (counter-trend push in deep bear)
- Backbone: weekly -0.22, cascade=-3 (deepest bear in the cluster), v3=BEAR, macro_broken=True. SUPPLY_FAR (3.06ATR),
  clean_sky=True, demand 0.7ATR below. Form: a gentle grind up with a strong last bar (C1925.82 closing near
  the high). entry_up=1.0 (full up-effort) but **bubbles sell_mL=10 — the heaviest sell cluster in the set**, NAS
  SHORT x5 (unanimous bearish), RSI 49 with no divergence.
- NATURE: an effortful counter-trend bounce inside a deep, unanimous bear, advancing toward heavy overhead sell
  supply. The strong entry bar is real but it is climbing into the heaviest distribution in the cluster — supply-as-wall.
- EXPECTATION (if read right): the bounce runs into the sell cluster and stalls before the 3.06ATR supply matters;
  the deep cascade reasserts. **Falsifier:** continued acceptance up with the sell bubbles failing to cap (a true
  trend reversal off the cascade low), which the unanimous NAS-SHORT + no-divergence argues against.
- Confidence: **med-high**. BLOCKED-limited: MED — TPO says ACCEPTED_ABOVE_VALUE but that is TIME not VOLUME; the
  real question (is the bounce being volume-accepted or just time-grinding) needs the blocked VA.

### 6887 — 2024-06-14 — supply-as-fuel (bull-transition breakout, clean runway)
- Backbone: weekly +0.90, cascade=+1, v3=TRANSITION, macro intact (macro_broken=False). SUPPLY_FAR (3.17ATR),
  clean_sky=True, demand 1.98ATR below. Form: an impulsive expansion leg — four green bodies 2306 -> 2334, real
  range expansion. NAS flips SHORT->LONG, entry_up=1.0, last6_up=0.578, ACCEPTED_ABOVE_VALUE. bubbles buy_mL=3,
  RSI 59 (room left, not overbought).
- NATURE: a bull-transition breakout with a clean 3.17ATR runway and no overhead wall — supply is far enough to be
  fuel/room rather than a cap; effort and structure both point up, RSI not yet extended.
- EXPECTATION (if read right): continuation/expansion into the clean sky; the impulse holds its breakout.
  **Falsifier:** an immediate failure back into the demand 1.98ATR below (impulse was a blow-off, not a breakout).
- Confidence: **med-high**. BLOCKED-limited: LOW-MED — clean sky + intact macro carry it; volume VA would only
  refine how extended the entry bar already is.

### 7426 — 2024-10-18 — supply-as-fuel BUT extended (bull, clean sky, overbought)
- Backbone: weekly +0.85, cascade=+3, v3=BULL, macro intact. **CLEAN_SKY, no overhead at all**, demand 2.6ATR below.
  Form: a steady stair-step grind up (controlled, not vertical). bubbles buy_mL=13 (large buy cluster), entry_up=0.957,
  last6_up=0.745 (sustained buying). The caution flag is **RSI=77.26 — clearly overbought**.
- NATURE: a strong, orderly bull with a genuinely clean runway (no wall) — supply-as-fuel — but entered while
  momentum is already stretched. Nature is healthy-trend; the risk is timing-into-extension, not structure.
- EXPECTATION (if read right): trend continues / the stair-step persists because there is no overhead, though a
  shallow shake of the overbought is plausible first. **Falsifier:** a sharp mean-reversion break of the stair
  structure on falling up-effort (the overbought resolved by price, not by time).
- Confidence: **med**. BLOCKED-limited: MED — overbought + clean sky is a known tension; the volume VA would tell me
  if price is accepted-above-value (sustainable) or rich-above-value (exhaustion). Blocked, so I hold at med.

### 8878 — 2025-09-28 — supply-as-wall / timing-bad-despite-bull-thesis (rejection at near supply)
- Backbone: weekly +0.58, cascade=+3, v3=BULL, macro intact — so the macro thesis is bull. BUT **SUPPLY_NEAR
  dist_supply=0.59ATR** (a wall right overhead) and demand 0.94ATR below (boxed in). Form: rally then the **last full
  bar reverses hard** — O3783.05 H3783.24 L3760.63 C3761.24 (a large upper-wick rejection giving back the whole
  bar), and the entry bar opens lower at 3760.57. NAS SHORT x5, bubbles buy_mL=4, RSI 65. **entry_up=None (BLOCKED)** —
  I lose the single most diagnostic field here.
- NATURE: bull macro but entered into a near-supply wall on a clear rollover/rejection bar — supply-as-wall inside a
  bull, i.e. right thesis / wrong location-and-timing. The structure at the entry bar is a give-back, not a thrust.
- EXPECTATION (if read right): stall/pullback off the 0.59ATR supply before any continuation; the bull thesis needs
  to absorb/reclaim that wall first. **Falsifier:** an immediate reclaim that closes back above the rejected high on
  renewed up-effort (the rollover bar was a liquidity grab, not distribution).
- Confidence: **med** (would be high but entry_up is blocked exactly where it matters). BLOCKED-limited: **HIGH** —
  entry_up=None removes the effort read on the decisive bar; volume VA also blocked. Most effort-blind episode of the set.

### 8923 — 2025-10-08 — late/vertical-climax chase (clean sky, extreme extension)
- Backbone: weekly +0.85, cascade=+3, v3=BULL, macro intact. CLEAN_SKY, no overhead, demand far (3.7ATR). Form:
  an **explosive near-vertical leg** 3984 -> 4049 with very wide green bars. bubbles buy_mL=18 (the most extreme buy
  cluster in the cluster), entry_up=1.0, last6_up=0.884, **RSI=82.36 (extreme overbought)**, ACCEPTED_ABOVE_VALUE.
- NATURE: a powerful trend with clean sky, but entered at the top of a vertical climax with the most extreme
  momentum/RSI in the set — supply-as-fuel by geometry, but the bar trajectory is a parabolic chase. Nature is
  strong-but-late; clean sky says "room," extreme RSI + verticality says "stretched."
- EXPECTATION (if read right): either continuation (clean sky, no wall) or a sharp snap-back of the vertical leg —
  the climax shape makes both live, so the honest read is "high-energy, two-sided at this exact bar."
  **Falsifier of the continuation lean:** an outside-down reversal bar that breaks the vertical, signalling the
  climax topped at entry.
- Confidence: **low-med** (the verticality is genuinely ambiguous at the entry bar). BLOCKED-limited: **HIGH** —
  this is the case where rich-above-value vs accepted-above-value (volume VA) is the whole question, and it is BLOCKED.
  TPO acceptance is TIME-only and cannot resolve a parabola.

### 8940 — 2025-10-13 — supply-as-fuel continuation (bull, clean sky, less extended)
- Backbone: weekly +1.06 (steepest weekly in the set), cascade=+3, v3=BULL, macro intact. CLEAN_SKY, no overhead,
  demand 2.44ATR. Form: strong expansion 3980 -> 4063 with wide ranges but **not the vertical parabola of 8923**;
  it pulls and re-expands (more two-way inside the up-leg). bubbles buy_mL=13, entry_up=1.0, last6_up=0.711,
  **RSI=66.32 (strong, NOT extreme)** — notably cooler than 8923's 82.
- NATURE: a strong bull continuation into clean sky with momentum that is firm but not exhausted — the healthiest of
  the late-2025 bull trio because RSI is reset relative to 8923 while the runway is still clean. Supply-as-fuel.
- EXPECTATION (if read right): continuation/expansion holds; the cooler RSI gives room the climax case lacks.
  **Falsifier:** failure back through the prior expansion candle's body on declining effort.
- Confidence: **med-high**. BLOCKED-limited: MED — clean sky + non-extreme RSI make this less VA-dependent than 8923/7426.

### 4926 — 2023-03-09 — supply-as-wall / honest-residual mid-range (post-impulse pullback under blocks)
- Backbone: weekly +0.54 (same week as 4918), cascade=+1, v3=TRANSITION, **macro_broken=False**. **SUPPLY_BLOCKS**
  (sup_cat distinct from the others), clean_sky=False, has_overhead, dist_supply=1.61ATR / dist_demand=1.92ATR — i.e.
  **boxed roughly in the middle of a range** with supply blocks overhead. Form: an impulsive rally 1813 -> 1834 and
  then the **entry bar gives back** (H1834.97 L1828.96 C1830.74 — closes well off the high, a rejection candle).
  NAS flips LONG->SHORT, bubbles sell_mL=6, RSI=52.92 (neutral, no divergence), entry_up=1.0, last6_up=0.778.
- NATURE: a mid-range, post-impulse pullback into overhead supply blocks within an intact (not broken) transition —
  no fresh CHoCH-at-a-level edge, no oversold/divergence, no clean runway. Supply-as-wall / honest-residual: the
  structure neither absorbs at a floor nor breaks into clean sky; it stalls under blocks in the middle of value.
- EXPECTATION (if read right): chop/rejection under the 1.61ATR supply blocks; no decisive directional resolution
  off this bar — a range/residual, not an edge. **Falsifier:** a clean break-and-accept ABOVE the supply blocks
  (turns it into a breakout) OR a flush back to the 1.92ATR demand that sets a fresh lower edge.
- Confidence: **med**. BLOCKED-limited: MED — SUPPLY_BLOCKS + mid-range geometry carry the "no-edge/wall" read; volume
  VA would tell me whether price is being accepted in the middle (range) or rejected (turning), which I can't see.

---

## 4. NEAR-TWIN CONTRAST — 4918 vs 4926 (same week, Mar-2023)

**Verdict: OPPOSITE nature.** Same weekly slope (0.54) and same calendar week is the surface look-alike; the CAUSAL
backbone separates them cleanly:

| field | 4918 (Mar-08) | 4926 (Mar-09) | implication |
|---|---|---|---|
| cascade / macro | **-1, macro_broken=TRUE** (transition DOWN inside broken macro) | **+1, macro_broken=FALSE** (transition UP, macro intact) | opposite directional context |
| supply geometry | SUPPLY_FAR 4.01ATR, **clean_sky=True** | **SUPPLY_BLOCKS** 1.61ATR, clean_sky=False, has_overhead | runway vs wall |
| location vs demand | **ON demand (0.02ATR)** — at the floor | mid-range (1.92ATR away) — in the middle | edge-at-level vs no-edge |
| form/trajectory | **coil/volatility-collapse doji** at the shelf | **post-impulse give-back** rejection under blocks |compression-at-floor vs rejection-mid-range |
| RSI | **35 + Regular Bullish divergence** | 52.9 neutral, **no divergence** | oversold-turn vs neutral-residual |
| effort split | entry_up 0.919 > last6 0.431 (buyers stepping in after selling) | entry_up 1.0, last6 0.778 (already-elevated, then rejected) | absorption vs exhaustion-into-wall |

4918 reads as **washout/change-of-character compressed on demand with clean sky and a bullish divergence**; 4926 reads
as a **mid-range post-impulse pullback stalling under supply blocks with neutral momentum and no edge**. The shared
bearish indicator surface (NAS flipping to SHORT, sell bubbles in both) is exactly the *look-alike trap* — it is the
same surface over two structurally opposite setups. The discriminator is location-on-demand + clean_sky + RSI
divergence (4918) versus SUPPLY_BLOCKS + mid-range + neutral RSI (4926). **The causal fields make them OPPOSITE.**

---

## 5. STRUCTURAL CONTINUATION (3b) RELATIONSHIPS

- **8878 -> 8923 -> 8940 (late-Sep to mid-Oct 2025):** a single bull-leg sequence. 8878 is the boxed near-supply
  rollover *inside* the up-leg; 8923 is the subsequent vertical climax extension of that same leg (RSI 82); 8940 is
  the cooler continuation (RSI 66) after the climax re-bases. Read as one trending leg sampled at three phases —
  wall-pause -> climax -> reset-continuation. The 3b relationship matters: 8940's cooler RSI is only meaningful
  *relative to* 8923's extreme, i.e. the leg shed momentum and re-loaded.
- **4918 -> 4926 (Mar-08 -> Mar-09 2023):** consecutive but NOT a clean continuation — the cascade sign flips
  (-1 then +1) and macro_broken flips (True then False). So if 4918 is a floor change-of-character, 4926 is the
  pullback *after* an initial leg up off it, now stalling under supply blocks mid-range. Sequential, but phase-shifted
  (bottom-formation bar vs first-pullback-into-wall bar), which is precisely why their natures diverge.
- **6887 / 7426** (2024 bull) and **5701** (2023 bear bounce) are standalone within this cluster — no adjacent twin
  in the packet; each read on its own backbone.

---

## 6. HOW THE CAUSAL (NO LOOK-AHEAD) BACKBONE SHAPED THE READ

The anchor ending at the entry bar forced me to read **trajectory and location**, never destination. Two places it
changed the call: (a) 8923's vertical bar — with look-ahead I might have labelled it a climax-top or a runner; causally
I can only say "extreme energy, two-sided at this exact bar" and lean on clean-sky vs RSI-82 tension. (b) 4918 — the
bearish NAS/bubble surface would, on outcome, tempt a trap label; causally the divergence + on-demand location +
volatility-collapse doji describe an absorption setup, so I read change-of-character, not trap. The blocked VOLUME value
area is the recurring ceiling on confidence: in every "is this accepted-above-value or rich/exhausted" case (7426, 8923,
5701) and every "is this cheap-below-value absorption" case (4918), the decisive field is BLOCKED and the TPO proxy is
TIME-only, so I capped those at med / low-med rather than overstating.
