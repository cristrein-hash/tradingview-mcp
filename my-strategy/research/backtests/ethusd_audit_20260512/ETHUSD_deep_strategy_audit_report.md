# ETHUSD Deep Strategy Audit — Relatório Executivo

**Data:** 2026-05-12
**Modo:** read-only research / backtest CSV
**Ativo:** PEPPERSTONE:ETHUSD
**Custo padrão usado:** 0.05R/trade (spread retail)

---

## 1. Cobertura de dados

| TF | Bars | Início | Fim | Span |
|---|---:|---|---|---:|
| 1D | 2789 | 2017-10-22 | 2026-05-10 | 8.5 anos |
| 12H | 5629 | 2017-10-23 | 2026-05-11 | 8.5 anos |
| 4H | 11580 | 2020-12-31 | 2026-05-11 | **5.4 anos** ← swing |
| 1H | 11766 | 2024-12-31 | 2026-05-11 | **1.4 anos** ← intraday |
| 30M | 23523 | 2024-12-31 | 2026-05-11 | 1.4 anos |
| 15M | 12512 | 2025-12-31 | 2026-05-11 | 5 meses |

⚠️ **Limitação importante:** dados 4H começam em 2020-12-31, perdemos o bull rally 2017-2020 (~10.000% de ETH). Sample pode ser viesado para período mais difícil/lateral.

## 2. Veredito direto

### 🔴 Módulos atuais NÃO se sustentam no backtest

| Módulo atual | n | Total Net R | Avg R | PF | Veredito |
|---|---:|---:|---:|---:|---|
| **A_ETHUSD_4H_LONG_BREAKOUT_CONTINUATION** (atual) | 613 | **-35.68** | -0.058 | 0.89 | ❌ **NEGATIVO em 5.4 anos** |
| A_runner_8R variant | 613 | -8.78 | -0.014 | 0.97 | ❌ negativo |
| A_no_RSI52 filter variant | 640 | -36.10 | -0.056 | 0.89 | ❌ negativo |
| **B_ETHUSD_30M_CONFIRMED_MOMENTUM_LONG** (atual) | 1078 | **-170.20** | -0.158 | 0.67 | ❌❌ **DESASTRE** |
| B_ETHUSD_30M_CONFIRMED_MOMENTUM_SHORT | 983 | -94.99 | -0.097 | 0.78 | ❌ negativo |
| B combined LONG+SHORT | 2061 | **-265.20** | -0.129 | 0.72 | ❌❌❌ |
| B sem confirmação | 1078 | -170.20 | -0.158 | 0.67 | ❌ idêntico (filtro irrelevante) |

### ⚠️ Régua antiga global também não funciona para ETH

| Variante | n | Total Net R | Avg R | PF |
|---|---:|---:|---:|---:|
| RSI extremo + Bubble + Rejection LONG | 65 | -16.89 | -0.260 | 0.52 |
| Idem SHORT | 79 | -26.95 | -0.341 | 0.42 |
| RSI extremo apenas LONG | 118 | -25.61 | -0.217 | 0.59 |

### ✅ Estratégias com edge encontradas

| Novo modelo | n | /sem | /mês | Total Net R | Avg R | PF | Win% | r-top10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **D_4H_BREAKOUT_REGIME_FILTERED target=5R** | 158 | 0.58 | 2.54 | **+12.82** | 0.081 | 1.16 | 25.3% | -33.4 ⚠️ |
| D_4H_BREAKOUT_REGIME target=6R | 158 | 0.58 | 2.54 | +8.97 | 0.057 | 1.11 | 20.9% | -41.5 |
| D_4H_BREAKOUT_REGIME target=4R | 158 | 0.58 | 2.54 | +6.00 | 0.038 | 1.08 | 27.8% | -32.3 |
| D_4H_BREAKOUT_REGIME target=3R | 158 | 0.58 | 2.54 | +2.76 | 0.018 | 1.04 | 28.5% | -26.7 |
| **F_1H_BREAKOUT_REGIME_FILTERED_LONG** | 116 | **1.70** | **7.39** | **+18.39** | **0.159** | **1.42** | 32.8% | **-15.7** |
| E_30M_BREAKOUT_REGIME_FILTERED | 240 | 3.44 | 14.94 | -31.52 | -0.131 | 0.70 | 26.2% | -61.0 ❌ |
| G_30M_SHORT_BREAKDOWN_REGIME | 219 | 3.16 | 13.75 | -45.51 | -0.208 | 0.57 | 18.7% | -75.0 ❌ |

