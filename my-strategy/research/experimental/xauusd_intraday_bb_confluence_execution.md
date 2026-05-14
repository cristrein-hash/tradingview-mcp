# XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION

Status: experimental / forward-test only  
Asset: PEPPERSTONE:XAUUSD  
Strategy Layer: Intraday  
Primary Context: 4H + 1H  
Setup TF: 30M  
Execution TF: 15M  
Direction: LONG and SHORT allowed  
Execution: manual only  

## 1. Purpose

This module defines a separate intraday strategy for XAUUSD using multi-timeframe BigBeluga / BB / SMC confluence.

It is independent from:

- XAUUSD_4H_LONG_REJECTION_SWING
- XAUUSD_1H_LONG_REJECTION_EXECUTION
- generic intraday dynamic-zone monitoring

The purpose is to increase trade frequency while keeping structure and confirmation requirements strict.

## 2. Timeframe hierarchy

4H:
- macro intraday context;
- major supply/demand;
- structural bias;
- avoid trading directly into major opposing zones.

1H:
- primary decision zone;
- main intraday demand/supply;
- determines whether the area is worth monitoring.

30M:
- setup confirmation;
- reaction quality;
- candidate-strong layer.

15M:
- execution trigger;
- CHoCH/BOS;
- retest;
- sweep/reentry;
- invalidation refinement.

## 3. Core principle

No trade from a single signal.

A valid intraday setup requires:

HTF zone/context  
+ 1H/30M reaction  
+ 15M execution trigger  
+ clear stop  
+ R:R >= 2:1

## 4. LONG setup requirements

A LONG setup requires:

1. Price is near or inside relevant 4H/1H demand/support.
2. 30M shows reaction, reclaim, rejection, or sweep/reentry.
3. 15M confirms with at least one:
   - bullish CHoCH/BOS;
   - sweep + reentry;
   - bullish rejection close;
   - retest hold;
   - NAS LONG / BOTTOM near the zone.
4. Stop is technical:
   - below zone;
   - below sweep low;
   - below 15M/30M swing low.
5. R:R >= 2:1.
6. No immediate macro red window.
7. MCP/chart reading is reliable.

## 5. SHORT setup requirements

A SHORT setup requires:

1. Price is near or inside relevant 4H/1H supply/resistance.
2. 30M shows rejection, failure, distribution, or sweep/reentry.
3. 15M confirms with at least one:
   - bearish CHoCH/BOS;
   - sweep + reentry;
   - bearish rejection close;
   - retest failure;
   - NAS SHORT / TOP near the zone.
4. Stop is technical:
   - above zone;
   - above sweep high;
   - above 15M/30M swing high.
5. R:R >= 2:1.
6. No immediate macro red window.
7. MCP/chart reading is reliable.

## 6. SETUP_CANDIDATO_FORTE_INTRADAY

Use this when:

- 4H/1H zone is relevant;
- price is reacting in or near the zone;
- 30M confirms the setup is forming;
- stop and R:R are plausible;
- 15M trigger is not fully confirmed yet.

This classification should go to Telegram as review/human attention.

It is not automatic entry.

## 7. SETUP_VALIDO_INTRADAY

Use this only when:

- context is valid;
- setup is formed;
- 15M execution trigger is present;
- stop is clear;
- R:R >= 2:1;
- entry is not late/chasing.

SETUP_VALIDO_INTRADAY is still manual execution only.

## 8. Priority score

Priority A:
- 4H + 1H zone alignment;
- 30M reaction confirmed;
- 15M trigger confirmed;
- NAS signal aligned;
- R:R >= 2:1;
- stop clear.

Priority B:
- 1H/30M zone alignment;
- reaction present;
- one execution trigger present;
- R:R valid;
- some confluence missing.

Priority C:
- area is interesting but trigger is incomplete;
- use for observation only unless trigger appears.

## 9. Promotion triggers

Allowed triggers:

- REJECTION_CLOSE
- SWEEP_REENTRY
- CHOCH_BOS
- BREAKOUT_RETEST
- RETEST_HOLD
- NAS_SIGNAL_AT_ZONE

Dense confluence alone is not enough for SETUP_VALIDO_INTRADAY.

## 10. Hard blocks

Do not classify as SETUP_VALIDO_INTRADAY if:

- no 15M trigger;
- no clear stop;
- R:R < 2:1;
- price already moved too far from ideal entry;
- chart/MCP reading unreliable;
- only a dry zone touch;
- range tight with no direction;
- signal is purely RSI, NAS, bubble, or zone touch alone;
- macro red window is immediate.

## 11. Management

Default management:

- Entry: manual, near 15M trigger/retest/reentry.
- Stop: structural, beyond invalidation.
- Move stop to breakeven after +1R only if structure supports.
- First target: 2R.
- Extended target: 3R or next HTF zone.
- If price moves too far before entry, do not chase; wait for retest.

## 12. Required Claude output

When this module is relevant, Claude must include:

Strategy Module: XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION  
Intraday Context: 4H / 1H  
Setup TF: 30M  
Execution TF: 15M  
Priority: A/B/C  
Classificação:  
Direção:  
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

## 13. Telegram formatting

Recommended title:

🟠 [XAUUSD INTRADAY BB CONFLUENCE]

Required fields:

- Strategy Module: XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION
- Classificação:
- Direção:
- Priority:
- Context: 4H / 1H
- Setup: 30M
- Execution: 15M
- Trigger:
- Entry status:
- Stop:
- R:R:
- Manual execution only.

## 14. Research status

This module is experimental.

It must be tracked separately in D1, D2, and D2R.

Do not merge with the 4H or 1H XAUUSD modules.

Before adoption:
- collect at least 30–50 D2R events;
- measure total R;
- measure average R;
- separate LONG vs SHORT;
- separate Priority A/B/C;
- identify false positives;
- identify late-entry problems.
