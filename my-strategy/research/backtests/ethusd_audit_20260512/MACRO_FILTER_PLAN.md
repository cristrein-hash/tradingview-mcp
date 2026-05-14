# Plano de filtro macro para ETHUSD

**Objetivo:** reduzir a fragilidade fat-tail da estratégia ETHUSD adicionando contexto fora do gráfico que detecte regime favorável vs hostil.

## Por que isso é necessário

O audit de fat-tail mostrou que **a diferença entre big winners e losers em ETH é o REGIME MACRO**, não features técnicas do candle de sinal:
- Todos os 10 piores losers foram em 2021 (chop pós-rally)
- 7 dos 10 melhores winners foram em 2024-2025 (bull regime)
- Features técnicas (RSI, ADX, body, range) são quase **idênticas** entre os dois grupos

A única forma de discriminar ex-ante é **olhar para fora do candle ETH** — para variáveis macro que sinalizam o regime.

## Variáveis macro propostas (em ordem de importância)

### 1. 🥇 BTC dominance (CRYPTOCAP:BTC.D) — **mais importante**
- **Símbolo TradingView:** `CRYPTOCAP:BTC.D`
- **Status atual ao vivo:** 60.82% (verificado via MCP)
- **Lógica:** BTC.D em queda = capital saindo de BTC para alts = ETH outperforming
- **Filtro proposto:** operar ETH só quando `BTC.D < EMA50(BTC.D)` no 4H

### 2. 🥈 ETHBTC ratio (BINANCE:ETHBTC) — direta
- **Símbolo TradingView:** `BINANCE:ETHBTC`
- **Status atual ao vivo:** 0.02832, -5.22% últimas 100 barras 4H (ETH **fraca vs BTC**)
- **Lógica:** ETHBTC subindo = ETH ganhando força relativa ao bellwether
- **Filtro proposto:** operar ETH só quando `ETHBTC > EMA50(ETHBTC)` no 4H

### 3. 🥉 BTCUSD regime (PEPPERSTONE:BTCUSD) — bellwether
- **Símbolo TradingView:** `PEPPERSTONE:BTCUSD`
- **Lógica:** ETH segue BTC. Se BTC está em bear regime, ETH bull setups falham.
- **Filtro proposto:** operar ETH só quando BTCUSD em regime bull (close > EMA200 + EMA50 > EMA200) no 4H

### 4. (Opcional) DXY (TVC:DXY)
- **Lógica:** Dólar forte = risk-off = ruim para cripto
- **Filtro proposto:** operar quando DXY < EMA50

### 5. (Avançado, não imediato) Outros sinais não-OHLCV
- USDT.D / USDC.D (CRYPTOCAP) — flight-to-safety; sobe em risk-off
- TOTAL2 (cap altcoins ex-BTC) trending up — altseason
- M2 global (estes dependeriam de Fed APIs externas — não viável agora)

## Plano de execução em 2 fases

### FASE 1 — Backtest validation (BLOCKED — aguarda exports do usuário)

**Você precisa exportar do TradingView 3 CSVs (4H, mesma janela ou maior que ETHUSD):**

1. Abrir `CRYPTOCAP:BTC.D` no TF 4H em janela ampla (>= 5 anos)
2. Export CSV → salvar em `~/Downloads/` como **CRYPTOCAP_BTC.D, 240.csv** (TradingView geralmente gera com o nome correto)
3. Repetir para `BINANCE:ETHBTC` → **BINANCE_ETHBTC, 240.csv**
4. Repetir para `PEPPERSTONE:BTCUSD` → **PEPPERSTONE_BTCUSD, 240.csv**
5. (opcional) `TVC:DXY` → **TVC_DXY, 240.csv**

**Como exportar:** no TradingView desktop, com gráfico aberto, vá em ☰ Menu → "Exportar dados do gráfico" → CSV → todos os dados visíveis. Salvar no diretório `~/Downloads/`.

**Após upload, rode:**
```bash
cd /Users/cristrein/tradingview-mcp/my-strategy/research/backtests/ethusd_audit_20260512
python3 macro_filter_framework.py
```

O script:
- Detecta automaticamente os CSVs
- Computa features macro (EMAs, slopes, alignment)
- Faz join temporal com ETHUSD 4H
- Testa ~10 combinações de filtros macro
- Reporta total_net_r, avg_r, PF, win_rate, year-by-year
- Output: `ETHUSD_macro_filter_test.csv`

