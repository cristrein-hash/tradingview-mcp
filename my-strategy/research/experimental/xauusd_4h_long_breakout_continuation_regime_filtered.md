# XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED

**Status:** active (substitui `XAUUSD_4H_LONG_REJECTION_SWING` em 2026-05-12)
**Asset:** PEPPERSTONE:XAUUSD
**Timeframe:** 4H
**Direction:** LONG only
**Strategy Layer:** Swing / 4H Momentum
**Execution TF:** 4H
**Execution:** manual only
**Default classification:** `SETUP_VALIDO` quando todos os critérios passam
**Module backtest n:** 234 trades (2019-01-01 → 2026-05-12, 7.4 anos)

## 1. Purpose

Capturar continuação bullish de XAUUSD em 4H quando todos os filtros de regime apontam para tendência viva. Substitui o módulo anterior `XAUUSD_4H_LONG_REJECTION_SWING` que produzia expectancy negativo em backtest e disparava em chop.

A ideia central: **XAUUSD paga bem em continuação 4H quando o regime é trending bull com volatilidade expandindo.** O regime filter resolve a parte "quando não operar" — fora de regime bull com ADX e ATR favoráveis, o módulo não dispara.

## 2. Backtest basis

Backtest CSV histórico, walk-forward bar-a-bar, dados 2019-2026 (7.4 anos):

- 234 trades (~0.65/sem, 2.81/mês)
- Total net R @ 0.05R spread: **+64.57R**
- Avg net R/trade: **+0.276R**
- Profit factor net: **1.64**
- Win rate: 28.6%
- Max losing streak: 16
- Sem top 10 winners: ainda **+25.07R net** (robusto, não overfit a fat tails)
- Best trade: +3.95R; worst: -1.05R

### Estabilidade por ano (net @ 0.05R)

| Ano | Trades | Net R | Avg R | Win% | Regime |
|---|---:|---:|---:|---:|---|
| 2019 | 26 | +19.07 | 0.733 | 38.5% | bull ✅ |
| 2020 | 30 | +21.82 | 0.727 | 30.0% | bull (COVID rally) ✅ |
| 2021 | 12 | -0.61 | -0.051 | 16.7% | chop — quase flat ✅ |
| 2022 | 20 | -12.25 | -0.613 | 15.0% | chop — único ano perdedor |
| 2023 | 28 | +0.29 | 0.010 | 21.4% | chop — flat ✅ |
| 2024 | 42 | +1.91 | 0.045 | 31.0% | bull ✅ |
| 2025 | 68 | +22.04 | 0.324 | 29.4% | bull ✅ |
| 2026 (parcial) | 8 | +12.31 | 1.539 | 50.0% | bull ✅ |

### Comparação com versão sem filtros de regime

| Métrica | Sem filtros | Com regime (atual) | Δ |
|---|---:|---:|---:|
| Trades | 846 | 234 | -72% |
| Total Net R | +34.54 | +64.57 | +87% |
| Avg Net R | 0.041 | 0.276 | +574% |
| PF Net | 1.09 | 1.64 | +51% |
| Max losing streak | 31 | 16 | -48% |
| Sem top 10 | -4.96R | +25.07R | sai do negativo |

## 3. Trigger (todos obrigatórios)

Em candle 4H fechado:

1. `close > swing_high(10)` — fechou acima da máxima dos últimos 10 candles
2. `close > open` — candle bullish
3. `body_pct >= 0.5` — corpo é ao menos 50% do range total do candle
4. `RSI(14) > RSI-based MA` — momentum RSI alinhado bullish

## 4. Filtros de regime (TODOS obrigatórios — gate de entrada)

Todos devem ser verdadeiros no candle de sinal. Se qualquer um falhar, **NÃO operar**.

| Filtro | Definição | Função |
|---|---|---|
| `ADX(14) >= 20` | DX(14) suavizado de Wilder | Confirma força direcional |
| `Close > EMA(200)` | Close 4H acima da EMA 200 | Bias bull macro |
| `EMA(50) > EMA(200)` | EMA 50 acima da EMA 200 | Golden cross macro |
| `EMA(50) slope > 0` | EMA50 atual − EMA50 5 bars atrás > 0 | Tendência viva, não estagnada |
| `ATR(14) > ATR_MA(20)` | ATR atual maior que sua média de 20 bars | Volatilidade expandindo |

## 5. Stop técnico

```
stop = low_signal_bar - 0.5 × ATR(14)
```

Stop posicionado abaixo do low do candle de sinal com buffer de meio ATR. Se R = |entry - stop| > 5 × ATR, descartar setup (stop largo demais).

## 6. Target e gestão

