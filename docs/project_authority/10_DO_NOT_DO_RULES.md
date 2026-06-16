# 10 — Do Not Do Rules

Este arquivo lista proibições operacionais do projeto Trading System.

## Dados e backtests

Não usar `slim_features` como fonte de verdade para validação de estratégia.

Não calibrar thresholds com SLIM.

Não tratar proxy como indicador real.

Não usar features inventadas ou interpretativas como se fossem leitura de mercado.

Não validar estratégia baseada em zonas, NAS, Bubbles, SMC, RSI divergência, Auction Theory ou contexto visual sem RAW/source-field/visual check.

Não rodar backtest sem gate manifest.

Não rodar backtest se nome da variante e definição textual do usuário divergirem.

Não tratar `nome_da_estratégia` como definição. A definição são os gates reais.

Não aceitar resultados de backtest sem saber:

- fonte;
- período;
- campos;
- predicados;
- exemplos pass/fail;
- limitações.

## Estratégias

Não promover estratégia por PF alto isolado.

Não promover estratégia sem visual review.

Não promover estratégia sem walk-forward/sensibilidade quando relevante.

Não tratar high MFE teórico como resultado operacional.

Não confundir fat-tail potential com execução capturável.

Não misturar estratégias diferentes apenas porque compartilham alguns indicadores.

Não reclassificar estratégia sem atualizar status e evidência.

Não deixar estratégia rejeitada ou suspeita com rota operacional viva.

## Indicadores

Não assumir que `NAS LONG` significa uma única coisa. Confirmar evento, recent, anchor price e timing.

Não assumir que `Bubbles` são buy/sell confirmation. Confirmar side, size, cluster, localização e reação posterior.

Não tratar `CHoCH` como um único tipo. Distinguir internal vs swing.

Não usar zona derivada/proxy como se fosse BigBeluga/Custom OB literal.

Não assumir que label visual e timestamp de detecção são a mesma coisa.

## Produção

Não tocar produção sem autorização explícita.

Não alterar catalog, monitor, strategy_rules, Pine, outcomes, LaunchAgents ou logs ativos sem autorização.

Não chamar TradingView/MCP para plot sem pausar daemon/cron quando necessário.

Não deixar daemon/cron pausados sem reportar claramente.

Não limpar drawings se o usuário pediu para deixar no gráfico.

Não iniciar, matar, arquivar ou modificar processos fora do escopo autorizado.

## Arquitetura e cleanup

Não fazer cleanup destrutivo sem inventário.

Não deletar fonte de verdade.

Não preservar lixo por padrão se o usuário pediu limpeza, mas classificar antes de apagar.

Não criar nova arquitetura para corrigir erro simples.

Não adicionar diretórios, scripts ou docs sem necessidade clara.

Não transformar tarefa operacional simples em framework.

## Comunicação

Não responder ao que não foi pedido.

Não gerar relatório longo quando o usuário pediu resposta curta.

Não recomendar parar o projeto por erro do assistente ou Claude.

Não justificar erro com excesso de explicação.

Não fazer elogio vazio.

Não suavizar erro grave.

Não inventar certeza.

Não dizer “validado” quando é apenas exploratório.

Não usar linguagem que esconda limitação.

## Processo

Não seguir se houver ambiguidade danosa.

Não assumir “original” sem verificar definição.

Não continuar cadeia de análise se o input base está errado.

Não criar PDF, plot, commit ou push sem autorização.

Não esquecer que o usuário decide direção, continuidade e risco.

## Regra final

Se a ação não é simples, segura, rastreável e autorizada, não executar.
