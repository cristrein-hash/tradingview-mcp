# US500_1H_LONG_BREAKOUT_REGIME_FILTERED

**Status:** active (atualizado em 2026-05-12 com filtros HTF)
**Asset:** PEPPERSTONE:US500
**Timeframe:** 1H
**Direction:** LONG only
**Strategy Layer:** Intraday / 1H Breakout Continuation com HTF gate
**Execution TF:** 1H
**Execution:** manual only
**Default classification:** **`SETUP_CANDIDATO_FORTE`** (NÃO promove a SETUP_VALIDO_INTRADAY automaticamente)
**Module backtest n:** 222 trades (2024-01 → 2026-05, 2.3 anos)
**D2R required:** true

## 1. Purpose

Capturar breakouts intraday em US500 1H dentro de regime trending bull confirmado por HTF (1D e 4H). É o melhor candidato intraday US500 encontrado no audit profundo, mas com edge marginal — por isso classificação ficou em SETUP_CANDIDATO_FORTE, não SETUP_VALIDO_INTRADAY.

**Substitui operacionalmente:** `US500_INTRADAY_LONG_PULLBACK_EXECUTION` (deactivated, perdia -105.20R em backtest).

## 2. Backtest basis

Backtest CSV walk-forward, dados 2024-01 → 2026-05 (2.3 anos):

- **222 trades** (1.85/sem, 8.06/mês)
- Total net R @ 0.05R spread: **+18.93R**
- Avg net R/trade: **+0.085R**
- Profit factor net: **1.22**
- Win rate: **40.5%**
- Max losing streak: **11**
- Sem top 5: -0.47R (quase neutro)
- Sem top 10: -12.58R (frágil)

### Estabilidade por ano

| Ano | Trades | Net R | Avg R | Win% |
|---|---:|---:|---:|---:|
| 2024 | 108 | **+22.72** | 0.210 | **42.6%** ✅ |
| 2025 | 79 | **-12.32** | -0.156 | 32.9% ⚠️ |
| 2026 (parcial) | 35 | **+8.52** | 0.244 | 51.4% ✅ |

**2025 negativo** é fragilidade real do módulo — por isso NÃO classifica como SETUP_VALIDO automático.

### Evolução

| Versão | n | Total Net R | Avg R | PF | Win% | Sem top 5 |
|---|---:|---:|---:|---:|---:|---:|
| F original (sem HTF) | 225 | +6.05 | 0.027 | 1.06 | 32.0% | -13.70 |
| **F + HTF 1D + HTF 4H** | **222** | **+18.93** | **+0.085** | **1.22** | **40.5%** | **-0.47** |

Adição dos filtros HTF aumentou edge em 3x e elevou win rate de 32% → 40.5%.

## 3. Trigger (todos obrigatórios)

Em candle 1H fechado:

1. `close > swing_high(10)` — rompimento da máxima dos últimos 10 candles 1H
2. `close > open` — candle bullish
3. `body_pct >= 0.5` — corpo >= 50% do range
4. `RSI(14) > RSI-based MA` — momentum alinhado

## 4. Filtros técnicos de regime (TODOS obrigatórios)

| Filtro | Definição |
|---|---|
| `Close > EMA(200)` no 1H | Close 1H acima EMA200 |
| `EMA(50) > EMA(200)` no 1H | Golden cross local |
| `EMA(50) slope (5 bars) > 0` | Tendência viva |
| `ATR(14) > ATR_MA(20)` | Volatilidade expandindo |
| `ADX(14) >= 20` | Força direcional |

## 5. ★ Filtros HTF (TODOS obrigatórios — novo em 2026-05-12)

| Filtro | Definição |
|---|---|
| **HTF 1D close > HTF 1D EMA(50)** | Diário em bull regime |
| **HTF 4H close > HTF 4H EMA(50)** | 4H em bull regime |

Se qualquer filtro HTF falha → NÃO operar (downgrade para SETUP_EM_OBSERVACAO).

## 6. Stop técnico

```
stop = low_signal_bar − 0.5 × ATR(14)
```

Sanity: rejeitar se `R > 5 × ATR(14)`.

## 7. Target e gestão

| Item | Valor |
|---|---|
| Target | **4R fixo** |
| Move stop para BE | Após +1R |
| Trailing | Desabilitado |
| Max hold | **20 candles 1H** (= 20h) |

## 8. Por que NÃO SETUP_VALIDO_INTRADAY automático

| Critério | Mínimo | F + HTF |
|---|---:|---|
| Avg R líquido | > +0.15R | 0.085 ❌ |
| PF líquido | > 1.10 | 1.22 ✅ |
| Sample n | >= 30 | 222 ✅ |
| Sem top 5 ainda positivo | sim | -0.47 ⚠️ marginal |
| Max losing streak | <= 12 | 11 ✅ |
| Funciona em > 1 ano | sim | 2024+/2025-/2026+ ⚠️ |
| Trades/sem | >= 2 | 1.85 ⚠️ marginal |

3 critérios marginais/negativos. **Não atende standard de SETUP_VALIDO_INTRADAY.**

Edge real mas frágil. Manter como SETUP_CANDIDATO_FORTE com revisão humana é a decisão estatisticamente correta.

## 9. Classificação produzida

```
Strategy Module: US500_1H_LONG_BREAKOUT_REGIME_FILTERED
Module backtest n: 222
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: trigger + 5 filtros técnicos + 2 filtros HTF passaram
Module score: A (todos confortavelmente + RSI > 60 + ADX > 25) | B (default)
Operational signal: YES_MANUAL_REVIEW
D2R required: true
Hard block triggered: NONE
Module checklist failed on: NONE
Promotion trigger: MOMENTUM_CONTINUATION
Promotion status: KEEP_AS_CANDIDATO_FORTE
Priority: A | B
Trigger: close > swing_high(10) + body >= 0.5 + RSI > MA
Execution TF: 60
Entrada ideal: close do candle de sinal
Preço atual: <preço atual>
Entrada atrasada: SIM | NÃO
Entry late distance R: <número>
Classificação: SETUP_CANDIDATO_FORTE  ← default
Direção: LONG
```

## 10. Critérios para promoção futura a SETUP_VALIDO_INTRADAY

Pode ser promovido se em produção ao vivo apresentar:
- 30+ trades reais com avg_r > +0.15R
- PF > 1.40
- Sem top 5 ainda positivo
- Max losing streak <= 10

## 11. Avisos operacionais

1. **Edge marginal:** apenas 0.085R/trade. Disciplinas operacionais (não chasing, BE +1R) são críticas.
2. **2025 foi negativo** (-12.32R em 79 trades). Aceitar que pode haver anos negativos.
3. **Sample 2.3 anos** é curto. Confiança estatística limitada.
4. **HTF filters são o que torna este módulo viável.** Sem eles, edge era +6R = quase zero.
5. **Spread real US500:** se > 0.07R, edge cai dramaticamente.
6. **Trades 1.85/sem** está no limite de "intraday".

## 12. Substituições

Substitui: `US500_INTRADAY_LONG_PULLBACK_EXECUTION` (deactivated, perdia -105R).

## 13. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.1 | Adicionados filtros HTF 1D + HTF 4H. Edge triplicou (de +6R para +19R). Substitui US500_INTRADAY_LONG_PULLBACK_EXECUTION. Classificação SETUP_CANDIDATO_FORTE. |
