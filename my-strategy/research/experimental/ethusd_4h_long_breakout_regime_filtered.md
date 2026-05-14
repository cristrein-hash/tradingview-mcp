# ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED — v1.2 (com macro filter)

**Status:** active
**Versão:** 1.2 (2026-05-12)
**Asset:** PEPPERSTONE:ETHUSD
**Timeframe:** 4H
**Direction:** LONG only
**Strategy Layer:** Swing / 4H Momentum + Macro Filter
**Execution TF:** 4H
**Execution:** manual only
**Default classification:** **`SETUP_VALIDO`** ✅ (promovido em v1.2 de SETUP_CANDIDATO_FORTE)
**Module backtest n:** 72 trades (2021-01 → 2026-05, 5.4 anos)
**D2R required:** true

## 1. Purpose

Capturar continuação bullish de ETHUSD em 4H em regime trending bull técnico **E** com ETH outperformando BTC (macro context favorável). Substitui o `ETHUSD_4H_LONG_BREAKOUT_CONTINUATION` deprecado e evolui da v1.0/v1.1 com filtro ETHBTC.

**Por que o filtro macro é crítico:**

O audit fat-tail mostrou que 100% das features técnicas do candle de sinal são quase idênticas entre big winners e losers em ETH. O que separa é o **regime macro** — especificamente **se ETH está outperformando BTC**. O filtro ETHBTC > EMA50 captura isso em tempo real.

## 2. Backtest basis — v1.2 (com filtro ETHBTC)

Backtest CSV walk-forward, dados 2021-01 → 2026-05 (5.4 anos):

- **72 trades** (~1.1/sem, ~1.1/mês)
- Total net R @ 0.05R spread: **+38.42R**
- Avg net R/trade: **+0.534R** (3.5x melhor que v1.0)
- Profit factor net: **2.13**
- Win rate: **36.1%**
- Max losing streak: **9**
- **Sem top 5 net: +13.67R ✅** (positivo e robusto — fat-tail problema resolvido)
- Sem top 10 net: -6.02R (negativo mas dramaticamente melhor que -26R baseline)

### Estabilidade por ano (net @ 0.05R)

| Ano | Trades | Net R | Avg R | Win% | Regime |
|---|---:|---:|---:|---:|---|
| 2021 | 18 | -2.54 | -0.141 | 22.2% | chop — quase neutralizado (vs -16R baseline) ✅ |
| 2022 | 10 | +3.02 | 0.302 | 40.0% | flat → positivo ✅ |
| 2023 | 10 | **+8.91** | **0.891** | 40.0% | recuperação forte ✅ |
| 2024 | 11 | **+9.24** | **0.840** | **45.5%** | bull ✅ |
| 2025 | 23 | **+19.80** | **0.861** | 39.1% | bull forte ✅ |

**4 de 5 anos com edge muito forte.** 2021 quase neutralizado.

### Evolução de versões

| Versão | n | Total Net R | Avg R | PF | Sem top 5 | Mudança |
|---|---:|---:|---:|---:|---:|---|
| Original (deprecated) | 613 | -35.68 | -0.058 | 0.89 | -60.43 | baseline RSI>=52 |
| v1.0 (regime filter) | 158 | +12.82 | 0.081 | 1.16 | -11.93 | + ADX/EMA stack |
| v1.1 (body 60%) | 95 | +30.51 | 0.321 | 1.65 | +5.76 | + body_pct >= 0.6 |
| **v1.2 (+ETHBTC bull)** | **72** | **+38.42** | **0.534** | **2.13** | **+13.67** | **+ macro filter** ✅ |

## 3. Trigger (todos obrigatórios)

Em candle 4H fechado:

1. `close > swing_high(10)` — rompimento da máxima dos últimos 10 candles
2. `close > open` — candle bullish
3. **`body_pct >= 0.6`** — corpo >= 60% do range (v1.1)
4. `RSI(14) > RSI-based MA` — momentum alinhado

## 4. Filtros técnicos de regime (TODOS obrigatórios)

| Filtro | Definição |
|---|---|
| `ADX(14) >= 25` | DX(14) suavizado de Wilder (mais estrito que XAU=20) |
| `Close > EMA(200)` | Close 4H acima da EMA 200 |
| `EMA(50) > EMA(200)` | Golden cross macro |
| `EMA(50) slope > 0` | EMA50 atual − EMA50 5 bars atrás > 0 |
| `ATR(14) > ATR_MA(20)` | Volatilidade expandindo |

## 5. ★ Filtro MACRO (v1.2 — obrigatório)

| Filtro | Definição | Lógica |
|---|---|---|
| **`BINANCE:ETHBTC close > EMA50(BINANCE:ETHBTC)` no 4H** | Close atual de ETHBTC > sua EMA50 no TF 4H | ETH está outperformando BTC — único regime estatisticamente onde breakouts ETH pagam |

**Como obter em produção (Claude headless via MCP):**

1. Salvar símbolo atual: `current = "PEPPERSTONE:ETHUSD"`
2. `chart_set_symbol("BINANCE:ETHBTC")`
3. `chart_set_timeframe("240")`
4. `data_get_ohlcv(count=100)` — puxar 100 candles 4H
5. Computar EMA50 das 50 últimas closes (alpha = 2/51): manual em Python
6. Comparar: `close_atual > ema50_calculada`?
7. `chart_set_symbol("PEPPERSTONE:ETHUSD")` — restaurar
8. `chart_set_timeframe("240")` — restaurar

**Política de fallback (CRÍTICA):**

Se qualquer um dos passos 2-7 falhar (MCP unreliable, símbolo não acessível, erro de leitura):

