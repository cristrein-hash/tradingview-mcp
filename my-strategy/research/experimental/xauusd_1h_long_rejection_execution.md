# XAUUSD_1H_LONG_REJECTION_EXECUTION

Status: experimental / validated by offline backtest v0.4-v0.6  
Asset: PEPPERSTONE:XAUUSD  
Timeframe: 1H  
Direction: LONG only  
Strategy Layer: Execution / Short Swing  
Signal Level: SETUP_CANDIDATO_FORTE allowed as operational manual signal  
Execution: manual only  

## 1. Purpose

This module defines a more frequent XAUUSD 1H long-only execution strategy.

It is separate from:

- XAUUSD_4H_LONG_REJECTION_SWING
- broader swing strategy
- intraday dynamic zone monitoring

The purpose is to capture high-quality 1H bullish rejection setups in XAUUSD with enough frequency to complement the rare 4H swing module.

## 2. Backtest basis

Historical offline backtest using exported TradingView CSV data.

Instrument:
PEPPERSTONE:XAUUSD

Timeframe:
1H

Sample:
2024-01 to 2026-05

Best tested family:
XAUUSD 1H v0.4 / v0.6

Core model:
- LONG only
- REJECTION_CLOSE
- quality_rejection
- SETUP_CANDIDATO_FORTE allowed as operational manual signal
- stop to breakeven after +1R
- trailing after +3R
- trailing distance: 0.75R

Observed v0.4 result:
- 21 trades
- total theoretical result: approximately +15.34R
- average result: approximately +0.73R per trade
- max losing streak: 3

Interpretation:
The module has higher frequency than the 4H swing module and remains positive in R. It should be monitored as a separate 1H execution layer.

## 3. Core setup

A valid module event requires:

1. Asset is PEPPERSTONE:XAUUSD.
2. Timeframe is 1H.
3. Direction is LONG only.
4. Trigger is REJECTION_CLOSE.
5. Candle quality is strong enough: quality_rejection.
6. Price reacts from demand/support or a meaningful local rejection area.
7. Stop is technical and clearly defined.
8. R:R is at least 2:1.
9. Setup is not a falling knife.
10. MCP/chart reading is reliable.

## 4. Quality rejection definition

A bullish quality rejection requires:

- candle touches or sweeps a relevant lower area;
- meaningful lower wick;
- close away from the low;
- close supports bullish continuation/reversal;
- not just a weak doji in range;
- not a chase after price already moved too far;
- stop can be placed structurally below rejection/swing low;
- R:R remains valid.

## 5. SETUP_CANDIDATO_FORTE behavior

Unlike the 4H swing module, this 1H module allows:

SETUP_CANDIDATO_FORTE as an operational manual signal.

This means:

- send Telegram;
- manual review required;
- no automatic execution;
- entry may be considered manually if price, stop and R:R are still valid;
- quality_rejection must be present;
- candidate must not be only a weak zone touch.

SETUP_CANDIDATO_FORTE is acceptable when:

- quality_rejection is present;
- R:R >= 2:1;
- stop is clear;
- price is not in obvious falling-knife continuation;
- at least one additional confluence exists.

Additional confluences include:

- HTF bullish or not strongly bearish;
- NAS LONG / BOTTOM signal nearby;
- seller bubble nearby;
- bullish RSI divergence;
- RSI turning up;
- local support/demand reaction;
- reclaim after sweep;
- constructive price compression.

These confluences improve priority, but NAS/bubbles/divergence are not mandatory.

## 6. Priority score

Claude must assign a priority:

Priority A:
- quality_rejection;
- R:R >= 2:1;
- clear stop;
- HTF bullish or supportive;
- at least two additional confluences.

Priority B:
- quality_rejection;
- R:R >= 2:1;
- clear stop;
- at least one additional confluence;
- no strong falling-knife context.

Priority C:
- quality_rejection present but context is mixed;
- R:R barely valid;
- weak confluence;
- manual caution required.

Do not send as this module if quality_rejection is absent.

## 7. Management rules

Default management:

- Entry: manual review around rejection close / valid pullback.
- Stop: structural stop below rejection low / local swing low.
- Move stop to breakeven after +1R.
- Do not take partial profit early by default.
- Activate trailing only after +3R.
- Trailing distance: 0.75R.
- Optional target reference: 4R.
- Manual execution only.

## 8. What this module is NOT

This module is not:

- a 4H swing module;
- a SHORT strategy;
- a zone-touch strategy;
- a CHOCH/BOS-only setup;
- a NAS-only setup;
- a bubble-only setup;
- an automatic entry model.

## 9. Disallowed signals

Do not classify as this module if any are true:

- direction is SHORT;
- timeframe is not 1H;
- no bullish quality rejection close;
- R:R < 2:1;
- stop is unclear;
- MCP/chart reading unreliable;
- price is in strong falling-knife continuation;
- setup is only a weak touch of a zone;
- entry would chase far above the rejection area;
- macro red window is immediate.

## 10. Required Claude output

When this module is detected, Claude must clearly label it:

Strategy Module: XAUUSD_1H_LONG_REJECTION_EXECUTION  
Classificação: SETUP_CANDIDATO_FORTE or SETUP_VALIDO  
Direção: LONG  
Timeframe: 1H  
Trigger: REJECTION_CLOSE  
Priority: A/B/C  

Claude must include:

- entry reference;
- stop técnico;
- R:R estimado;
- quality rejection explanation;
- priority score reason;
- management plan;
- invalidation;
- note that execution is manual.

## 11. Telegram formatting

Recommended title:

🟢 [XAUUSD 1H LONG REJECTION EXECUTION]

Required message elements:

- Strategy Module: XAUUSD_1H_LONG_REJECTION_EXECUTION
- Classificação:
- Direção: LONG
- Timeframe: 1H
- Trigger: REJECTION_CLOSE
- Priority: A/B/C
- Entry: manual review
- Stop: structural
- Management: BE after +1R, trailing after +3R with 0.75R distance

Include:

This is the 1H execution module.  
More frequent than 4H swing.  
Manual execution only.

## 12. Research status

This module is approved for experimental monitoring.

It is not yet a permanent strategy_rules.json rule.

Before permanent adoption, continue tracking:

- live occurrences;
- D2 outcomes;
- D2R outcomes;
- false positives;
- missed valid setups;
- performance by Priority A/B/C;
- whether trailing after +3R remains optimal.

## 13. Current decision

Implement as a separate experimental 1H execution module.

Do not merge with broader swing/intraday strategy yet.