| Item | Valor |
|---|---|
| Target principal | **4R** (entry + 4 × R) |
| Move stop para BE | Após preço atingir **+1R** |
| Trailing | **NÃO** ativo por padrão (testado e piora resultado) |
| Max hold | **24 candles 4H** (= 96 horas / 4 dias) |
| Saída por tempo | Mark-to-market no candle 24 com close |

## 7. Classificação produzida

```
Strategy Module: XAUUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED
Module backtest n: 234
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: (trigger + 5 filtros regime passaram)
Module score: A (quando todos os 5 filtros passam confortavelmente; ex.: ADX > 25, ATR > 1.2×ATR_MA20)
                 B (quando filtros passam marginalmente)
Operational signal: YES_MANUAL_REVIEW
D2R required: true
Hard block triggered: NONE
Module checklist failed on: NONE
Promotion trigger: MOMENTUM_CONTINUATION
Promotion status: PROMOTE_TO_SETUP_VALIDO
Priority: A | B
Trigger: close > swing_high(10) + body >= 0.5 + RSI > MA
Execution TF: 240
Entrada ideal: close do candle de sinal
Preço atual: <preço de mercado>
Entrada atrasada: SIM | NÃO (calcular entry_late_distance_r contra entry ideal)
Entry late distance R: <número>
Classificação: SETUP_VALIDO
Direção: LONG
```

## 8. Quando bloquear (resumo operacional)

O módulo **NÃO dispara** quando qualquer dos seguintes for verdadeiro:

- `ADX(14) < 20` → mercado sem força direcional
- `close <= EMA(200)` → não há bias bull macro
- `EMA(50) <= EMA(200)` → não há golden cross macro
- `EMA(50) slope <= 0` → tendência estagnada ou virando
- `ATR(14) <= ATR_MA(20)` → volatilidade contraindo (chop)
- Falta qualquer um dos 4 itens do trigger
- Hard blocks globais falham (R:R < 2:1, MCP unreliable, macro red window, etc.)

**Isso resolve ~80% do problema "quando não operar".** O único regime que ainda gera perdas é chop com volatilidade ENGANOSAMENTE expandindo (caso 2022) — não corrigível sem overfit.

## 9. Telegram routing

🟢 [XAUUSD 4H BREAKOUT CONTINUATION — SETUP_VALIDO]

Mensagem deve conter:

- Strategy Module
- Direção: LONG
- Trigger técnico
- Filtros de regime (todos com valor atual)
- Entrada ideal / Preço atual / Entrada atrasada
- Stop técnico (preço numérico)
- Alvo (preço numérico)
- R:R estimado
- Priority A/B
- Aviso: execução manual; revisar broker/spread antes de entrar

## 10. Avisos operacionais

1. **Frequência baixa:** 2.81 trades/mês em média. Pode haver semanas sem sinal — não forçar trades.
2. **Win rate é 28.6% — psicologicamente exige disciplina.** O edge vem da assimetria 4R target × stop 1R com 28% acerto.
3. **Spread real do broker XAUUSD:** se > 0.07R/trade, edge degrada. Margem de segurança líquida ~0.04R/trade.
4. **2022 ainda é ponto fraco:** -12.3R em chop com filtros ainda passando. Aceitar como custo do regime ou pausar manualmente em janelas de chop visível.
5. **Não confiar em sample pequena:** primeiros 25-30 trades em produção podem desviar do backtest por azar. Avaliar ao chegar em 100 trades.
6. **Manter rigor com filtros:** se algum filtro estiver no limite (ex.: ADX = 19.8), tratar como FAIL. Não relaxar para aumentar frequência.

## 11. Pesquisa futura

Próximos refinements possíveis (research):

- Filtro adicional para 2022-like chop: ATR expansion sustentável (5 bars) em vez de bar único
- HTF 1D bullish como filtro substituto (testado: piora marginalmente)
- ADX direction (DI+ > DI-) como filtro adicional (testado: marginal)
- Pyramid em runners (entrar 2x no mesmo trade pós +2R)
- Target dinâmico baseado em ATR vs R fixo

Nada disso é prioridade — o módulo atual já tem edge robusto. Não modificar sem nova evidência estatística substancial.

## 12. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.0 | Criação. Substitui XAUUSD_4H_LONG_REJECTION_SWING (deprecado em mesma data) |

## 13. Substituições

Este módulo **substitui** operacionalmente:

- `XAUUSD_4H_LONG_REJECTION_SWING` → marcado como DEACTIVATED (mantido em research history)

E **não substitui** (continuam ativos):

- `XAUUSD_1H_LONG_REJECTION_EXECUTION` → SETUP_CANDIDATO_FORTE com revisão manual
- `XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION` → forward-test, depende de zonas BB
