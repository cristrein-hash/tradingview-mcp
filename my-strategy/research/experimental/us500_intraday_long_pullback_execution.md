# US500_INTRADAY_LONG_PULLBACK_EXECUTION — DEACTIVATED

**Status: DEACTIVATED em 2026-05-12** — substituído por `US500_1H_LONG_BREAKOUT_REGIME_FILTERED` (SETUP_CANDIDATO_FORTE).

**Razão da desativação:**

Audit profundo de backtest CSV em 2026-05-12 (1.3 anos, n=943 trades) mostrou:

- Total Net R @ 0.05R: **-105.20R** (CATASTROFICAMENTE NEGATIVO)
- Avg R: -0.112
- Profit Factor: **0.78**
- Win rate: 17.9%
- Max losing streak: 32
- Frequência absurda: 14 trades/semana
- Sem top 10: -144.70R

Foi o **pior módulo de todo o sistema** em backtest. Cada semana sangrava ~2R/semana em comissão líquida negativa.

Razões prováveis do fracasso:
- 30M pullback "execution" em índice large-cap não tem edge — mercado eficiente demais
- 14 trades/sem garante exposição máxima ao spread (custos compounding)
- Backtest original que justificava o módulo não foi reproduzível com regras escritas

**Comportamento operacional:**
- Não deve mais gerar `SETUP_VALIDO_INTRADAY` nem `SETUP_CANDIDATO_FORTE`.
- Eventos não devem ser roteados para este módulo.
- Para intraday LONG em US500, usar `US500_1H_LONG_BREAKOUT_REGIME_FILTERED` (SETUP_CANDIDATO_FORTE com revisão manual).
- SHORT em US500 continua **NÃO automatizado** — bias bull estrutural.

**Substituto operacional:**
`US500_1H_LONG_BREAKOUT_REGIME_FILTERED` (+18.93R net em 2.3y, PF 1.22, edge marginal mas positivo com filtros HTF 1D + 4H).

**Conteúdo abaixo mantido apenas como histórico de research.**

---

## Histórico (não usar como referência operacional)

Asset: PEPPERSTONE:US500  
Strategy Layer: Intraday (DESCONTINUADO)
Direction: LONG only (DESCONTINUADO)
Context TFs: 4H + 1H  
Setup TF: 30M  
Execution TF: 15M  
Execution: manual only  

## 1. Purpose

This module defines a US500 intraday long-only pullback execution strategy.

It is independent from:

- US500_4H_LONG_PULLBACK_REJECTION
- XAUUSD_4H_LONG_REJECTION_SWING
- XAUUSD_1H_LONG_REJECTION_EXECUTION
- XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION
- generic dynamic-zone monitoring

The goal is to capture frequent intraday long pullbacks in US500 while preserving quality through 4H/1H context and 15M execution confirmation.

## 2. Backtest basis

Historical offline backtest using exported TradingView CSV data:

- 15M
- 30M
- 1H
- 4H

Best quality model:

- LONG only
- 4H/1H bullish or supportive context
- pullback/rejection structure
- 15M execution trigger
- score threshold equivalent to high-quality setup
- structural stop
- breakeven after +1R
- target 4R
- max hold: 48 candles of 15M
- cooldown: 48 candles of 15M

Observed quality model result:

- approx. 71 trades
- approx. 2.9 trades per week
- total theoretical result: approx. +43R
- average result: approx. +0.60R per trade
- max losing streak: 3

Observed frequency model result:

- approx. 117 trades
- approx. 4.9 trades per week
- total theoretical result: approx. +71R
- average result: approx. +0.60R per trade
- max losing streak: 4

Interpretation:

The module is suitable for experimental forward monitoring. The quality model should be used for SETUP_VALIDO_INTRADAY. The frequency model can be used for SETUP_CANDIDATO_FORTE_INTRADAY with manual review.

## 3. Core principle

No shorts.

US500 intraday edge comes from long pullbacks in bullish/supportive context.

Do not attempt to call tops or short price discovery.

Valid structure:

4H/1H supportive context  
+ 30M pullback/reaction  
+ 15M execution trigger  
+ clear stop  
+ R:R >= 2:1

## 4. Timeframe hierarchy

4H:
- primary regime filter;
- avoid strong bearish breakdown;
- identify whether index is in bullish/supportive structure.

