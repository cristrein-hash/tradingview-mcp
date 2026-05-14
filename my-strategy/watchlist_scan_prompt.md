# Prompt de Varredura Top-Down da Watchlist v0.1

Leia obrigatoriamente estes arquivos antes de qualquer análise:

/Users/cristrein/tradingview-mcp/my-strategy/operational_prompt.md
/Users/cristrein/tradingview-mcp/my-strategy/strategy_rules.json

Depois use o TradingView MCP para fazer uma varredura top-down da watchlist.

Objetivo:
Identificar quais ativos estão próximos de zonas relevantes, quais merecem monitoramento, quais podem receber alertas automáticos e quais devem ser ignorados por enquanto.

Watchlist:
USOUSD, BRENT, XAUUSD, XAGUSD, XPTUSD, ETHUSD, BTCUSD, US500, EURUSD, USDJPY, GBPUSD

Ordem de análise:
1. Primeiro analisar D, 12H e 4H.
2. Só analisar 1H, 30M ou 15M se o ativo estiver próximo de zona relevante ou em SETUP EM OBSERVAÇÃO ou superior.
3. Não gastar tempo refinando ativos sem zona relevante.

Classificações permitidas:
- NO TRADE
- MONITORAR
- PRÓXIMO DE ZONA
- SETUP EM OBSERVAÇÃO
- SETUP VÁLIDO
- SETUP FORTE
- SETUP EXCELENTE

Regras:
- Não gerar sinal operacional fora da whitelist.
- Não desenhar no gráfico sem confirmação.
- Não editar Pine Script.
- Não modificar indicadores.
- Não executar ordens.
- Pode criar alertas automaticamente se:
  - ativo está na whitelist;
  - existe zona relevante;
  - ativo está em PRÓXIMO DE ZONA, SETUP EM OBSERVAÇÃO ou superior;
  - alerta é apenas de monitoramento;
  - não há alerta duplicado equivalente.

Pode criar alertas para:
- preço entrando em zona relevante;
- RSI entrando em sobrecompra/sobrevenda;
- RSI saindo do extremo com reação;
- preço rompendo ou rejeitando nível;
- preço tocando invalidação;
- preço tocando alvo relevante;
- candle fechando acima/abaixo de nível crítico.

Não pode:
- criar alerta que execute ordem;
- deletar alerta sem confirmação;
- modificar alerta existente sem confirmação;
- criar alertas duplicados;
- criar mais de 3 alertas por ativo/timeframe.

Formato da resposta:

1. Health check
   - success
   - cdp_connected
   - api_available

2. Resumo geral da watchlist
   Tabela com:
   - ativo
   - timeframe principal analisado
   - contexto
   - zona relevante
   - RSI
   - TOP/BOTTOM
   - Bubbles/reação
   - classificação
   - prioridade
   - alerta criado? Sim/Não

3. Ativos de alta prioridade
   Liste apenas os ativos que merecem monitoramento nas próximas horas.

4. Alertas criados automaticamente
   Para cada alerta criado, informar:
   - nome
   - ativo
   - timeframe
   - condição
   - motivo
   - próxima ação esperada

5. Ativos ignorados por enquanto
   Explique brevemente por que não merecem atenção agora.

6. Próxima ação recomendada
   Escolha uma:
   - aguardar alertas
   - refinar ativo específico
   - pedir confirmação para desenhar setup
   - nenhuma ação

## Payload obrigatório para alertas criados por Claude

Todo alerta criado automaticamente deve usar uma mensagem JSON contendo pelo menos:

```json
{
  "symbol": "{{exchange}}:{{ticker}}",
  "timeframe": "{{interval}}",
  "alert_type": "monitor_zone",
  "event": "tradingview_alert",
  "message": "[TRADINGVIEW][AUTO_CLAUDE] Descrição do alerta",
  "price": "{{close}}",
  "time": "{{time}}",
  "time_now": "{{timenow}}",
  "created_by": "AUTO_CLAUDE"
}

```

O campo `alert_type` deve ser escolhido conforme o objetivo do alerta:

- test_connectivity
- monitor_zone
- monitor_rsi_extreme
- monitor_rsi_exit
- monitor_rejection
- monitor_breakout
- monitor_invalidation
- monitor_target
- setup_recheck