## 3. Análise temporal — D_4H_BREAKOUT_REGIME_FILTERED target=5R (melhor swing)

| Ano | Trades | Net R | Avg | Win% |
|---|---:|---:|---:|---:|
| 2021 | 40 | **-16.23** | -0.406 | 12.5% |
| 2022 | 15 | +2.24 | 0.150 | 40.0% |
| 2023 | 28 | +2.28 | 0.082 | 25.0% |
| 2024 | 34 | +2.07 | 0.061 | 26.5% |
| 2025 | 38 | **+25.61** | 0.674 | 34.2% |
| 2026 (parcial) | 3 | -3.15 | -1.050 | 0.0% |

**Crítica:** Edge depende fortemente de 2025 (+25.6R) e 2021 foi catastrófico (-16R). Sem top 10 winners → -33.4R **negativo**. Esta estratégia **depende de fat tails** — não é robusta como o equivalente XAUUSD (que dava +25R sem top 10).

## 4. Filter Impact — 4H LONG breakout baseline (5.4 anos)

| Filtro | n | Total Net R | Avg R | PF | Efeito |
|---|---:|---:|---:|---:|---|
| Baseline (RSI > MA) | 640 | -36.10 | -0.056 | 0.89 | ❌ baseline perde |
| + RSI >= 52 | 613 | -35.68 | -0.058 | 0.89 | ❌ neutro |
| + Close > EMA200 | 448 | +9.24 | 0.021 | 1.04 | ✅ ajuda |
| **+ EMA50 > EMA200** | 337 | **+17.26** | 0.051 | **1.10** | ✅ **filtro mais forte isolado** |
| + ATR expanding | 359 | +13.01 | 0.036 | 1.07 | ✅ ajuda |
| + ADX >= 20 | 436 | -0.83 | -0.002 | 1.00 | 🟡 neutro |
| + ADX >= 25 | 316 | +10.78 | 0.034 | 1.07 | ✅ ajuda |
| + EMA50 slope positivo | 465 | -17.34 | -0.037 | 0.93 | ❌ **piora isoladamente** |
| **+ Full regime filter (todos)** | 158 | **+12.82** | 0.081 | **1.16** | ✅ |

**Insight crítico:** filtros funcionam mas o edge é **marginal**. Diferente de XAUUSD onde o regime filter triplicou o avg_R (de 0.041 → 0.276), em ETHUSD o regime filter vira a estratégia de negativo para positivo, mas o avg_R fica em apenas +0.081R.

## 5. Cost sensitivity — D_4H_BREAKOUT_REGIME target=5R

| Spread | Total Net R | Avg Net R | PF Net | Positivo? |
|---:|---:|---:|---:|---|
| 0.00R (gross) | +20.72 | 0.131 | 1.27 | ✅ |
| 0.02R | +17.56 | 0.111 | 1.22 | ✅ |
| 0.03R | +15.98 | 0.101 | 1.20 | ✅ |
| **0.05R (retail)** | **+12.82** | **0.081** | **1.16** | ✅ |
| 0.07R | +9.66 | 0.061 | 1.11 | ✅ |
| 0.10R | +4.92 | 0.031 | 1.06 | ⚠️ marginal |

**Break-even spread:** 0.131R/trade (margem confortável vs 0.05R retail)

## 6. Análise por elemento individual em ETHUSD