1H:
- confirms intraday context;
- identifies decision zones and pullback areas.

30M:
- setup forming;
- pullback/reaction area;
- candidate layer.

15M:
- execution trigger;
- rejection close;
- reclaim;
- micro-break;
- CHoCH/BOS;
- invalidation refinement.

## 5. SETUP_VALIDO_INTRADAY requirements

Use SETUP_VALIDO_INTRADAY when all are true:

1. Asset is PEPPERSTONE:US500.
2. Direction is LONG.
3. 4H/1H context is bullish or supportive.
4. Price has pulled back into a relevant support/demand/pullback area.
5. 30M shows reaction or constructive pullback behavior.
6. 15M confirms execution trigger.
7. Stop is structural and clear.
8. R:R >= 2:1.
9. Entry is not late/chasing.
10. MCP/chart reading is reliable.

Preferred management:

- BE after +1R;
- target reference: 4R;
- max hold: around 48 x 15M candles;
- manual execution only.

## 6. SETUP_CANDIDATO_FORTE_INTRADAY requirements

Use SETUP_CANDIDATO_FORTE_INTRADAY when:

- 4H/1H context is bullish/supportive;
- 30M setup is forming;
- price is near a relevant pullback/support area;
- stop and R:R are plausible;
- 15M trigger is incomplete or only partially confirmed.

This should go to Telegram as human review.

It is not automatic entry.

## 7. Valid execution triggers

Allowed 15M triggers:

- REJECTION_CLOSE
- SWEEP_REENTRY
- RETEST_HOLD
- CHOCH_BOS
- MICRO_BREAK_RECLAIM
- NAS_LONG_AT_PULLBACK

A single NAS signal, bubble, RSI reading or zone touch is not enough.

## 8. Priority score

Priority A:

- 4H/1H bullish context;
- 30M pullback reaction confirmed;
- 15M trigger confirmed;
- stop clear;
- R:R >= 2:1;
- entry not late;
- preferably NAS LONG/BOTTOM or seller bubble supports the pullback.

Priority B:

- 4H/1H context supportive;
- 30M setup forming;
- 15M trigger partial;
- stop/R:R plausible;
- needs human review.

Priority C:

- area interesting but trigger incomplete;
- weak confluence;
- wait only.

## 9. Hard blocks

Do not classify as SETUP_VALIDO_INTRADAY if:

- direction is SHORT;
- 4H/1H context is bearish breakdown;
- no pullback;
- price is extended/chasing;
- no 15M trigger;
- no clear stop;
- R:R < 2:1;
- signal is only NAS/bubble/RSI/zone touch;
- MCP/chart reading unreliable;
- macro red window is immediate.

## 10. Management

Default:

- Entry: manual review around 15M trigger / retest / rejection close.
- Stop: structural, below 15M/30M pullback low or invalidation.
- Move stop to breakeven after +1R.
- Target reference: 4R.
- Max hold: around 48 candles of 15M.
- If price moves too far from ideal entry, do not chase.

## 11. Required Claude output

When this module is relevant, Claude must include:

Strategy Module: US500_INTRADAY_LONG_PULLBACK_EXECUTION  
Intraday Context: 4H / 1H  
Setup TF: 30M  
Execution TF: 15M  
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

## 12. Telegram formatting

Recommended title:

🟢 [US500 INTRADAY LONG PULLBACK]

Required fields:

- Strategy Module: US500_INTRADAY_LONG_PULLBACK_EXECUTION
- Classificação:
- Direção: LONG
- Priority:
- Context: 4H / 1H
- Setup: 30M
- Execution: 15M
- Trigger:
- Entry status:
- Stop:
- R:R:
- Management: BE after +1R, target reference 4R
- Manual execution only.

## 13. Research status

This module is experimental.

Track separately in D1, D2 and D2R.

Before permanent adoption:

- collect 30–50 live/D2R events;
- separate Priority A/B/C;
- measure total R;
- measure average R;
- measure max losing streak;
- confirm that frequency remains at least around 2 trades/week;
- verify that false positives do not cluster during weak regimes.

## 14. Current decision

Implement as a separate experimental US500 intraday module.

Do not merge with US500_4H_LONG_PULLBACK_REJECTION yet.
