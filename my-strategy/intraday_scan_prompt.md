# Prompt de Varredura Intraday v0.1

Leia obrigatoriamente antes da análise:

/Users/cristrein/tradingview-mcp/my-strategy/operational_prompt.md
/Users/cristrein/tradingview-mcp/my-strategy/strategy_rules.json

Objetivo:
Fazer uma varredura intraday independente usando 1H, 30M e 15M, procurando setups locais válidos da estratégia.

Ativos prioritários intraday:
- XAUUSD
- XAGUSD
- US500
- BTCUSD
- ETHUSD
- EURUSD

Timeframes:
- 1H
- 30M
- 15M

Regra central:
Um setup intraday pode ser válido mesmo sem estar em zona BigBeluga 4H/12H/D, desde que exista uma zona local relevante no timeframe de execução ou no timeframe imediatamente superior.

Para 15M:
- zona válida pode estar em 15M, 30M ou 1H.

Para 30M:
- zona válida pode estar em 30M ou 1H.

Para 1H:
- zona válida pode estar em 1H ou 4H.

O contexto HTF deve ser tratado como filtro de qualidade, não como bloqueio absoluto.

Classificações permitidas:
- INTRADAY_NO_TRADE
- INTRADAY_EM_OBSERVACAO
- INTRADAY_SETUP_VALIDO
- INTRADAY_SETUP_FORTE
- INTRADAY_SETUP_EXCELENTE

Condições obrigatórias para compra intraday:
1. Ativo na whitelist e preferencialmente na lista de prioridade intraday.
2. Timeframe 15M, 30M ou 1H.
3. Zona local relevante no timeframe atual ou imediatamente superior.
4. BOTTOM, LONG ou sinal bullish válido dentro/próximo da zona local.
5. RSI em sobrevenda ou recém saindo da sobrevenda com reação clara.
6. Reação clara ou cluster de Market Order Bubbles local.
7. Stop abaixo da invalidação local.
8. R:R mínimo de 2:1.

Condições obrigatórias para venda intraday:
1. Ativo na whitelist e preferencialmente na lista de prioridade intraday.
2. Timeframe 15M, 30M ou 1H.
3. Zona local relevante no timeframe atual ou imediatamente superior.
4. TOP, SHORT ou sinal bearish válido dentro/próximo da zona local.
5. RSI em sobrecompra ou recém saindo da sobrecompra com reação clara.
6. Reação clara ou cluster de Market Order Bubbles local.
7. Stop acima da invalidação local.
8. R:R mínimo de 2:1.

Regras:
- Não executar ordens.
- Não editar Pine Script.
- Não alterar strategy_rules.json.
- Não criar alerta TradingView via MCP enquanto alert_create estiver falhando.
- Nesta primeira rodada, não desenhar.
- Apenas ler, classificar e ranquear.
- Se encontrar setup válido ou superior, destacar claramente.

Formato de resposta:

1. Health check:
   - success
   - cdp_connected
   - api_available

2. Tabela geral intraday:
   - ativo
   - melhor timeframe intraday
   - contexto local
   - zona local relevante
   - RSI
   - TOP/BOTTOM
   - Bubbles/reação
   - contexto HTF ajuda/neutro/atrapalha
   - classificação intraday
   - prioridade
   - probabilidade qualitativa

3. Setups intraday válidos ou fortes:
   - ativo
   - direção
   - timeframe
   - entrada aproximada
   - stop
   - alvo
   - R:R aproximado
   - bloqueio ou risco principal

4. Ativos em observação:
   - o que falta para virar setup válido

5. Ativos sem interesse intraday agora

6. Próxima ação recomendada
