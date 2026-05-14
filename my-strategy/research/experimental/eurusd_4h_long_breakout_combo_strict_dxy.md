# EURUSD_4H_LONG_BREAKOUT_COMBO_STRICT_DXY

**Status:** active (criado em 2026-05-12)
**Asset:** PEPPERSTONE:EURUSD
**Timeframe:** 4H
**Direction:** LONG only
**Strategy Layer:** Swing / 4H Breakout + Multi-TF Strict + Macro DXY
**Execution TF:** 4H
**Execution:** manual only
**Default classification:** **`SETUP_VALIDO`** ✅
**Module backtest n:** 47 trades (2019-01 → 2026-05, 7.4 anos)
**D2R required:** true

## 1. Purpose

Capturar breakouts bullish em EURUSD 4H apenas quando há **multi-confluência forte**: trigger técnico decisivo + regime trending em múltiplos timeframes + macro DXY bearish. Substitui operacionalmente o módulo `EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION` deactivated (que perdia -104.34R em backtest).

**Por que este módulo funciona quando outros falham em EURUSD:**

EURUSD é o par forex mais líquido do mundo — mercado eficiente onde estratégias técnicas isoladas raramente entregam edge. O audit V2 de 2026-05-12 testou 28+ variantes e a fórmula vencedora exigiu **6 filtros simultâneos**: HTF1D + HTF12H bullish + multi-TF stack EMA + ADX 25 + body 60% + range 1.2×ATR + DXY bearish. Cada filtro isolado tem edge marginal, mas a combinação produz PF 2.03 e win rate 42.6%.

## 2. Backtest basis

Backtest CSV walk-forward, dados 2019-01 → 2026-05 (7.4 anos):

- **47 trades** (~0.13/sem, ~0.59/mês — frequência baixa, qualidade alta)
- Total net R @ 0.05R spread: **+13.35R**
- Avg net R/trade: **+0.284R** (forte)
- Profit factor net: **2.03**
- Win rate: **42.6%** (excelente)
- Max losing streak: **4** (muito baixo)
- **Sem top 5 net: +1.10R ✅** (positivo — não fat-tail)
- Sem top 10 net: -7.47R

### Estabilidade por ano (6 de 8 anos positivos)

| Ano | Trades | Net R | Avg R | Win% |
|---|---:|---:|---:|---:|
| 2019 | 6 | **+1.77** | 0.294 | 33.3% ✅ |
| 2020 | 11 | **+1.58** | 0.144 | 36.4% ✅ |
| 2021 | 2 | -0.68 | -0.340 | 50.0% (sample pequeno) |
| 2022 | 1 | **+2.45** | 2.450 | 100% (sample pequeno) |
| 2023 | 7 | **+1.02** | 0.145 | 42.9% ✅ |
| 2024 | 9 | **-1.44** | -0.160 | 33.3% ⚠️ |
| 2025 | 8 | **+3.81** | 0.476 | 50.0% ✅ |
| 2026 (parcial) | 3 | **+4.85** | 1.617 | 66.7% ✅ |

### Cost sensitivity (mantém positivo até 0.10R spread)

| Spread | Total Net R | Avg | PF | Positivo? |
|---:|---:|---:|---:|---|
| 0.00R | +15.70 | 0.334 | 2.36 | ✅ |
| 0.05R | **+13.35** | **0.284** | **2.03** | ✅ |
| 0.07R | +12.41 | 0.264 | 1.92 | ✅ |
| 0.10R | +11.00 | 0.234 | 1.77 | ✅ |

## 3. Trigger (todos obrigatórios)

Em candle 4H fechado:

1. `close > swing_high(10)` — rompimento da máxima dos últimos 10 candles 4H
2. `close > open` — candle bullish
3. `body_pct >= 0.6` — corpo >= 60% do range (decisivo)
4. `range >= 1.2 × ATR(14)` — barra de alta amplitude
5. `RSI(14) > RSI-based MA` — momentum alinhado

## 4. Filtros técnicos de regime (TODOS obrigatórios)

| Filtro | Definição |
|---|---|
| `Close > EMA(200)` no 4H | Bias bull macro confirmado |
| `EMA(50) > EMA(200)` no 4H | Golden cross |
| `ATR(14) > ATR_MA(20)` | Volatilidade expandindo |
| `ADX(14) >= 25` | Força direcional confirmada |

## 5. Filtros HTF (TODOS obrigatórios)

| Filtro | Definição |
|---|---|
| **HTF 1D close > HTF 1D EMA(50)** | Diário em bull regime |
| **HTF 12H close > HTF 12H EMA(50)** | 12H em bull regime |

## 6. ★ Filtro MACRO DXY (obrigatório — pull live via MCP)

| Filtro | Definição |
|---|---|
| **TVC:DXY close < EMA50(DXY) no 4H** | DXY em bearish regime — USD fraqueza confirma EUR forte |

**Procedimento exato em produção (Claude headless via MCP):**

1. Salvar mentalmente: símbolo atual = PEPPERSTONE:EURUSD, TF = 240
2. `chart_set_symbol("TVC:DXY")`
3. `chart_set_timeframe("240")`
4. `data_get_ohlcv(count=100)` — 100 candles 4H de DXY
5. Calcular EMA50 dos 50 últimos closes (alpha = 2/51)
6. Comparar: `close_atual_DXY < EMA50_calculada`?
7. `chart_set_symbol("PEPPERSTONE:EURUSD")` — restaurar
8. `chart_set_timeframe("240")` — restaurar
9. Reportar no output (`Macro context (DXY): DXY < EMA50 (X.XX < Y.YY) ✅`)