- **NÃO emitir SETUP_VALIDO**
- **Emitir SETUP_CANDIDATO_FORTE** com `macro_context: UNKNOWN` no log
- O usuário decide manualmente se opera (conservador por design)

## 6. Stop técnico

```
stop = low_signal_bar − 0.5 × ATR(14)
```

Sanity: rejeitar se `R = |entry − stop| > 5 × ATR(14)`.

## 7. Target e gestão

| Item | Valor |
|---|---|
| Target | **5R fixo** |
| Move stop para BE | Após +1R |
| Trailing | Desabilitado (testado e piora) |
| Max hold | **30 candles 4H** (= 5 dias) |
| Saída por tempo | Mark-to-market no candle 30 |

## 8. Classificação produzida

### Caso A — todos filtros passam + ETHBTC bullish confirmado

```
Strategy Module: ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED
Module version: v1.2
Module backtest n: 72
Macro context: ETHBTC > EMA50 (X.XXXXX > Y.YYYYY) ✅
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: trigger + 5 filtros regime técnicos + 1 filtro macro passaram
Module score: A (todos filtros passam confortavelmente + ADX > 30 + RSI > 60) | B (default)
Operational signal: YES_MANUAL_REVIEW
D2R required: true
Hard block triggered: NONE
Module checklist failed on: NONE
Promotion trigger: MOMENTUM_CONTINUATION
Promotion status: PROMOTE_TO_SETUP_VALIDO
Priority: A | B
Trigger: close > swing_high(10) + body >= 0.6 + RSI > MA
Execution TF: 240
Entrada ideal: close do candle de sinal
Preço atual: <preço atual>
Entrada atrasada: SIM | NÃO
Entry late distance R: <número>
Classificação: SETUP_VALIDO  ← v1.2 promovido
Direção: LONG
```

### Caso B — filtros técnicos passam mas ETHBTC NÃO está bullish

```
Macro context: ETHBTC <= EMA50 (X.XXXXX <= Y.YYYYY) ⚠️
Module checklist failed on: macro_filter_ethbtc_below_ema50
Promotion status: KEEP_AS_CANDIDATO_FORTE
Classificação: SETUP_CANDIDATO_FORTE  ← downgrade por macro
```

### Caso C — MCP falhou ao consultar ETHBTC

```
Macro context: UNKNOWN (MCP failed to read BINANCE:ETHBTC)
Module checklist failed on: macro_filter_unverifiable
Promotion status: KEEP_AS_CANDIDATO_FORTE
Classificação: SETUP_CANDIDATO_FORTE  ← conservador
```

## 9. Quando bloquear completamente (NO_TRADE)

- Hard blocks globais falham (R:R < 2:1, MCP chart unreliable em ETHUSD, etc.)
- Algum item do trigger falha
- Algum filtro técnico de regime falha

## 10. Telegram routing

🟢 [ETHUSD 4H BREAKOUT REGIME — SETUP_VALIDO]  (caso A)
🟠 [ETHUSD 4H BREAKOUT REGIME — SETUP_CANDIDATO_FORTE]  (caso B/C)

Mensagem deve incluir:
- Strategy Module + version v1.2
- Macro context atual (ETHBTC value vs EMA50)
- Trigger técnico + 5 filtros regime
- Entrada ideal / Preço atual / Stop / Alvo 5R
- Priority A/B
- Aviso: execução manual obrigatória

## 11. Avisos operacionais

1. **Frequência baixa:** ~1.1 trades/mês. Pode haver semanas sem sinal — não forçar trades.
2. **Win rate 36% com R:R 5:1** — economicamente positivo mas exige disciplina psicológica.
3. **2021 (chop): -2.54R / 18 trades.** Filtro macro reduziu drasticamente vs -16R baseline, mas não eliminou totalmente.
4. **Sem top 10: -6.02R.** Ainda há leve dependência fat-tail mas dramaticamente reduzida (vs -26R baseline).
5. **Sample 5.4 anos** — pode degradar em períodos sem dados análogos.
6. **Spread real:** se > 0.10R/trade, edge fica marginal. Margem atual conforta.
7. **ETHBTC EMA50 calculation:** Claude deve usar amostra de pelo menos 50 candles 4H para EMA estável; idealmente 100+.
8. **MCP failure recovery:** sempre fallback para SETUP_CANDIDATO_FORTE quando macro não puder ser confirmado.

## 12. Pesquisa futura

- Testar adição de filtro BTCUSD bull regime (combo trabaja mas reduz trades para 65, melhora max_streak para 6)
- Testar EMA20 vs EMA50 no ETHBTC (mais sensível, possíveis falsos sinais)
- Implementar cache de ETHBTC state (atualizar a cada 4H, evitar pull repetido)
- Validação ao vivo após 30+ trades

## 13. Critérios para reverter classificação (downgrade futuro)

Se em produção ao vivo o módulo apresentar:
- Avg R líquido < +0.10R em 30 trades reais
- Max losing streak > 12 em produção
- Sem top 5 de produção volta para negativo

→ Reverter para SETUP_CANDIDATO_FORTE.

## 14. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.0 | Criação inicial. Regime filter técnico (ADX/EMA/ATR). n=158, +12.82R, PF 1.16 |
| 2026-05-12 | v1.1 | + body_pct >= 0.6. n=95, +30.51R, PF 1.65 |
| 2026-05-12 | **v1.2** | **+ filtro macro ETHBTC > EMA50. n=72, +38.42R, PF 2.13. Default = SETUP_VALIDO** |

## 15. Substituições

Substitui (deprecado): `ETHUSD_4H_LONG_BREAKOUT_CONTINUATION`
