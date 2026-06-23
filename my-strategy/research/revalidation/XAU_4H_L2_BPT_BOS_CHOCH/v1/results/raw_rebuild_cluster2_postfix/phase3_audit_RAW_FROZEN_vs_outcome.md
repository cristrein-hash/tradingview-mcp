# PHASE-3 OUTCOME AUDIT — RAW-FROZEN vs REALIZED — Cluster 2 (macro-negative, post-anchor-fix)

> FRESH INDEPENDENT auditor. Did NOT produce the reading. SANITY_PROBE: per-episode reading-QUALITY diagnostic, NOT a hit-rate / gate / promotion.
> Frozen reading = blind, causal, look-ahead-free packet (commit 1267c8d). Outcome data = Phase-9 RAW-clean rebuild, uncapped MFE + post-entry path. Reader NEVER saw outcome.
> Convention: fuel/washout/constructive read → CONFIRMED if ran, REFUTED if stopped. wall/trap/fade read → REFUTED if ran as runner/monster, CONFIRMED if stopped.
> INSUFFICIENT_RAW_CONTEXT reserved for cases where BLOCKED volume VA was the true arbiter and the reader honestly under-determined (reader flagged 5627 + 1623 as most blocked).

---

## (1) ONE-LINE VERDICT PER EPISODE

### SUB-BLOCO A — clean sky

- **5826 — CONFIRMED.** Read: washout-with-change-of-character (constructive), confidence ALTA. Outcome: mfe_R=16.73, WIN_RUNNER, monster_flag=1, hit2 at t=1, mae_R=0.0, stop_before_2R=0. Ran exactly as called — flush-and-reclaim with buyer effort (entry_up=1.0) became a monster. The reading nailed it. Mother-question evidence: macro-negative did NOT trap.

- **1623 — CONFIRMED (correct caution).** Read: incomplete-base-absorption / weak-effort, NOT convicted reclaim, confidence MÉDIA, flagged as MOST-BLOCKED. Outcome: STOP_LOSS, mfe_R=0.31, mae_R=1.35, stop_before_2R=1. The reader refused to call it constructive precisely because entry_up=0.14 (no buyer); price rose without sponsorship then stopped. Caution vindicated — the "base incomplete, no buyer" read matched a clean stop. (Honest note: reader was BLOCKED here and did not commit to a direction; outcome confirms the skeptical lean.)

### SUB-BLOCO B — supply near

- **4401 — REFUTED.** Read: supply-as-WALL / bear-pullback-trap (push-into-wall), confidence MÉDIA-ALTA *for trap*. Outcome: mfe_R=10.31, WIN_HELD, **runner_flag=1, monster_flag=1**, hit10=True, stop_before_2R=0. It RAN as a monster. The wall pole was wrong here — supply at 1.57 ATR became fuel, not ceiling. Reader's own falsifier ("acceptance ABOVE supply → fuel") fired. Note the reader explicitly downgraded confidence via anchor warnings (close_fidelity=False) — honest hedge, but the trap call still missed.

- **3825 — CONFIRMED.** Read: supply-as-WALL with rejection-already-in-progress (lower-closes encadeados, last6 collapsed to 0.24), confidence ALTA. Outcome: STOP_LOSS, mfe_R=0.96, mae_R=1.05, stop_before_2R=1. Rejection consummated exactly as read — never reached +2R, rolled over. Clean hit for the wall pole.

### SUB-BLOCO C — flush under supply

- **1522 — MODIFIED.** Read: incomplete-base-absorption, flush immature, needs another buyer bar, confidence MÉDIA, BLOCKED. Outcome: WIN_BE (capped 0.9R) but mfe_R=5.65, runner_bucket=R5_10, runner_flag=1, hit5=True, time_to_2R=29 (slow), stop_before_2R=0. Directionally the constructive lean was RIGHT (it ran to +5.65R uncapped, did NOT stop) — but the reader's "needs another bar / risk of range first" caution was also borne out by the slow 29-bar maturation and BE-capped exit. Reader under-committed (MÉDIA) on something that became a mid-runner → MODIFIED: right direction, under-weighted the upside.

- **1873 — CONFIRMED.** Read: bear-pullback-trap with explicit Regular Bearish div, wall at 1.23 ATR, demand void below, confidence ALTA. Outcome: STOP_LOSS, mfe_R=1.2, mae_R=1.92, stop_before_2R=1. Stopped before 2R, leg-down materialized (next-40b dnMove −25.51). The div-bearish + wall + void thesis was the cleanest trap call of the cluster — confirmed.

