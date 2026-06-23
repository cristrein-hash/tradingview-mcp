# PHASE 3 AUDIT — FROZEN BLIND READING vs REALIZED OUTCOME (Cluster 2 Error-Only)

> Fresh independent auditor. The reader NEVER saw any of this. SANITY_PROBE: per-episode
> diagnostic, NOT a hit-rate / gate / rule. Brutally honest reconciliation.
> Outcome guide: mfe_R uncapped; runner_flag/monster_flag = ran; stop_before_2R=1 = stopped early.

---

## OUTCOME TABLE (the 6 judged episodes)

| Ep | Frozen classification | mfe_R | capped exit | runner | monster | stop<2R | reality |
|----|----------------------|------:|-------------|:------:|:-------:|:-------:|---------|
| 5627 | **SUPPLY_WALL** | **5.96** | WIN_HELD (+1.96R) | 1 | 0 | 0 | **RAN** |
| 1522 | VA_ACCEPTANCE_EXPANSION | 5.65 | WIN_BE (+0.9R) | 1 | 0 | 0 | RAN (mod) |
| 3825 | OVERFADE_RISK | 0.96 | STOP_LOSS (−1.1R) | 0 | 0 | 1 | stopped |
| 3929 | SUPPLY_CONSUMPTION | 0.05 | STOP_LOSS (−1.1R) | 0 | 0 | 1 | stopped |
| 3949 | **OVERFADE_RISK** | **6.62** | WIN_HELD (+3.54R) | 1 | 0 | 0 | **RAN** |
| 4401 | **INSUFFICIENT (lean SUPPLY_WALL)** | **10.31** | WIN_HELD (+2.76R) | 1 | **1** | 0 | **RAN (monster)** |

**Scoreboard:** 4 of 6 episodes RAN (5627, 1522, 3949, 4401). Only 2 stopped (3825, 3929).
The reading called 3 of the 4 runners as wall / overfade / lean-wall. That is the headline.

---

## PER-EPISODE AUDIT

### 5627 — frozen SUPPLY_WALL → mfe 5.96R, WIN_HELD +1.96R, runner. **REFUTED_LENS.**
The reader's hardest-failing leg was floor geometry: "demand floor 10.57ATR away (absent)... lifts get
absorbed because there is no floor beneath to convert pressure into a base." Outcome: price did NOT get
sold back into the block. mae_R 0.14 (it barely went against entry), hit2/3/5 all True, ran to ~+6R,
held. dnMove over next 40b = −1.30 only; upMove +51. The "rejection wick re-testing POC from above"
read as terminal distribution was, in realized path, a shakeout before continuation. **The floor-geometry
variable (demand-floor absent ⇒ wall) is REFUTED on 5627.** Absent mapped demand did NOT mean no floor —
price built its own and ran. The 15-sell/0-buy bubble "distribution wall" likewise did not cap it.

### 1522 — frozen VA_ACCEPTANCE_EXPANSION → mfe 5.65R, WIN_BE +0.9R, runner. **CONFIRMED_EXISTING_LENS (directionally), with a sting.**
The one clean PASS of the triad. It did run (runner_bucket R5_10, hit2/3/5 True). Directionally the
absorption reading was CORRECT — value did develop up off the floor. BUT note the realized texture: mae_R
1.30, mae_before_mfe 0.54, time_to_2R = 29 bars. It took a deep heat (−1.3R) and a long time (29 bars to
2R) before paying — capped exit was only WIN_BE +0.9R because the late, drawn-out follow-through interacts
with the BE/time machinery. So the triad's single clean pass is **confirmed as a real runner**, but it was
the SLOWEST and most drawn-down of the four runners. The triad's "clean fuel" episode was not the cleanest
*outcome* in the set — 5627 (0.14 mae, 2R in 5 bars) and 4401 (monster) both behaved better while being
condemned. The lens is confirmed for 1522 but it does NOT rank the runners correctly.

### 3825 — frozen OVERFADE_RISK → mfe 0.96R, STOP_LOSS −1.1R, stopped. **CONFIRMED_EXISTING_LENS.**
Genuine fade. Never reached 2R, stopped early, dnMove −17.87/−50.29. The reader honestly flagged this as
the genuinely ambiguous coil (silent bubbles, two walls <1ATR, faded thrust) and leaned bear-of-balance.
Outcome vindicates the lean. This is the one episode where the reading and the outcome cleanly agree on a
loser. No new variable; the faded-thrust / overhead-cap read held.