| Elemento | Edge em ETHUSD | Recomendação |
|---|---|---|
| RSI extremo | **Não funciona** — Avg R -0.22 com filtro RSI extremo isolado | Não usar como filtro principal |
| RSI > MA | Neutro (parte do gatilho mas não filtra losses) | Manter como confluência |
| RSI >= 52 (filtro do módulo atual) | **Praticamente nulo** (vira -35R com ou sem) | Remover ou tornar opcional |
| NAS TOP/BOTTOM | Não testado isoladamente; em B com confirmação irrelevante | Tratar como confluência opcional |
| Market Order Bubbles | Em B com 1+ confirmação não melhora | Confluência opcional |
| Divergência regular | Não testada isoladamente em ETH | Confluência opcional |
| Rejection close | **Negativo** em ETH (régua antiga) | Não usar como gatilho principal |
| Breakout/momentum continuation | **Marginal positivo com regime filter** | Gatilho principal recomendado |
| Close > EMA200 | **Positivo (+9.24R isolado)** | ✅ filtro obrigatório |
| EMA50 > EMA200 | **Positivo (+17.26R isolado)** | ✅ filtro obrigatório |
| EMA50 slope positivo | **Negativo isoladamente** (-17R) | 🟡 testar mais — mantém no combo |
| ATR expanding | **Positivo (+13R isolado)** | ✅ filtro obrigatório |
| ADX >= 20 | Marginal | 🟡 manter como gate fraco |
| ADX >= 25 | Positivo (+10.78R) | Alternativa para ADX >= 20 |
| Full regime filter | **+12.82R em 5.4y, robusto temporalmente** | ✅ recomendado |
| 5R target | Melhor que 3R/4R/6R em D | ✅ manter target 5R |
| 4R target | Pior que 5R | 🟡 |
| 8R runner | Pior que 5R | ❌ não usar |
| 30M momentum | **Negativo em ambas direções** | ❌ descartar |
| 1H breakout | **Positivo (PF 1.42)** mas sample 1.4y | ✅ candidato — validar mais |
| SHORT em ETH | **Sem edge sistemático** em qualquer TF | ❌ não automatizar |

## 7. Comparação final consolidada

| # | Estratégia | TF | Direção | Trades | /sem | /mês | Total Net R | Avg Net | PF | r-top10 | Recomendação |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Régua antiga RSI+Bubble LONG | 4H | LONG | 65 | 0.27 | 1.17 | -16.89 | -0.260 | 0.52 | -33.3 | ❌ **DESCARTAR** |
| 2 | Régua antiga RSI ext softened | 4H | LONG | 118 | 0.44 | 1.93 | -25.61 | -0.217 | 0.59 | -45.1 | ❌ **DESCARTAR** |
| 3 | **ETHUSD_4H_LONG_BREAKOUT_CONTINUATION atual** | 4H | LONG | 613 | 2.23 | 9.72 | **-35.68** | -0.058 | 0.89 | -85.2 | ❌ **AJUSTAR ou desativar** |
| 4 | **ETHUSD_30M_CONFIRMED_MOMENTUM atual LONG** | 30M | LONG | 1078 | 15.31 | 66.6 | **-170.20** | -0.158 | 0.67 | -209.7 | ❌❌ **DESCARTAR** |
| 5 | ETHUSD_30M_CONFIRMED_MOMENTUM atual SHORT | 30M | SHORT | 983 | 13.99 | 60.8 | -94.99 | -0.097 | 0.78 | -134.5 | ❌ **DESCARTAR** |
| 6 | **NOVO D_4H_BREAKOUT_REGIME_FILTERED 5R** | 4H | LONG | 158 | 0.58 | 2.54 | **+12.82** | 0.081 | 1.16 | -33.4 | ⚠️ **CANDIDATO_FORTE** (edge frágil) |
| 7 | **NOVO F_1H_BREAKOUT_REGIME_FILTERED** | 1H | LONG | 116 | 1.70 | 7.39 | **+18.39** | **0.159** | **1.42** | **-15.7** | ⚠️ **CANDIDATO_FORTE** (sample 1.4y só) |
| 8 | E_30M_BREAKOUT_REGIME LONG | 30M | LONG | 240 | 3.44 | 14.94 | -31.52 | -0.131 | 0.70 | -61.0 | ❌ **DESCARTAR** |
| 9 | G_30M_SHORT_BREAKDOWN_REGIME | 30M | SHORT | 219 | 3.16 | 13.75 | -45.51 | -0.208 | 0.57 | -75.0 | ❌ **DESCARTAR** |