**Critério de aprovação:**
- Pelo menos 1 combo macro deve melhorar a baseline v1.1 (body>=60%) em PF e/ou robustez sem top 10
- Se nenhum melhorar, decidir entre manter v1.1 puro ou esperar mais dados

### FASE 2 — Integração ao vivo (após FASE 1 aprovar filtros)

**Arquitetura proposta:**

```
Alerta TradingView ETH chega
        ↓
Receiver (tv_webhook_receiver.py)
        ↓
chama claude_recheck.py
        ↓
Claude headless via MCP:
  1. lê gráfico ETHUSD principal
  2. CHAMA chart_set_symbol(CRYPTOCAP:BTC.D) → reads
  3. CHAMA chart_set_symbol(BINANCE:ETHBTC) → reads
  4. CHAMA chart_set_symbol(PEPPERSTONE:BTCUSD) → reads
  5. CHAMA chart_set_symbol(PEPPERSTONE:ETHUSD) → restaura
        ↓
Computa estado macro:
  - BTC.D < EMA50 4H?
  - ETHBTC > EMA50 4H?
  - BTC bull regime 4H?
        ↓
Aplica como filtro adicional ao módulo ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED v1.1
        ↓
Se filtros macro OK → SETUP_CANDIDATO_FORTE
Se filtros macro NÃO OK → SETUP_EM_OBSERVACAO ou NO_TRADE
```

**Modificações de código necessárias (após FASE 1 validar):**

1. `claude_recheck.py`:
   - Adicionar bloco de instrução para Claude consultar BTC.D / ETHBTC / BTCUSD via MCP **antes** de classificar setups ETHUSD
   - Adicionar campo de output `macro_context` com 3 booleanos: `btcd_bearish`, `ethbtc_bullish`, `btc_bull_regime`

2. `strategy_rules.json` → `ETHUSD_4H_LONG_BREAKOUT_REGIME_FILTERED.regime_filters_all_required`:
   - Adicionar 3 filtros macro (após FASE 1 dizer quais)

3. `tv_webhook_receiver.py` parser:
   - Adicionar extração do campo `macro_context` para persistir no log

4. Documento do módulo `.md`:
   - Atualizar para v2.0 com macro filters

**Custos operacionais da integração live:**

- Cada análise ETHUSD demora ~3-5s a mais (3-4 chart_set_symbol round-trips)
- Maior risco de timeout no receiver
- Necessidade de robustez: se algum símbolo não acessível, fallback para "macro unknown"

**Alternativa mais leve:** computar macro state em **batch a cada 4H** (em vez de a cada alerta) e cachear em arquivo JSON. Receiver lê o cache. Reduz overhead, mas perde precisão para alertas em meio de candle.

## Decisão imediata

**O que faço agora:**
- Framework `macro_filter_framework.py` pronto e testado (roda mas reporta "nenhum CSV encontrado")
- Aguardo seus 3 (ou 4) exports CSVs em `~/Downloads/`
- Quando uploadar, rodo o backtest e te mando resultado

**O que VOCÊ faz agora:**
1. Abrir TradingView desktop
2. Para cada um dos símbolos:
   - `CRYPTOCAP:BTC.D` (4H)
   - `BINANCE:ETHBTC` (4H)
   - `PEPPERSTONE:BTCUSD` (4H)
   - (opcional) `TVC:DXY` (4H)
3. Fazer "Exportar dados do gráfico" → CSV → janela ampla (idealmente desde 2019)
4. Confirmar nomes no padrão `EXCHANGE_SYMBOL, 240*.csv` em `~/Downloads/`
5. Me avisar — rodo o backtest na hora

## Estimativa de impacto (qualitativo)

Com base no padrão do XAUUSD (que ganhou +574% no avg_R com regime filter):

**Expectativa otimista:** Macro filter + Body>=60% (v1.1) eleva ETH para:
- Avg R: +0.32 → +0.45-0.55
- PF: 1.65 → 1.8-2.0
- Sem top 10 sai do negativo
- Justifica promoção a `SETUP_VALIDO` automático

**Expectativa pessimista:** Macro filter reduz frequência demais (de 1.6/mês para 0.5/mês) sem ganho proporcional de qualidade. Edge não compensa. Mantém SETUP_CANDIDATO_FORTE.

**O backtest com seus CSVs vai dizer qual cenário ocorre.** Sem chute.

## Próximos passos

1. ✅ Framework construído
2. ⏳ Aguardando seus exports CSV
3. ⏭ Rodar backtest macro filter
4. ⏭ Decidir filtros baseado em evidência
5. ⏭ Implementar integração live (se aprovar)