- **5627 — REFUTED (but the causal fix made the read more honest).** Read: timing-bad / honest-residual, rejection-of-top, confidence MÉDIA, flagged as MOST-BLOCKED (tied with 1623). Outcome: WIN_HELD, mfe_R=5.96, runner_bucket=R5_10, runner_flag=1, hit5=True, mae_R=0.14, stop_before_2R=0. It RAN to a mid-runner — did NOT stop. The residual/rejection lean was wrong on direction. HOWEVER: the causal fix (dist_supply 1.87 not 0.84) is what stopped the reader from calling it a hard "trap-na-parede"; the read landed on a hedged "indefinição/residual" with MÉDIA confidence rather than a confident trap. So the fix moved the read TOWARD the outcome (away from a confident wrong wall-call) even though the final lean still missed. Reader self-flagged this as the most under-determined case in the cluster. See §4.

- **1775 — CONFIRMED.** Read: washout still capitulating, buyer effort near-null (last6=0.066), NOT a reclaim, confidence MÉDIA. Outcome: STOP_LOSS, mfe_R=0.53, mae_R=1.27, **next-40b dnMove −110.26** (the deepest continued capitulation in the cluster), stop_before_2R=1. "Still capitulating, no change-of-character yet" was exactly right — it kept falling. Confirmed.

### SUB-BLOCO D — same day, identical macro −0.6657, inverted geometry

- **3949 — CONFIRMED.** Read: washout-with-change-of-character despite extreme macro, SUPPLY_FAR 2.42 ATR, V-reversal with buyer effort, confidence ALTA. Outcome: WIN_HELD, mfe_R=6.62, runner_bucket=R5_10, runner_flag=1, hit5=True, mae_R=0.5, stop_before_2R=0. Ran as a runner. The "open-sky washout → continuation" call confirmed.

- **3929 — CONFIRMED.** Read: supply-as-WALL / push-into-supply at 1.34 ATR, same buyer momentum but colliding with near supply, confidence MÉDIA-ALTA *for wall*. Outcome: STOP_LOSS, mfe_R=0.05 (barely moved up), mae_R=1.25, **next-20b dnMove −38.09**, stop_before_2R=1. Rejected at the wall almost immediately. Confirmed — cleanest wall call of the cluster.

---

## (2) THE TWO KEY VERDICTS

### (a) 3949 vs 3929 — geometry as the causal axis: **CONFIRMED, CLEANLY.**
Same day, identical macro (−0.6657), same cascade, same SMC (5×BOS), same entry_up=1.0 — everything controlled except supply geometry. The post-fix reader bet that GEOMETRY of supply was the sole discriminant: 3949 SUPPLY_FAR (2.42 ATR) = washout-constructive; 3929 SUPPLY_BLOCKS (1.34 ATR) = push-into-wall. Outcome split exactly along that axis:
- **3949 → runner, mfe 6.62R, did NOT stop.**
- **3929 → STOP_LOSS, mfe 0.05R, −38R over 20b.**
The divergence the reader predicted from causal supply-distance ALONE is fully realized. This is the strongest single confirmation in the cluster that supply-geometry is a real causal axis under matched macro, not a look-ahead artifact. Both poles of the pair hit.

### (b) "weekly negative = trap" — **CONFIRMED BROKEN.**
The reader declared the mother-premise QUEBRADA: macro-negative does NOT force trap. Outcome bears this out decisively:
- **5826** (weekly −0.21, clean sky, constructive read) → **monster, 16.73R.**
- **3949** (weekly −0.6657, the MOST extreme macro of the cluster, constructive read) → **runner, 6.62R.**
Two macro-negative episodes — including the single most-negative one — ran as winners. Trap was NOT a function of weekly sign. It was a function of the CONJUNCTION the reader named: near supply (WALL) × push-into/rejection form × absent buyer effort × (where present) div-bearish. The trap episodes that confirmed (3825, 1873, 3929, 1775) all carried that conjunction; the washouts that ran (5826, 3949) did not. The premise is empirically broken in the realized data.

---

## (3) DID THE CAUSAL FIX IMPROVE THE WALL-POLE READS (4401 / 1522 / 5627) vs CONTAMINATED PRE-FIX?

