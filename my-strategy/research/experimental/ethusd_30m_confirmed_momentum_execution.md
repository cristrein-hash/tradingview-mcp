# ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION — DEACTIVATED

**Status: DEACTIVATED em 2026-05-12** — sem substituto direto. Não opera mais como módulo válido.

**Razão da desativação:**

Audit profundo de backtest CSV em 2026-05-12 (1.4 anos disponíveis no 30M, n=2061 trades combinados) mostrou:

| Direção | Trades | Total Net R @ 0.05R | Avg R | PF | Win% |
|---|---:|---:|---:|---:|---:|
| LONG (atual) | 1078 | **-170.20R** | -0.158 | 0.67 | 25.7% |
| SHORT (atual) | 983 | -94.99R | -0.097 | 0.78 | 25.8% |
| Combined | 2061 | **-265.20R** | -0.129 | 0.72 | 25.8% |

A configuração com "1+ confirmação adicional (NAS / bubble / divergência / RSI reclaim / retest hold / CHoCH-BOS)" é **idêntica em resultado** à configuração sem confirmação — o filtro não exclui losses. Edge não foi reproduzido nos dados disponíveis.

O backtest original que apontava +144R / 542 trades não é reproduzível com as regras atuais. Possíveis razões:
- Período de backtest original diferente (window favorável)
- Parâmetros de stop/target/management diferentes
- Definição de "momentum confirmado" mais restritiva

**Comportamento operacional:**
- NÃO deve mais gerar `SETUP_VALIDO_INTRADAY` nem `SETUP_CANDIDATO_FORTE`.
- Eventos não devem ser roteados para este módulo.
- Para sinais intraday em ETHUSD, usar `ETHUSD_1H_LONG_PULLBACK_EMA50_REGIME` (LONG only).
- SHORT em ETHUSD **não tem edge sistemático** em nenhum TF testado — não automatizar.

**Substituto operacional:**
- Intraday LONG ETH: `ETHUSD_1H_LONG_PULLBACK_EMA50_REGIME` (+23.19R / 1.4y, PF 1.68)
- Intraday SHORT ETH: NENHUM (não recomendar)

**Conteúdo abaixo mantido apenas como histórico de research.**

---

## Histórico (não usar como referência operacional)

Asset: PEPPERSTONE:ETHUSD  
Strategy Layer: Intraday / Momentum Execution (DESATIVADO)
Context TFs: 4H + 1H  
Setup TF: 30M  
Execution TF: 15M refinement  
Direction: LONG and SHORT allowed (DESATIVADO)
Execution: manual only  

## 1. Purpose

This module defines a higher-frequency ETHUSD intraday momentum strategy.

It is independent from:

- ETHUSD_4H_LONG_BREAKOUT_CONTINUATION
- XAUUSD modules
- US500 modules
- generic dynamic-zone monitoring

The purpose is to capture confirmed ETHUSD 30M momentum continuation moves with HTF context and at least one extra confirmation.

## 2. Backtest basis

Historical offline backtest using exported TradingView CSV data.

Timeframes analyzed:
- 1D
- 12H
- 4H
- 1H
- 30M
- 15M

Best tested version:
ETHUSD v0.3 frequency strategy search

Best LONG model:
ETHUSD_30M_LONG_CONFIRMED_MOMENTUM_T4

Observed LONG result:
- approx. 331 trades
- approx. 4.7 trades/week
- total theoretical result: approx. +121R
- average result: approx. +0.36R per trade
- max losing streak: 4

Best SHORT model:
ETHUSD_30M_SHORT_CONFIRMED_MOMENTUM_T4

Observed SHORT result:
- approx. 306 trades
- approx. 4.3 trades/week
- total theoretical result: approx. +116R
- average result: approx. +0.38R per trade
- max losing streak: 4

Combined model:
ETHUSD_30M_CONFIRMED_MOMENTUM_BOTH_T4

Observed combined result:
- approx. 542 trades
- approx. 7.6 trades/week
- total theoretical result: approx. +144R
- average result: approx. +0.26R per trade
- max losing streak: 8

Interpretation:
ETHUSD intraday works better as confirmed momentum continuation, not as simple rejection/reversal or zone-touch logic.

## 3. Core principle

Do not trade ETHUSD intraday from a single signal.

A valid setup requires:

HTF context  
+ 30M momentum confirmation  
+ at least one additional confirmation  
+ clear stop  
+ R:R >= 2:1  
+ entry not late

This module is manual execution only.

## 4. LONG setup requirements

A LONG setup requires:

1. Asset is PEPPERSTONE:ETHUSD.
2. Setup timeframe is 30M.
3. Direction is LONG.
4. 4H/1H context is bullish or supportive.
5. 30M shows confirmed bullish momentum.
6. At least one additional confirmation is present:
   - NAS LONG / BOTTOM recent;
   - seller bubble / exhaustion against the move before reclaim;
   - bullish divergence;
   - RSI reclaim / momentum recovery;
   - breakout/retest hold;
   - 15M CHoCH/BOS bullish.
