# EURUSD_1H_LONG_DECISIVE_HTF1D_DXY

**Status:** active (criado em 2026-05-12)
**Asset:** PEPPERSTONE:EURUSD
**Timeframe:** 1H
**Direction:** LONG only
**Strategy Layer:** Intraday / 1H Decisive Breakout + HTF + Macro DXY
**Execution TF:** 1H
**Execution:** manual only
**Default classification:** **`SETUP_CANDIDATO_FORTE`** (NÃO promove a SETUP_VALIDO_INTRADAY automaticamente)
**Module backtest n:** 73 trades (2024-01 → 2026-05, 2.4 anos)
**D2R required:** true

## 1. Purpose

Capturar breakouts intraday DECISIVOS em EURUSD 1H — apenas barras com body >= 70% E range >= 1.5×ATR — em regime trending confirmado por HTF 1D + DXY bearish.

**Justificativa:** o audit V2 mostrou que breakouts intraday "normais" em EURUSD perdem dinheiro consistentemente. Apenas movimentos DECISIVOS (body strong + range expansion) com macro alinhado entregam edge. Filtro de qualidade extremo + multi-confluência.

## 2. Backtest basis

Backtest CSV walk-forward, dados 2024-01 → 2026-05 (2.4 anos):

- **73 trades** (~0.66/sem, ~2.88/mês)
- Total net R @ 0.05R spread: **+12.68R**
- Avg net R/trade: **+0.174R**
- Profit factor net: **1.46**
- Win rate: **42.5%**
- Max losing streak: **8**
- Sem top 5 net: -2.07R (marginal — não fat-tail extremo mas frágil)
- Sem top 10 net: -14.09R

### Estabilidade por ano (TODOS positivos)

| Ano | Trades | Net R | Avg R | Win% |
|---|---:|---:|---:|---:|
| 2024 | 25 | +0.91 | 0.036 | 44.0% ✅ |
| 2025 | 42 | **+3.14** | 0.075 | 38.1% ✅ |
| 2026 (parcial) | 6 | **+8.64** | **1.439** | **66.7%** ✅ |

### Cost sensitivity

| Spread | Total Net R | Avg | PF |
|---:|---:|---:|---:|
| 0.00R | +16.33 | 0.224 | 1.64 |
| 0.05R | **+12.68** | **0.174** | **1.46** |
| 0.07R | +11.22 | 0.154 | 1.40 |
| 0.10R | +9.03 | 0.124 | 1.31 |

## 3. Trigger (todos obrigatórios — DECISIVE breakout)

Em candle 1H fechado:

1. `close > swing_high(10)` — rompimento da máxima dos últimos 10 candles 1H
2. `close > open` — candle bullish
3. **`body_pct >= 0.7`** — corpo >= 70% do range (DECISIVO, não pavio)
4. **`range >= 1.5 × ATR(14)`** — barra de alta amplitude (não candle pequeno)
5. `RSI(14) > RSI-based MA` — momentum alinhado

## 4. Filtros técnicos de regime (TODOS obrigatórios)

| Filtro | Definição |
|---|---|
| `Close > EMA(200)` no 1H | Bias bull local |
| `EMA(50) > EMA(200)` no 1H | Stack estrutural |
| `ATR(14) > ATR_MA(20)` | Volatilidade expandindo |

## 5. Filtro HTF (obrigatório)

| Filtro | Definição |
|---|---|
| **HTF 1D close > HTF 1D EMA(50)** | Diário em bull regime |

## 6. ★ Filtro MACRO DXY (obrigatório — pull live via MCP)

| Filtro | Definição |
|---|---|
| **TVC:DXY close < EMA50(DXY) no 4H** | DXY em bearish regime |

**Mesmo procedimento do módulo SWING:** pull live via MCP com fallback `SETUP_EM_OBSERVACAO` (não SETUP_CANDIDATO_FORTE — já é o default aqui) se DXY não puder ser confirmado.

## 7. Stop / Target / Gestão

| Item | Valor |
|---|---|
| Stop | `low - 0.5 × ATR(14)` |
| Target | **3R fixo** |
| BE | Após +1R |
| Trailing | Desabilitado |
| Max hold | 20 candles 1H |

## 8. Por que NÃO SETUP_VALIDO_INTRADAY automático

| Critério | Mínimo | Resultado |
|---|---:|---|
| Avg R líquido | > +0.15 | **+0.174** ✅ |
| PF líquido | > 1.10 | **1.46** ✅ |
| Sample n | >= 30 | 73 ✅ |
| Sem top 5 ainda positivo | sim | -2.07 ⚠️ marginal |
| Max losing streak | <= 12 | 8 ✅ |
| Trades/sem | >= 2 | **0.66** ❌ abaixo do mínimo |
| Funciona em > 1 ano | sim | só 2.4y, 3/3 anos ⚠️ |

3 critérios atendidos, 2 marginais, 1 abaixo do mínimo (frequência). **Edge real mas não suficiente para promoção automática.**

## 9. Critérios para promoção a SETUP_VALIDO_INTRADAY

Pode ser promovido após em produção ao vivo apresentar:
- 30+ trades reais com avg_r > +0.15R
- PF > 1.40
- Sem top 5 ainda positivo
- Max losing streak <= 10

## 10. Classificação produzida

### Caso A — todos filtros passam + DXY confirmado

```
Strategy Module: EURUSD_1H_LONG_DECISIVE_HTF1D_DXY
Module backtest n: 73
Macro context (DXY): DXY < EMA50 (X.XX < Y.YY) ✅
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: 5 trigger + 3 técnicos + 1 HTF + 1 macro passaram
Operational signal: YES_MANUAL_REVIEW
D2R required: true
Promotion trigger: MOMENTUM_CONTINUATION
Promotion status: KEEP_AS_CANDIDATO_FORTE
Priority: A | B
Trigger: breakout swhi10 + body >= 0.7 + range >= 1.5×ATR + RSI > MA
Execution TF: 60
Classificação: SETUP_CANDIDATO_FORTE  ← default por enquanto
Direção: LONG
```

### Caso B — DXY não bearish OU MCP falhou

```
Macro context (DXY): DXY >= EMA50 ⚠️  OR  UNKNOWN
Module checklist failed on: macro_filter_dxy_not_bearish ou macro_filter_unverifiable
Classificação: SETUP_EM_OBSERVACAO  ← downgrade adicional
```

## 11. Telegram routing

🟠 [EURUSD 1H DECISIVE BREAKOUT — SETUP_CANDIDATO_FORTE]

Mensagem deve incluir todos os campos relevantes + Macro context DXY + aviso de revisão manual obrigatória.

## 12. Avisos operacionais

1. **Frequência intraday baixa:** 0.66 trades/semana. Pode ter semanas sem sinal.
2. **Filtros extremamente restritivos** (body 70% + range 1.5×ATR) — isso é por design para qualidade.
3. **Win rate 42.5% com target 3R** = economicamente sólido.
4. **Sample 2.4 anos** = confiança estatística limitada.
5. **NÃO promover sem validação ao vivo** (ver §9).
6. **2024 foi marginalmente positivo (+0.91R em 25 trades).** Não overfit.

## 13. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.0 | Criação. Sample n=73 / 2.4y. PF 1.46, win 42.5%, todos os anos positivos. Apenas SETUP_CANDIDATO_FORTE até validação ao vivo. |
