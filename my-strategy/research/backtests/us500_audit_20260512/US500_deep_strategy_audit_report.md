# US500 Deep Strategy Audit — Relatório Executivo

**Data:** 2026-05-12
**Modo:** read-only research / backtest CSV
**Ativo:** PEPPERSTONE:US500
**Spread custom:** 0.05R/trade

---

## ⚠️ VEREDITO IMPACTANTE EM UMA FRASE

**Os dois módulos US500 atuais perdem dinheiro significativamente (-67R e -105R em backtest), e NENHUMA das 28 estratégias testadas (atuais + régua antiga + regime-filtered + buy-the-dip + breakout-low-target) produz edge robusto suficiente para justificar SETUP_VALIDO automático. US500 deve ser DESATIVADO como módulo automático e mantido apenas como contexto de mercado.**

---

## 1. Cobertura de dados

| TF | Bars | Início | Fim | Span |
|---|---:|---|---|---:|
| 1D | 3423 | 2013-02-21 | 2026-05-11 | 13.2 anos |
| 12H | 6106 | 2014-07-20 | 2026-05-12 | 11.8 anos |
| 4H | 6825 | 2021-12-03 | 2026-05-08 | **4.4 anos** ← swing |
| 1H | 13875 | 2024-01-01 | 2026-05-08 | 2.3 anos |
| 30M | 15906 | 2025-01-01 | 2026-05-08 | 1.3 anos |
| 15M | 10308 | 2025-11-30 | 2026-05-08 | 5 meses |

4H cobre 2022 bear + 2023-2025 bull rally — boa diversidade de regime para teste.

## 2. Módulos atuais — RESULTADO

### A. US500_4H_LONG_PULLBACK_REJECTION (atual)

| Métrica | Valor |
|---|---:|
| Trades | 412 (4.4y) |
| Total Net R @ 0.05R | **-67.65R** |
| Avg Net R | -0.164 |
| Profit Factor | **0.68** |
| **Win rate** | **12.9%** |
| Max losing streak | 35 |
| Sem top 10 | -112.15R |

**Year-by-year:** TODOS os anos negativos (2022 -11, 2023 -21, 2024 -5, 2025 -28, 2026 -2).

❌ **Estratégia matematicamente perdedora.** Win rate 13% com target 4.5R precisaria de 22%+ pra empatar. Não atinge.

### B. US500_INTRADAY_LONG_PULLBACK_EXECUTION (proxy 30M)

| Métrica | Valor |
|---|---:|
| Trades | 943 (1.3y) |
| Total Net R | **-105.20R** |
| Avg Net R | -0.112 |
| Profit Factor | **0.78** |
| Win rate | 17.9% |
| Max losing streak | 32 |
| Sem top 10 | -144.70R |

❌ **DESASTRE.** Frequência 14 trades/semana mas perde -0.11R/trade. Custo: ~50R/ano em comissão líquida negativa.

## 3. Régua antiga — também perde

| Variante | Trades | Net R | Avg | PF |
|---|---:|---:|---:|---:|
| RSI ext + Bubble LONG 4H | 46 | -6.05 | -0.131 | 0.76 |
| RSI ext + Bubble SHORT 4H | 66 | **-35.30** | -0.535 | 0.18 |
| RSI ext softened LONG | 67 | -10.10 | -0.151 | 0.72 |

❌ Régua antiga também sem edge. SHORT é catastrófico (-35R em 66 trades).

## 4. Novas hipóteses testadas (28 estratégias) — apenas 2 chegam ao breakeven

### 4.1 Regime-filtered breakout (estilo XAU/ETH)

| Variante | n | Total Net R | Avg | PF | Sem top 10 |
|---|---:|---:|---:|---:|---:|
| target=3R | 87 | -3.30 | -0.038 | 0.91 | -24.94 |
| target=4R | 87 | -4.50 | -0.052 | 0.88 | -24.94 |
| target=4.5R | 87 | -1.80 | -0.021 | 0.95 | -24.53 |
| target=5R | 87 | -1.80 | -0.021 | 0.95 | -24.53 |
| **target=4.5R + body 60%** | **72** | **+1.01** | **0.014** | **1.03** | **-18.93** |
| target=4.5R + ADX 25 | 56 | -6.57 | -0.117 | 0.73 | -21.14 |

⚠️ Melhor: regime + body60% chega a **+1.01R em 4.4 anos** = praticamente zero. Sem top 10: -18.93R (negativo).

### 4.2 Pullback to EMA50 em bull regime

