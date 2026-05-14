# US500_4H_LONG_PULLBACK_REJECTION — DEACTIVATED

**Status: DEACTIVATED em 2026-05-12** — substituído por `US500_4H_LONG_FAILED_BREAKDOWN_REGIME`.

**Razão da desativação:**

Audit profundo de backtest CSV em 2026-05-12 (4.4 anos, n=412 trades) mostrou:

- Total Net R @ 0.05R: **-67.65R** (NEGATIVO)
- Avg R: -0.164
- Profit Factor: **0.68**
- Win rate: **12.9%** (catastrófico)
- Max losing streak: 35
- **TODOS os anos negativos** (2022 -11R, 2023 -21R, 2024 -5R, 2025 -28R, 2026 -2R)

Win rate de 13% torna o target 4.5R **matematicamente impossível** de gerar edge — precisaria de win rate >= 22% para empatar.

Razões prováveis do fracasso:
- "Pullback rejection" no índice large-cap mais eficiente do mundo é capturado pelos algos institucionais
- Pavios em índices não predizem reversão como em FX/cripto
- Backtest original v0.3 provavelmente foi em janela favorável + small sample

**Comportamento operacional:**
- Não deve mais gerar `SETUP_VALIDO`.
- Eventos novos devem usar `US500_4H_LONG_FAILED_BREAKDOWN_REGIME` se critérios deste se aplicam, ou classificação inferior.

**Substituto operacional ativo:**
`US500_4H_LONG_FAILED_BREAKDOWN_REGIME` (+15.26R net em 4.4y, PF 1.83, todos os anos completos positivos).

**Conteúdo abaixo mantido apenas como histórico de research.**

---

## Histórico (não usar como referência operacional)

Asset: PEPPERSTONE:US500  
Timeframe: 4H  
Direction: LONG only  
Strategy Layer: Swing / Index Pullback (DESCONTINUADO)
Signal Level: SETUP_VALIDO only (DESCONTINUADO)
Execution: manual only  

## 1. Purpose

This module defines a separate 4H long-only pullback/rejection strategy for US500.

It is independent from:

- XAUUSD_4H_LONG_REJECTION_SWING
- XAUUSD_1H_LONG_REJECTION_EXECUTION
- XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION
- generic intraday dynamic-zone monitoring

The purpose is to capture high-quality US500 long pullbacks in bullish regimes.

## 2. Backtest basis

Historical offline backtest using exported TradingView CSV data.

Instrument:
PEPPERSTONE:US500

Timeframe:
4H

Sample:
2021-12 to 2026-05

Best tested version:
US500 4H v0.3 management/robustness

Best model:
- LONG only
- pullback/rejection in bullish regime
- structural stop
- move stop to breakeven after +1R
- hard target 4.5R
- no trailing
- no shorts

Observed result:
- 39 trades
- total theoretical result: approximately +23.53R
- average result: approximately +0.60R per trade
- max losing streak: 3
- positive across 2023, 2024, 2025
- 2022 was negative

Interpretation:
The module is suitable for experimental monitoring as a US500-specific swing strategy. It is not a generic reversal strategy and should not be applied symmetrically to shorts.

## 3. Core setup

A valid setup requires:

1. Asset is PEPPERSTONE:US500.
2. Timeframe is 4H.
3. Direction is LONG only.
4. Context is bullish or structurally supportive.
5. Price pulls back into a relevant demand/support/pivot area.
6. Candle closes with bullish rejection or constructive pullback reaction.
7. Stop is structural and clearly defined.
8. R:R is at least 2:1, preferably toward 4.5R target.
9. Setup is not a falling knife.
10. MCP/chart reading is reliable.

## 4. Bull regime definition

Bull regime is preferred when at least one of the following is true:

- price above relevant moving-average structure;
- higher-high / higher-low structure intact;
- price in broad bullish continuation;
- pullback occurs after prior bullish impulse;
- 4H context is not bearish breakdown;
- demand zones are being respected.

If regime is mixed, require stronger rejection and clearer stop/R:R.

If regime is clearly bearish, do not classify as this module.

## 5. Pullback/rejection definition

A valid bullish pullback/rejection requires:

- price pulls back into demand/support;
- candle rejects lower prices;
- close is away from the low;
- close supports bullish continuation;
- stop can be placed structurally below the pullback low/demand;
- target toward 4.5R remains plausible.

This module is not based on dry zone touch alone.

## 6. Management rules

Default management:

- Entry: manual review near 4H rejection close.
- Stop: structural stop below pullback/rejection low or demand boundary.
- Move stop to breakeven after +1R.
- Target: 4.5R.
- Do not use trailing by default.
- Do not take early partials by default.
- Let valid index pullbacks breathe.

## 7. What this module is NOT

This module is not:

- a SHORT strategy;
- a top-calling strategy;
- a price-discovery short strategy;
- a 1H/30M/15M intraday module;
- a zone-touch strategy;
- a NAS-only setup;
- a bubble-only setup;
- an automatic entry model.

## 8. Disallowed signals

Do not classify as this module if any are true:

- direction is SHORT;
- timeframe is not 4H;
- no bullish pullback/rejection;
- price is in clear bearish breakdown;
- no clear stop;
- R:R < 2:1;
- entry is late/chasing far from the pullback area;
- signal is only RSI, NAS, bubble, or zone touch;
- MCP/chart reading is unreliable;
- macro red window is immediate.

## 9. SETUP_CANDIDATO_FORTE behavior

SETUP_CANDIDATO_FORTE may be used as preparation only.

It means:

- US500 4H is approaching a potentially valid long pullback area;
- human attention is justified;
- no entry yet;
- final SETUP_VALIDO requires rejection/pullback confirmation and valid R:R.

Do not treat SETUP_CANDIDATO_FORTE as entry.

## 10. SETUP_VALIDO behavior

Classify as SETUP_VALIDO only when:

- bull regime/supportive structure is present;
- 4H pullback/rejection is confirmed;
- stop is structural and clear;
- R:R is valid;
- entry is not late.

Execution remains manual.

## 11. Required Claude output

When this module is detected, Claude must clearly label it:

Strategy Module: US500_4H_LONG_PULLBACK_REJECTION  
Classificação: SETUP_VALIDO or SETUP_CANDIDATO_FORTE  
Direção: LONG  
Timeframe: 4H  
Trigger: PULLBACK_REJECTION  
Priority: A/B/C  

Claude must include:

- entry reference;
- stop técnico;
- R:R estimado;
- target reference around 4.5R;
- breakeven rule after +1R;
- invalidation;
- whether entry is late;
- note that execution is manual.

## 12. Telegram formatting

Recommended title:

🟢 [US500 4H LONG PULLBACK REJECTION]

Required message elements:

- Strategy Module: US500_4H_LONG_PULLBACK_REJECTION
- Classificação:
- Direção: LONG
- Timeframe: 4H
- Trigger: PULLBACK_REJECTION
- Entry: manual review
- Stop: structural
- Management: BE after +1R, target 4.5R, no trailing by default

Include:

This is the US500 4H long-only pullback module.  
Not a short strategy.  
Not intraday.  
Manual execution only.

## 13. Research status

This module is approved for experimental monitoring.

It is not yet a permanent strategy_rules.json rule.

Before permanent adoption, continue tracking:

- live occurrences;
- D2 outcomes;
- D2R outcomes;
- false positives;
- missed valid setups;
- performance by year/regime;
- whether 4.5R remains optimal;
- whether 2022-style weak regimes can be filtered better.

## 14. Current decision

Implement as a separate experimental US500 4H module.

Do not merge with broader swing/intraday strategy yet.
