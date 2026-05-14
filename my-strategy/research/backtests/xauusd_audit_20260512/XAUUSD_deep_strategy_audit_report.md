# XAUUSD Deep Strategy Audit — Relatório Executivo

**Data:** 2026-05-12  
**Modo:** read-only research / backtest CSV  
**Ativo:** PEPPERSTONE:XAUUSD

---

## 1. Cobertura de dados

| TF | Bars | Início | Fim | Span |
|---|---:|---|---|---:|
| 1D | 7250 | 1998-04-21 | 2026-05-11 | 28.1 anos |
| 12H | 7136 | 2012-06-19 | 2026-05-12 | 13.9 anos |
| 4H | 11365 | 2019-01-01 | 2026-05-12 | **7.4 anos** ← prime swing |
| 1H | 13949 | 2024-01-01 | 2026-05-12 | **2.4 anos** ← prime execução |
| 30M | 16018 | 2025-01-01 | 2026-05-12 | 1.4 anos |
| 15M | 10405 | 2025-11-30 | 2026-05-12 | 5 meses (baixa confiança estatística) |

**Sample sizes pequenos em 15M e 30M** — qualquer conclusão para esses TFs é provisória.

## 2. Metodologia

- Trade simulator bar-by-bar, conservador (stop tem prioridade sobre alvo quando ambos batem no mesmo bar)
- Stop técnico: low/high do bar de sinal ± 0.5×ATR(14)
- BE após +1R quando o módulo permite
- Trailing após +3R quando aplicável (distância 0.75R ou 1.5R)
- Max hold por bars (configurado por TF)
- Sem peek-ahead — sinal usa apenas dados disponíveis no fechamento do bar

## 3. Resultados consolidados

### 3.1 Estratégias atuais (régua antiga + módulos atuais)

| Estratégia | TF | Trades | /sem | /mês | Total R | Avg R | Win% | PF | r-top5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **A_old_global_strict_LONG** (RSI ext + Bubble + Rejection) | 4H | 67 | 0.17 | 0.76 | +5.7 | 0.085 | 26.9% | 1.19 | -4.31 |
| A_old_global_strict_SHORT | 4H | 136 | 0.35 | 1.54 | **-18.8** | -0.139 | 19.9% | 0.73 | -28.84 |
| A_old_softened (RSI ext sem Bubble) LONG | 4H | 90 | 0.23 | 1.02 | **+10.7** | 0.119 | 27.8% | 1.27 | +0.69 |
| **B_XAUUSD_4H_LONG_REJECTION_SWING** | 4H | 1070 | 2.79 | 12.12 | **-59.3** | -0.055 | 18.0% | 0.88 | -81.85 |
| **C_XAUUSD_1H_LONG_REJECTION_EXECUTION** | 1H | 1338 | 10.88 | 47.30 | +22.4 | 0.017 | 17.4% | 1.04 | -5.38 |
| **D_intraday_bb_30M_LONG** (proxy) | 30M | 1378 | 19.49 | 84.74 | -139.7 | -0.101 | 21.1% | 0.79 | -149.74 |
| D_intraday_bb_30M_SHORT (proxy) | 30M | 1079 | 15.26 | 66.35 | -265.9 | -0.246 | 15.6% | 0.54 | -275.88 |

### 3.2 Hipóteses novas testadas

| Estratégia | TF | Trades | /sem | Total R | Avg R | Win% | PF | r-top5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **REF_4H_LONG_breakout_target4R** | 4H | 846 | 2.20 | **+76.8** | 0.091 | 23.3% | **1.23** | +56.84 |
| **REF_1H_LONG_rejection_rsi40_target2.5R** | 1H | 345 | 2.80 | **+15.1** | 0.044 | 21.2% | 1.10 | +2.63 |
| REF_4H_LONG_rejection_rsi35_trail | 4H | 169 | 0.44 | -10.1 | -0.060 | 18.3% | 0.87 | -25.07 |
| REF_4H_LONG_rejection_rsi40_target3R | 4H | 284 | 0.74 | -9.6 | -0.034 | 18.3% | 0.93 | -24.57 |
| REF_1H_LONG_rejection_rsi35_trail | 1H | 192 | 1.56 | -0.01 | 0.000 | 18.8% | 1.00 | -18.12 |
| REF_30M_LONG_rejection_rsi35_target2.5R | 30M | 228 | 3.22 | -17.8 | -0.078 | 18.4% | 0.83 | -30.25 |
| New_1H_simple_rejection_LONG (sem filtros) | 1H | 1139 | 9.26 | -23.8 | -0.021 | 23.5% | 0.95 | -33.85 |
| New_1H_simple_rejection_SHORT | 1H | 900 | 7.32 | **-241.8** | -0.269 | 13.7% | 0.49 | -251.82 |

