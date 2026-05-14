# XAUUSD_1H_LONG_DECISIVE_BODY60_HTF

**Status:** active (criado em 2026-05-12)
**Asset:** PEPPERSTONE:XAUUSD
**Timeframe:** 1H
**Direction:** LONG only
**Strategy Layer:** Intraday / 1H Decisive Breakout + Multi-HTF
**Execution TF:** 1H
**Execution:** manual only
**Default classification:** **`SETUP_CANDIDATO_FORTE`** (NÃO promove a SETUP_VALIDO_INTRADAY automaticamente)
**Module backtest n:** 127 trades (2024-01 → 2026-05, 2.36 anos)
**D2R required:** true

## 1. Purpose

Capturar breakouts intraday em XAUUSD 1H com **multi-confluência HTF** — body sólido (≥60%) + range expandido (≥1.2×ATR) + HTF 1D bullish + HTF 4H bullish. Substitui operacionalmente o módulo `XAUUSD_1H_LONG_REJECTION_EXECUTION` legacy (rejection-based, confirmado sem edge em backtest profundo).

**Justificativa:** o audit de 2026-05-12 testou 44 variantes em XAU 1H. A combinação vencedora foi **body 60% + HTF1D + HTF4H + target 2.5R**, com no_top5 +14.75R e no_top10 +2.50R (ambos positivos — robustez raramente vista em intraday).

**Descoberta contra-intuitiva:** o filtro "body decisive ≥ 70%" do EURUSD V2 NÃO traduz pra XAU. Body 60% gerou +13R a mais que body 70% no mesmo combo HTF. XAU tem bars de continuação com pavio superior moderado que ainda têm follow-through positivo.

## 2. Backtest basis

Backtest CSV walk-forward, dados 2024-01 → 2026-05 (2.36 anos):

- **127 trades** (~1.07/sem, ~4.58/mês)
- Total net R @ 0.05R spread: **+27.00R**
- Avg net R/trade: **+0.213R**
- Profit factor net: **1.57**
- Win rate: **44.9%**
- Max losing streak: **9**
- **Sem top 5 net: +14.75R ✅** (positivo)
- **Sem top 10 net: +2.50R ✅** (positivo — raro em intraday)

### Estabilidade por ano

| Ano | Trades | Net R | Avg R | Win% |
|---|---:|---:|---:|---:|
| 2024 | 49 | **−5.82** | −0.119 | 34.7% ⚠️ |
| 2025 | 62 | **+28.25** | +0.456 | 53.2% ✅ |
| 2026 (parcial) | 16 | **+4.57** | +0.286 | 43.8% ✅ |

**2024 negativo** mas 2 de 3 anos positivos. Mesmo padrão do EURUSD 4H (regime macro daquele ano não favoreceu LONG metals/risk-on intraday).

### Cost sensitivity (mantém edge até 0.10R)

| Spread | Total Net R | Avg | PF |
|---:|---:|---:|---:|
| 0.00R | +33.35 | 0.263 | 1.76 |
| 0.05R | **+27.00** | **0.213** | **1.57** |
| 0.07R | +24.46 | 0.193 | 1.50 |
| 0.10R | +20.65 | 0.163 | 1.40 |

## 3. Trigger (todos obrigatórios)

Em candle 1H fechado:

1. `close > swing_high(10)` — rompimento da máxima dos últimos 10 candles 1H
2. `close > open` — candle bullish
3. **`body_pct >= 0.6`** — corpo >= 60% do range (sólido mas não extremo como EUR/V2)
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

Nota: HTF 12H foi testada e NÃO acrescentou edge — redundante com HTF1D+HTF4H em XAU.

## 6. Filtros NÃO incluídos (e por quê)

| Filtro testado | Resultado | Razão de exclusão |
|---|---|---|
| body_pct >= 0.7 (decisive EUR/V2) | -13R vs body 60% | Muito restritivo em XAU |
| HTF 12H bullish | Sem efeito (linhas idênticas) | Redundante com HTF1D+HTF4H |
| London/NY session | Reduziu volume sem ganho | XAU tem trades válidos fora |
| ADX >= 25 | Caiu fora do top 10 | Filtra contexto que ainda funciona |
| PULLBACK EMA50 + RSI reclaim | Não entrou no top | Padrão ETH não traduz pra XAU |

