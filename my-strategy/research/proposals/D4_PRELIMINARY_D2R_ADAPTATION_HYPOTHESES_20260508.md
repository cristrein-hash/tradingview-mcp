# D4 Preliminary — D2R Adaptation Hypotheses

Status: preliminary / no rule changes approved  
Date: 2026-05-08  
Source: setup_r_outcome_log.jsonl

## 1. Objective

Use D2R R-multiple outcomes to identify whether SETUP_EM_OBSERVACAO and SETUP_CANDIDATO_FORTE are too conservative, and where practical adaptations may be needed.

No changes to strategy_rules.json are approved by this document.

## 2. Key D2R cases

### US500 15M LONG — 2026-05-04 16:15

Outcome:
- win_2r
- +3.07R theoretical
- setup_valid_retro: true
- blocker_valid: false

Learning:
Deep RSI extreme + sweep/reentry + zone/LTA confluence at oversold session lows was high-quality. Telegram-for-review behavior was correct. With 4+ strong confluences and extreme RSI, this may justify escalation.

### EURUSD 1H LONG — 2026-05-05 05:00

Outcome:
- win_2r
- +1.96R theoretical
- setup_valid_retro: false
- blocker_valid: false

Learning:
Dynamic BB zone touch with favorable HTF context may justify SETUP_CANDIDATO_FORTE even without perfect RSI, but this case was not clearly tradeable enough for SETUP_VALIDO.

### BTCUSD 4H LONG — 2026-05-05 05:00

Outcome:
- win_2r
- +2.0R theoretical
- setup_valid_retro: true
- blocker_valid: true

Learning:
Breakout should not be entered immediately. Waiting for retest was correct. Need retest monitoring rather than immediate SETUP_VALIDO on breakout.

### USDJPY 4H SHORT — 2026-05-05 13:00

Outcome:
- win_2r
- +6.0R theoretical
- setup_valid_retro: false
- blocker_valid: false

Learning:
Dense NAS100 SHORT cluster + supply BB SMC + HTF/P3 ceiling inside a tight price band may override the need for RSI extreme at the SETUP_CANDIDATO_FORTE level.

### USOUSD 4H SHORT — 2026-05-05 14:00

Outcome:
- win_2r
- +2.42R theoretical
- setup_valid_retro: true
- blocker_valid: false

Learning:
When the alert bar closes as a strong rejection candle at a fresh LTA loss, that close may be the trigger. Waiting for an extra candle can miss a valid setup.

## 3. Adaptation hypotheses

### H1 — Structural confluence can promote to SETUP_CANDIDATO_FORTE without RSI extreme

If all are present:
- BB/SMC zone
- dense NAS100 cluster at or inside zone
- HTF/P3 level
- tight price band
- clear stop
- R:R >= 2:1

Then RSI extreme may not be mandatory for SETUP_CANDIDATO_FORTE.

Risk:
Could increase false positives if used without stop/R:R discipline.

### H2 — Closed rejection candle can be sufficient trigger

If the alert candle closes with:
- strong wick rejection
- close away from the extreme
- zone/line confluence
- R:R >= 2:1

Then no extra confirmation candle may be needed.

Risk:
Requires strict candle definition to avoid subjective interpretation.

### H3 — Breakout needs retest logic

Breakout alert alone should remain SETUP_EM_OBSERVACAO unless:
- price retests the broken level
- retest holds
- stop is clear
- R:R >= 2:1

Action:
Create or monitor retest zones after breakout.

### H4 — Dynamic BB + HTF favorable context can justify SETUP_CANDIDATO_FORTE

If price touches a dynamic BB zone aligned with HTF context and there is compression or constructive price action, it may deserve SETUP_CANDIDATO_FORTE even without perfect RSI.

Risk:
This is weaker evidence than H1/H2 and needs more cases.

## 4. What not to change yet

Do not:
- loosen SETUP_VALIDO globally;
- remove RSI filters;
- remove Bubbles/MOB filters;
- treat SETUP_CANDIDATO_FORTE as entry;
- modify strategy_rules.json.

## 5. Next evidence needed

- Increase D2R sample to 25–30 events.
- Separate candidates by asset and direction.
- Track whether confirmation trigger appeared after candidate alert.
- Compare SETUP_CANDIDATO_FORTE conditional vs immediately actionable.
- Review chart screenshots for the 5 cases above.

## 6. Preliminary conclusion

The system is not simply too conservative. It is missing a structured promotion path:

SETUP_EM_OBSERVACAO  
→ SETUP_CANDIDATO_FORTE  
→ SETUP_VALIDO after objective trigger.

The next improvement should focus on the promotion logic, not on weakening the base rules.
