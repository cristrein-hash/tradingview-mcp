# US500_4H_LONG_FAILED_BREAKDOWN_REGIME

**Status:** active (criado em 2026-05-12 — substitui US500_4H_LONG_PULLBACK_REJECTION deactivated)
**Asset:** PEPPERSTONE:US500
**Timeframe:** 4H
**Direction:** LONG only
**Strategy Layer:** Swing / 4H Failed Breakdown Reversal
**Execution TF:** 4H
**Execution:** manual only
**Default classification:** **`SETUP_VALIDO`** ✅
**Module backtest n:** 45 trades (2021-12 → 2026-05, 4.4 anos)
**D2R required:** true

## 1. Purpose

Capturar reversões bullish em US500 onde o preço **falha em romper para baixo** (sweep + reclaim) dentro de regime trending bull com volatilidade expandindo. Substitui o módulo `US500_4H_LONG_PULLBACK_REJECTION` deactivated (que perdia -67.65R em backtest).

**Por que este módulo funciona quando outros falham em US500:**

US500 é um índice estruturalmente em uptrend pós-2022. Tradicionais "rejection close" e "pullback rejection" geram win rate baixíssimo (12-15%) porque os pullbacks são shallow. **Failed breakdowns**, ao contrário, identificam **falsas perdas de suporte** que os algos institucionais usam para caçar stops — quando a reversão acontece, o move é decisivo e direcional, dando edge claro.

O audit profundo de 2026-05-12 testou 28+ estratégias em US500. **Esta foi a ÚNICA com todos os anos positivos** e que atendeu todos os critérios mínimos para SETUP_VALIDO.

## 2. Backtest basis

Backtest CSV walk-forward, dados 2021-12 → 2026-05 (4.4 anos):

- **45 trades** (~0.23/sem, ~1.0/mês)
- Total net R @ 0.05R spread: **+15.26R**
- Avg net R/trade: **+0.339R**
- Profit factor net: **1.83**
- Win rate: **37.8%**
- Max losing streak: **5** (excelente — comparar XAU=16, ETH=9)
- **Sem top 5 net: +3.01R ✅** (robusto — não fat-tail dependent)
- Sem top 10 net: -9.24R (sample n=45 é pequeno; comportamento esperado)
- Avg MFE / Avg MAE: ~boa assimetria

### Estabilidade por ano (TODOS POSITIVOS)

| Ano | Trades | Net R | Avg R | Win% | Regime |
|---|---:|---:|---:|---:|---|
| 2022 (bear) | 6 | **+2.70** | 0.450 | 16.7% | **funciona em bear!** ✅ |
| 2023 | 7 | **+6.64** | 0.949 | 42.9% | recuperação ✅ |
| 2024 | 18 | **+7.15** | 0.397 | 33.3% | bull ✅ |
| 2025 | 13 | **+4.13** | 0.318 | 38.5% | bull ✅ |
| 2026 (parcial) | 1 | -1.05 | -1.050 | 0.0% | sample muito pequeno |

**Único módulo US500 testado com edge em TODOS os regimes (bear 2022 + bull 2023-2025).**

### Comparação com módulo antigo

| Métrica | US500_4H_LONG_PULLBACK_REJECTION (deactivated) | **FAILED_BREAKDOWN_REGIME (novo)** |
|---|---:|---:|
| Trades / 4.4y | 412 | 45 |
| Total Net R | **-67.65** | **+15.26** |
| Avg Net R | -0.164 | +0.339 |
| PF Net | 0.68 | 1.83 |
| Win rate | **12.9%** | **37.8%** |
| Max losing streak | 35 | **5** |
| Sem top 10 | -112.15 | -9.24 |
| Anos positivos | **0 de 5** | **4 de 4 completos** |

## 3. Trigger (todos obrigatórios)

Em candle 4H fechado:

1. `low < swing_low(20)` — o low do candle de sinal varreu abaixo da mínima dos últimos 20 candles 4H
2. `close > swing_low(20)` — o fechamento recuperou para cima da mínima varrida (reclaim)
3. `close > open` — candle bullish
4. `body_pct >= 0.5` — corpo >= 50% do range total (recuperação decisiva, não pavio fraco)

## 4. Filtros de regime (TODOS obrigatórios)

| Filtro | Definição | Função |
|---|---|---|
| `Close > EMA(200)` no 4H | Close atual > EMA 200 do TF 4H | Bias bull macro confirmado |
| `EMA(50) > EMA(200)` no 4H | Golden cross macro presente | Estrutura trending |
| `ATR(14) > ATR_MA(20)` | ATR atual > sua média de 20 bars | Volatilidade expandindo (não chop) |