Mixed — the fix helped HONESTY and one read, but did not rescue the wall pole as a directional caller. Outcome of the three "wall/trap-ish" reads:
- **4401 → RAN (monster, 10.31R)** — wall call REFUTED.
- **1522 → RAN (mid-runner, 5.65R)** — but this was already read as base/incomplete (constructive-leaning, MÉDIA), so MODIFIED not a wall miss.
- **5627 → RAN (mid-runner, 5.96R)** — residual/rejection lean REFUTED on direction.

What the causal fix demonstrably changed:
- **5627 is the showcase.** The causal dist_supply (1.87 ATR, vs the contaminated ~0.84 ATR that look-ahead implied) MOVED the read off a confident "trap-na-parede" onto a hedged "indefinição / honest-residual, MÉDIA confidence, MOST-BLOCKED." Since 5627 actually RAN, a confident pre-fix wall call would have been MORE wrong; the post-fix read is LESS wrong (hedged, low-confidence, self-flagged blocked). The fix moved the read toward the outcome direction even though it did not flip the lean. Net: causal data improved the read's CALIBRATION here, exactly as the dossier claimed.
- **4401 still missed.** The reader downgraded confidence via anchor warnings (close_fidelity=False) but still leaned trap MÉDIA-ALTA; outcome ran. The fix did not save this one — supply at 1.57 ATR became fuel. This is a genuine WALL-pole REFUTAL on causal data, not an artifact.
- **1522** was never a confident wall — the constructive lean was correct on direction; the fix is neutral here.

VERDICT on the wall pole: in the pre-fix audit the WALL pole was "largely REFUTED (they ran)." Post-fix, the wall pole is now **SPLIT, not uniformly refuted**: confident, conjunction-backed wall calls (3825, 1873, 3929) all CONFIRMED (stopped); the wall calls that lacked the full conjunction or sat on contaminated geometry (4401 push-into despite anchor-warning; 5627 residual) RAN. The causal fix sharpened the boundary — it did not make every wall call right, but it made the reader's CONFIDENCE track the outcome better (high-confidence wall calls all hit; the misses were the hedged/anchor-warned ones). That is an improvement in calibration even where direction still missed.

---

## (4) INSUFFICIENT / HONESTLY-BLOCKED CASES

The reader explicitly flagged **5627** and **1623** as the two most BLOCKED by the missing VOLUME value area.
- **1623** — classified CONFIRMED (correct caution), but note the reader did NOT commit to a direction; it leaned skeptical ("base incomplete, no buyer") and the stop validated the skepticism. The directional question ("base incomplete vs real escape") was genuinely under-determined by the packet; the VOLUME VA would have been decisive. The CONFIRMED label reflects that the skeptical lean matched a stop, not that the read had full information.
- **5627** — classified REFUTED on direction, but it is the honest INSUFFICIENT case of the cluster: demand void 10.57 ATR below + no VOLUME VA meant the reader could not distinguish "accepted accumulation grind" from "pause before falling." It hedged to MÉDIA / residual, and the causal dist_supply fix is what kept it from a confident wrong trap-call. The miss is on direction; the read's honesty about being blocked is intact.

No episode is left as pure INSUFFICIENT_RAW_CONTEXT (every episode received a directional outcome verdict), but 1623 and 5627 are the two where the BLOCKED volume VA was the true arbiter and the reader correctly signaled under-determination.

---

## COUNT BY LABEL

| Label | Count | Episodes |
|---|---|---|
| CONFIRMED | 7 | 5826, 1623, 3825, 1873, 1775, 3949, 3929 |
| MODIFIED | 1 | 1522 |
| REFUTED | 2 | 4401, 5627 |
| INSUFFICIENT_RAW_CONTEXT | 0 | (1623 + 5627 flagged as honestly-blocked within their verdicts) |
| HONEST_RESIDUAL | 0 | (5627 read as residual but received a directional REFUTED) |

**Cluster 2 reading quality: 7 CONFIRMED / 1 MODIFIED / 2 REFUTED.** The two key structural bets — (a) supply-geometry as causal axis (3949 vs 3929) and (b) "weekly-negative ≠ trap" — both CONFIRMED cleanly. The two REFUTALS (4401, 5627) are precisely the cases the reader had already hedged (anchor-warning on 4401; MOST-BLOCKED / causal-fixed residual on 5627), so the misses fell where the reader's own confidence was lowest — calibration held even in error.
