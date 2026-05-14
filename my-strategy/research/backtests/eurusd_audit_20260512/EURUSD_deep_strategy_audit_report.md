# EURUSD Deep Strategy Audit — Relatório Executivo

**Data:** 2026-05-12
**Modo:** read-only research / backtest CSV
**Ativo:** PEPPERSTONE:EURUSD
**Spread custom:** 0.05R/trade

---

## ⚠️ VEREDITO EM UMA FRASE

**O módulo EURUSD atual perde -104R em backtest. NENHUMA das 40+ estratégias testadas — incluindo filtros macro DXY que teoricamente deveriam funcionar — produz edge significativo. Recomenda-se DESATIVAR o módulo atual e considerar tratar EURUSD apenas como SETUP_CANDIDATO_FORTE (D_4H_BREAKOUT_REGIME, edge ~zero mas não negativo).**

---

## 1. Cobertura de dados

| TF | Bars | Início | Fim | Span |
|---|---:|---|---|---:|
| 1D | 6829 | 1999-01-03 | 2026-05-10 | 27.3 anos |
| 12H | 7914 | 2011-02-07 | 2026-05-11 | 15.3 anos |
| 4H | 11447 | 2019-01-01 | 2026-05-11 | **7.4 anos** ← swing |
| 30M | 16826 | 2025-01-01 | 2026-05-11 | 1.4 anos |
| 15M | 10903 | 2025-11-30 | 2026-05-11 | 5 meses |

**Não há CSV de 1H disponível.** Não impede análise.

DXY (TVC) disponível: 6.3 anos (2020-01 → 2026-05) — usado como filtro macro.

## 2. Módulo atual — RESULTADO CATASTRÓFICO

### A. EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION (atual)

| Métrica | Valor |
|---|---:|
| Trades | 605 (1.4y) |
| Total Net R | **-104.34R** |
| Avg Net R | -0.173 |
| Profit Factor | **0.65** |
| Win rate | 21.5% |
| Max losing streak | 23 |
| Frequência | 8.8 trades/semana (overtrade) |

❌ **Pior que US500_INTRADAY_LONG_PULLBACK_EXECUTION proporcionalmente.** Perde -0.17R/trade.

## 3. Estratégias novas testadas — TODAS marginais ou negativas

### 3.1 4H Regime-filtered Breakout (XAU/ETH pattern)

| Variante | n | Total Net R | Avg | PF | Win% |
|---|---:|---:|---:|---:|---:|
| **D_4H_BREAKOUT_REGIME target 3R** | 117 | **+3.64** | 0.031 | **1.08** | 30.8% |
| target 4R | 117 | -3.41 | -0.029 | 0.92 | 29.9% |
| target 5R | 117 | -3.41 | -0.029 | 0.92 | 29.9% |

✅ Único candidato positivo do grupo regime. Mas edge é **zero estatístico**.

### 3.2 Failed Breakdown (US500 winner pattern)

| Variante | n | Net R | Avg | PF |
|---|---:|---:|---:|---:|
| target 2.5R | 17 | +1.83 | 0.108 | 1.42 |
| target 3.0R | 17 | -0.24 | -0.014 | 0.95 |

⚠️ Sample muito pequeno (17 trades em 7.4y = 1 a cada 5 meses). Não confiável.

### 3.3 Macro DXY Filter — NÃO ajuda

| Filtro | Trades | Total Net R | vs Baseline |
|---|---:|---:|---:|
| Sem DXY filter (D regime) | 117 | +3.64 | baseline |
| + DXY bearish | 115 | +3.50 | similar |
| + DXY falling | 116 | +2.45 | pior |
| + DXY bearish + falling | 115 | +3.50 | similar |
| + DXY in macro bear regime (<EMA200 + falling) | 342 | **-33.87** | **PIOR!** |

🔴 **Contraintuitivo:** DXY filter NÃO melhora EURUSD! Possíveis razões:
- Correlação EUR/DXY é -0.95 em magnitude (direção) mas timing é diferente
- DXY suas próprias oscilações no curto prazo geram noise
- Momentum EUR em micro-timeframes não tracks DXY tightly

### 3.4 Pullback EMA20 / EMA50 — falham

| Variante | n | Total Net R | Avg |
|---|---:|---:|---:|
| H2_EMA20_pullback_4H target 3R | 419 | **-73.11** | -0.175 |
| H2_EMA20_pullback_30M target 2R | 685 | **-149.78** | -0.219 |
| G_pullback_EMA50_4H | 150 | -24.78 | -0.165 |

❌ Forex de major pairs não respeita EMA pullback como FX exotic ou cripto.

### 3.5 Inside Bar, Hammer, RSI Oversold Bounce

| Variante | n | Total Net R | Avg | Veredito |
|---|---:|---:|---:|---|
| H5_inside_bar_break_4H | 150 | -55.56 | -0.370 | ❌ |
| H_hammer_4H | 152 | -38.58 | -0.254 | ❌ |
| H6_RSI_oversold_bounce_4H | 70 | -17.51 | -0.250 | ❌ |
| H1_london_open_30M | 85 | -15.45 | -0.182 | ❌ |

❌ Padrões clássicos forex todos falharam.

### 3.6 BB Squeeze 4H

| Variante | n | Total Net R | Avg |
|---|---:|---:|---:|
| target 3R | 110 | -5.68 | -0.052 |
| target 4R | 110 | -18.14 | -0.165 |

❌ Squeeze breakouts não funcionam em EURUSD.

## 4. Year-by-year do melhor candidato (D_4H_BREAKOUT_REGIME 3R)

