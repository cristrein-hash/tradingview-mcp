# PHASE 3 AUDIT — Cluster 2 WITH-VALUE-AREA reread vs REALIZED outcome

> FRESH INDEPENDENT auditor. SANITY_PROBE: per-episode diagnostic, NOT a hit-rate / gate / rule.
> The frozen reader saw a causal packet that INCLUDED the real volume value-area. It NEVER saw outcome.
> Brutally honest. Reads classified CONFIRMED / MODIFIED / REFUTED / INSUFFICIENT / HONEST_RESIDUAL.
> Outcome convention: washout/fuel/constructive read CONFIRMED if it RAN, REFUTED if STOPPED.
> wall/trap read CONFIRMED if it STOPPED, REFUTED if it RAN as runner/monster.

---

## Per-episode ledger

| Ep | Frozen read | Conf | mfe_R | exit / flags | Ran? | Verdict |
|----|-------------|------|-------|--------------|------|---------|
| 5826 | washout-CoC (constructive) | HIGH | 16.73 | WIN_RUNNER, runner+monster | RAN (monster) | **CONFIRMED** |
| 1623 | incomplete-base, leaning constructive | MED | 0.31 | STOP_LOSS, stop<2R | STOPPED | **CONFIRMED** |
| 4401 | supply-as-fuel-if-it-holds | MED-LOW | 10.31 | WIN_HELD, runner+monster | RAN (monster) | **CONFIRMED** |
| 3825 | supply-as-wall / trap | HIGH | 0.96 | STOP_LOSS, stop<2R | STOPPED | **CONFIRMED** |
| 1522 | incomplete-base-absorption | MED-LOW | 5.65 | WIN_BE, runner (not monster) | RAN (mod) | **REFUTED** (called undecided; ran to 5.65R) |
| 1873 | bear-pullback-trap | HIGH | 1.20 | STOP_LOSS, stop<2R | STOPPED | **CONFIRMED** |
| 5627 | trap/wall (VA-flip) | MED-HIGH | 5.96 | WIN_HELD, runner (not monster) | RAN | **REFUTED** (trap-flip wrong; ran) |
| 1775 | supply-as-wall / honest-residual | HIGH | 0.53 | STOP_LOSS, stop<2R | STOPPED | **CONFIRMED** |
| 3949 | washout-CoC | HIGH | 6.62 | WIN_HELD, runner (not monster) | RAN | **CONFIRMED** |
| 3929 | incomplete-base / bad-timing | MED | 0.05 | STOP_LOSS, stop<2R | STOPPED | **CONFIRMED** |

**Count: 8 CONFIRMED / 2 REFUTED / 0 MODIFIED / 0 INSUFFICIENT / 0 HONEST_RESIDUAL.**

The two REFUTED are both false-trap / false-undecided calls (the reader was too bearish on episodes that ran): **1522** and **5627**.

---

## Detail on the calls that matter

### CONFIRMED, clean
- **5826** — the reader's flagship washout-CoC call. ACCEPTING_ABOVE_VALUE + tpo ACCEPTED_ABOVE + clean sky. Ran +16.73R, runner+monster, time_to_2R=1 bar. As confident a hit as the set offers.
- **4401** — read as the WEAKEST constructive case (MED-LOW, "fuel ONLY if it absorbs through 1633.9"). It absorbed: +10.31R, runner+monster, time_to_2R=4. The VA "above-POC = supply-as-fuel" framing landed despite the tpo-INSIDE hedge. Reader under-rated it but the directional call was right.
- **3825, 1873, 1775** — the three HIGH-confidence wall/trap calls, all stopped (0.96 / 1.20 / 0.53R mfe, all stop_before_2R=1). These are the spine of the VA thesis and they held perfectly. 1775 in particular (dist_poc −0.86, ACCEPTED_BELOW, hard flush bar) flushed −110R over 40 bars — textbook honest-residual, correctly read.
- **1623, 3929** — both read as IN_VALUE / unresolved / unproven, both stopped. The "IN_VALUE = no acceptance yet = unproven base" gate correctly demoted these bull-looking surfaces (1623 NAS just-flipped LONG; 3929 5×LONG/5×BOS). 3929 mfe 0.05R — died instantly, exactly the "pre-acceptance, stalls under supply" expectation.
- **3949** — washout-CoC despite weekly −0.67. Ran +6.62R, WIN_HELD, runner. The deepest above-value acceptance in the cluster (dist_poc +2.83) did resolve up. Confirmed.

