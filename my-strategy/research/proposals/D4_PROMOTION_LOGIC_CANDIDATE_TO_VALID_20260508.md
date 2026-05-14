# D4 Proposal — Promotion Logic: SETUP_CANDIDATO_FORTE → SETUP_VALIDO

Status: proposal / not approved  
Date: 2026-05-08  
Source: D2R 30-event audit  
Files reviewed:
- setup_research_log.jsonl
- setup_outcome_log.jsonl
- setup_r_outcome_log.jsonl
- setup_candidato_forte_policy.md

## 1. Problem observed

The system has produced zero SETUP_VALIDO classifications despite active market movement and 200+ D1 events.

D2R analysis shows that most blocked events were correctly blocked, but a small subset of SETUP_CANDIDATO_FORTE / SETUP_EM_OBSERVACAO events later behaved like valid setups in R-multiple terms.

The issue is not that the whole strategy is too restrictive.

The issue is that the system lacks a clear promotion path:

SETUP_EM_OBSERVACAO  
→ SETUP_CANDIDATO_FORTE  
→ SETUP_VALIDO after objective trigger

## 2. Evidence summary

D2R sample:
- Total events evaluated: 30
- win_2r: 7
- win_1r: 3
- loss_1r: 15
- no_trade: 5
- Total theoretical R: +7.99R
- Average R per event: +0.32R

Tradeability:
- tradeable: 7
- not tradeable: 23

Retroactive setup validity:
- setup_valid_retro true: 4
- setup_valid_retro false: 26

Blocker assessment:
- blocker valid: 25
- blocker excessive/invalid: 5

Conclusion:
Most blockers are valid. However, some candidate setups had enough objective confirmation to justify escalation.

## 3. Key cases

### 3.1 US500 15M LONG — 2026-05-04 16:15

Outcome:
- win_2r
- +3.07R
- setup_valid_retro: true
- blocker_valid: false

Evidence:
- deep RSI extreme;
- sweep/reentry;
- LTA + zone confluence;
- clear stop;
- R:R above 2:1;
- price never threatened stop;
- target reached cleanly.

Learning:
When 4+ strong confluences cluster at session lows with RSI extreme and stop/R:R clear, SETUP_CANDIDATO_FORTE can be promoted after confirmation.

### 3.2 USOUSD 4H SHORT — 2026-05-05 14:00

Outcome:
- win_2r
- +2.42R
- setup_valid_retro: true
- blocker_valid: false

Evidence:
- alert candle closed as strong rejection candle;
- long upper wick;
- close far below high;
- fresh LTA loss / structural rejection;
- R:R above 2:1.

Learning:
A closed rejection candle at the alert bar can itself be the trigger. Waiting for an extra candle may be unnecessarily conservative.

### 3.3 BTCUSD 4H LONG — 2026-05-05

Outcome:
- win_2r
- +2R
- setup_valid_retro: true
- blocker_valid: true

Evidence:
- initial breakout was correctly kept as observation;
- valid opportunity appeared on retest;
- retest logic would have captured the setup.

Learning:
Breakout impulse alone should not be SETUP_VALIDO. Retest of the broken level is the actionable trigger.

### 3.4 USDJPY 4H SHORT — 2026-05-05

Outcome:
- win_2r
- +6R
- blocker_valid: false

Evidence:
- dense NAS100 SHORT cluster;
- supply BB/SMC;
- HTF/P3 ceiling;
- all inside a tight price band;
- strong R potential.

Learning:
Dense structural confluence may justify SETUP_CANDIDATO_FORTE even without RSI extreme.

## 4. Hypothesis

SETUP_CANDIDATO_FORTE should not be treated as entry.

It should be treated as a high-priority watch state that can be promoted to SETUP_VALIDO only after objective confirmation appears.

Promotion should require:
- clear direction;
- technical stop;
- R:R >= 2:1;
- at least one objective trigger;
- no major invalidation/macro conflict;
- no MCP reading failure.

## 5. Proposed promotion triggers

