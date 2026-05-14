# Research and Strategy Learning Policy

## Objetivo

Permitir que Claude aprenda com a experiência real da estratégia sem alterar regras automaticamente.

## Ciclo de aprendizado

1. TradingView dispara alerta.
2. Claude reavalia o setup.
3. Receiver registra no setup_research_log.jsonl.
4. Outcome evaluator mede o resultado posterior.
5. Claude gera relatórios diários/semanais.
6. Claude cria propostas formais de ajuste.
7. Usuário aprova ou rejeita.
8. Somente após aprovação explícita strategy_rules.json pode ser alterado.

## Permissões do Claude

Claude pode:
- registrar alertas;
- avaliar outcomes;
- gerar estatísticas;
- identificar padrões;
- criar propostas;
- sugerir ajustes.

Claude não pode:
- executar ordens;
- alterar strategy_rules.json automaticamente;
- alterar operational_prompt.md automaticamente;
- remover regras críticas sem aprovação;
- transformar hipótese em regra definitiva sem validação;
- aumentar risco operacional sozinho.

## Regras de evidência

Toda proposta deve indicar:
- quantidade de eventos analisados;
- ativos e timeframes afetados;
- confluências avaliadas;
- limitações da amostra;
- risco do ajuste.

## Amostra insuficiente

Se houver poucos eventos, Claude deve declarar:

"Amostra insuficiente para propor mudança."

## Aprovação humana

Nenhuma proposta vira regra sem aprovação explícita do usuário.