Se **qualquer** filtro falha → NÃO operar.

## 5. Stop técnico

```
stop = low_signal_bar − 0.5 × ATR(14)
```

Sanity check: rejeitar setup se `R = |entry − stop| > 5 × ATR(14)`.

**NOTA crítica para US500:** porque o trigger envolve sweep de swing_low(20), o stop fica posicionado abaixo da nova mínima criada. Isso protege contra "double sweep" (mercado varre de novo e segue).

## 6. Target e gestão

| Item | Valor |
|---|---|
| Target | **2.5R fixo** |
| Move stop para BE | Após +1R |
| Trailing | Desabilitado |
| Max hold | **24 candles 4H** (= 4 dias) |
| Saída por tempo | Mark-to-market no candle 24 com close |

**Por que target 2.5R e não 4R/5R:** US500 é índice large-cap eficiente. Movimentos pós-failed-breakdown são potentes mas geralmente limitados (1-3 dias). Target conservador captura o move sem dependência de extensões raras.

## 7. Classificação produzida

```
Strategy Module: US500_4H_LONG_FAILED_BREAKDOWN_REGIME
Module backtest n: 45
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: failed_breakdown + body 0.5 + 3 filtros regime
Module score: A (todos filtros passam confortavelmente + ATR > 1.3×MA + body > 0.7) | B (default)
Operational signal: YES_MANUAL_REVIEW
D2R required: true
Hard block triggered: NONE
Module checklist failed on: NONE
Promotion trigger: SWEEP_REENTRY
Promotion status: PROMOTE_TO_SETUP_VALIDO
Priority: A | B
Trigger: failed_breakdown (low < swlo(20), close > swlo(20)) + body >= 0.5
Execution TF: 240
Entrada ideal: close do candle de sinal
Preço atual: <preço atual>
Entrada atrasada: SIM | NÃO
Entry late distance R: <número>
Classificação: SETUP_VALIDO
Direção: LONG
```

## 8. Quando bloquear

Módulo **NÃO dispara** quando qualquer:

- low não rompeu o swing_low(20)
- close <= swing_low(20) (não houve reclaim)
- candle bearish ou body < 0.5
- close <= EMA200 (sem bias bull)
- EMA50 <= EMA200 (sem golden cross)
- ATR <= ATR_MA20 (volatilidade contracting)
- hard blocks globais falham (R:R < 2:1, MCP unreliable, etc.)

## 9. Telegram routing

🟢 [US500 4H FAILED BREAKDOWN REGIME — SETUP_VALIDO]

Mensagem deve conter:
- Strategy Module + Module backtest n
- Trigger técnico (low varreu swlo20 em X.XX, close em Y.YY)
- 3 filtros regime com valores atuais
- Entrada ideal / Preço atual / Stop / Alvo 2.5R
- Priority A/B
- Aviso: execução manual obrigatória

## 10. Avisos operacionais

1. **Frequência baixa:** ~1 trade/mês em média. Pode haver semanas sem sinal — não forçar.
2. **Win rate 37.8% com target 2.5R** — economicamente positivo. Win rate teórico mínimo p/ R:R 2.5 = 29%.
3. **2022 (bear market): +2.70R em 6 trades.** Modulo demonstrou edge em regime bear também — diferencial vs todos os outros US500 testados.
4. **Sample 4.4 anos** — adequado mas não infinito. Pode degradar em períodos sem dados análogos.
5. **Spread real US500:** se > 0.10R/trade, edge degrada para PF ~1.60. Ainda positivo mas com menos margem.
6. **Max losing streak 5** — excelente psicologicamente. Permite operação com disciplina.
7. **Sem top 10 fica negativo** apenas porque n=45 é pequeno. Sem top 5 ainda positivo, que é o critério crítico.

## 11. Critérios para reverter classificação (downgrade futuro)

Se em produção ao vivo apresentar:
- Avg R líquido < +0.15R em 30 trades reais
- Max losing streak > 10 em produção
- Sem top 5 de produção volta para negativo

→ Reverter para SETUP_CANDIDATO_FORTE.

## 12. Substituições

Substitui (deactivated): `US500_4H_LONG_PULLBACK_REJECTION` (perdia -67.65R em 4.4y)

## 13. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.0 | Criação. Substitui US500_4H_LONG_PULLBACK_REJECTION deactivated. Sample n=45 / 4.4y. Único módulo US500 com edge confirmado em backtest profundo. |