## 8. Decisões diretas

### 8.1 ETHUSD_4H_LONG_BREAKOUT_CONTINUATION (atual)

**❌ Versão atual perde -35.68R em 5.4 anos. Não confirma edge.**

**Recomendação:** AJUSTAR para `D_4H_BREAKOUT_REGIME_FILTERED target=5R` adicionando os filtros de regime:
- Close > EMA(200)
- EMA(50) > EMA(200)
- EMA(50) slope positivo
- ATR(14) > ATR_MA(20)
- ADX(14) >= 20

Após ajuste: +12.82R em 5.4y, avg 0.081R, PF 1.16.

**Mas: edge frágil** (-33R sem top 10). **Não emitir SETUP_VALIDO automático. Manter como SETUP_CANDIDATO_FORTE com revisão manual.**

### 8.2 ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION (atual)

**❌❌ DESCARTAR ou DESATIVAR.**

- LONG: -170R em 1.4 anos
- SHORT: -95R em 1.4 anos
- Combined: -265R
- Filtro de confirmação não muda nada (mesmo resultado com e sem)
- Backtest original que mostrou +144R/542 trades não é reproduzível com as regras atuais

**Recomendação:** DESATIVAR módulo até reavaliar com sample melhor ou redesenho completo.

### 8.3 SHORT em ETH

**❌ Sem edge sistemático em nenhum TF testado.** Mesma situação do XAUUSD: ativo com bias bull estrutural pós-2020. SHORTS não vencem.

**Recomendação:** NÃO automatizar SHORT em ETHUSD.

### 8.4 Novo módulo proposto: ETHUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED

**Substitui:** ETHUSD_4H_LONG_BREAKOUT_CONTINUATION

**Definição:**
- Asset: PEPPERSTONE:ETHUSD
- TF: 4H
- Direção: LONG only
- Gatilho:
  - `close > swing_high(10)`
  - `close > open`
  - `body_pct >= 0.5`
  - `RSI > RSI-based MA`
- Filtros regime (TODOS obrigatórios):
  - `Close > EMA(200)`
  - `EMA(50) > EMA(200)`
  - `EMA(50) slope (5 bars) > 0`
  - `ATR(14) > ATR_MA(20)`
  - `ADX(14) >= 20`
- Stop: low − 0.5 × ATR(14)
- Target: 5R
- BE após +1R; sem trailing default
- Max hold: 30 bars

**Métricas backtest (5.4y, 0.05R spread):**
- 158 trades / 2.54 mês / 0.58 sem
- Total Net R: +12.82
- Avg Net R: +0.081
- PF Net: 1.16
- Win rate: 25.3%
- Max losing streak: 18
- ⚠️ Sem top 10: -33.41R (depende de fat tails)

**Classificação recomendada:** `SETUP_CANDIDATO_FORTE` (NÃO emitir SETUP_VALIDO automático devido à fragilidade).

### 8.5 Novo módulo experimental: ETHUSD_1H_LONG_BREAKOUT_REGIME_FILTERED

**Definição:**
- Asset: PEPPERSTONE:ETHUSD
- TF: 1H
- Direção: LONG only
- Mesmos gatilho e filtros do 4H acima
- Target: 4R
- BE após +1R
- Max hold: 24 bars

**Métricas backtest (1.4y, 0.05R spread):**
- 116 trades / 7.39 mês / 1.70 sem
- Total Net R: +18.39
- Avg Net R: +0.159
- PF Net: 1.42
- Win rate: 32.8%
- Max losing streak: 13
- ⚠️ Sem top 10: -15.65R (frágil mas menos)

**Classificação recomendada:** `SETUP_CANDIDATO_FORTE` em forward-test. Sample n=116 está acima do mínimo 25, mas 1.4 ano de histórico é curto. Promover para `SETUP_VALIDO_INTRADAY` somente após 30+ eventos ao vivo positivos.