| Variante | n | Total Net R | Avg | PF |
|---|---:|---:|---:|---:|
| 4H pullback EMA50 target 3R | 102 | -7.76 | -0.076 | 0.82 |
| 4H pullback EMA50 target 4R | 102 | -10.22 | -0.100 | 0.77 |
| 1H pullback EMA50 target 3R | 222 | -44.92 | -0.202 | 0.59 |
| 1H pullback EMA50 + HTF1D 3R | 206 | -35.48 | -0.172 | 0.64 |

❌ Pullback EMA50 falha em US500 (diferente de ETH onde funcionou). HTF filter ajuda marginalmente mas não suficiente.

### 4.3 1H/30M breakout regime-filtered

| Variante | n | Total Net R | Avg | PF | Sem top 10 |
|---|---:|---:|---:|---:|---:|
| **F_1H_BREAKOUT_REGIME_FILTERED** | 225 | **+6.05** | 0.027 | 1.06 | -29.16 |
| G_30M_BREAKOUT_REGIME_FILTERED | 233 | -8.73 | -0.038 | 0.92 | -36.33 |

⚠️ 1H breakout regime chega a +6.05R em 2.3y. **Mas sem top 10 vira -29.16R — completamente fat-tail dependent.**

### 4.4 Buy-the-dip variantes (testes extras)

| Variante | n | Net R | Avg | PF |
|---|---:|---:|---:|---:|
| BTD_4H_pullback_EMA50_target3R | 149 | +1.00 | 0.007 | 1.02 |
| BREAK_2R_1H_regime | 248 | +0.24 | 0.001 | 1.00 |
| BTD_4H_pullback_EMA50_HTF1D_2.5R | 144 | -1.94 | -0.014 | 0.97 |
| BREAK_2R_4H_regime | 117 | -2.57 | -0.022 | 0.94 |

⚠️ Melhor é +1R em 149 trades = literalmente zero edge.

## 5. Filter impact (4H LONG breakout baseline 4.5R)

| Filtro | n | Total Net R | Avg | PF |
|---|---:|---:|---:|---:|
| Baseline RSI > MA | 569 | -60.54 | -0.106 | 0.78 |
| + close > EMA200 | 472 | -55.26 | -0.117 | 0.77 |
| + EMA50 > EMA200 | 397 | -52.40 | -0.132 | 0.73 |
| + ATR expanding | 247 | -14.90 | -0.060 | 0.87 |
| + ADX 20 | 382 | -47.53 | -0.124 | 0.75 |
| + ADX 25 | 253 | -27.71 | -0.110 | 0.78 |
| + EMA50 slope > 0 | 466 | -48.18 | -0.103 | 0.79 |
| + Full regime filter | 87 | -1.80 | -0.021 | 0.95 |
| **+ Full regime + body 60%** | **72** | **+1.01** | **0.014** | **1.03** |

Mesmo o melhor combo de filtros mal sai do negativo.

## 6. Cost sensitivity — melhor candidato (4H breakout regime body 60%)

| Spread | Total Net R | Avg | PF | Positivo? |
|---:|---:|---:|---:|---|
| 0.00R (gross) | +4.61 | 0.064 | 1.16 | ✅ |
| 0.02R | +3.17 | 0.044 | 1.11 | ✅ |
| 0.03R | +2.45 | 0.034 | 1.08 | ✅ |
| **0.05R (retail)** | **+1.01** | **0.014** | **1.03** | ✅ marginal |
| 0.07R | -0.43 | -0.006 | 0.99 | ❌ |
| 0.10R | -2.59 | -0.036 | 0.92 | ❌ |

Edge tão fraco que **qualquer spread acima de 0.07R o aniquila.**

## 7. Análise temporal — top candidatos

### D_4H_BREAKOUT_REGIME_body60_4.5R (melhor swing, n=72, 4.4y)

| Ano | Trades | Net R | Avg | Win% |
|---|---:|---:|---:|---:|
| 2022 (bear) | 13 | -1.92 | -0.148 | 30.8% |
| 2023 | 25 | -5.00 | -0.200 | 24.0% |
| 2024 | 24 | **+13.91** | **0.580** | **66.7%** |
| 2025 | 10 | -5.99 | -0.599 | 0.0% |

**Edge concentrado em 2024 (1 ano).** 3 anos de 4 perdem dinheiro. **Não passa critério de "funcionar em mais de um regime".**

### F_1H_BREAKOUT_REGIME_FILTERED (melhor intraday, n=225, 2.3y)

| Ano | Trades | Net R | Avg | Win% |
|---|---:|---:|---:|---:|
| 2024 | 108 | +12.62 | 0.117 | 35.2% |
| 2025 | 81 | -15.91 | -0.196 | 23.5% |
| 2026 (parcial) | 36 | +9.34 | 0.259 | 41.7% |

