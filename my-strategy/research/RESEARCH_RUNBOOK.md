# Research Runbook — D1 a D5

## Objetivo

Manter um fluxo de pesquisa e backtest operacional baseado em alertas reais da estratégia.

O objetivo não é executar ordens automaticamente, mas permitir que Claude aprenda com a prática, meça resultados e proponha melhorias com aprovação humana.

## Estado atual

- D1 — Journal automático de setups: instalado
- D2 — Avaliação posterior dos setups: instalado
- D3 — Relatórios de aprendizado: preparado
- D4 — Propostas formais de ajuste: preparado
- D5 — Aprovação humana obrigatória: preparado

## Fluxo normal

1. TradingView dispara alerta em desenho AUTO_CLAUDE_.
2. Webhook receiver recebe o alerta.
3. Claude reavalia o gráfico.
4. Telegram só é enviado se houver relevância operacional.
5. Receiver grava o evento em setup_research_log.jsonl.
6. Após candles suficientes, evaluate_setup_outcomes.py mede o que aconteceu.
7. Outcomes são gravados em setup_outcome_log.jsonl.
8. Claude usa os logs para relatórios e propostas.

## Arquivos principais

Journal:
~/tradingview-mcp/alert-bridge/logs/setup_research_log.jsonl

Outcomes:
~/tradingview-mcp/alert-bridge/logs/setup_outcome_log.jsonl

Status:
~/tradingview-mcp/alert-bridge/research_status.py

Avaliador:
~/tradingview-mcp/alert-bridge/evaluate_setup_outcomes.py

Prompt de revisão:
~/tradingview-mcp/my-strategy/research/research_review_prompt.md

Política:
~/tradingview-mcp/my-strategy/research/RESEARCH_POLICY.md

Template de proposta:
~/tradingview-mcp/my-strategy/research/proposals/PROPOSAL_TEMPLATE.md

## Comandos úteis

Ver status:

python3 "$HOME/tradingview-mcp/alert-bridge/research_status.py"

Ver último evento do journal:

tail -n 1 "$HOME/tradingview-mcp/alert-bridge/logs/setup_research_log.jsonl" | python3 -m json.tool

Ver eventos pendentes para D2:

python3 "$HOME/tradingview-mcp/alert-bridge/evaluate_setup_outcomes.py" --dry-run --limit 5

Rodar D2:

python3 "$HOME/tradingview-mcp/alert-bridge/evaluate_setup_outcomes.py" --limit 5

Ver último outcome:

tail -n 1 "$HOME/tradingview-mcp/alert-bridge/logs/setup_outcome_log.jsonl" | python3 -m json.tool

## Quando rodar D2

Rodar D2 manualmente quando houver alertas reais suficientes no journal.

Não rodar D2 automaticamente ainda para evitar consumo desnecessário de tokens.

Sugestão:
- após alguns alertas relevantes;
- após algumas horas de mercado;
- ao fim do dia;
- antes de gerar relatório diário.

## Como lidar com insufficient_data

Se D2 retornar insufficient_data, isso é normal.

Significa que ainda não há candles suficientes para avaliar 5, 10, 20 ou 50 candles após o alerta.

Não forçar conclusão.

## D3 — relatório de aprendizado

Gerar relatório diário apenas quando houver:
- eventos reais no setup_research_log.jsonl;
- outcomes avaliados no setup_outcome_log.jsonl.

Se a amostra for pequena, declarar:
“Amostra insuficiente para propor mudança.”

## D4 — propostas

Claude pode criar propostas em:

~/tradingview-mcp/my-strategy/research/proposals/

Toda proposta deve usar PROPOSAL_TEMPLATE.md.

## D5 — aprovação humana

Nenhuma proposta altera strategy_rules.json automaticamente.

Toda mudança de estratégia exige aprovação explícita do usuário.

## Regras de segurança

Claude pode:
- registrar eventos;
- avaliar outcomes;
- gerar relatórios;
- sugerir melhorias.

Claude não pode:
- executar ordens;
- alterar strategy_rules.json sem aprovação;
- alterar operational_prompt.md sem aprovação;
- transformar hipótese em regra definitiva sem validação;
- ignorar amostra insuficiente.