## 7. Filtro MACRO DXY (PENDENTE — futuro)

**Não incluído nesta v1.0** porque o CSV de DXY não estava disponível no momento do audit.

**Hipótese a testar (v1.1):** adicionar `TVC:DXY close < EMA50(DXY) no 4H` via MCP live pull deve melhorar PF e win rate em 10–15% baseado em correlação XAU/DXY conhecida.

Quando ativado, seguir o mesmo padrão dos módulos EURUSD (procedimento MCP de 9 passos + fallback policy).

## 8. Stop / Target / Gestão

| Item | Valor |
|---|---|
| Stop | `low - 0.5 × ATR(14)` |
| Sanity | rejeitar se R > 5 × ATR(14) |
| Target | **2.5R fixo** |
| BE | Após +1R |
| Trailing | Desabilitado |
| Max hold | 20 candles 1H (~20h) |

**Por que target 2.5R:** o audit comparou 2R, 2.5R, 3R, 4R. Target 2.5R teve no_top10 positivo (+2.50R) enquanto 3R/4R tiveram no_top10 negativo. 2.5R captura o move com robustez extra contra reversão intraday.

## 9. Por que NÃO SETUP_VALIDO_INTRADAY automático

| Critério | Mínimo | Resultado |
|---|---:|---|
| n | ≥ 30 | 127 ✅ |
| PF | ≥ 1.40 | 1.57 ✅ |
| avg_r_net | ≥ 0.15 | +0.213 ✅ |
| no_top5 positivo | sim | +14.75 ✅ |
| no_top10 positivo | sim | +2.50 ✅ |
| max_streak | ≤ 12 | 9 ✅ |
| trades/sem | ≥ 2 | 1.07 ⚠️ abaixo |
| Anos cobertos | ≥ 3 | 2.36 ⚠️ |
| Anos positivos | ≥ 80% | 2 de 3 (66.7%) ⚠️ |

6 de 9 critérios atendidos, 3 marginais. **Mesma calibração conservadora do EURUSD 1H + ETHUSD 1H.** Edge real confirmado, mas sample limitado a 2.36y justifica validação ao vivo antes de promoção.

## 10. Critérios para promoção a SETUP_VALIDO_INTRADAY

Pode ser promovido após em produção ao vivo apresentar:
- 30+ trades reais com avg_r > +0.15R
- PF > 1.40
- Sem top 5 ainda positivo
- Max losing streak <= 10

## 11. Classificação produzida

```
Strategy Module: XAUUSD_1H_LONG_DECISIVE_BODY60_HTF
Module backtest n: 127
Global hard blocks: PASS
Module checklist: PASS
Module checklist notes: 5 trigger + 3 técnicos + 2 HTF passaram
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

## 12. Telegram routing

🟠 [XAUUSD 1H DECISIVE BREAKOUT — SETUP_CANDIDATO_FORTE]

Mensagem deve incluir todos os campos relevantes + Trigger + HTF context + aviso de revisão manual obrigatória.

## 13. Avisos operacionais

1. **Frequência intraday moderada:** ~1.07 trades/sem. Pode haver semanas com 0–3 sinais.
2. **2024 foi negativo (-5.82R em 49 trades).** Não overfit, mas indica que regime macro pode invalidar temporariamente.
3. **Sample 2.36 anos** — confiança estatística limitada para promoção automática.
4. **DXY filter PENDENTE** (v1.1) — refinamento futuro com pull MCP live.
5. **NÃO operar SHORT em XAUUSD** — nenhum módulo SHORT confirmado em XAU intraday.
6. **Body 60% é específico para XAU** — não confundir com body 70% do EURUSD/V2.

## 14. Substituições

Substitui operacionalmente (legacy): `XAUUSD_1H_LONG_REJECTION_EXECUTION` (rejection-based, audit confirmou sem edge — PF 1.04, no_top5 -5.38R, n=1338).

## 15. Histórico de versões

| Data | Versão | Mudança |
|---|---|---|
| 2026-05-12 | v1.0 | Criação. Sample n=127 / 2.36y. PF 1.57, win 44.9%, no_top5 +14.75, no_top10 +2.50. Default SETUP_CANDIDATO_FORTE até validação ao vivo. DXY filter pendente para v1.1. |
