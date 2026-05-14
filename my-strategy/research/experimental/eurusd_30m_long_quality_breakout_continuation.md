# EURUSD_30M_LONG_QUALITY_BREAKOUT_CONTINUATION — DEACTIVATED

**Status: DEACTIVATED em 2026-05-12** — sem substituto direto.

**Razão da desativação:**

Audit profundo de backtest CSV em 2026-05-12 (1.4 anos, n=605 trades) mostrou:

- Total Net R @ 0.05R: **-104.34R** (CATASTROFICAMENTE NEGATIVO)
- Avg R: -0.173
- Profit Factor: **0.65**
- Win rate: 21.5%
- Max losing streak: 23
- Frequência: 8.8 trades/semana (overtrade)
- Sem top 10: -133.84R

Foi um dos piores módulos do sistema. Cada semana sangrava ~2R em comissão líquida negativa.

**Testes adicionais feitos no mesmo audit:**

Foram testadas 40+ alternativas para EURUSD:
- Regime-filtered breakout (XAU/ETH pattern): +3.64R apenas (edge zero)
- Failed breakdown (US500 winner): apenas 17 trades em 7.4y, sample inutilizável
- Pullback EMA20/EMA50: -73R a -149R (catastrófico)
- Inside bar / Hammer / RSI oversold bounce: todos negativos
- London open breakout: -15R a -21R
- BB squeeze: -5R a -18R
- **Macro DXY filter: não ajuda (contraintuitivo mas comprovado)**
- Multi-TF strict alignment: catastrófico (-233R a -277R)

**NENHUMA estratégia testada atendeu critérios mínimos para SETUP_VALIDO em EURUSD.**

**Razão estrutural:**

EURUSD é o par forex mais líquido do mundo ($1.5T/dia de volume). Mercado eficiente onde estratégias técnicas simples raramente entregam edge sustentável. Preços determinados por Fed/ECB events, yield differentials e carry trades — não por candle patterns.

**Comportamento operacional:**

- NÃO deve mais gerar `SETUP_VALIDO_INTRADAY` nem `SETUP_CANDIDATO_FORTE`.
- Eventos não devem ser roteados para este módulo.
- EURUSD permanece na watchlist mas **sem módulo operacional automático**.
- Pode ser lido para contexto USD strength/weakness mas não para sinal.

**Aguardando validação futura:**

- Fase 1 Passive Logging do External Market Factors (iMac analyst, 2026-05-12) pode revelar valor preditivo macro previously inacessível em backtest CSV
- Após 50+ eventos com macro logado + outcomes em D2R, decidir se há base para criar módulo EURUSD_MACRO_VALIDATED

**Conteúdo abaixo mantido apenas como histórico de research.**

---

## Histórico (não usar como referência operacional)

Asset: PEPPERSTONE:EURUSD  
Strategy Layer: Intraday / Forex Breakout Continuation (DESCONTINUADO)
Context TFs: 4H + 12H + 1D  
Setup TF: 30M  
Execution TF: 30M / 15M refinement  
Direction: LONG only (DESCONTINUADO)
Execution: manual only  

## 1. Purpose

This module defines a EURUSD intraday long-only quality breakout continuation strategy.

It is independent from:

- XAUUSD modules
- US500 modules
- ETHUSD modules
- generic dynamic-zone monitoring

The goal is to capture quality 30M bullish continuation breakouts in EURUSD with supportive higher-timeframe context and moderate targets.

## 2. Backtest basis

Historical offline backtest using exported TradingView CSV data.

Timeframes analyzed:
- 1D
- 12H
- 4H
- 30M
- 15M

Best tested version:
EURUSD v0.2 refinement

Best model:
- LONG only
- 30M quality breakout
- lookback: approx. 20 candles
- RSI minimum: approx. 54
- strong/quality breakout candle
- 4H/12H/1D supportive context
- structural stop
- move stop to breakeven after +1R
- target reference: 3R
- max hold: approx. 48 candles of 30M
- cooldown: approx. 16 candles of 30M

Observed result:
- approx. 150 trades
- approx. 2.16 trades per week
- total theoretical result: approx. +59R
- average result: approx. +0.39R per trade
- win rate: approx. 46%
- max losing streak: 5

Interpretation:
EURUSD performed best as a 30M long-only quality breakout continuation strategy. Generic swing/rejection and short models did not validate in the first searches.

## 3. Core principle

Do not trade EURUSD from a single signal.

A valid setup requires:

HTF supportive context  
+ 30M quality bullish breakout  
+ RSI/momentum confirmation  
+ clear stop  
+ R:R >= 2:1  
+ entry not late

This module is manual execution only.

## 4. LONG setup requirements

A valid LONG setup requires:

1. Asset is PEPPERSTONE:EURUSD.
2. Setup timeframe is 30M.
3. Direction is LONG.
4. 4H/12H/1D context is bullish or supportive.
5. 30M candle breaks above recent structure/high.
6. Breakout candle is strong enough, not weak/wicky.
7. RSI 30M is supportive, preferably >= 54.
8. Stop is technical and clear.
9. R:R >= 2:1.
10. Entry is not late/chasing.
11. MCP/chart reading is reliable.

## 5. Quality breakout definition

A quality bullish breakout requires:

- 30M close above recent structure/high;
- close near the upper portion of the candle;
- candle has meaningful body/expansion;
- breakout is not just a wick above resistance;
- context does not contradict the move;
- stop can be placed structurally below breakout base / pullback low;
- target path toward 3R is realistic.

## 6. Valid triggers

Allowed triggers:

- QUALITY_BREAKOUT
- BREAKOUT_RETEST
- RETEST_HOLD
- MICRO_BREAK_RECLAIM
- RSI_MOMENTUM_RECLAIM
- 15M_CONFIRMATION_RETEST

Do not use zone touch alone.

## 7. Priority score

Priority A:
- HTF context clearly supportive;
- 30M quality breakout confirmed;
- RSI supportive;
- stop clear;
- R:R >= 2:1;
- entry not late;
- path to 3R relatively clean.

Priority B:
- breakout valid;
- HTF context acceptable but not perfect;
- R:R valid;
- manual review required.

Priority C:
- breakout forming but not confirmed;
- wait only.

## 8. Management rules

Default management:

- Entry: manual review after confirmed 30M breakout close or controlled retest.
- Stop: structural stop below breakout base / swing low / invalidation level.
- Move stop to breakeven after +1R.
- Target reference: 3R.
- Max hold reference: approx. 48 candles of 30M.
- Do not chase if price already moved too far from ideal entry.
- Execution is manual only.

## 9. What this module is NOT

This module is not:

- a SHORT strategy;
- a 4H swing strategy;
- a range-fade strategy;
- a zone-touch strategy;
- a NAS-only setup;
- a bubble-only setup;
- an automatic entry model.

## 10. Hard blocks

Do not classify as SETUP_VALIDO_INTRADAY if:

- direction is SHORT;
- no confirmed 30M quality breakout;
- RSI/momentum does not support continuation;
- HTF context is bearish or strongly contradictory;
- no clear stop;
- R:R < 2:1;
- entry is late/chasing;
- signal is only RSI/NAS/bubble/zone touch;
- MCP/chart reading unreliable;
- macro red window is immediate.

## 11. SETUP_CANDIDATO_FORTE_INTRADAY behavior

Use SETUP_CANDIDATO_FORTE_INTRADAY when:

- EURUSD 30M breakout is forming;
- HTF context is supportive or acceptable;
- R:R may be valid if confirmation appears;
- but the 30M close/retest is not fully confirmed yet.

This is preparation only. It is not automatic entry.

## 12. SETUP_VALIDO_INTRADAY behavior

Use SETUP_VALIDO_INTRADAY only when:

- 30M quality breakout is confirmed;
- HTF context is supportive;
- stop is clear;
- R:R >= 2:1;
- entry is not late.

Execution remains manual.

## 13. Required Claude output

When this module is relevant, Claude must clearly label it:

Strategy Module: EURUSD_30M_LONG_QUALITY_BREAKOUT_CONTINUATION  
Intraday Context: 4H / 12H / 1D  
Setup TF: 30M  
Execution TF: 30M / 15M  
Priority: A/B/C  
Classificação:  
Direção: LONG  
Trigger:  
Promotion trigger:  
Promotion status:  
R:R estimado:  
Stop técnico:  
Entrada ideal:  
Preço atual:  
Entrada atrasada: SIM/NÃO  
Gatilho faltante:  
Ação tomada:  
Próxima ação:  

## 14. Telegram formatting

Recommended title:

🟢 [EURUSD 30M LONG QUALITY BREAKOUT]

Required fields:

- Strategy Module: EURUSD_30M_LONG_QUALITY_BREAKOUT_CONTINUATION
- Classificação:
- Direção: LONG
- Priority:
- Context: 4H / 12H / 1D
- Setup: 30M
- Execution: 30M / 15M
- Trigger:
- Entry status:
- Stop:
- R:R:
- Management: BE after +1R, target reference 3R
- Manual execution only.

## 15. Research status

This module is experimental.

Track separately in D1, D2 and D2R.

Before permanent adoption:

- collect 30–50 live/D2R events;
- separate Priority A/B/C;
- measure total R;
- measure average R;
- measure max losing streak;
- verify behavior across London and NY sessions;
- validate that target 3R remains appropriate.

## 16. Current decision

Implement as a separate EURUSD intraday module.

Do not create EURUSD swing module yet.