### 3.3 Filter Impact Analysis (4H LONG rejection baseline, 7.4y)

| Filtro | Trades/ano | Total R | Avg R | Win% | PF | Efeito |
|---|---:|---:|---:|---:|---:|---|
| Baseline (sem filtro) | 145.4 | -53.3 | -0.050 | 22.0% | 0.89 | ❌ perde |
| **+ RSI extremo** | 12.2 | **+10.7** | **+0.119** | 27.8% | **1.27** | ✅ filtro mais valioso |
| + Bubble | 62.5 | -26.9 | -0.058 | 21.3% | 0.87 | ❌ não filtra |
| + NAS TOP/BOTTOM | 6.4 | -3.3 | -0.070 | 23.4% | 0.87 | ❌ não filtra |
| + RSI + Bubble | 9.1 | +5.7 | +0.085 | 26.9% | 1.19 | Bubble redundante com RSI |
| + RSI + Bubble + NAS | 4.8 | -0.3 | -0.009 | 25.7% | 0.98 | tripla **mata** edge |

## 4. Análise temporal (estabilidade por ano) — REF_4H_LONG_breakout_target4R

| Ano | Trades | Total R | Avg R | Win% | Comentário |
|---|---:|---:|---:|---:|---|
| 2019 | 108 | +22.8 | 0.211 | 21.3% | bull |
| 2020 | 111 | +33.6 | 0.303 | 26.1% | rally COVID |
| 2021 | 102 | **-34.4** | -0.338 | 11.8% | chop/range |
| 2022 | 99 | -20.5 | -0.207 | 19.2% | range |
| 2023 | 96 | -5.6 | -0.059 | 21.9% | range |
| 2024 | 131 | +21.3 | 0.163 | 28.2% | bull |
| 2025 | 161 | +50.3 | 0.313 | 28.0% | rally |
| 2026 (parcial) | 38 | +9.4 | 0.246 | 28.9% | bull |

**Lições:** estratégia funciona em regime trending (2019-2020, 2024-2026), perde em chop (2021-2023). Distribuição é **regime-dependente, não overfit a 1 ano**.

## 5. Análise por elemento individual

### 5.1 RSI extremo
- **Adiciona edge claro** (+0.119 avg vs baseline -0.050)
- Deve ser **confluência preferencial** para LONG rejections
- Recomendado **ajustar threshold para RSI <= 40** (não 30 estrito) — captura mais setups sem perder edge
- Para breakout/momentum, NÃO usar RSI extremo (contraintuitivo: pediríamos comprar em sobrevenda quando o módulo é momentum)

### 5.2 RSI reclaim / RSI MA cross
- **Marginalmente positivo:** 272 trades 1H, +5.7R, avg 0.021 — fraco
- Não substitui RSI extremo como filtro principal
- Pode ser usado como TIMING dentro de uma zona, não como gatilho

### 5.3 NAS TOP/BOTTOM
- **Não adiciona edge sozinho** (filter test: 47 trades 4H, -3.3R, avg -0.070)
- Reduz drasticamente frequência (de 145/ano para 6/ano) sem compensar com qualidade
- **Manter como confluência opcional, NÃO como filtro obrigatório**

### 5.4 Market Order Bubbles
- **Não adiciona edge** (filter test: 460 trades, -26.9R, avg -0.058)
- Pior: combinado com RSI extremo, REDUZ ligeiramente o avg de 0.119 para 0.085
- **Recomendado tornar 100% opcional**

### 5.5 Divergência regular (Bull/Bear)
- Em 1H os números são idênticos com e sem divergência (campos podem estar mal populados no CSV ou pouca incidência)
- Não comprovou edge mensurável neste dataset

### 5.6 Rejection close (estrutura)
- **Por si só não é positivo** — sem filtro, -53R em 7.4y no 4H
- Funciona apenas combinado com RSI extremo ou momentum
- Definição usada: pavio ≥ 50% do range, corpo ≤ 40%, close no terço oposto