A SETUP_CANDIDATO_FORTE may be promoted to SETUP_VALIDO if one of the following objective triggers occurs:

### Trigger A — Rejection close

Valid when:
- price touches relevant zone/line;
- candle closes with strong rejection;
- wick rejects the zone;
- close is away from the extreme;
- stop is clear;
- R:R >= 2:1.

### Trigger B — Sweep + reentry confirmation

Valid when:
- price sweeps below/above zone or level;
- price reclaims the zone/level;
- reentry candle closes back inside/above/below relevant level;
- stop is beyond sweep extreme;
- R:R >= 2:1.

### Trigger C — CHoCH/BOS confirmation

Valid when:
- price reacts at zone/line;
- local CHoCH/BOS confirms direction;
- stop is clear;
- R:R >= 2:1.

### Trigger D — Breakout retest

Valid when:
- breakout occurs;
- price retests broken level;
- retest holds;
- stop is clear;
- R:R >= 2:1.

### Trigger E — Dense structural confluence

Valid for SETUP_CANDIDATO_FORTE, not automatic SETUP_VALIDO, when:
- BB/SMC zone;
- NAS100 cluster;
- HTF/P3 level;
- tight price band;
- clear stop;
- R:R >= 2:1.

Promotion to SETUP_VALIDO still requires one of Trigger A/B/C/D.

## 6. What should not change

Do not:
- loosen SETUP_VALIDO globally;
- remove RSI rules;
- remove bubbles/MOB rules;
- treat zone touch alone as setup;
- treat SETUP_CANDIDATO_FORTE as entry;
- ignore R:R;
- ignore stop clarity;
- enter on breakout impulse without retest;
- trade MCP reading failures.

## 7. Risk of the adjustment

Main risk:
More SETUP_VALIDO classifications may increase false positives if confirmation triggers are not strict.

Specific risks:
- rejection candle may be interpreted subjectively;
- sweep/reentry may be identified too early;
- dense confluence may become an excuse to ignore RSI;
- dynamic zones may create more alerts and more noise.

Mitigation:
- require R:R >= 2:1;
- require stop clarity;
- require objective trigger;
- keep SETUP_CANDIDATO_FORTE separate from SETUP_VALIDO;
- continue D2R measurement on every promoted setup.

## 8. Test plan

Run this proposal experimentally for the next 25–30 candidate events.

Track:
- number of SETUP_CANDIDATO_FORTE;
- number promoted to SETUP_VALIDO;
- D2R result of promoted setups;
- win_2r count;
- loss_1r count;
- average R;
- blocker_valid false/true;
- whether trigger type A/B/C/D/E was present.

Minimum evidence before rule change:
- at least 20 promoted events;
- positive total R;
- average R > +0.25;
- no single asset dominating all wins;
- losses not clustered from same false trigger.

## 9. Proposed output changes

Claude should explicitly output:

Promotion trigger:
- NONE
- REJECTION_CLOSE
- SWEEP_REENTRY
- CHOCH_BOS
- BREAKOUT_RETEST
- DENSE_STRUCTURAL_CONFLUENCE

Promotion status:
- NOT_PROMOTED
- PROMOTE_TO_SET_UP_VALIDO
- KEEP_AS_CANDIDATO_FORTE
- DOWNGRADE_TO_OBSERVACAO

Example:

Classificação: SETUP_CANDIDATO_FORTE  
Candidato forte: SIM  
Promotion trigger: SWEEP_REENTRY  
Promotion status: KEEP_AS_CANDIDATO_FORTE  
Gatilho faltante: candle 30M fechar acima de X  

or:

Classificação: SETUP_VALIDO  
Candidato forte: SIM  
Promotion trigger: REJECTION_CLOSE  
Promotion status: PROMOTE_TO_SET_UP_VALIDO  

## 10. Recommendation

Do not apply directly to strategy_rules.json yet.

Recommended next step:
Create an experimental promotion policy document and update claude_recheck.py to report promotion trigger/status, without changing core strategy rules.

This allows measurement before committing rule changes.