Mistura. 2025 catastrófico. Edge não consistente.

## 8. Análise por elemento individual em US500

| Elemento | Edge em US500 | Recomendação |
|---|---|---|
| RSI extremo | Negativo isolado, neutro combinado | Não usar |
| RSI > MA | Neutro | Apenas confluência |
| Rejection close (pavio inferior) | **Catastrófico** (-67R baseline) | **DESCARTAR** |
| Momentum continuation (breakout) | Marginal mesmo com regime | Apenas com filtros estritos |
| EMA200/EMA50 stack | Útil mas não suficiente | Manter como filtro |
| ATR expanding | Adiciona algum edge | Manter |
| ADX 20 | Marginal | ADX 25 ligeiramente melhor |
| Body >= 60% | Único filtro que vira regime positivo | **Usar se manter algo** |
| HTF 1D bullish | Marginal | Confluência opcional |
| Pullback EMA50 | **Não funciona** (vs ETH onde funciona) | **DESCARTAR** |
| Pullback EMA20 | Catastrófico | **DESCARTAR** |
| SHORT direção | **Catastrófico** (-35R) | **NÃO automatizar** |
| 4H setup | Pouco edge | Vide acima |
| 1H setup | Marginal | F é o "menos pior" |
| 30M setup | Negativo | **DESCARTAR** |
| 15M trigger | Não testado isoladamente; dados insuficientes | N/A |
| Target 2R | Win rate sobe mas total flat | Não compensa |
| Target 4.5R / 5R | Tradicional mas exige win rate impossível em US500 | Não usar sem regime forte |
| Trailing | Não testado (já é "off" por design) | Manter off |
| BE após +1R | Standard | Manter |

## 9. Comparação final consolidada

| # | Estratégia | TF | Direção | Trades | Net R | Avg | PF | Sem top 10 | Veredito |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | Régua antiga RSI+Bubble | 4H | LONG | 46 | -6.05 | -0.131 | 0.76 | -24.80 | ❌ DESCARTAR |
| 2 | Régua antiga softened | 4H | LONG | 67 | -10.10 | -0.151 | 0.72 | -29.60 | ❌ DESCARTAR |
| 3 | Régua antiga SHORT | 4H | SHORT | 66 | -35.30 | -0.535 | 0.18 | -42.80 | ❌ DESCARTAR (catastrófico) |
| 4 | **US500_4H_LONG_PULLBACK_REJECTION atual** | 4H | LONG | 412 | **-67.65** | -0.164 | 0.68 | -112.15 | ❌❌ **DESATIVAR** |
| 5 | **US500_INTRADAY_LONG_PULLBACK_EXECUTION atual** | 30M | LONG | 943 | **-105.20** | -0.112 | 0.78 | -144.70 | ❌❌❌ **DESATIVAR** |
| 6 | D_4H_breakout_regime body60 4.5R | 4H | LONG | 72 | +1.01 | 0.014 | 1.03 | -18.93 | ⚠️ Marginal — não passa critério mínimo |
| 7 | F_1H_breakout_regime | 1H | LONG | 225 | +6.05 | 0.027 | 1.06 | -29.16 | ⚠️ Marginal + fat-tail |
| 8 | BTD_4H_pullback_EMA50 target 3R | 4H | LONG | 149 | +1.00 | 0.007 | 1.02 | -26.92 | ⚠️ Zero edge |
| 9 | BREAK_2R_1H_regime | 1H | LONG | 248 | +0.24 | 0.001 | 1.00 | -18.33 | ❌ Zero edge |
| 10 | Pullback EMA50 1H | 1H | LONG | 222 | -44.92 | -0.202 | 0.59 | -74.42 | ❌ DESCARTAR |

## 10. Critérios mínimos para SETUP_VALIDO — NENHUM ATENDE

| Critério | Mínimo | Melhor US500 candidato (F 1H) |
|---|---:|---:|
| Avg R líquido | > +0.20 | 0.027 ❌ |
| PF líquido | > 1.40 | 1.06 ❌ |
| Sem top 10 ainda positivo | sim | -29.16 ❌ |
| Funciona em > 1 ano | sim | 2024+/2025-/2026+ — instável ❌ |
| Trades/mês | >= 1 | 8.17 ✅ (única que passa) |

## 11. Decisões diretas

### 11.1 US500_4H_LONG_PULLBACK_REJECTION (atual)

**❌❌ DESATIVAR.** -67.65R em 4.4 anos com PF 0.68 é absurdo. Win rate 13% torna o target 4.5R matematicamente perdedor.