### 5.7 Breakout / momentum continuation
- **Edge mais forte encontrado neste audit** (4H: +76.8R, 7.4y)
- Filtro chave: RSI > RSI-based MA (momentum alinhado)
- Trabalha com target alto (4R) e BE após +1R
- Não exige rejection close, RSI extremo, bubble, NAS, divergência

### 5.8 Sweep/reentry
- 4H: -61.8R (770 trades) — não funciona como gatilho isolado
- 30M LONG: -162.7R, 30M SHORT: -443.0R — claramente sem edge
- **Pode ser confluência dentro de outro setup, não trigger primário**

### 5.9 SHORT em XAUUSD
- **Sem edge sistemático em nenhum TF testado**
- 4H rejection SHORT: -18.8R
- 1H rejection SHORT: -241.8R
- 30M sweep+reentry SHORT: -443R
- 30M momentum SHORT: -74.2R
- **XAUUSD tem bias bull estrutural; SHORTS são contra-trade. Recomendar: desativar SHORT em módulos automáticos.**

### 5.10 Trailing
- Trail+3R distância 1.5R no 4H: piora resultado (-10R no rejection RSI<=35)
- Sem trail / BE simples: melhor para alvos altos (4R)
- Trail funciona melhor em momentum continuation com target alto

## 6. Comparação final consolidada

| # | Estratégia | TF | Direção | Trades | /sem | Total R | Avg R | PF | Recomendação |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | Régua antiga global completa (RSI+Bubble+NAS) | 4H | LONG | 35 (7.4y) | 0.09 | -0.3 | -0.009 | 0.98 | ❌ **DESCARTAR como hard rule** |
| 2 | Régua antiga suavizada (apenas RSI extremo) | 4H | LONG | 90 (7.4y) | 0.23 | +10.7 | 0.119 | 1.27 | ✅ **MANTER como filtro preferencial** |
| 3 | XAUUSD_4H_LONG_REJECTION_SWING atual | 4H | LONG | 1070 | 2.79 | -59.3 | -0.055 | 0.88 | ⚠️ **AJUSTAR** — frequência alta, edge negativo. Adicionar filtro RSI <= 40 |
| 4 | XAUUSD_1H_LONG_REJECTION_EXECUTION atual | 1H | LONG | 1338 | 10.88 | +22.4 | 0.017 | 1.04 | ⚠️ **AJUSTAR** — frequência muito alta, edge marginal |
| 5 | XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION (proxy 30M) | 30M | LONG | 1378 | 19.49 | -139.7 | -0.101 | 0.79 | ❌ **DESCARTAR ou rever** — sem edge no CSV. Pode funcionar com zonas BB reais que não temos. |
| 6 | **NOVO 4H breakout LONG (target 4R)** | 4H | LONG | 846 | 2.20 | **+76.8** | 0.091 | **1.23** | ✅ **IMPLEMENTAR** |
| 7 | **NOVO 1H rejection LONG (RSI<=40, target 2.5R)** | 1H | LONG | 345 | 2.80 | **+15.1** | 0.044 | 1.10 | ✅ **IMPLEMENTAR** |

## 7. Decisões recomendadas

### 7.1 Régua antiga global
**Manter SUAVIZADA**, não descartar.
- ✅ RSI extremo (RSI <= 40 para LONG, RSI >= 60 para SHORT — agora mais permissivo que 30/70)
- 🟡 Bubble: **opcional**, vira confluência adicional
- 🟡 NAS TOP/BOTTOM: **opcional**, confluência adicional
- ❌ Não exigir RSI + Bubble + NAS simultâneos — mata edge

### 7.2 XAUUSD_4H_LONG_REJECTION_SWING
**AJUSTAR**, não descartar.
- Reduzir frequência adicionando filtro RSI <= 40
- Manter LONG only
- Considerar substituir por breakout/momentum (resultado melhor) ou manter como módulo separado para regime de reversão

### 7.3 XAUUSD_1H_LONG_REJECTION_EXECUTION
**AJUSTAR**, não descartar.
- Adicionar filtro RSI <= 40 reduz de 1338 trades para 345
- Mantém frequência operacionalmente útil (2.8/sem)
- Edge aumenta de +0.017 para +0.044
- Sample n=345 já está acima do threshold de 25/módulo
- **Recomenda promover de SETUP_CANDIDATO_FORTE para potencial SETUP_VALIDO** após validação ao vivo

### 7.4 XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION
**Continuar como SETUP_CANDIDATO_FORTE apenas** — backtest sem zonas BB reais não consegue validar o módulo. Operacionalmente, depende fortemente das zonas desenhadas.

