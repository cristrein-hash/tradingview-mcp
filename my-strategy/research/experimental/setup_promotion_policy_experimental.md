# SETUP Promotion Policy — Experimental

Status: experimental / measurement only  
Applies to: SETUP_CANDIDATO_FORTE → SETUP_VALIDO  
Do not modify strategy_rules.json yet.

## 1. Objective

Create a clear promotion path:

SETUP_EM_OBSERVACAO
→ SETUP_CANDIDATO_FORTE
→ SETUP_VALIDO after objective confirmation

The goal is to avoid two errors:

1. Keeping too many real opportunities stuck in observation.
2. Promoting weak setups too early.

## 2. Core Principle

SETUP_CANDIDATO_FORTE is not an entry.

It means:
- strong asymmetric opportunity;
- human review required;
- no automatic execution;
- waiting for objective trigger.

SETUP_VALIDO requires:
- candidate-quality setup;
- objective trigger;
- clear stop;
- R:R >= 2:1;
- reliable chart reading.

## 3. Minimum Requirements Before Promotion

A setup can only be promoted if all are true:

- clear direction: long, short, breakout, breakdown, or reentry;
- relevant zone or line;
- clear technical stop;
- estimated R:R >= 2:1;
- no red macro window;
- no MCP/chart reading failure;
- objective trigger is present.

## 4. Promotion Triggers

### A. REJECTION_CLOSE

Use when price touches a relevant zone/line and the candle closes with clear rejection.

Valid when:
- wick rejects the zone/line;
- close is away from the rejected extreme;
- close supports the trade direction;
- stop remains clear;
- R:R >= 2:1.

### B. SWEEP_REENTRY

Use when price sweeps liquidity and reclaims the level/zone.

For long:
- price sweeps below support/demand;
- price reclaims the level/zone;
- stop is below sweep low;
- R:R >= 2:1.

For short:
- price sweeps above resistance/supply;
- price returns below the level/zone;
- stop is above sweep high;
- R:R >= 2:1.

### C. CHOCH_BOS

Use when local structure confirms the direction.

For long:
- reaction at demand/support;
- bullish CHoCH/BOS;
- stop below zone/swing;
- R:R >= 2:1.

For short:
- reaction at supply/resistance;
- bearish CHoCH/BOS;
- stop above zone/swing;
- R:R >= 2:1.

### D. BREAKOUT_RETEST

Use when breakout has already happened and price retests the broken level.

Valid when:
- breakout occurred;
- price retests the broken level;
- retest holds;
- confirmation candle supports the breakout direction;
- stop is behind retest;
- R:R >= 2:1.

### E. DENSE_STRUCTURAL_CONFLUENCE

This trigger alone does not promote to SETUP_VALIDO.

It can justify SETUP_CANDIDATO_FORTE when:
- BB/SMC zone;
- dense NAS100 cluster;
- HTF/P3 level;
- tight price band;
- clear stop;
- R:R >= 2:1.

To become SETUP_VALIDO, it still needs A, B, C, or D.

## 5. Hard Blocks

Do not promote if any are true:

- R:R < 2:1;
- stop unclear;
- MCP/chart reading unreliable;
- range tight with no direction;
- macro red window;
- dry zone touch without reaction;
- against strong HTF context without confirmation;
- candle still in freefall or vertical impulse without close;
- entry depends on a distant target only;
- stop is too wide for the timeframe/asset.

## 6. Required Output Fields

Claude must include:

Classificação:
Direção:
R:R estimado:
Stop técnico:
Candidato forte:
Motivo candidato forte:
Promotion trigger:
Promotion status:
Gatilho faltante:
Ação tomada:
Próxima ação:

## 7. Promotion Trigger Values

Allowed values:

- NONE
- REJECTION_CLOSE
- SWEEP_REENTRY
- CHOCH_BOS
- BREAKOUT_RETEST
- DENSE_STRUCTURAL_CONFLUENCE

## 8. Promotion Status Values

Allowed values:

- NOT_PROMOTED
- KEEP_AS_CANDIDATO_FORTE
- PROMOTE_TO_SETUP_VALIDO
- DOWNGRADE_TO_OBSERVACAO
- NO_TRADE

## 9. Telegram Behavior

SETUP_VALIDO:
- send Telegram;
- execution/review manual;
- not automatic trade.

SETUP_CANDIDATO_FORTE:
- send Telegram;
- human review;
- wait for final trigger if not already present.

SETUP_EM_OBSERVACAO:
- normally do not send Telegram.

NO_TRADE:
- do not send Telegram except real invalidation or critical event.

## 10. Measurement

Every promoted or candidate event must be tracked in D2R.

Measure:
- r_outcome_label;
- theoretical_r_outcome;
- hit_stop_first;
- hit_2r;
- setup_valid_retro;
- main_blocker_was_valid;
- promotion trigger performance.

## 11. Approval

This policy is experimental.

Do not modify strategy_rules.json until:
- at least 20 promoted events are measured in D2R;
- total R remains positive;
- average R > +0.25;
- no single asset dominates the results;
- false positives are controlled.
