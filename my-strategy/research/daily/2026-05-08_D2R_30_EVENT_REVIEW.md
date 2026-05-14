# D2R Review — 30 Event R-Multiple Audit

Status: research review / no rule changes approved  
Date: 2026-05-08  
Source: setup_r_outcome_log.jsonl  
Sample: 30 D2R events

## 1. Executive Summary

D2R evaluated 30 events in theoretical R-multiple terms.

Results:
- win_2r: 7
- win_1r: 3
- loss_1r: 15
- no_trade: 5

Total theoretical R:
+7.99R

Average R per event:
+0.32R

Tradeability:
- tradeable: 7
- not tradeable: 23

Retroactive setup validity:
- setup_valid_retro true: 4
- setup_valid_retro false: 26

Blocker assessment:
- blocker valid: 25
- blocker excessive/invalid: 5

Main conclusion:
The system is not simply too restrictive. Most blocked events were correctly blocked. However, a small subset of events shows that the system lacks a structured promotion path from SETUP_CANDIDATO_FORTE to SETUP_VALIDO after an objective trigger.

## 2. Main Strategic Finding

The correct improvement is not global loosening.

The correct improvement is a promotion framework:

SETUP_EM_OBSERVACAO
→ SETUP_CANDIDATO_FORTE
→ SETUP_VALIDO after objective trigger

This preserves caution while allowing strong opportunities to become actionable when confirmation appears.

## 3. Best Patterns Found

### Pattern A — Deep RSI + sweep/reentry + zone/LTA

Example:
US500 15M LONG, 2026-05-04 16:15

Outcome:
- win_2r
- +3.07R
- setup_valid_retro: true
- blocker_valid: false

Learning:
Deep RSI extreme plus sweep/reentry plus zone/LTA confluence at session lows can justify escalation. Telegram-for-review behavior was correct. With 4+ strong confluences and clear stop/R:R, this may become SETUP_VALIDO after confirmation.

### Pattern B — Closed rejection candle as trigger

Example:
USOUSD 4H SHORT, 2026-05-05 14:00

Outcome:
- win_2r
- +2.42R
- setup_valid_retro: true
- blocker_valid: false

Learning:
When the alert candle itself closes as a strong rejection candle at a relevant line/zone, that close may be the trigger. Waiting for another candle can miss the setup.

### Pattern C — Breakout requires retest

Example:
BTCUSD 4H LONG, 2026-05-05 05:00

Outcome:
- win_2r
- +2R
- setup_valid_retro: true
- blocker_valid: true

Learning:
The initial breakout should remain SETUP_EM_OBSERVACAO. The valid setup is the retest of the broken level, not the breakout impulse itself.

### Pattern D — Dense structural confluence can compensate for imperfect RSI

Example:
USDJPY 4H SHORT, 2026-05-05 13:00

Outcome:
- win_2r
- +6R
- blocker_valid: false

Learning:
Dense NAS100 cluster + supply BB/SMC + HTF/P3 ceiling inside a tight price band may justify SETUP_CANDIDATO_FORTE even without RSI extreme.

## 4. Filters That Should Remain Strong

D2R losses confirm the value of several existing blockers:

- no rejection candle;
- no CHoCH/BOS;
- no fresh confirmation;
- shorting against strong HTF bullish context;
- longing into vertical selloff without base;
- R:R below 2:1;
- stop placement too tight after a sweep;
- RSI extreme alone without structure.

These should not be removed.

## 5. Early Adaptation Hypotheses

### H1 — Promotion after objective trigger

SETUP_CANDIDATO_FORTE can become SETUP_VALIDO only after an objective trigger such as:
- rejection candle close;
- reclaim/reentry close;
- CHoCH/BOS in direction;
- retest hold;
- RSI turn after extreme;
- fresh NAS100 signal at zone;
- stop/R:R still valid.

### H2 — Rejection close can be enough

If the alert candle itself closes as a strong rejection candle at a valid zone/line, do not always require another candle.

### H3 — Retest alerts after breakout

Breakouts should create/activate retest monitoring. The retest is where SETUP_VALIDO can emerge.

### H4 — Dense structural confluence can allow SETUP_CANDIDATO_FORTE without RSI extreme

If there are 3+ strong structural confluences in a tight band and R:R >= 2:1, RSI extreme may be preferred but not mandatory for SETUP_CANDIDATO_FORTE.

## 6. What Not To Change Yet

Do not:
- loosen SETUP_VALIDO globally;
- remove RSI filters;
- remove bubbles/MOB filters;
- treat SETUP_CANDIDATO_FORTE as entry;
- change strategy_rules.json yet;
- promote all dynamic BB touches.

## 7. Recommended Next Step

Create a D4 proposal focused only on promotion logic:

SETUP_CANDIDATO_FORTE
→ SETUP_VALIDO after objective confirmation.

Do not change base setup rules yet.

## 8. Manual Review Candidates

Review visually:
- US500 15M LONG 2026-05-04 16:15
- USOUSD 4H SHORT 2026-05-05 14:00
- BTCUSD 4H LONG breakout/retest 2026-05-05
- USDJPY 4H SHORT 2026-05-05
- XAUUSD 30M failed candidate 2026-05-04 11:00

These should define the promotion logic.
