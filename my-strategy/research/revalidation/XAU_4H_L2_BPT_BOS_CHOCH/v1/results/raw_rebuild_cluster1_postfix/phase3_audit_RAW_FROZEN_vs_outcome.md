# PHASE 3 AUDIT — RAW FROZEN READING vs REALIZED OUTCOME (Cluster 1, POST-ANCHOR-FIX)

> Fresh independent auditor. Did NOT produce the reading. SANITY_PROBE: per-episode reading-QUALITY
> diagnostic, NOT a hit-rate, NOT a gate, NOT a promotion signal. Outcome data was hidden from the reader.
> Sources: `reader_dossier_RAW_FROZEN.md` (blind, causal/look-ahead-free) vs CLUSTER 1 of `raw_rebuild_phase3_audit_data.txt`.

---

## 1. ONE-LINE VERDICT PER EPISODE

**4918 — CONFIRMED.** Read: washout/change-of-character absorption at demand, clean sky, resolves UP. Realized mfe **19.79R**, WIN_RUNNER, monster, stop_before_2R=0. The read called the runner direction correctly through a bearish look-alike surface — exactly right.

**1661 — CONFIRMED.** Read: bear-pullback-trap into near supply wall, "no buyers," resumes lower. Realized **STOP_LOSS, mfe 0.0R**, stop_before_2R=1, dnMove −69.55 over 40b. Fade/wall/trap read, it died — textbook confirmation. High-confidence call validated.

**5701 — CONFIRMED.** Read: supply-as-wall, effortful counter-trend bounce into heaviest sell cluster, "stalls before supply matters." Realized **STOP_LOSS, mfe 0.42R**, stop_before_2R=1, drifts lower (40b dn −24.88). The "is the bounce volume-accepted or just time-grinding" question resolved to NOT accepted — wall held. Confirmed.

**6887 — REFUTED.** Read: supply-as-fuel bull-transition breakout, "continuation into clean sky." Realized **STOP_LOSS, mfe 0.0R**, stop_before_2R=1 — never made a single new high (maxHigh over next 10b = entry close exactly), immediate failure back to demand. The fuel/continuation/constructive read died at once. The reader's OWN falsifier ("immediate failure back into the demand 1.98ATR below") fired. Clean refutation.

**7426 — MODIFIED.** Read: supply-as-fuel but extended/overbought (RSI 77), "continues, maybe shallow shake first." Realized **SCRATCH, mfe 4.61R** — hit 2R and 3R, then NOT 5R; max_run 4.61R with mae 3.93R (a deep give-back). Directionally up enough to clear 3R, but the extension caution was the dominant fact: it did NOT run as a monster, it chopped and scratched. The read's two-sided lean ("continues but overbought tension") matched a partial up-move that failed to extend — neither a clean runner-CONFIRM nor a stop-REFUTE. Honest MODIFIED.

**8878 — CONFIRMED-CONTRARY (counts as REFUTED of the stated lean).** Read: supply-as-wall inside a bull, "stall/pullback off the 0.59ATR wall before continuation," right-thesis/wrong-timing. Realized **WIN_HELD, mfe 18.78R**, monster, mae only 0.03R — NO stall, NO pullback; it thrust straight up 93pts in 10b. The wall did NOT cap; the reader's falsifier ("immediate reclaim on renewed up-effort") fired. The entry_up=None blindness the reader flagged was decisive: the rollover bar was a liquidity grab, not distribution. **REFUTED** (the explicit "stall before continuation" expectation broke), with the mitigation that the reader pre-registered this exact failure mode and named entry_up=None as the reason confidence couldn't be high.

**8923 — CONFIRMED.** Read: late/vertical-climax chase, RSI 82, "two-sided; continuation OR sharp snap-back of the vertical leg." Realized **WIN_BE, mfe 0.58R**, stop_before_2R=1, next 10b dn −93.51 — the climax topped at/near entry and snapped back hard. The reader explicitly held this two-sided and named the snap-back as a live outcome; the snap-back is what happened. The honest "high-energy, two-sided, can't resolve with VA blocked" read is vindicated — the dangerous side materialized. Confirmed (the read refused a false bull-CONFIRM and the caution was correct).