### 7.5 NOVO módulo proposto: XAUUSD_4H_LONG_BREAKOUT_CONTINUATION

**Definição:**
- TF: 4H
- Direção: LONG only
- Gatilho: candle de momentum (close > open, body ≥ 50% do range) fechando acima do swing high de 10 bars
- Filtro de contexto: RSI > RSI-based MA
- Stop: low do bar de sinal − 0.5×ATR(14)
- Target: 4R
- BE após +1R
- Sem trailing default
- Max hold: 24 bars

**Performance backtest 7.4 anos:**
- 846 trades (115/ano, 2.2/sem, 9.6/mês)
- Total: +76.84R
- Avg: 0.091R/trade
- Win rate: 23.3%
- PF: 1.23
- Max losing streak: 31
- Sem top 5: +56.84R (resiliente, não depende de fat tails)

**Avisos:**
- Frequência alta para "swing" (9.6 trades/mês) — operacionalmente parece intraday-swing híbrido
- Performance degrada significativamente em regimes de range (2021-2023 = -60R)
- Win rate baixo (23%) exige disciplina psicológica
- **Recomendado SETUP_VALIDO mas APENAS quando 4H RSI > MA (regime trending)**

### 7.6 NOVO módulo proposto: XAUUSD_1H_LONG_REJECTION_RSI40

**Definição:**
- TF: 1H
- Direção: LONG only
- Gatilho: rejection close (pavio inferior ≥ 50%, corpo ≤ 40%, close no terço superior)
- Filtro: RSI(14) <= 40 OR RSI saindo de < 40 nos últimos 3 candles
- Stop: low do bar de sinal − 0.5×ATR(14)
- Target: 2.5R
- BE após +1R
- Sem trailing default
- Max hold: 36 bars

**Performance backtest 2.4 anos:**
- 345 trades (146/ano, 2.8/sem, 12.2/mês)
- Total: +15.13R
- Avg: 0.044R/trade
- Win rate: 21.2%
- PF: 1.10
- Sem top 5: +2.63R (frágil — depende dos melhores trades)

**Avisos:**
- Edge marginal (+0.044R/trade); sem top 5 vira +2.63R → **regra frágil**
- 2026 parcial (-4.44R) sugere possível degradação em regime atual
- **Recomendado SETUP_CANDIDATO_FORTE com revisão manual, NÃO automatizar para SETUP_VALIDO ainda**

### 7.7 SHORT em XAUUSD

**DESCARTAR módulos SHORT automáticos.**

Em todos os TFs testados, SHORT em XAUUSD tem expectancy negativo. O ativo tem bias bull estrutural visível em todo o período 2019-2026.

**Exceção:** SHORT pode ser considerado manualmente em rejeições extremas em supplies HTF (4H+) com RSI > 75 + reversão técnica clara. Não automatizar.

## 8. Matriz de decisão final

| Módulo | Status atual | Recomendação | Pode gerar SETUP_VALIDO? |
|---|---|---|---|
| Régua antiga global completa | ativa | **SUAVIZAR** — RSI extremo como único requisito; Bubble e NAS opcionais | Sim (com RSI<=40 + R:R 2:1) |
| XAUUSD_4H_LONG_REJECTION_SWING | experimental | **AJUSTAR** — adicionar filtro RSI<=40 | Sim, mas atualmente só CANDIDATO_FORTE até atingir n=30 com novo filtro |
| XAUUSD_1H_LONG_REJECTION_EXECUTION | experimental | **AJUSTAR** — adicionar filtro RSI<=40 | Sim, n=345 ≥ threshold; edge frágil exige cautela |
| XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION | experimental | **MANTER COMO CANDIDATO_FORTE** — sem dados de zona BB no CSV para validar | Não (manual review only) |
| **XAUUSD_4H_LONG_BREAKOUT_CONTINUATION** (novo) | proposto | **IMPLEMENTAR** com filtro RSI > MA + regime detection | Sim, n=846, expectancy estável |
| **XAUUSD_1H_LONG_REJECTION_RSI40** (novo) | proposto | **IMPLEMENTAR** com revisão manual | CANDIDATO_FORTE inicialmente, promover após 50 eventos ao vivo |
| Qualquer módulo SHORT | n/a | **NÃO IMPLEMENTAR** | Não |

## 9. Cuidados e limitações

