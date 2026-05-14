# Research Review Prompt v0.1

Objetivo:
Analisar os logs reais da estratégia para identificar padrões, confluências úteis, falsos positivos e possíveis melhorias.

Arquivos de entrada:
- ~/tradingview-mcp/alert-bridge/logs/setup_research_log.jsonl
- ~/tradingview-mcp/alert-bridge/logs/setup_outcome_log.jsonl
- ~/tradingview-mcp/my-strategy/strategy_rules.json
- ~/tradingview-mcp/my-strategy/operational_prompt.md
- ~/tradingview-mcp/my-strategy/macro_context_daily.md

Diretórios de saída:
- ~/tradingview-mcp/my-strategy/research/daily/
- ~/tradingview-mcp/my-strategy/research/weekly/
- ~/tradingview-mcp/my-strategy/research/proposals/

Regras fundamentais:
- Não alterar strategy_rules.json automaticamente.
- Não alterar operational_prompt.md automaticamente.
- Não executar ordens.
- Não criar alertas.
- Não editar Pine Script.
- Não desenhar no TradingView.
- Apenas analisar dados, resumir padrões e propor melhorias.
- Se houver poucos dados, declarar insuficiência de amostra.
- Separar observação, hipótese e proposta.
- Não tratar correlação fraca como conclusão definitiva.

Tipos de análise desejados:

1. Qualidade dos alertas
- Quantos alertas foram recebidos?
- Quantos foram silenciados?
- Quantos geraram Telegram?
- Quantos eram NO TRADE?
- Quantos eram SETUP EM OBSERVAÇÃO?
- Quantos eram SETUP VÁLIDO ou quase válido?

2. Performance posterior
- O preço reagiu a favor após o alerta?
- O alerta foi ruído?
- O alerta veio cedo demais?
- O alerta veio tarde demais?
- A zona ajudou?
- O setup teria dado R:R aceitável?

3. Confluências
Avaliar, quando houver dados:
- RSI extremo
- RSI saindo de extremo
- BigBeluga 30M
- BigBeluga 1H
- BigBeluga 4H
- TOP/BOTTOM
- Market Order Bubbles
- rejeição por candle
- LTA/LTB
- contexto HTF favorável/neutro/contra
- contexto macro favorável/neutro/contra

4. Por ativo
- XAUUSD
- XAGUSD
- XPTUSD
- US500
- BTCUSD
- ETHUSD
- USOUSD
- EURUSD
- USDJPY

5. Por camada
- Intraday
- Swing
- Ambas

6. Por timeframe de origem
- 30M
- 1H
- 4H
- 1D

Formato de relatório diário:

# Daily Strategy Research Review

Data:
Período analisado:
Total de eventos:
Total de outcomes avaliados:

## 1. Resumo executivo
- principal achado:
- principal risco:
- melhor ativo:
- pior ativo:
- melhor confluência:
- confluência mais fraca:
- nível de confiança da análise: alto / médio / baixo / insuficiente

## 2. Estatísticas gerais
Tabela com:
- eventos totais
- Telegram enviados
- Telegram silenciados
- setups válidos
- quase setups
- observações
- no trades
- invalidações

## 3. Resultados por ativo
Para cada ativo:
- número de eventos
- principais alertas
- resultado médio
- observações relevantes
- dados insuficientes, se aplicável

## 4. Resultados por confluência
Separar:
- confluências que ajudaram
- confluências que falharam
- confluências inconclusivas

## 5. Erros ou ruídos observados
Exemplos:
- alerta disparou muito cedo
- alerta disparou muito tarde
- zona macro boa, mas intraday fraca
- RSI neutro bloqueou corretamente
- setup teria funcionado apesar de ser silenciado
- Telegram foi útil ou ruidoso

## 6. Aprendizados provisórios
Listar hipóteses, não regras definitivas.

## 7. Propostas de ajuste
Se houver dados suficientes, criar propostas claras.
Se não houver dados suficientes, escrever:
“Amostra insuficiente para propor mudança.”

Cada proposta deve conter:
- problema observado
- evidência no journal/outcomes
- ajuste sugerido
- risco do ajuste
- período recomendado de teste
- se deve ou não alterar strategy_rules.json agora

## 8. Próximas ações
- manter estratégia sem alteração
- coletar mais dados
- revisar algum ativo
- ajustar alertas
- criar proposta formal em /proposals/

Formato de proposta formal:

# Strategy Adjustment Proposal

Data:
Título:
Status: proposta / aprovada / rejeitada / em teste

## 1. Problema observado

## 2. Evidência

## 3. Ajuste sugerido

## 4. Risco

## 5. Plano de teste

## 6. Critério de aprovação

## 7. Decisão do usuário

Política:
Uma proposta só pode virar alteração em strategy_rules.json depois de aprovação explícita do usuário.
