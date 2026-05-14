# Prompt de Macro Scan Diário v0.1

Leia antes de iniciar:

/Users/cristrein/tradingview-mcp/my-strategy/operational_prompt.md
/Users/cristrein/tradingview-mcp/my-strategy/strategy_rules.json

Objetivo:
Gerar um contexto macro diário otimizado para apoiar a estratégia de trading, sem excesso de detalhes e sem consumir tokens desnecessários nos monitores recorrentes.

Frequência recomendada:
- 1 vez antes da sessão Londres.
- Opcionalmente 1 atualização antes ou no início da sessão NY.

Escopo:
Analisar apenas eventos e notícias que possam influenciar diretamente ou indiretamente os ativos da watchlist.

Watchlist:
- USOUSD
- BRENT
- XAUUSD
- XAGUSD
- XPTUSD
- ETHUSD
- BTCUSD
- US500
- EURUSD
- USDJPY
- GBPUSD

Moedas / temas prioritários:
- USD
- EUR
- GBP
- JPY
- risco global / risk-on / risk-off
- juros dos EUA
- inflação
- emprego
- petróleo / energia
- metais preciosos
- crypto / apetite por risco
- tensões geopolíticas relevantes

Eventos macro prioritários:
- CPI
- PPI
- PCE
- NFP / Payroll
- unemployment / desemprego
- PMI
- PIB
- decisões de juros
- FOMC / Fed speakers
- ECB / BoE / BoJ
- estoques de petróleo
- OPEC / OPEP
- conflitos geopolíticos relevantes
- notícias regulatórias relevantes para crypto

Regras:
- Foque no dia atual e nas próximas 24–48h.
- Não faça análise longa.
- Não tente prever o mercado com certeza.
- Não gere sinais de trade.
- Não altere strategy_rules.json.
- Não execute ordens.
- Produza um resumo útil para os monitores swing e intraday.
- Destaque horários críticos em horário local do usuário, se possível.
- Quando houver incerteza sobre horário/fuso, declarar.

Formato de saída obrigatório:

# Macro Context Daily

Data:
Gerado em:

## 1. Resumo executivo
- Viés macro geral:
- Risk sentiment:
- Dólar:
- Juros:
- Commodities:
- Crypto:
- Observação principal do dia:

## 2. Eventos econômicos importantes
Tabela:
- horário
- moeda/país
- evento
- impacto esperado
- ativos afetados
- comentário operacional

## 3. Notícias macro/geopolíticas relevantes
Tabela:
- tema
- resumo
- ativos afetados
- possível impacto
- nível de atenção

## 4. Impacto por ativo da watchlist
Para cada ativo:
- ativo
- impacto macro atual: positivo / negativo / neutro / misto
- atenção operacional
- evitar operar em algum horário? Sim/Não
- comentário curto

## 5. Janelas de cautela
Listar horários em que o Claude deve reduzir confiança em sinais técnicos ou exigir confirmação extra.

## 6. Orientação para os monitores
Regras curtas que os monitores devem considerar hoje, por exemplo:
- Evitar novos setups em XAUUSD 30 min antes/depois de CPI.
- Ter cautela com US500 perto de fala do Fed.
- Petróleo sensível a notícia de estoque/OPEC.
- Crypto sensível a risk sentiment.

## 7. Token policy
Este arquivo deve ser usado pelos monitores como contexto macro salvo.
Os monitores recorrentes não devem fazer novas buscas web a cada ciclo.

## Política de linguagem macro — filtro de risco, não bloqueio absoluto

A análise macro deve ser usada como filtro de risco, timing e confiança, não como gerador ou anulador automático de trade.

Regras:

- A análise técnica continua sendo a base da decisão.
- Macro não gera trade sozinho.
- Macro não invalida setup técnico sozinho.
- Macro ajusta confiança, prioridade, timing, tamanho e cautela.
- Eventos de alto impacto exigem confirmação técnica mais forte.
- Janelas de notícia devem ser tratadas como períodos de volatilidade elevada.

Evitar linguagem absoluta, exceto em casos extremos e claramente justificados.

Evitar frases como:

- "não operar"
- "não disparar setup"
- "bloquear trade"
- "suspender sinal"
- "setup proibido"

Preferir frases como:

- "reduzir confiança"
- "exigir confirmação técnica extra"
- "evitar entrada imediatamente antes/depois do evento"
- "tratar como ambiente de alta volatilidade"
- "reduzir prioridade"
- "considerar menor tamanho"
- "aguardar candle de confirmação após o evento"
- "manter setup em observação até o evento passar"

Quando houver evento de altíssimo impacto, como FOMC, CPI, NFP, decisão de juros ou choque geopolítico relevante, orientar os monitores a:

1. manter a análise técnica;
2. reduzir a confiança em setups incompletos;
3. exigir confluências adicionais;
4. evitar leitura apressada em candles de spike;
5. aguardar estabilização do preço após o evento quando possível.

A saída macro deve sempre diferenciar:

- contexto macro;
- impacto provável;
- risco de volatilidade;
- efeito sobre confiança técnica;
- orientação prática para os monitores.