**8940 — MODIFIED.** Read: supply-as-fuel continuation, cooler RSI 66, "healthiest of the late-2025 trio, continuation holds." Realized **WIN_BE, mfe 4.96R** — hit 2R/3R (not 5R), max_run 4.96R then gave back to BE (40b shows a round-trip: up to 4381 then back to 4087). Genuine up-move (correct direction, beat the climax-case 8923's 0.58R, consistent with "cooler/healthier"), but it did NOT deliver the clean sustained continuation implied — it ran modestly then retraced. Partial vindication: MODIFIED.

**4926 — REFUTED.** Read: supply-as-wall / honest-residual mid-range, "no edge, chop/rejection under supply blocks, no decisive directional resolution." Realized **WIN_RUNNER, mfe 18.03R**, monster, mae only 0.27R, time_to_2R=4 — it ran almost immediately and massively (78.99 up in 10b). The "no-edge / wall / residual / chop" read is flatly contradicted by an 18R monster runner. Clean refutation.

---

## 2. THE 4918 vs 4926 CONTRAST — DID THE POST-FIX OPPOSITE READ HOLD OR BREAK?

**It BROKE.** Decisively.

The post-fix reader called 4918 and 4926 **OPPOSITE in nature**: 4918 = legitimate washout/absorption-at-demand with clean sky and bullish divergence (will run up); 4926 = supply-wall / honest-residual mid-range with no edge (will chop/reject, no directional resolution).

Realized outcome:
- 4918: mfe **19.79R**, WIN_RUNNER, monster.
- 4926: mfe **18.03R**, WIN_RUNNER, monster.

**They were TWINS, not opposites.** Both were near-identical monster runners the very next day. The reader got 4918 exactly right (CONFIRMED) but got 4926 exactly backwards (REFUTED) — and the entire causal discriminator (cascade sign, SUPPLY_BLOCKS vs clean_sky, on-demand vs mid-range, RSI div vs neutral) successfully separated 4918's nature but FAILED to predict that 4926 would behave identically to 4918.

**Causal data vs pre-fix:** The pre-fix audit reportedly called the contrast BROKEN (could not cleanly distinguish them). The post-fix, look-ahead-free reasoning produced a *confident, well-argued OPPOSITE read* — but that confident contrast is **wrong on outcome**. So the anchor fix made the read *internally sharper and more defensible* (the 4918 side is genuinely better — a strong CONFIRM through a trap surface), yet on the specific 4918-vs-4926 question the post-fix reader is **more confidently incorrect about 4926** than a "broken/can't-tell" verdict would have been. The honest read of this twin: **the discriminator the reader trusts (SUPPLY_BLOCKS + mid-range + neutral RSI ⇒ no-edge) does not survive contact with outcome** — 4926 ran just as hard as 4918 despite the "wall" geometry. The fix improved the 4918 call; it did not rescue, and arguably worsened the calibration of, the 4926 call.

---

## 3. INSUFFICIENT / BLOCKED-VOLUME-VA AS TRUE ARBITER

No episode is labeled INSUFFICIENT_RAW_CONTEXT, but the BLOCKED LuxAlgo volume VA was honestly the true arbiter in these, and the reader flagged each:

- **8923 (VA-blocked HIGH):** rich-above-value vs accepted-above-value was *the whole question* (reader's words). The snap-back (−93.51 in 10b) means it was rich/exhausted, not accepted — exactly the side VA would have disambiguated. The read survived only because it refused to pick a side. Genuinely under-determined; the read handled the blindness correctly.
- **8878 (entry_up=None, VA-blocked HIGH):** the single most diagnostic field (entry_up on the decisive bar) was blocked. The reader said so and capped confidence. Outcome (18.78R thrust) shows the missing effort field would likely have flipped the "rollover/distribution" read to "absorption/liquidity-grab." Under-determined by data loss, honestly flagged.
- **7426 (VA-blocked MED):** accepted-above-value (sustainable) vs rich-above-value (exhaustion) was the crux; the scratch/give-back (mae 3.93R) leaned rich — VA would have sharpened it. Read honestly held at med.
- **4926 (VA-blocked MED):** "accepted in the middle (range) vs rejected (turning)" was named as the unresolvable question. Outcome = neither; it broke UP and ran. The geometry read (SUPPLY_BLOCKS=wall) over-rode what VA might have shown (accumulation/acceptance below blocks). This is where the blocked VA most hurt the call.

Across these, the reader was disciplined about flagging VA-blindness and capping confidence — the methodology did not overstate. The failures (4926, 8878, 6887) are reading/geometry errors, not dishonest certainty.

---

## 4. SHORT HONEST SUMMARY — DID THE ANCHOR FIX CHANGE ANY VERDICT vs PRE-FIX?

- **Net record (Cluster 1, n=9):** CONFIRMED 4 (4918, 1661, 5701, 8923) · MODIFIED 2 (7426, 8940) · REFUTED 3 (6887, 8878, 4926). Roughly half the reads held against brutal outcome; three broke; two were partially right.
- **What the fix improved:** The 4918 call is the standout — a *correct, confident* runner read driven through a fully bearish look-alike surface (NAS SHORT, sell bubbles) purely on causal geometry + divergence + on-demand location. That is the read the contaminated pre-fix version could not be trusted to have made honestly. The bear-trap reads (1661, 5701) and the climax-caution (8923) are clean, well-calibrated CONFIRMs. So the causal data made the *individual-episode reasoning genuinely better and more honest* — confidence is tied to what was visible at entry, and the strongest call (4918) is correct.
- **What the fix did NOT fix — the headline:** The **4918-vs-4926 contrast BROKE.** The pre-fix audit called it broken; the post-fix reader replaced "broken" with a *confident OPPOSITE* read that is wrong on 4926 (an 18R twin runner mislabeled "no-edge wall/residual"). So on the marquee test, the anchor fix did **not** rescue the contrast — it produced a sharper-sounding but outcome-incorrect verdict. The supply-geometry discriminator (SUPPLY_BLOCKS ⇒ wall/no-edge) is empirically unreliable here: 4926 and 8878 both had "wall" geometry and both ran as monsters.
- **Verdict-change vs pre-fix:** For the contrast specifically, the fix changed the verdict from *"broken/can't-tell"* to *"confident-opposite"* — and outcome shows the honest label is still **broken** (the opposite read fails on 4926). For the standalone 4918 episode, the fix is a real improvement (CONFIRMED with justified confidence). The blocked volume VA, not the anchor, remains the binding constraint on the three under-determined calls (8923, 8878, 4926/7426).

> Bottom line: causal data sharpened per-episode reasoning and produced one excellent contrarian CONFIRM (4918), but the "wall = no-edge" geometry logic over-fades real runners (4926, 8878), and the 4918-vs-4926 OPPOSITE contrast does not hold against outcome.