**Política de fallback (CRÍTICA):**

- Se qualquer passo falhar (MCP unreliable, símbolo não acessível, OHLCV vazio):
  - `macro_context: UNKNOWN`
  - **Classificação: SETUP_CANDIDATO_FORTE** (downgrade conservador, NUNCA SETUP_VALIDO)
  - `Module checklist failed on: macro_filter_unverifiable`

- Se DXY close >= EMA50 (DXY NÃO bearish):
  - `macro_context: DXY >= EMA50`
  - **Classificação: SETUP_CANDIDATO_FORTE** (downgrade por macro)
  - `Module checklist failed on: macro_filter_dxy_not_bearish`

- Se DXY close < EMA50 + todos outros filtros passam:
  - **Classificação: SETUP_VALIDO** ✅

## 7. Stop técnico

```
stop = low_signal_bar − 0.5 × ATR(14)
```

Sanity: rejeitar se `R = |entry − stop| > 5 × ATR(14)`.

## 8. Target e gestão

| Item | Valor |
|---|---|
| Target | **2.5R fixo** |
| Move stop para BE | Após +1R |
| Trailing | Desabilitado |
| Max hold | **24 candles 4H** (= 4 dias) |

**Por que target 2.5R:** EURUSD tem movimentos limitados — extensões grandes são raras. Target conservador captura o move sem dependência de fat tails.

## 9. Classificação produzida

### Caso A — todos filtros passam + DXY confirmado bearish

```
Strategy Module: EURUSD_4H_LONG_BREAKOUT_COMBO_STRICT_DXY
Module backtest n: 47
Macro context (DXY): DXY < EMA50 (X.XXX < Y.YYY) ✅
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: 5 trigger + 4 técnicos + 2 HTF + 1 macro passaram
Module score: A | B
Operational signal: YES_MANUAL_REVIEW
D2R required: true
Hard block triggered: NONE
Module checklist failed on: NONE
Promotion trigger: MOMENTUM_CONTINUATION
Promotion status: PROMOTE_TO_SETUP_VALIDO
Priority: A | B
Trigger: breakout swhi10 + body >= 0.6 + range >= 1.2 ATR + RSI > MA
Execution TF: 240
Entrada ideal: close do candle de sinal
Preço atual: <preço>
Entrada atrasada: SIM | NÃO
Entry late distance R: <número>
Classificação: SETUP_VALIDO  ← v1.0
Direção: LONG
```

### Caso B — DXY NÃO bearish

```
Macro context (DXY): DXY >= EMA50 (X.XXX >= Y.YYY) ⚠️
Module checklist failed on: macro_filter_dxy_not_bearish
Promotion status: KEEP_AS_CANDIDATO_FORTE
Classificação: SETUP_CANDIDATO_FORTE  ← downgrade
```

### Caso C — MCP falhou ao consultar DXY

```
Macro context (DXY): UNKNOWN (MCP failed to read TVC:DXY)
Module checklist failed on: macro_filter_unverifiable
Promotion status: KEEP_AS_CANDIDATO_FORTE
Classificação: SETUP_CANDIDATO_FORTE  ← conservador
```

## 10. Quando bloquear completamente (NO_TRADE)

- Hard blocks globais falham (R:R < 2:1, MCP chart EUR unreliable, etc.)
- Algum item do trigger falha
- Algum filtro técnico (EMA, ATR, ADX) ou HTF falha

## 11. Telegram routing

🟢 [EURUSD 4H BREAKOUT COMBO STRICT — SETUP_VALIDO] (caso A)
🟠 [EURUSD 4H BREAKOUT COMBO STRICT — SETUP_CANDIDATO_FORTE] (caso B/C)

Mensagem deve incluir:
- Strategy Module + version
- Macro context (DXY) com valores
- Trigger + 4 filtros técnicos + 2 HTF
- Entrada ideal / Preço atual / Stop / Alvo 2.5R
- Priority A/B
- Aviso: execução manual obrigatória

## 12. Avisos operacionais

1. **Frequência muito baixa:** ~0.59 trade/mês. Pode haver MESES sem sinal — não forçar.
2. **Win rate 42.6% + R:R 2.5** = economicamente sólido. Apenas operar dentro do plano.
3. **2024 foi negativo (-1.44R)**. Aceitar como custo do regime macro daquele ano.
4. **Sample 7.4 anos** — sólido mas não infinito.
5. **MCP DXY pull adiciona ~3s** por análise EURUSD 4H — aceitável.
6. **NUNCA emitir SETUP_VALIDO sem confirmação DXY bearish** — risco de auto-confirm sem validação macro real.

## 13. Critérios para reverter classificação (downgrade futuro)

Se em produção ao vivo apresentar:
- Avg R líquido < +0.15R em 30 trades reais
- Max losing streak > 8
- Sem top 5 de produção volta para negativo

→ Reverter para SETUP_CANDIDATO_FORTE.

## 14. Substituições

Substitui (deactivated): `EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION` (perdia -104R em backtest).

## 15. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.0 | Criação. Substitui EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION deactivated. Sample n=47 / 7.4y. PF 2.03, win 42.6%, 6/8 anos positivos. Primeiro módulo EURUSD com edge confirmado em backtest profundo após audit V2 testar 60+ variantes. |