### REFUTED
- **1522** — read "incomplete-base-absorption, balanced inside value, undecided" (MED-LOW), explicit "rotates in value until it accepts above VAH." Outcome: ran to **mfe 5.65R**, runner_flag=1, hit5=True. It did NOT just rotate — it resolved upward materially. The IN_VALUE/dist_poc+0.16/tpo-INSIDE "undecided" read under-called a genuine runner. Mild over-bearishness. (Note: capped exit was WIN_BE at +0.9R and it gave back to 1873 lastClose — but the UNCAPPED excursion the reader was implicitly forecasting clearly RAN.)
- **5627** — the headline VA-driven trap-flip. See dedicated section below.

---

## (a) Proposed-rule HOLD/BREAK test

Reader's two-arm rule, tested against outcome across all 10:

> **Arm 1:** weekly-neg + ACCEPTING_ABOVE_VALUE (real dist_poc) → washout / CoC (should RUN).
> **Arm 2:** weekly-neg + IN_VALUE/below-POC + tpo ACCEPTED_BELOW → trap / wall (should STOP).

**Arm 1 (ACCEPTING_ABOVE_VALUE → runs): HOLDS 3/3.**
- 5826 (+16.73R), 4401 (+10.31R), 3949 (+6.62R). Every ACCEPTING_ABOVE_VALUE episode ran. Zero misses. This is the strong, clean arm of the rule.

**Arm 2 (IN_VALUE + tpo ACCEPTED_BELOW → trap/stops): HOLDS 2/3, BREAKS on 5627.**
- 3825 (ACCEPTED_BELOW) → STOP ✓
- 1775 (ACCEPTED_BELOW) → STOP ✓
- 5627 (ACCEPTED_BELOW) → **RAN +5.96R ✗ BREAK**

**The IN_VALUE-without-ACCEPTED_BELOW residue (the "unresolved" bucket):** mixed.
- 1623 (tpo ACCEPTED_ABOVE but state IN_VALUE) → STOP ✓ (reader leaned constructive — half-miss in spirit, but he hedged "unproven by value")
- 3929 (tpo INSIDE) → STOP ✓
- 1522 (tpo INSIDE) → **RAN +5.65R ✗** (reader said undecided/rotate; it ran)
- 1873 (tpo INSIDE, dist_poc −0.16, +Bearish div) → STOP ✓ (reader called trap, correct)

**Where it holds:** the ACCEPTING_ABOVE_VALUE → run arm is perfect (3/3). The explicit ACCEPTED_BELOW → stop arm is 2/3.
**Where it breaks:** ACCEPTED_BELOW did NOT guarantee a wall — 5627 carried that exact signature and still ran +5.96R. And IN_VALUE/INSIDE "undecided" was not reliably inert — 1522 ran +5.65R from a balanced-INSIDE state the reader called undecided. So the bullish arm is well-calibrated; the bearish arm over-condemns. Two of the bearish-leaning reads (5627, 1522) were runners.

---

## (b) 5627 trap-flip verdict

**REFUTED.** This is the headline VA failure of the reread.

The reader EXPLICITLY flipped 5627 from a constructive surface (quiet up-drift, BOS×4, NAS LONG×3) to **trap/wall** using the VA: IN_VALUE + tpo ACCEPTED_BELOW_VALUE + demand 10.57ATR away (no floor). He named it "the strongest single VA-driven reversal of read in the set."

Outcome: **mfe_R 5.96, runner_flag=1, WIN_HELD, hit2/hit3/hit5=True, mae only 0.14R, time_to_2R=5.** It ran cleanly with almost no adverse excursion. The "no demand floor → falls away" thesis is directly contradicted — next-10b dnMove was only −1.30 while it pushed +25.20 up.