### 11.2 US500_INTRADAY_LONG_PULLBACK_EXECUTION (atual)

**❌❌❌ DESATIVAR URGENTEMENTE.** -105R em 1.3 ano. Pior módulo do sistema. Frequência 14 trades/semana garante perdas contínuas.

### 11.3 Existe estratégia swing US500 melhor?

**Marginalmente. O melhor encontrado é breakeven (+1R em 4.4 anos).** Não vale implementar — qualquer slippage adicional o aniquila.

### 11.4 Existe estratégia intraday US500 melhor?

**Marginalmente. F_1H_breakout_regime tem +6R em 2.3 anos.** Mas depende de fat-tails (sem top 10 = -29R) e 2025 foi negativo. Não confiável.

### 11.5 LONG-only continua sendo melhor?

**Sim — SHORT em US500 é catastrófico (-35R em 66 trades, win rate 6%).** US500 tem bull bias estrutural absoluto pós-2022.

### 11.6 SHORT deve continuar proibido?

**SIM, absolutamente.** Em 13 anos de dados, S&P500 subiu ~300%. Tentar shortar é matematicamente lutar contra a curva.

### 11.7 O que implementar no Claude?

**Nada novo para US500.** Recomendo:
1. Desativar ambos os módulos atuais
2. Manter US500 na watchlist apenas para CONTEXT (interpretação macro/risk-on)
3. Não automatizar nenhum módulo US500 como SETUP_VALIDO
4. Aceitar que US500 não é bom candidato para systematic retail trading com estratégias técnicas simples

### 11.8 Quais módulos podem gerar SETUP_VALIDO?

**NENHUM em US500.** Não há edge robusto encontrado.

### 11.9 Quais devem ficar como SETUP_CANDIDATO_FORTE?

Se quiser **manter alguma presença operacional US500**, o melhor candidato é:

- **F_1H_BREAKOUT_REGIME_FILTERED** como SETUP_CANDIDATO_FORTE apenas, com revisão manual obrigatória.
- Edge marginal (+0.027 avg) mas pode ser útil em janelas favoráveis.
- **NÃO promover automaticamente** sob nenhuma circunstância.

### 11.10 O que medir em D2R nos próximos 30-50 eventos

Como sugestão (se manter US500 ativo):
- Performance condicional a "S&P 500 em rally claro" vs "consolidação"
- Sazonalidade de horários (Asia open vs US open)
- Spread real do broker em US500 — pode estar acima de 0.07R que mata edge

## 12. Hipóteses para pesquisa futura (NÃO recomendar implementar agora)

1. **Filtros de volatilidade índice (VIX):** quando VIX < 15 = chop ruim, VIX > 25 = oportunidade. Requer dados externos.
2. **Eventos macro filtrados:** operar US500 apenas em dia de FOMC/CPI/NFP? Pode haver edge em moves direcionais.
3. **Pair trade NQ vs SPX:** quando NASDAQ supera S&P, sinal de risk-on amplo. Cross-asset signal.
4. **Open range breakout (intraday):** primeira hora forma range, romper o range em direção da tendência diária = trade. Não testado aqui (sem dados de sessão).
5. **Long-vol regime filter:** SP500 com ATR > média de 30 dias = ambiente diferente.

Nenhuma dessas tem dados suficientes pra validar **agora**. Não vale gastar esforço sem evidência.

## 13. Avisos importantes

⚠️ **Diferente de XAUUSD e ETHUSD onde encontramos edge robusto, em US500 NÃO há edge claro nos dados disponíveis.** Isso não é "falha do audit" — é uma propriedade do ativo.

⚠️ **US500 é um dos mercados mais eficientes do mundo.** Estratégias técnicas simples (pullback, breakout, rejection) raramente entregam edge sustentável em índices large-cap líquidos. O dinheiro real em SP500 vem de:
- Earnings season swings (event-driven)
- Macro positioning (Fed, recessão, etc.)
- Mean reversion em extremos com posições gigantes
- Carry trades (vol, dividend, options structures)

Nenhum desses é capturável por candle-pattern retail tradicional.

⚠️ **Conselho honesto:** considerar **REMOVER US500 da watchlist operacional automática** e tratar como ativo de **contexto de mercado apenas** — usar para entender risk-on/risk-off antes de operar outros ativos (XAUUSD, ETHUSD).

## 14. Resumo em uma frase

**US500 não tem edge sistemático nos dados disponíveis com estratégias técnicas simples; recomenda-se desativar ambos os módulos atuais que perdem dinheiro significativamente, NÃO substituir, e considerar usar US500 apenas como contexto macro para outros ativos da watchlist.**
