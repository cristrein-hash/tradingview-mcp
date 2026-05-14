# ETHUSD_1H_LONG_PULLBACK_EMA50_REGIME

**Status:** active (novo módulo criado em 2026-05-12)
**Asset:** PEPPERSTONE:ETHUSD
**Timeframe:** 1H
**Direction:** LONG only
**Strategy Layer:** Intraday / 1H Pullback Continuation
**Execution TF:** 1H
**Execution:** manual only
**Default classification:** `SETUP_CANDIDATO_FORTE`
**Module backtest n:** 96 trades (2024-12 → 2026-05, ~1.4 anos)
**D2R required:** true

## 1. Purpose

Capturar continuação bullish de ETHUSD em 1H aproveitando **pullbacks à EMA50** dentro de regime trending bull confirmado por HTF (1D).

**Diferença vs breakout puro:** pullback espera correção e entra no retest da EMA50 — menos chase, menos top-10 dependency. Backtest mostrou PF 1.68 (vs 1.42 do breakout 1H baseline), max losing streak apenas 9 e **edge positivo ainda sem os top 5 winners** (+8.44R) — qualitativamente superior.

## 2. Backtest basis

Backtest CSV 1H, walk-forward, dados 2024-12-31 → 2026-05-11 (~1.4 anos):

- **96 trades** (1.41/sem, 6.11/mês)
- Total net R @ 0.05R spread: **+23.19R**
- Avg net R/trade: **+0.242R**
- Profit factor net: **1.68**
- Win rate: **33.3%**
- Max losing streak: **9** (baixo)
- **Sem top 5 net: +8.44R ✅** (positivo sem fat tails grandes)
- Sem top 10 net: -6.31R (quase neutro — bem melhor que outras ETH)

### Estabilidade por ano (net @ 0.05R)

| Ano | Trades | Net R | Avg R | Win% |
|---|---:|---:|---:|---:|
| 2025 | 72 | +11.16 | 0.155 | 31.9% |
| 2026 (parcial) | 24 | **+12.03** | **0.501** | **37.5%** |

⚠️ Sample limitado a 1.4 anos — necessário forward-test ao vivo.

### Comparação com alternativas intraday

| Estratégia | n | Net R | Avg R | PF | Streak | -top10 |
|---|---:|---:|---:|---:|---:|---:|
| **PULLBACK_EMA50 + HTF1D (este)** | 96 | **+23.19** | **0.242** | **1.68** | **9** | **-6.31** |
| Breakout 1H + HTF1D | 101 | +21.61 | 0.214 | 1.58 | 13 | -12.44 |
| Breakout 1H + HTF12H | 114 | +20.49 | 0.180 | 1.49 | 13 | -13.55 |
| Breakout 1H regime base | 116 | +18.39 | 0.159 | 1.42 | 13 | -15.65 |

Este módulo ganha em todos os indicadores de qualidade.

## 3. Trigger (todos obrigatórios)

Em candle 1H fechado:

1. `low <= EMA(50)` — pullback toca/atravessa EMA50
2. `close > EMA(50)` — fechamento recupera para cima da EMA50
3. `close > open` — candle bullish
4. `body_pct >= 0.4` — corpo >= 40% do range (não precisa ser tão forte quanto breakout)
5. `RSI(14) > RSI-based MA` — momentum reclaim bullish

## 4. Filtros de regime (TODOS obrigatórios)

| Filtro | Definição | Função |
|---|---|---|
| `Close > EMA(200)` no 1H | Close 1H acima da EMA 200 1H | Bias bull macro local |
| `EMA(50) > EMA(200)` no 1H | EMA50 acima EMA200 no 1H | Estrutura trending |
| `HTF 1D close > HTF 1D EMA(50)` | Diário acima da sua EMA50 | **HTF context bullish** — gate crítico |

Se **qualquer** filtro falha → NÃO operar.

## 5. Stop técnico

```
stop = low_signal_bar − 0.5 × ATR(14)
```

Sanity: rejeitar se `R > 5 × ATR(14)`.

## 6. Target e gestão