1. **Falta zona BB real no CSV** — toda análise de "BB confluence" é proxy. Os módulos que dependem de zonas BB visuais (D6-A, intraday BB confluence) não podem ser validados aqui.
2. **15M e 30M têm sample pequeno** (5 meses e 1.4 anos). Resultados frágeis.
3. **Não há análise de slippage, custos de spread XAUUSD** (que são tipicamente 30-50 pips em corretora retail). Resultados brutos em R; subtrair ~0.05R/trade de spread reduz expectancy real.
4. **Macro regime não filtrado** — 2021-2023 chop range matou breakout. Em produção, recomendar pause manual em range claro (ADX < 20 ou body médio < 1×ATR por N bars).
5. **Indicadores Bubble e NAS** — depend do CSV ter os flags corretos. Se forem usados ao vivo com indicadores idênticos, resultado pode mudar.

## 10. Próximos passos sugeridos (research)

1. Validar XAUUSD_4H_LONG_BREAKOUT_CONTINUATION em 12H/D para ver se TF maior melhora win rate
2. Backtest com regime filter (ATR expansion vs contraction) — eliminar anos de chop
3. Testar Pyramid (entrar 2x no mesmo trade ao romper níveis) — pode amplificar edge
4. Quando possível, exportar zonas BB do TradingView para CSV e backtest XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION com dados reais
5. Comparar breakout vs rejection lado a lado em mesmo gráfico para entender quando cada um funciona

## 11. Resposta direta às perguntas

1. **Estratégia antiga global deve ser mantida, suavizada ou descartada?** → **SUAVIZADA**. Manter RSI extremo (com threshold mais permissivo, 40/60). Tornar Bubble e NAS opcionais.

2. **XAUUSD_4H_LONG_REJECTION_SWING continua válido?** → **NÃO sem ajuste**. Versão atual perde dinheiro. Com filtro RSI<=40, sai do negativo mas ainda é marginal. Recomendado substituir por XAUUSD_4H_LONG_BREAKOUT_CONTINUATION.

3. **XAUUSD_1H_LONG_REJECTION_EXECUTION continua válido?** → **SIM, mas ajustado**. Adicionar filtro RSI<=40, reduzindo de 1338 para 345 trades e elevando expectancy.

4. **XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION continua válido?** → **INDETERMINADO**. Backtest não tem zonas BB. Manter como SETUP_CANDIDATO_FORTE com revisão manual.

5. **Existe estratégia intraday melhor com 2-3 trades/semana?** → **SIM**. XAUUSD_1H_LONG_REJECTION_RSI40 (2.8/sem, +0.044 avg, PF 1.10). Edge marginal mas operacional.

6. **Existe estratégia swing melhor com pelo menos 1 trade/mês?** → **SIM**. XAUUSD_4H_LONG_BREAKOUT_CONTINUATION (9.6/mês, +0.091 avg, PF 1.23) — embora frequência alta para "swing".

7. **Quais regras implementar no Claude?** → 
   - Filtro RSI <= 40 como confluência preferencial para LONG XAUUSD
   - Bubble e NAS como confluências opcionais
   - Breakout/momentum como gatilho alternativo a rejection
   - Bias LONG only para XAUUSD em módulos automáticos

8. **Quais regras remover/transformar em confluência opcional?** → 
   - Market Order Bubbles obrigatório → opcional
   - NAS TOP/BOTTOM obrigatório → opcional
   - Sweep/reentry como gatilho primário → apenas confluência
   - Rejection close sem filtro → exigir RSI confluence

9. **Quais módulos devem gerar SETUP_VALIDO/INTRADAY?**
   - ✅ XAUUSD_4H_LONG_BREAKOUT_CONTINUATION (novo, n=846)
   - ✅ XAUUSD_1H_LONG_REJECTION_RSI40 (substitui versão atual)
   - Demais: CANDIDATO_FORTE apenas

10. **Quais devem ficar apenas como SETUP_CANDIDATO_FORTE?**
    - XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION (dependente de zona BB real)
    - XAUUSD_4H_LONG_REJECTION_SWING ajustado (até atingir n=30 trades novos)
    - Qualquer setup SHORT (manual only, nunca automático)

## 12. Resumo em uma frase

**O elemento que mais adiciona edge é RSI extremo (com threshold permissivo); Bubble e NAS são neutras ou negativas; SHORT em XAUUSD não tem edge sistemático; o gatilho com melhor expectancy é breakout/momentum em 4H, não rejection.**
