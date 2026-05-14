# XAGUSD_1H_LONG_DECISIVE_DXY_STRUCTURAL

**Status:** active (criado em 2026-05-12)
**Asset:** PEPPERSTONE:XAGUSD
**Timeframe:** 1H
**Direction:** LONG only
**Strategy Layer:** Intraday / 1H Decisive Breakout + Multi-HTF + Macro DXY Estrutural
**Execution TF:** 1H
**Execution:** manual only
**Default classification:** **`SETUP_CANDIDATO_FORTE`** (NÃO promove a SETUP_VALIDO_INTRADAY automaticamente)
**Module backtest n:** 69 trades (2024-01 → 2026-05, 2.36 anos)
**D2R required:** true

## 1. Purpose

Capturar breakouts intraday em XAGUSD 1H apenas quando o regime macro estrutural está alinhado: DXY abaixo da EMA200 (USD bearish estrutural, não apenas tático).

**Descoberta crítica do audit:** para XAGUSD, `DXY < EMA200` (estrutural) funciona MELHOR que `DXY < EMA50` (tático). XAG responde a USD weakness de longo prazo, diferente do EURUSD onde o filtro tático EMA50 já é suficiente.

## 2. Backtest basis

Backtest CSV walk-forward, dados 2024-01 → 2026-05 (2.36 anos):

- **69 trades** (~0.55/sem, ~2.4/mês)
- Total net R @ 0.05R spread: **+16.12R**
- Avg net R/trade: **+0.234R**
- Profit factor net: **1.79**
- Win rate: **44.9%**
- **Max losing streak: 4** (excepcionalmente baixo)
- **Sem top 5 net: +1.37R ✅** (positivo)
- Sem top 10 net: −9.50R ⚠️ (fat-tail no segundo tier)

### Estabilidade por ano (TODOS positivos)

| Ano | Trades | Net R | Avg R | Win% |
|---|---:|---:|---:|---:|
| 2024 | 17 | **+5.22** | +0.307 | **58.8%** ✅ |
| 2025 | 38 | **+10.87** | +0.286 | 42.1% ✅ |
| 2026 (parcial) | 13 | **+1.28** | +0.098 | 30.8% ✅ |

### Cost sensitivity

| Spread | Total Net R | Avg | PF |
|---:|---:|---:|---:|
| 0.00R | +20.76 | 0.305 | 2.18 |
| 0.05R | **+16.12** | **0.234** | **1.79** |
| 0.07R | +14.74 | 0.214 | 1.69 |
| 0.10R | +12.70 | 0.184 | 1.55 |

Estável até 0.10R spread.

## 3. Trigger (todos obrigatórios)

Em candle 1H fechado:

1. `close > swing_high(10)` — rompimento da máxima dos últimos 10 candles 1H
2. `close > open` — candle bullish
3. **`body_pct >= 0.6`** — corpo >= 60% do range
4. **`range >= 1.2 × ATR(14)`** — barra de amplitude expandida
5. `RSI(14) > RSI-based MA` — momentum alinhado

## 4. Filtros técnicos de regime (TODOS obrigatórios)

| Filtro | Definição |
|---|---|
| `Close > EMA(200)` no 1H | Bias bull local |
| `EMA(50) > EMA(200)` no 1H | Stack estrutural |
| `ATR(14) > ATR_MA(20)` | Volatilidade expandindo |

## 5. Filtros HTF (TODOS obrigatórios)

| Filtro | Definição |
|---|---|
| **HTF 1D close > HTF 1D EMA(50)** | Diário em bull regime |
| **HTF 4H close > HTF 4H EMA(50)** | 4H em bull regime |

## 6. ★ Filtro MACRO DXY ESTRUTURAL (obrigatório — pull live via MCP)

| Filtro | Definição |
|---|---|
| **TVC:DXY close < EMA200(DXY) no 4H** | DXY em bearish ESTRUTURAL — USD weakness de longo prazo |

**IMPORTANTE — diferença vs EURUSD:** Para XAG usamos **EMA200** (estrutural), não EMA50 (tático). XAG responde a USD weakness de longo prazo.

**Procedimento MCP em produção (Claude headless):**

1. Lembrar estado: símbolo atual = PEPPERSTONE:XAGUSD, TF = 60
2. `chart_set_symbol("TVC:DXY")`
3. `chart_set_timeframe("240")`
4. `data_get_ohlcv(count=250)` — 250 candles 4H de DXY (precisamos de pelo menos 200 para EMA200)
5. Calcular EMA200 dos últimos 200 closes (alpha = 2/201)
6. Comparar: `close_atual_DXY < EMA200_calculada`?
7. `chart_set_symbol("PEPPERSTONE:XAGUSD")` — restaurar
8. `chart_set_timeframe("60")` — restaurar
9. Reportar no output: `Macro context (DXY): DXY < EMA200 (X.XXX < Y.YYY) ✅`

**Política de fallback:**

| Caso | Resultado | Classificação |
|---|---|---|
| A — DXY < EMA200 + todos filtros passam | Default | SETUP_CANDIDATO_FORTE |
| B — DXY >= EMA200 (não bearish estrutural) | Downgrade | SETUP_EM_OBSERVACAO |
| C — MCP falhou ao consultar DXY | Downgrade conservador | SETUP_EM_OBSERVACAO |