| Item | Valor |
|---|---|
| Target | **3R** |
| Move stop para BE | Após +1R |
| Trailing | Desabilitado |
| Max hold | **20 candles 1H** (= 20 horas) |

**Por que 3R e não 4R/5R:** pullback continuation tem expectativa de menor amplitude que breakout puro. Target 3R captura a continuação intraday típica sem exigir movimento extraordinário.

## 7. Classificação produzida

```
Strategy Module: ETHUSD_1H_LONG_PULLBACK_EMA50_REGIME
Module backtest n: 96
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: pullback toca EMA50 + recuperação + regime bull + HTF1D bullish
Module score: A (pullback limpo + RSI > 55 + HTF strongly bullish) | B (default)
Operational signal: YES_MANUAL_REVIEW
D2R required: true
Hard block triggered: NONE
Module checklist failed on: NONE
Promotion trigger: RETEST_HOLD
Promotion status: KEEP_AS_CANDIDATO_FORTE  ← inicial
Priority: A | B
Trigger: pullback to EMA50 + close > EMA50 + RSI > MA + HTF1D bull
Execution TF: 60
Entrada ideal: close do candle de sinal
Preço atual: <preço atual>
Entrada atrasada: SIM | NÃO
Entry late distance R: <número>
Classificação: SETUP_CANDIDATO_FORTE  ← default por enquanto
Direção: LONG
```

## 8. Critérios para promoção futura a SETUP_VALIDO_INTRADAY

O módulo pode ser **promovido** para emitir `SETUP_VALIDO_INTRADAY` quando, em produção ao vivo, TODOS os critérios abaixo forem atingidos:

| Critério | Valor mínimo |
|---|---|
| Trades reais executados/medidos em D2R | **>= 30** |
| Avg R líquido | **>= +0.15R** |
| Profit Factor líquido | **>= 1.40** |
| Max losing streak | **<= 12** |
| Sem dependência única de fat tails | sem top 5 ainda positivo |

Reavaliar a cada 30 trades. Até lá, **manter como SETUP_CANDIDATO_FORTE** com revisão humana.

## 9. Quando bloquear

O módulo **NÃO dispara** quando qualquer dos seguintes for verdadeiro:

- Close <= EMA(200) no 1H
- EMA(50) <= EMA(200) no 1H
- HTF 1D close <= HTF 1D EMA(50)
- Algum item do trigger falha (low não tocou EMA50, close abaixo EMA50, candle bearish, body < 40%, RSI <= MA)
- Hard blocks globais falham

## 10. Telegram routing

🟠 [ETHUSD 1H PULLBACK EMA50 — SETUP_CANDIDATO_FORTE]

Mensagem deve conter:
- Strategy Module
- Direção: LONG
- Trigger técnico (pullback + recuperação)
- 3 filtros regime com valor atual
- Entrada ideal / Preço atual
- Stop técnico
- Alvo 3R
- R:R estimado
- Priority A/B
- Aviso: revisão manual obrigatória

## 11. Avisos operacionais

1. **Frequência ~1.4 trades/semana** — operacionalmente útil para intraday.
2. **Win rate 33% — boa para target 3R** mas exige disciplina (2 em cada 3 trades param em -1R ou BE).
3. **Sample 1.4 anos** — confiança estatística limitada. Performance pode degradar fora desse período.
4. **HTF 1D filter é crítico** — se ETH entra em bear regime no 1D, o módulo não opera automaticamente (correto).
5. **Pullback timing exige paciência** — não entrar antes do candle fechar com close > EMA50.
6. **NÃO promover a SETUP_VALIDO_INTRADAY antes da validação ao vivo** (ver §8).
7. **Spread real:** se > 0.10R/trade, edge fica marginal mas ainda positivo.

## 12. Pesquisa futura

Próximos refinements possíveis (não implementar agora):

- Testar EMA20 vs EMA50 (entradas mais frequentes mas menor pullback)
- Adicionar filtro de divergência regular bullish para Priority A
- Testar target 4R com trailing após +2R
- Sazonalidade (US session vs Asia session) — sample atual pode esconder bias

## 13. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.0 | Criação. Não substitui módulos anteriores (módulo intraday novo). Sample n=96 / 1.4y. |
