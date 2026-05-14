# XAUUSD_4H_LONG_REJECTION_SWING — DEACTIVATED

**Status: DEACTIVATED em 2026-05-12** — substituído por `XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED`.

**Razão da desativação:**

Audit profundo de backtest CSV em 2026-05-12 (7.4 anos, n=1070 trades) mostrou:
- Total R em backtest: **-59.3R** (negativo)
- Avg R: -0.055
- Profit factor: 0.88
- Mesmo com filtro RSI <= 40 adicionado, edge permaneceu marginal/negativo

A premissa original (rejection close em 4H como swing seletivo) não se validou no histórico amplo. O backtest v1.3 mencionado abaixo provavelmente sofreu de sample insuficiente ou seleção de janela favorável.

**Comportamento operacional:**
- Não deve mais gerar `SETUP_VALIDO`.
- Pode aparecer em logs históricos; mapeamento para nova classificação via régua manual.
- Conteúdo abaixo mantido apenas como histórico de research.

**Substituto operacional ativo:**
`XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED` (+64.57R net em 7.4 anos, PF 1.64).

---

## Histórico (não usar como referência operacional)

Asset: PEPPERSTONE:XAUUSD  
Timeframe: 4H  
Direction: LONG only  
Strategy Layer: Swing  
Signal Level: SETUP_VALIDO only (DESCONTINUADO)
Execution: manual only  

## 1. Purpose (histórico)

This module defined a separate, rare, high-quality swing strategy for XAUUSD 4H.

It was independent from the broader swing/intraday strategy.

The purpose is to capture long swing opportunities in XAUUSD when price rejects a relevant demand/support area with a confirmed rejection close and valid R:R.

## 2. Backtest basis

Historical offline backtest using exported TradingView CSV data:

- Instrument: PEPPERSTONE:XAUUSD
- Timeframe: 4H
- Sample: approx. 2021-08 to 2026-05
- Direction: LONG only
- Trigger: REJECTION_CLOSE only
- Trade mode: SETUP_VALIDO only
- Management:
  - structural stop
  - move stop to breakeven after +1R
  - trailing stop after +3R
  - trailing distance: 1.5R

Best tested version:
v1.3 trailing sensitivity

Observed result:
- 9 valid trades
- total theoretical result: approximately +10.55R
- average result: approximately +1.17R per trade
- max losing streak: 1

Interpretation:
The module is rare but high-quality. It should be monitored separately as a swing layer.

## 3. Core setup

A valid setup requires all of the following:

1. Asset is PEPPERSTONE:XAUUSD.
2. Timeframe is 4H.
3. Direction is LONG only.
4. Trigger is REJECTION_CLOSE.
5. Price reacts from a relevant demand/support region.
6. Candle closes with clear bullish rejection.
7. Stop is structural and clearly defined.
8. R:R is at least 2:1.
9. Regime filter does not indicate strong falling-knife / bear continuation.
10. Setup is not based only on CHOCH/BOS, sweep/reentry, or candidate context.

## 4. Rejection close definition

A bullish rejection close requires:

- price touches or sweeps a relevant demand/support area;
- candle leaves a meaningful lower wick;
- candle closes away from the low;
- close supports the LONG thesis;
- stop can be placed structurally below the rejection/swing low;
- planned R:R remains valid.

## 5. Management rules

Default management:

- Entry: close of the 4H rejection candle.
- Stop: structural stop below the rejection low / demand boundary.
- Move stop to breakeven after +1R.
- Do not take partial profit early by default.
- Activate trailing only after +3R.
- Trailing distance: 1.5R.
- Let the trade breathe.

## 6. What this module is NOT

This module is not:

- an intraday setup;
- a 1H / 30M / 15M execution model;
- a SHORT strategy;
- a SETUP_CANDIDATO_FORTE entry;
- a sweep/reentry-only setup;
- a CHOCH/BOS-only setup;
- a generic dynamic zone touch.

## 7. Disallowed signals

Do not classify this module as valid if any are true:

- direction is SHORT;
- timeframe is not 4H;
- setup is only SETUP_CANDIDATO_FORTE;
- trigger is only SWEEP_REENTRY;
- trigger is only CHOCH_BOS;
- price is in strong falling-knife continuation;
- stop is unclear;
- R:R is below 2:1;
- rejection candle is not closed;
- entry would be a chase far from the rejection zone;
- MCP/chart reading is unreliable.

## 8. Required Claude output

When this module is detected, Claude must clearly label it:

Strategy Module: XAUUSD_4H_LONG_REJECTION_SWING  
Classificação: SETUP_VALIDO  
Direção: LONG  
Timeframe: 4H  
Trigger: REJECTION_CLOSE  

Claude must also include:

- entry reference;
- stop técnico;
- R:R estimado;
- management plan;
- invalidation;
- note that execution is manual.

## 9. Telegram formatting

Telegram should make this module visually distinct.

Recommended title:

🟢 [XAUUSD 4H LONG REJECTION SWING]

Required message elements:

- Strategy Module: XAUUSD_4H_LONG_REJECTION_SWING
- Classificação: SETUP_VALIDO
- Direção: LONG
- Timeframe: 4H
- Trigger: REJECTION_CLOSE
- Entry: manual review
- Stop: structural
- Management: BE after +1R, trailing after +3R with 1.5R distance

Include:

This is a rare 4H swing module.  
Not intraday.  
Not candidate-only.  
Manual execution only.

## 10. Research status

This module is approved for experimental monitoring.

It is not yet a permanent strategy_rules.json rule.

Before permanent adoption, continue tracking:
- live occurrences;
- D2 outcomes;
- D2R outcomes;
- false positives;
- missed valid setups;
- whether trailing after +3R remains optimal.

## 11. Current decision

Implement as a separate experimental swing module.

Do not merge with the broader swing/intraday strategy yet.