### 3929 — frozen SUPPLY_CONSUMPTION → mfe 0.05R, STOP_LOSS −1.1R, stopped. **CONFIRMED_EXISTING_LENS.**
The "real effort, mislocated — rallying from below POC into an overhead block, effort consumed not based"
read is VINDICATED. mfe only 0.05R (it never even ran 0.1R), dnMove −13.67/−38.09. The rising staircase WAS
short-covering into supply, exactly as adjudicated. This is the cleanest correct condemnation in the cluster.
The location-of-effort distinction (effort below POC into a ceiling vs effort building a floor) is real and
held against outcome. No new variable.

### 3949 — frozen OVERFADE_RISK ("extended above value, floorless, rubber-band") → mfe 6.62R, WIN_HELD +3.54R, runner. **REFUTED_LENS.**
The reader said: "a rubber-band stretch above value with nothing beneath; if it rolls there is no mapped
demand to catch it — over-extension, not supported acceptance." Outcome: it did NOT roll. It built a NEW
value shelf and ran to +6.6R (the reader's own falsifier — "builds a NEW value shelf at/above VAH creating
a floor where None existed" — is exactly what happened). mae_R 0.5, dnMove −5.37 over 10b. **The
location/floorless-extension variable (dist_poc +2.83ATR, demand=None ⇒ overfade) is REFUTED on 3949.**
ACCEPTING_ABOVE_VALUE was acceptance, not exhaustion. Distance-above-POC over-condemned a runner — this is
the dist_poc failure mode from Cluster 1 reappearing, only mirrored (extended-above instead of at-POC).

### 4401 — frozen INSUFFICIENT / lean SUPPLY_WALL → mfe 10.31R, WIN_HELD +2.76R, runner, **MONSTER.** **REFUTED_LENS (the lean was wrong; the INSUFFICIENT hedge saved it).**
The single biggest miss. The reader leaned SUPPLY_WALL (11 sell/0 buy, above-value markup into a block, NAS
SHORT-flip at the top) but — crucially — refused to commit, parking it at INSUFFICIENT on data-fidelity
warnings. Outcome: monster_flag=1, mfe 10.31R, hit2/3/5/8/10 all True, mae 0.38, time_to_2R 4 bars, clean
hold. **The wall lean was REFUTED.** The honest "read SOFTER / the close demand floor (0.87) is the honest
hedge" instinct was the correct one and it pointed at the right answer — the 0.87 floor held and the markup
into the block was NOT capped, it broke through. The fidelity-INSUFFICIENT refusal-to-condemn is the part of
the reading that survives; the directional wall lean does not.

---

## DOES THE FLOOR-BACKED-ABSORPTION TRIAD HOLD, OR OVER-CONDEMN RUNNERS?

**It OVER-CONDEMNS runners. Decisively — same failure mode as Cluster 1's dist_poc.**

The triad classified exactly ONE episode (1522) as fuel/PASS and condemned the other five as
wall/consumed/overfade/insufficient. Outcome: of those five "condemned" episodes, **THREE RAN**
(5627 +5.96R, 3949 +6.62R, 4401 +10.31R monster) and only two stopped (3825, 3929). The triad's
hit pattern on the runners:

- **Leg 1 (FLOOR GEOMETRY: demand-absent/remote ⇒ wall):** REFUTED on 5627 (dem 10.57ATR "absent") and
  on 3949 (dem=None "floorless") — both ran. Mapped-demand-distance is NOT a reliable floor proxy; price
  manufactured floors where the lens saw none. This is the literal dist_poc/distance pathology from Cluster 1.
- **Leg 2 (EFFORT POLARITY: one-sided sell_mL ⇒ distribution wall):** REFUTED hard. 5627 (15 sell/0 buy),
  4401 (11 sell/0 buy), and 3929 (10 sell/0 buy) all carried the heaviest one-sided sell signatures — yet
  5627 and 4401 RAN (4401 to monster), and only 3929 stopped. One-sided sell-bubbles did NOT discriminate
  runner from loser; 2 of the 3 heaviest sell-bubble episodes were runners. The "single cleanest standalone
  tell both readers independently elevated" is, against outcome, **near-inverted** for this set.
- **Leg 3 (OHLC sweep-hold vs markup-into-ceiling):** partially holds. The two genuine losers (3825 faded
  thrust, 3929 markup-into-block) match. But 3949's "parabolic +2.83ATR rubber-band" and 4401's "grind into
  block" were read as decay and both RAN. Markup-into-ceiling did not reliably mean failure.

So the triad gets the two LOSERS right (3825, 3929) and gets THREE of four RUNNERS wrong. A lens that
fires on losers but also condemns the majority of runners is exactly an over-condemning fade lens — it has
recall on the negatives and catastrophic false-positives on the positives. **The triad does not hold as a
runner-vs-loser separator inside IN_VALUE; it over-condemns, repeating Cluster 1.**

---

## ARE THE RESIDUALS SAME-AS-CLUSTER1, NEW, OR HONEST RESIDUE?

**SAME-AS-CLUSTER1 — but the reader had the direction of the claim backwards.**

The frozen verdict claimed the residual errors are "predominantly SAME-AS-CLUSTER1: IN_VALUE read as base
when the floor-effort triad said walled/consumed." It is correct that **no new variable is present** — but
it is correct for the OPPOSITE reason than stated. Cluster 1's lesson (per project memory: dist_poc
over-condemned runners) is that distance/location proxies fabricate false-negatives on runners. Here the
SAME pathology recurs: floor-geometry-by-mapped-distance (Leg 1) and location-above-value (3949) over-
condemned 5627, 3949, 4401 — all runners. The triad is **a new dress on the Cluster-1 dist_poc mistake**,
not a fix for it. So:

- **5627, 3949, 4401 → SAME-AS-CLUSTER1 over-condemnation (distance/location-as-floor-proxy), now empirically
  REFUTED by outcome.** These are NOT honest residue and NOT a new variable — they are the recurring
  false-negative-on-runners failure, confirmed.
- **3825, 3929 → CONFIRMED_EXISTING_LENS (genuine fades the lens correctly caught).** Honest residue-adjacent
  only in the sense the system would correctly skip them; the reading matched outcome.
- **1522 → CONFIRMED runner, lens directionally right but mis-ranks (slowest/deepest of the runners).**

No CONFIRMED_NEW_VARIABLE anywhere in the cluster. The one thing that genuinely separated runner from loser
here was NOT in the triad: the two losers (3825, 3929) shared *failed-thrust / effort-into-immediate-overhead-
with-no-follow-through within 1-2 bars*, while the three condemned runners all showed *low mae + fast or
eventual acceptance* — i.e. the post-entry HOLD, which the reader could only see structurally and got wrong.

---

## 5627 VERDICT (mandatory)

**5627: floor-geometry variable REFUTED.** Classified SUPPLY_WALL on "demand floor 10.57ATR away = floor
gone" + 15-sell/0-buy wall + rejection wick. Reality: mfe 5.96R, WIN_HELD +1.96R, runner, mae 0.14,
2R in 5 bars, 40b dnMove only −1.30. Absent mapped demand did NOT equal absent floor; the one-sided sell
wall did NOT cap it; the rejection wick was a shakeout, not distribution. The same is true for **3949**
(called OVERFADE/floorless, ran +6.62R) and **4401** (lean wall, ran +10.31R monster). Every episode the
triad called wall/overfade/lean-wall that the reader leaned bearish on, RAN. The floor-by-distance and
one-sided-sell-bubble legs are refuted as runner-condemnation signals on this cluster.

---

## FINAL (tight)

- **Per-episode:** 5627 REFUTED_LENS (5.96R/runner) · 1522 CONFIRMED_EXISTING_LENS (5.65R/runner, mis-ranked)
  · 3825 CONFIRMED_EXISTING_LENS (0.96R/stop) · 3929 CONFIRMED_EXISTING_LENS (0.05R/stop) · 3949 REFUTED_LENS
  (6.62R/runner) · 4401 REFUTED_LENS, INSUFFICIENT-hedge correct (10.31R/monster).
- **Triad:** OVER-CONDEMNS. Right on 2 losers, wrong on 3 of 4 runners. Floor-by-distance (Leg 1) and
  one-sided-sell-bubble (Leg 2) refuted as condemnation signals; OHLC hold (Leg 3) only partially holds.
- **Residuals:** SAME-AS-CLUSTER1 (distance/location-as-floor-proxy false-negative-on-runners), now empirically
  REFUTED — NOT a new variable, NOT honest residue. The reader's "no new variable" conclusion is right; its
  "the triad correctly names walled/consumed" conclusion is wrong against outcome.
- **5627:** floor-geometry REFUTED — it ran.
