# ETHUSD_4H_LONG_BREAKOUT_CONTINUATION — DEPRECATED

**Status: DEPRECATED em 2026-05-12** — substituído por `ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED`.

**Razão da depreciação:**

Audit profundo de backtest CSV em 2026-05-12 (5.4 anos, n=613 trades) mostrou:
- Total Net R @ 0.05R: **-35.68R** (NEGATIVO)
- Avg R: -0.058
- Profit Factor: 0.89
- Win rate: 19.1%
- Edge não confirmado nos dados disponíveis

A premissa original (RSI >= 52 + breakout) não produz edge estatístico. Os filtros de regime adicionais (EMA stack + ADX + ATR expanding) são necessários para sair do negativo.

**Comportamento operacional:**
- Não deve mais gerar `SETUP_VALIDO`.
- Eventos novos devem usar `ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED` (classificação inicial: SETUP_CANDIDATO_FORTE).
- Conteúdo abaixo mantido apenas como histórico de research.

**Substituto operacional ativo:**
`ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED` (+18.29R net em 5.4y, PF 1.29).

---

## Histórico (não usar como referência operacional)

Asset: PEPPERSTONE:ETHUSD  
Timeframe: 4H  
Direction: LONG only  
Strategy Layer: Swing / Momentum Continuation  
Signal Level: SETUP_VALIDO only for confirmed breakout (DESCONTINUADO)
Execution: manual only  

## 1. Purpose

This module defines a separate ETHUSD 4H long-only breakout continuation strategy.

It is independent from:

- XAUUSD modules
- US500 modules
- generic intraday dynamic-zone monitoring
- ETHUSD local zone reversal attempts

The purpose is to capture strong ETHUSD bullish continuation moves after confirmed 4H breakout in supportive higher-timeframe context.

## 2. Backtest basis

Historical offline backtest using exported TradingView CSV data.

Instrument:
PEPPERSTONE:ETHUSD

Timeframes analyzed:
- 1D
- 12H
- 4H
- 1H
- 30M
- 15M

Best tested version:
ETHUSD v0.2

Robust model:
- LONG only
- 4H breakout / momentum continuation
- HTF bullish or supportive context
- RSI >= 52
- structural stop
- move stop to breakeven after +1R
- target reference: 5R

Observed robust result:
- approx. 128 trades
- total theoretical result: approx. +39R
- average result: approx. +0.30R per trade
- max losing streak: 6

High-conviction model:
- more selective
- potential runner target up to 8R
- higher average R but more dependent on fewer large winners

Interpretation:
ETHUSD does not respond well to simple rejection/pullback logic. The most promising behavior is bullish breakout continuation in supportive HTF conditions.

## 3. Core setup

A valid setup requires:

1. Asset is PEPPERSTONE:ETHUSD.
2. Timeframe is 4H.
3. Direction is LONG only.
4. Context is bullish or supportive on 12H/1D.
5. 4H candle confirms breakout / momentum continuation.
6. RSI is supportive, preferably >= 52.
7. Breakout is not late/chasing.
8. Stop is structural and clearly defined.
9. R:R is at least 2:1, with target reference around 5R.
10. MCP/chart reading is reliable.

## 4. Breakout continuation definition

A valid bullish breakout continuation requires:

- 4H close breaks above relevant recent structure/high;
- candle shows impulse or expansion;
- price is not merely wicking above resistance and closing weak;
- HTF context does not contradict the breakout;
- stop can be placed structurally below breakout base / pullback low / invalidation level;
- target path is reasonably open.

## 5. Priority logic

Priority A:
- strong 4H breakout close;
- 12H/1D bullish or supportive;
- RSI supportive;
- clean structure above;
- stop clear;
- R:R strong;
- possible runner toward 8R if momentum remains strong.

Priority B:
- breakout valid but context less clean;
- R:R valid;
- some resistance nearby;
- manual review required.

Priority C:
- breakout forming but not confirmed;
- watch only;
- no entry yet.

## 6. Management rules

Default management:

- Entry: manual review after confirmed 4H breakout close or controlled retest.
- Stop: structural stop below breakout base / swing low / invalidation level.
- Move stop to breakeven after +1R.
- Base target: 5R.
- Priority A may allow runner logic up to 8R, but 8R is not default.
- Do not take early partials by default.
- Execution is manual only.

## 7. What this module is NOT

This module is not:

- a SHORT strategy;
- an intraday strategy;
- a rejection-close reversal strategy;
- a supply/demand mean-reversion strategy;
- a zone-touch strategy;
- a NAS-only setup;
- a bubble-only setup;
- an automatic entry model.

## 8. Disallowed signals

Do not classify as this module if any are true:

- direction is SHORT;
- timeframe is not 4H;
- no confirmed 4H breakout close;
- HTF context is bearish breakdown;
- RSI/momentum does not support continuation;
- stop is unclear;
- R:R < 2:1;
- entry is late/chasing after large extension;
- signal is only RSI/NAS/bubble/zone touch;
- MCP/chart reading unreliable.

## 9. SETUP_CANDIDATO_FORTE behavior

SETUP_CANDIDATO_FORTE can be used when:

- breakout is forming;
- price is near breakout level;
- HTF context is supportive;
- R:R may be valid if confirmation appears;
- but the 4H candle has not confirmed yet.

This is preparation only. It is not entry.

## 10. SETUP_VALIDO behavior

SETUP_VALIDO requires:

- confirmed 4H breakout close;
- supportive HTF context;
- structural stop;
- R:R >= 2:1;
- entry not late.

Execution remains manual.

## 11. Required Claude output

When this module is detected, Claude must clearly label it:

Strategy Module: ETHUSD_4H_LONG_BREAKOUT_CONTINUATION  
Classificação: SETUP_VALIDO or SETUP_CANDIDATO_FORTE  
Direção: LONG  
Timeframe: 4H  
Trigger: BREAKOUT_CONTINUATION  
Priority: A/B/C  

Claude must include:

- breakout level;
- entry reference;
- stop técnico;
- R:R estimado;
- target reference around 5R;
- whether runner to 8R is justified;
- breakeven rule after +1R;
- invalidation;
- whether entry is late;
- note that execution is manual.

## 12. Telegram formatting

Recommended title:

🟢 [ETHUSD 4H LONG BREAKOUT CONTINUATION]

Required fields:

- Strategy Module: ETHUSD_4H_LONG_BREAKOUT_CONTINUATION
- Classificação:
- Direção: LONG
- Timeframe: 4H
- Trigger: BREAKOUT_CONTINUATION
- Priority:
- Entry: manual review
- Stop: structural
- Management: BE after +1R, target reference 5R
- Runner: only if Priority A

Include:

This is the ETHUSD 4H breakout continuation module.  
Not intraday.  
Not reversal.  
Manual execution only.

## 13. Research status

This module is approved for experimental monitoring.

It is not yet a permanent strategy_rules.json rule.

Before permanent adoption, continue tracking:

- live occurrences;
- D2 outcomes;
- D2R outcomes;
- false breakouts;
- late entries;
- performance by market regime;
- whether 5R remains optimal;
- whether Priority A runner to 8R is justified.

## 14. Current decision

Implement as a separate experimental ETHUSD 4H module.

Do not create ETHUSD intraday module yet.