| Ano | Trades | Net R | Avg | Win% |
|---|---:|---:|---:|---:|
| 2019 | 14 | +0.66 | 0.047 | 21.4% |
| 2020 | 27 | **+8.12** | 0.301 | 37.0% |
| 2021 | 6 | -3.88 | -0.647 | 16.7% |
| 2022 | 8 | +0.83 | 0.104 | 37.5% |
| 2023 | 21 | -1.55 | -0.074 | 33.3% |
| 2024 | 18 | -3.90 | -0.217 | 22.2% |
| 2025 | 16 | -0.28 | -0.018 | 37.5% |
| 2026 (parcial) | 7 | +3.65 | 0.521 | 28.6% |

**Apenas 2020 carrega o edge.** 4 anos negativos + 4 anos positivos. **Edge não é estatisticamente robusto.**

## 5. Por que EURUSD é tão difícil

| Razão | Impacto |
|---|---|
| Par forex mais líquido do mundo ($1.5T/dia) | Mercado eficiente, sem ineficiências técnicas |
| Mean reversion estrutural | Breakouts falham frequentemente |
| Preços determinados por Fed/ECB events | Candle patterns não predicizem |
| Spread vs movement médio relativamente alto | Custo de execução come edge marginal |
| Carry trades dominam fluxos | Posições por interest differential, não momentum |

EURUSD é estruturalmente similar ao US500 — **mercado eficiente onde estratégias técnicas simples raramente entregam edge**.

## 6. Critérios SETUP_VALIDO — NENHUM ATENDE

| Critério | Mínimo | Melhor EURUSD (D_4H_3R) |
|---|---:|---:|
| Avg R líquido | > +0.20 | 0.031 ❌ |
| PF líquido | > 1.40 | 1.08 ❌ |
| Sem top 10 ainda positivo | sim | -21.85 ❌ |
| Funciona em > 1 regime | sim | apenas 2020 ❌ |
| Trades/mês | >= 1 | 1.42 ✅ (única que passa) |

## 7. Decisões diretas

### 7.1 EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION (atual)

**❌❌ DESATIVAR.** -104.34R em 1.4 ano. Pior módulo do sistema.

### 7.2 Existe estratégia swing EURUSD melhor?

**Marginalmente.** D_4H_BREAKOUT_REGIME target 3R: +3.64R em 7.4y = +0.49R/ano = edge praticamente nulo.

### 7.3 Existe estratégia intraday EURUSD melhor?

**NÃO.** Todas as variantes intraday testadas perdem dinheiro (-15R a -150R).

### 7.4 DXY como filtro macro

**NÃO ajuda.** Resultado similar a baseline. Contraintuitivo mas comprovado em backtest.

### 7.5 SHORT em EURUSD

Não testado isoladamente, mas paridade USD-bias atual sugere que SHORT teria edge negativo. **Manter proibido.**

## 8. Recomendações finais

### Opção A — Conservadora (recomendada)

1. **DESATIVAR `EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION`** (perde -104R)
2. **Criar `EURUSD_4H_LONG_BREAKOUT_REGIME` como SETUP_CANDIDATO_FORTE apenas** (não SETUP_VALIDO)
   - Edge marginal mas pelo menos não negativo
   - 1.4 trades/mês — frequência aceitável
   - Manual review obrigatório

### Opção B — Minimalista

1. **DESATIVAR `EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION`**
2. **Remover EURUSD da watchlist operacional automática**
3. Manter apenas para contexto (entender USD strength/weakness)

### Opção C — Forward-test agressivo

1. **DESATIVAR `EURUSD_30M_QUALITY_BREAKOUT_CONTINUATION`**
2. **Criar `EURUSD_4H_LONG_BREAKOUT_REGIME` como SETUP_CANDIDATO_FORTE** (Opção A)
3. **Tentar pesquisar dados ECB/Fed yield differentials** (não temos hoje) para construir filtro fundamentalista forte
4. Pesquisa futura: macro carry indicator, COT report, etc.

## 9. Definição do módulo alternativo (Opção A/C)

**EURUSD_4H_LONG_BREAKOUT_REGIME — SETUP_CANDIDATO_FORTE apenas**

```
Asset: PEPPERSTONE:EURUSD
TF: 4H, LONG only
Default classification: SETUP_CANDIDATO_FORTE
NUNCA emitir SETUP_VALIDO automaticamente

Trigger:
- close > swing_high(10)
- close > open + body_pct >= 0.5
- RSI > RSI-based MA

Filtros regime (todos):
- Close > EMA(200)
- EMA(50) > EMA(200)
- ATR(14) > ATR_MA(20)
- EMA(50) slope > 0
- ADX(14) >= 20

Stop: low - 0.5 × ATR(14)
Target: 3R
BE após +1R
Max hold: 24 candles 4H

Métricas backtest (7.4y, 0.05R spread):
- 117 trades, 1.42/mês
- Net R: +3.64 (marginal)
- Avg R: 0.031
- PF: 1.08
- Win rate: 30.8%
- Max losing streak: 8
- Sem top 10: -21.85R (FRÁGIL)

Manual execution obrigatório
D2R required: true
```

## 10. Resumo em uma frase

**EURUSD, como US500, é mercado eficiente onde estratégias técnicas simples não produzem edge estatístico. O módulo atual deve ser desativado por perder -104R. Substituto proposto (D_4H_BREAKOUT_REGIME) tem edge zero mas pelo menos não é catastrófico — manter como SETUP_CANDIDATO_FORTE apenas, ou considerar remover EURUSD da watchlist operacional.**