7. Stop is technical and clear.
8. R:R >= 2:1.
9. Entry is not late/chasing.

## 5. SHORT setup requirements

A SHORT setup requires:

1. Asset is PEPPERSTONE:ETHUSD.
2. Setup timeframe is 30M.
3. Direction is SHORT.
4. 4H/1H context is bearish, corrective, exhausted, or not strongly bullish.
5. 30M shows confirmed bearish momentum.
6. At least one additional confirmation is present:
   - NAS SHORT / TOP recent;
   - buyer bubble / exhaustion before breakdown;
   - bearish divergence;
   - RSI rejection / momentum loss;
   - breakdown/retest failure;
   - 15M CHoCH/BOS bearish.
7. Stop is technical and clear.
8. R:R >= 2:1.
9. Entry is not late/chasing.

## 6. Confirmed momentum definition

Confirmed momentum can be:

- 30M candle expansion in direction of the setup;
- 30M breakout/breakdown of local structure;
- 30M close beyond prior consolidation;
- 30M retest hold after breakout/breakdown;
- 15M execution trigger confirming the 30M move.

Momentum is not valid if price already moved too far from the ideal entry.

## 7. Valid triggers

Allowed triggers:

- MOMENTUM_CONTINUATION
- BREAKOUT_RETEST
- BREAKDOWN_RETEST
- RETEST_HOLD
- CHOCH_BOS
- MICRO_BREAK_RECLAIM
- NAS_SIGNAL_AT_ZONE
- RSI_MOMENTUM_RECLAIM
- RSI_MOMENTUM_REJECTION

Zone touch alone is not a valid trigger.

## 8. Priority score

Priority A:
- 4H/1H context aligned;
- 30M momentum confirmed;
- 15M trigger confirmed;
- NAS/bubble/divergence or RSI confirmation present;
- stop clear;
- R:R >= 2:1;
- entry not late.

Priority B:
- 30M momentum confirmed;
- HTF context acceptable;
- at least one confirmation present;
- stop/R:R valid;
- 15M trigger may need manual review.

Priority C:
- momentum forming but incomplete;
- context mixed;
- watch only;
- no entry yet.

## 9. Management rules

Default management:

- Entry: manual review near 30M momentum close / retest / 15M trigger.
- Stop: structural, beyond 30M/15M invalidation.
- Move stop to breakeven after +1R.
- Target reference: 4R.
- Do not chase if price has already moved too far from ideal entry.
- Execution is manual only.

## 10. Hard blocks

Do not classify as SETUP_VALIDO_INTRADAY if:

- no confirmed 30M momentum;
- no additional confirmation;
- no clear stop;
- R:R < 2:1;
- entry is late/chasing;
- signal is only zone touch;
- signal is only RSI/NAS/bubble without price structure;
- MCP/chart reading unreliable;
- macro red window is immediate.

## 11. SETUP_CANDIDATO_FORTE_INTRADAY behavior

Use SETUP_CANDIDATO_FORTE_INTRADAY when:

- ETHUSD 30M momentum is forming or partially confirmed;
- context is acceptable;
- stop/R:R are plausible;
- one confirmation exists;
- final trigger or retest is still missing.

This should go to Telegram as human review.

It is not automatic entry.

## 12. SETUP_VALIDO_INTRADAY behavior

Use SETUP_VALIDO_INTRADAY only when:

- 30M momentum is confirmed;
- at least one extra confirmation is present;
- stop is clear;
- R:R >= 2:1;
- entry is not late;
- manual execution is possible.

## 13. Required Claude output

When this module is relevant, Claude must clearly label it:

Strategy Module: ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION  
Intraday Context: 4H / 1H  
Setup TF: 30M  
Execution TF: 15M  
Priority: A/B/C  
Classificação:  
Direção: LONG or SHORT  
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

🟠 [ETHUSD 30M CONFIRMED MOMENTUM]

Required fields:

- Strategy Module: ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION
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
- Management: BE after +1R, target reference 4R
- Manual execution only.

## 15. Research status

This module is experimental.

Track separately in D1, D2 and D2R.

Before permanent adoption:

- collect 30–50 live/D2R events;
- separate LONG vs SHORT;
- separate Priority A/B/C;
- measure total R;
- measure average R;
- measure max losing streak;
- confirm that the strategy is not overtrading in chop;
- validate that target 4R remains appropriate.

## 16. Current decision

Implement as a separate ETHUSD intraday momentum module.

Do not merge with ETHUSD_4H_LONG_BREAKOUT_CONTINUATION.