## 7. Stop / Target / Gestão

| Item | Valor |
|---|---|
| Stop | `low - 0.5 × ATR(14)` |
| Sanity | rejeitar se R > 5 × ATR(14) |
| Target | **3R fixo** |
| BE | Após +1R |
| Trailing | Desabilitado |
| Max hold | 20 candles 1H |

**Por que target 3R:** o audit comparou 2R, 2.5R, 3R, 4R. Target 3R teve no_top5 positivo (+1.37R) com PF 1.79; target 4R teve mais total_r (+17.36R) mas no_top5 negativo (-0.58). 3R preferido pela robustez.

## 8. Por que NÃO SETUP_VALIDO_INTRADAY automático

| Critério | Mínimo | Resultado |
|---|---:|---|
| n | ≥ 30 | 69 ✅ |
| PF | ≥ 1.40 | 1.79 ✅ |
| avg_r_net | ≥ 0.15 | +0.234 ✅ |
| no_top5 positivo | sim | +1.37 ✅ |
| no_top10 positivo | sim | −9.50 ⚠️ |
| max_streak | ≤ 12 | 4 ✅ |
| trades/sem | ≥ 2 | 0.55 ⚠️ abaixo |
| Anos cobertos | ≥ 3 | 2.36 ⚠️ |
| Anos positivos | ≥ 80% | 3 de 3 (100%) ✅ |

7 de 9 critérios atendidos, 2 marginais (frequência baixa, sample limitado). **no_top10 negativo é o ponto fraco principal** — edge depende dos top 6-10 trades. Mesma calibração conservadora do EURUSD 1H + ETHUSD 1H + XAUUSD 1H.

## 9. Critérios para promoção a SETUP_VALIDO_INTRADAY

Pode ser promovido após em produção ao vivo apresentar:
- 30+ trades reais com avg_r > +0.15R
- PF > 1.40
- no_top5 ainda positivo
- Max losing streak <= 10

## 10. Filtros NÃO incluídos (e por quê)

| Filtro testado | Resultado | Razão |
|---|---|---|
| DXY < EMA50 (tático) | n=70, no_top5 +0.56, mais marginal | Funciona, mas EMA200 dá edge mais robusto para XAG |
| DXY strong_bear (EMA50 + falling) | n=57, PF 1.83 mas no_top5 +0.13 (quase zero) | Restrito demais — corta trades válidos |
| HTF12H | Redundante | Já coberto por HTF1D+HTF4H |
| body 70% (decisive EUR/V2) | Filtra trades bons | Body 60% é o equilíbrio certo para XAG |
| Pullback EMA50 (mirror ETH winner) | Sem edge | Padrão ETH não traduz pra XAG |
| ADX 25 | Reduz volume sem ganho | Não filtra losses |

## 11. Classificação produzida

### Caso A — todos filtros passam + DXY < EMA200 confirmado

```
Strategy Module: XAGUSD_1H_LONG_DECISIVE_DXY_STRUCTURAL
Module backtest n: 69
Macro context (DXY): DXY < EMA200 (X.XX < Y.YY) ✅
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: 5 trigger + 3 técnicos + 2 HTF + 1 macro estrutural passaram
Operational signal: YES_MANUAL_REVIEW
D2R required: true
Promotion trigger: MOMENTUM_CONTINUATION
Promotion status: KEEP_AS_CANDIDATO_FORTE
Priority: A | B
Trigger: breakout swhi10 + body >= 0.6 + range >= 1.2×ATR + RSI > MA
Execution TF: 60
Classificação: SETUP_CANDIDATO_FORTE
Direção: LONG
```

### Caso B — DXY NÃO bearish estrutural OU MCP falhou

```
Macro context (DXY): DXY >= EMA200 ⚠️ OR UNKNOWN
Module checklist failed on: macro_filter_dxy_not_structural_bear OR macro_filter_unverifiable
Classificação: SETUP_EM_OBSERVACAO  ← downgrade
```

## 12. Telegram routing

🟠 [XAGUSD 1H DECISIVE BREAKOUT + DXY structural — SETUP_CANDIDATO_FORTE]

Mensagem deve incluir Trigger + HTF context + Macro context DXY + aviso de revisão manual obrigatória.

## 13. Avisos operacionais

1. **Frequência baixa:** ~0.55 trade/sem, ~2.4/mês. Pode haver semanas sem sinal.
2. **DXY filter estrutural (EMA200)** é específico para XAG — NÃO confundir com filtro DXY tático (EMA50) dos módulos EURUSD.
3. **no_top10 negativo (−9.50R)** = edge depende dos top 6-10 trades. Risco de fat-tail no segundo tier.
4. **Sample 2.36 anos** — confiança estatística limitada para promoção automática.
5. **3 de 3 anos positivos é forte sinal**, mas a janela é curta.
6. **NÃO operar SHORT em XAGUSD** — nenhum módulo SHORT testado/aprovado.
7. **Audit NÃO encontrou módulo SWING 4H deployável** — apenas intraday 1H.

## 14. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.0 | Criação. Sample n=69 / 2.36y. PF 1.79, win 44.9%, no_top5 +1.37, 3 de 3 anos positivos. DXY estrutural (EMA200) descoberto como filtro superior ao tático (EMA50) para XAG. Default SETUP_CANDIDATO_FORTE. |