## 9. Resposta direta às perguntas

1. **ETHUSD_4H_LONG_BREAKOUT_CONTINUATION deve ser mantido?** → **AJUSTAR (urgente).** Versão atual perde dinheiro. Substituir por regime-filtered.

2. **ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION deve ser mantido?** → **DESATIVAR.** Perde -265R combinado. Sem edge reproduzível.

3. **Existe estratégia swing ETHUSD melhor?** → SIM: D_4H_BREAKOUT_REGIME_FILTERED target=5R (+12.82R em 5.4y), mas edge frágil.

4. **Existe estratégia intraday ETHUSD melhor?** → SIM: F_1H_BREAKOUT_REGIME_FILTERED (+18.39R em 1.4y), mas sample curto.

5. **LONG e SHORT devem continuar no mesmo módulo?** → **NÃO**. SHORT não tem edge. Separar e desativar SHORT.

6. **Quais regras implementar?**
   - Mover ETH para framework "regime-filtered breakout" igual XAUUSD
   - Substituir RSI >= 52 por filtros EMA + ATR + ADX
   - Manter target 5R no 4H, 4R no 1H

7. **Quais regras remover?**
   - RSI >= 52 (não filtra losses comprovadamente)
   - Runner 8R (piora resultado)
   - Filtro de "1+ confirmação NAS/Bubble/div" (irrelevante)
   - Toda lógica SHORT no 30M

8. **Quais módulos podem gerar SETUP_VALIDO/INTRADAY?**
   - **NENHUM em ETH ainda** — todos os candidatos têm edge marginal ou sample insuficiente.

9. **Quais devem ficar só como SETUP_CANDIDATO_FORTE?**
   - ETHUSD_4H_LONG_BREAKOUT_CONTINUATION_REGIME_FILTERED (ajustado)
   - ETHUSD_1H_LONG_BREAKOUT_REGIME_FILTERED (novo)
   - Ambos exigem revisão manual

10. **O que medir em D2R nos próximos 30-50 eventos?**
    - Distribuição de losses por filtro (qual filtro evita os piores trades)
    - Trades onde EMA50_slope estava positivo vs negativo (contraintuitivo isoladamente)
    - Sazonalidade (2021 foi outlier; 2025 puxou todo o edge)
    - MFE/MAE — se a maioria dos trades atinge +1R antes do stop, BE+1R está OK
    - Recheck de top-N robustness após adicionar 30-50 trades reais

## 10. Avisos e limitações

⚠️ **CRÍTICO — não tratar este audit como evidência conclusiva de edge:**

1. **Dados 4H começam em 2021** — perdemos o bull run histórico 2017-2020 de ETH (gerador potencial de muitos winners). Backtest pode estar viesado para período mais lateral.

2. **30M/1H/15M só têm 1.4 ano** — qualquer conclusão de intraday é provisória.

3. **Top-10 dependency** em quase todos os modelos positivos sugere que o edge depende de poucos grandes trades. Em produção, perder esses por azar deteriora rapidamente.

4. **ETHUSD tem volatilidade diferente de XAUUSD** — spreads e slippage podem ser mais altos (especialmente em momentos de alta vol cripto). 0.05R pode subestimar custo real.

5. **2021 foi catastrófico** mesmo com regime filter (-16R). Indica que ETH em "false breakouts dentro de range trending" é difícil de filtrar.

6. **Não há substituto óbvio** para o módulo 30M atual. Forward-test com sample maior é necessário.

## 11. Resumo executivo em uma frase

**Os dois módulos ETHUSD atuais (4H_BREAKOUT_CONTINUATION e 30M_CONFIRMED_MOMENTUM) perdem dinheiro no backtest e devem ser substituídos/desativados; o melhor candidato substituto é a versão regime-filtered (filtros EMA200, EMA50>EMA200, ATR expanding, EMA50 slope+, ADX≥20) com target 5R no 4H ou 4R no 1H — mas o edge é marginal e dependente de fat tails, justificando classificação apenas como SETUP_CANDIDATO_FORTE com revisão manual, NUNCA SETUP_VALIDO automático.**