So the VA flip was wrong on the one episode where it did the most work. The constructive SURFACE the reader overrode (BOS×4 + NAS LONG) was the correct read; the ACCEPTED_BELOW tpo + no-floor framing led him to discard a genuine runner. This is a precise, costly miss: the VA's single most assertive intervention turned a winner into a "wall."

No OTHER IN_VALUE-called-trap episode that actually ran exists (1522 was called *undecided/incomplete*, not trap — still a miss, but a softer one). So among explicit trap-flips, 5627 is the sole and decisive break.

---

## (c) 3949 vs 3929 — did outcome confirm the VA separation?

**CONFIRMED.** The reader claimed the VA was the ENTIRE difference between two episodes with identical regime (weekly −0.67), identical NAS 5×LONG / SMC 5×BOS surface, three days apart:
- 3949 = ACCEPTING_ABOVE_VALUE, dist_poc +2.83 → confirmed CoC → **mfe +6.62R, WIN_HELD, runner.**
- 3929 = IN_VALUE, dist_poc −0.30, below POC → incomplete/pre-acceptance → **mfe +0.05R, STOP, died instantly.**

Outcome separation is total: +6.62R vs +0.05R. The reader's "3929 is the pre-acceptance version, 3949 is the same impulse after it accepted above value" is exactly what happened. Of all the VA claims in the dossier, this paired call is the cleanest empirical win — same surface, opposite outcome, separated solely by above-value acceptance. **VA earned its keep here.**

---

## (d) Did VALUE-AREA improve calibration vs the NO-VA reread?

Prior NO-VA reread of Cluster 2 was **7C / 1M / 2R** (10 episodes).
This WITH-VA reread audits to **8C / 2R / 0M**.

**Marginal — arguably a wash, with a redistribution of where the value was added vs lost.**

- **Raw confirmed count:** 8C (with-VA) vs 7C (no-VA) → +1 net. Slightly better on headline.
- **But the no-VA had only 2 REFUTED and the VA also has 2 REFUTED** — VA did NOT reduce the refuted count. It traded a MODIFIED for a CONFIRMED on net, but kept the same number of outright misses.
- **Where VA clearly HELPED:** the 3949 vs 3929 separation (c) is a genuine VA-only win — same surface, opposite outcome, only the VA told them apart. And the ACCEPTING_ABOVE_VALUE → run arm went 3/3 (5826, 4401, 3949), giving the bullish calls a crisp, correct discriminator.
- **Where VA clearly HURT:** 5627. The VA's most assertive single intervention (the trap-flip) was WRONG — it overrode a correct constructive surface (BOS×4 + NAS LONG) and turned a +5.96R runner into a "wall." Without the VA the reader said he'd have read 5627 constructive — which would have been the CORRECT read. So on 5627, the VA actively degraded a call that the simpler reading would have gotten right.

**Net judgment:** VA sharpened the BULLISH discriminator (ACCEPTING_ABOVE_VALUE is a reliable run-tell, 3/3, and rescued 3949 from the weekly-neg auto-condemn) but OVER-WEIGHTED the BEARISH discriminator (ACCEPTED_BELOW / no-floor), producing exactly one high-confidence false-wall (5627) it would not have made without the VA. The IN_VALUE "undecided" gate also mis-handled 1522 (ran +5.65R from a state called inert). So: **VA improved the upside reads, did not improve (and on 5627 worsened) the downside reads.** Calibration is not meaningfully better than no-VA; it is differently distributed. Honest verdict: roughly even, with a real localized VA win (3949/3929) and a real localized VA loss (5627).

---

## Brutal-honesty residuals
- The reader's HIGH-confidence calls went **5/5** directionally on the wall side that stopped (3825, 1873, 1775) AND on the run side (5826, 3949). HIGH confidence was well-earned where used.
- Both REFUTED episodes (1522, 5627) were over-bearish errors — the reader has no over-BULLISH miss in this cluster. The bias of the with-VA lens is toward calling traps that run, not chasing washouts that fail.
- ACCEPTED_BELOW_VALUE tpo is a 2/3 STOP signal, not the hard wall the dossier framed it as. 5627 proves a BOS×4 + NAS-LONG surface can run THROUGH an ACCEPTED_BELOW + no-floor reading.
- This is a 10-episode diagnostic. No rule, no gate, no promotion implied.
