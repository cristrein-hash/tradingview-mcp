# D6 — Dynamic Intraday BB Zones Experimental

Status: experimental / controlado  
Objetivo: permitir que Claude desenhe novas zonas intraday 15M/30M baseadas em regiões BB/BigBeluga recentes próximas do price action, sem alterar a estratégia principal e sem executar trades.

## 1. Objetivo

Criar uma camada dinâmica de marcação intraday para capturar novas regiões BB/BigBeluga que surgem com o price action em 15M e 30M.

Fluxo desejado:

Price action cria nova região BB 15M/30M
→ Claude identifica a zona
→ Claude desenha zona experimental AUTO_CLAUDE_DYNAMIC_
→ posteriormente TradingView pode monitorar toque
→ receiver reavalia via Claude
→ Telegram só envia se houver relevância operacional
→ D1/D2 medem outcome

## 2. Princípio central

Sobreposição com zonas maiores não é proibida.

Zonas 15M/30M dentro de zonas 1H/4H/D podem ser desejáveis quando acrescentam precisão operacional, melhoram entrada, reduzem stop ou aumentam R:R.

A regra é:

Evitar duplicação sem ganho operacional.
Permitir sobreposição que acrescente precisão.

## 3. Claude pode

- desenhar novas zonas BB/BigBeluga em 15M e 30M;
- usar apenas prefixo AUTO_CLAUDE_DYNAMIC_;
- desenhar zonas nested dentro de zonas HTF quando acrescentarem precisão;
- registrar motivo da zona;
- marcar zonas antigas/distantes como candidatas a limpeza manual;
- sugerir criação futura de alerta.

## 4. Claude não pode

- apagar desenhos;
- apagar alertas;
- alterar desenhos manuais do usuário;
- alterar strategy_rules.json;
- alterar operational_prompt.md sem aprovação;
- executar ordens;
- transformar zona dinâmica em entrada automática;
- criar alertas em massa;
- redesenhar a mesma zona repetidamente sem ganho operacional.

## 5. Tipos de sobreposição

### 5.1 Nested inside HTF zone

Permitido e desejável quando a zona 15M/30M está dentro de zona 1H/4H/D e melhora precisão.

Exemplo:
- zona 4H demand: 4500–4580
- zona dinâmica 30M demand: 4522–4536

Classificação:
overlap_type = nested_inside_htf_zone  
adds_precision = true

### 5.2 Partial overlap

Permitido com cautela quando a zona nova tem origem própria no price action e acrescenta informação.

Classificação:
overlap_type = partial_overlap  
duplication_risk = medium

### 5.3 Duplicate zone

Evitar quando a zona nova é praticamente igual a uma já existente e não melhora execução.

Classificação:
overlap_type = duplicate_without_edge  
adds_precision = false

## 6. Critérios para desenhar zona dinâmica

Claude pode desenhar uma zona dinâmica se todos forem verdadeiros:

1. Timeframe é 15M ou 30M.
2. Zona está próxima do price action atual.
3. Zona representa nova região BB/BigBeluga ou estrutura local clara.
4. Bordas da zona são objetivas.
5. Zona acrescenta precisão operacional ou representa nova reação local.
6. Zona não é duplicação quase idêntica sem ganho.
7. Nome usa prefixo AUTO_CLAUDE_DYNAMIC_.
8. Zona é experimental e não gera entrada automática.

## 7. Nome padrão

AUTO_CLAUDE_DYNAMIC_<ATIVO>_<TF>_<DEMAND/SUPPLY>_BB_<YYYYMMDD_HHMM>

Exemplos:
AUTO_CLAUDE_DYNAMIC_XAUUSD_15M_DEMAND_BB_20260430_1530
AUTO_CLAUDE_DYNAMIC_XAGUSD_30M_SUPPLY_BB_20260430_1600

Se for nested:
AUTO_CLAUDE_DYNAMIC_XAUUSD_30M_DEMAND_BB_NESTED_20260430_1530

## 8. Limite operacional

Referência inicial:
- até 4 zonas dinâmicas prioritárias por ativo próximas do preço.

Esse limite não é bloqueio rígido.

Se houver mais de 4 zonas úteis, Claude pode desenhar nova zona, mas deve sinalizar que há excesso operacional e recomendar revisão manual de zonas antigas/distantes.

Claude não deve deletar nada sozinho.

## 9. Alertas

Fase atual: desenho primeiro, alerta depois.

Na fase inicial, Claude só deve desenhar zonas dinâmicas, não criar alertas automaticamente.

A criação de alertas em desenhos será testada depois, em fase separada, com poucos ativos e payload específico.

Alert type futuro sugerido:
monitor_dynamic_bb_zone

## 10. Telegram

Zona dinâmica não significa Telegram.

Telegram só deve ser enviado depois de recheck se houver:
- SETUP_VALIDO;
- QUASE_VALIDO experimental explícito;
- invalidação real;
- evento crítico específico.

## 11. Pesquisa

Zonas dinâmicas devem ser avaliadas separadamente das zonas principais.

Perguntas de pesquisa:
- zonas nested performam melhor que zonas isoladas?
- zonas 15M dentro de 4H reduzem MAE?
- zonas 30M dentro de 1H melhoram R:R?
- zonas dinâmicas geram mais ruído ou mais oportunidade?
- reentry pós-sweep melhora expectancy?

## 12. Aprovação humana

Qualquer expansão de permissão deve ser aprovada pelo usuário.

Fases:
1. Documentar política.
2. Permitir desenho sem alerta.
3. Testar em 1 ativo.
4. Testar em poucos ativos.
5. Só depois testar alertas em desenhos.
6. Só depois avaliar expansão.

## 13. Correção operacional — zonas BB visíveis no indicador

Uma zona BB/BigBeluga visível no indicador NÃO deve ser tratada como duplicação por si só.

Para o D6, o objetivo é transformar regiões BB operacionais em desenhos AUTO_CLAUDE_DYNAMIC_ monitoráveis.

Portanto:

- Se a zona existe apenas no indicador BB/BigBeluga, mas ainda não existe como desenho AUTO_CLAUDE_ ou AUTO_CLAUDE_DYNAMIC_, ela pode ser desenhada.
- Isso é especialmente importante em 15M e 30M, porque o desenho permite criar alerta operacional depois.
- A zona só deve ser considerada duplicada se já houver desenho AUTO_CLAUDE_ ou AUTO_CLAUDE_DYNAMIC_ com bounds praticamente iguais e sem ganho operacional.

Regra prática:

Indicador BB visível = fonte da zona.
Desenho AUTO_CLAUDE_DYNAMIC_ = objeto operacional monitorável.

Não confundir os dois.

## 14. Correção operacional — scan obrigatório 15M/30M

Em varreduras D6-A, Claude deve verificar explicitamente 15M e 30M.

Mesmo que o alerta recebido esteja em 30M, deve inspecionar 15M quando o objetivo for buscar zona dinâmica intraday.

Se houver zona BB 15M próxima do price action que:
- tenha bordas claras;
- esteja próxima do preço;
- melhore precisão dentro de região HTF ou 30M;
- ainda não exista como desenho AUTO_CLAUDE_DYNAMIC_;

então Claude pode desenhá-la.

Exemplo de caso válido:
- BTCUSD 15M com zona BB demand/supply próxima do preço;
- zona aparece no indicador, mas ainda não existe como desenho AUTO_CLAUDE_DYNAMIC_;
- zona melhora monitoramento e pode virar candidata D6-B.

Nesse caso, a ação correta é desenhar, não rejeitar como duplicação.

## 15. Premissa operacional — MCP não lista/deleta desenhos de forma confiável

Já foi observado que o MCP não consegue listar ou deletar desenhos/alertas de forma confiável.

Portanto, D6-A não deve depender de `draw_list`, listagem de desenhos ou limpeza automática.

Premissas:
- Claude pode desenhar zonas AUTO_CLAUDE_DYNAMIC_ sem verificar lista completa de desenhos existentes.
- Claude deve usar nome único com timestamp.
- Claude nunca deve deletar desenhos.
- Claude nunca deve deletar alertas.
- O usuário fará limpeza manual de desenhos e alertas obsoletos.
- Duplicação visual é aceitável durante o experimento se a zona for operacionalmente útil.
- Se houver possível duplicação, Claude deve mencionar: "possível duplicação visual — limpeza manual".

Regra prática:
Não travar D6-A por incapacidade de listar/deletar desenhos.
Se a zona BB 15M/30M for clara, próxima do price action e útil para monitoramento, desenhar.

Questão ainda em aberto para D6-B:
Testar se Claude consegue criar alerta em um desenho criado por ele mesmo.

## 16. D6-B — teste controlado de alerta em desenho dinâmico

D6-B testa se Claude consegue criar alerta em um desenho AUTO_CLAUDE_DYNAMIC_ criado por ele mesmo.

Escopo inicial:
- 1 ativo;
- 1 desenho;
- 1 alerta;
- 1 tentativa;
- sem deletar alertas;
- sem deletar desenhos;
- usuário fará limpeza manual se necessário.

Claude só pode tentar criar alerta D6-B quando:
- alert_type = manual_d6b_create_alert;
- target_drawing_name estiver presente;
- o desenho alvo começar com AUTO_CLAUDE_DYNAMIC_;
- o usuário pedir explicitamente o teste.

Payload sugerido para o alerta:
{
  "symbol": "PEPPERSTONE:BTCUSD",
  "timeframe": "15",
  "alert_type": "monitor_dynamic_bb_zone",
  "event": "drawing_alert",
  "drawing_type": "rectangle_zone",
  "drawing_name": "AUTO_CLAUDE_DYNAMIC_BTCUSD_15M_DEMAND_BB_20260430_1330",
  "strategy_layer": "DynamicIntraday",
  "source_timeframe": "15M",
  "reason": "preco tocou zona dinamica BB 15M desenhada por Claude",
  "expected_recheck": "reavaliar zona dinamica D6, RSI 15M/30M, NAS100 signal, bubbles, rejeicao, CHoCH/BOS, R:R e contexto macro; enviar Telegram somente se houver SETUP_VALIDO, QUASE_VALIDO explicito, invalidacao real ou evento critico especifico"
}

Importante:
Criar alerta não significa trade.
Criar alerta não significa Telegram.
O alerta apenas aciona reavaliação futura.

## 17. D6-B2 — teste controlado de alerta por preço/borda da zona

Como o MCP atual não conseguiu criar alerta vinculado diretamente ao desenho AUTO_CLAUDE_DYNAMIC_, D6-B2 testa uma alternativa:

Criar alerta por preço/borda da zona, mantendo no payload o nome do desenho dinâmico.

Escopo inicial:
- 1 ativo;
- 1 preço;
- 1 alerta;
- 1 tentativa;
- sem criar novos desenhos;
- sem deletar desenhos;
- sem deletar alertas.

Claude só pode tentar criar alerta D6-B2 quando:
- alert_type = manual_d6b_create_price_alert;
- target_price estiver presente;
- target_drawing_name estiver presente;
- target_drawing_name começar com AUTO_CLAUDE_DYNAMIC_;
- o usuário pedir explicitamente.

Payload sugerido:
{
  "symbol": "PEPPERSTONE:BTCUSD",
  "timeframe": "15",
  "alert_type": "monitor_dynamic_bb_zone",
  "event": "price_alert",
  "drawing_type": "rectangle_zone",
  "drawing_name": "AUTO_CLAUDE_DYNAMIC_BTCUSD_15M_DEMAND_BB_20260430_1330",
  "strategy_layer": "DynamicIntraday",
  "source_timeframe": "15M",
  "zone_type": "demand",
  "zone_origin": "dynamic_bb_15m",
  "trigger_method": "price_crossing_zone_edge",
  "target_price": "76025",
  "reason": "preco tocou borda de zona dinamica BB 15M desenhada por Claude",
  "expected_recheck": "reavaliar zona dinamica D6, RSI 15M/30M, NAS100 signal, bubbles, rejeicao, CHoCH/BOS, R:R e contexto macro; enviar Telegram somente se houver SETUP_VALIDO, QUASE_VALIDO explicito, invalidacao real ou evento critico especifico"
}

Criar alerta por preço não significa trade.
Criar alerta por preço não significa Telegram.
O alerta apenas aciona reavaliação futura.

## 18. D6-A Daily Mode — prioridade 30M sobre 15M quando for a mesma região

Para a rotina diária de criação de zonas dinâmicas, a prioridade operacional é cobertura primeiro e refinamento depois.

Regra principal:

- Se 30M e 15M apontam para a mesma região de preço, preferir desenhar a zona 30M como zona principal.
- A zona 30M tem prioridade porque é mais ampla, captura melhor a região operacional e aumenta a chance de toque/alerta.
- A zona 15M deve ser usada como refinamento, não como substituta automática da 30M.

Quando desenhar 15M além da 30M:
- se a zona 30M for ampla demais;
- se a 15M estiver em uma borda ideal da 30M;
- se a 15M reduzir stop de forma relevante;
- se houver reentry pós-sweep;
- se houver CHoCH/BOS/divergência local mais clara no 15M;
- se o usuário pedir explicitamente foco em precisão.

Para alertas manuais:
- preferir alertas na zona 30M quando o objetivo for aumentar cobertura e amostra D1/D2;
- usar 15M para alerta adicional apenas quando houver ganho de precisão claro.

Resumo:
30M = zona principal de monitoramento.
15M = refinamento de execução.

## 19. D6-A — zonas 1H e linhas dinâmicas operacionais

A partir desta fase, D6-A também permite que Claude desenhe:

1. Zonas BB/BigBeluga em 1H, além de 15M e 30M.
2. Linhas operacionais dinâmicas quando forem úteis para monitoramento.

Tipos de linhas permitidas:
- suporte intraday;
- resistência intraday;
- linha de invalidação;
- linha de breakout;
- linha de breakdown;
- LTA local;
- LTB local;
- linha de reteste;
- linha de sweep/reentry.

Critério para desenhar linha:
A linha deve ter função operacional clara. Ela deve ajudar a monitorar:
- toque;
- rejeição;
- rompimento;
- invalidação;
- reentry pós-sweep;
- mudança estrutural CHoCH/BOS;
- região onde um novo alerta manual faria sentido.

Nome padrão para linhas:

AUTO_CLAUDE_DYNAMIC_<ATIVO>_<TF>_<TIPO>_LINE_<YYYYMMDD_HHMM>

Exemplos:
AUTO_CLAUDE_DYNAMIC_XAUUSD_15M_INVALIDATION_LINE_20260502_1430
AUTO_CLAUDE_DYNAMIC_XAUUSD_30M_BREAKOUT_LINE_20260502_1430
AUTO_CLAUDE_DYNAMIC_XAUUSD_1H_RESISTANCE_LINE_20260502_1430
AUTO_CLAUDE_DYNAMIC_XAUUSD_15M_REENTRY_LINE_20260502_1430
AUTO_CLAUDE_DYNAMIC_XAUUSD_30M_LTA_LINE_20260502_1430

Guardrails:
- Não desenhar linha sem função clara.
- Não redesenhar trendlines HTF principais já ajustadas manualmente pelo usuário.
- Não deletar desenhos.
- Não deletar alertas.
- Não criar alertas automáticos.
- Se houver possível duplicação visual, mencionar limpeza manual, mas não travar se a linha for útil.
- Preferir poucas linhas boas a muitas linhas fracas.

Hierarquia operacional:
- 1H: contexto intraday maior e níveis de decisão.
- 30M: zona principal de monitoramento.
- 15M: refinamento de execução, reentry, invalidação curta e microestrutura.

## 20. D6-A Full Rebuild Mode — reconstrução completa do ativo

Quando o usuário informar que removeu manualmente desenhos e alertas antigos de um ativo, Claude deve entrar em modo Full Rebuild.

Esse modo é diferente do Daily Maintenance.

### Daily Maintenance

Usar quando o gráfico já tem desenhos operacionais.

Objetivo:
- atualizar poucas zonas próximas do preço;
- evitar poluição visual;
- desenhar apenas novas zonas/linhas realmente necessárias.

### Full Rebuild

Usar quando o usuário limpou desenhos/alertas antigos ou pediu redesenho completo.

Objetivo:
- reconstruir o mapa operacional do ativo;
- avaliar 4H, 1H, 30M e 15M nessa ordem;
- não limitar a análise apenas ao price action imediato;
- desenhar zonas acima e abaixo do preço;
- desenhar linhas operacionais úteis.

### O que desenhar no Full Rebuild

Claude deve buscar, quando existirem com clareza:

4H:
- zona demand estrutural relevante;
- zona supply estrutural relevante;
- linha/pivot HTF de invalidação, breakout ou resistência/suporte maior.

1H:
- zona demand mais relevante abaixo do preço;
- zona supply mais relevante acima do preço;
- nível de decisão intraday.

30M:
- zona principal de monitoramento acima do preço;
- zona principal de monitoramento abaixo do preço.

15M:
- refinamento de execução apenas nas regiões mais próximas ou mais operacionais;
- linha de invalidação curta;
- linha de reentry pós-sweep;
- linha de breakout/breakdown local.

### Quantidade esperada

Em Full Rebuild, desenhar normalmente entre 5 e 10 objetos úteis.

Limite de referência:
- mínimo esperado: 4 objetos se houver estrutura suficiente;
- alvo normal: 6 a 10 objetos;
- máximo recomendado: 12 objetos por ativo.

Não desenhar objeto sem função operacional clara.

### Regra importante

Em Full Rebuild, não rejeitar zona apenas por estar distante do preço.

A pergunta correta é:

Essa zona/linha será útil para monitorar o ativo nas próximas sessões?

Se sim, pode desenhar.

### Hierarquia

4H = mapa estrutural.
1H = zonas intraday amplas.
30M = zonas principais de alerta.
15M = refinamento, reentry e invalidação curta.

### Alertas

Mesmo em Full Rebuild, Claude não cria alertas automaticamente.

Depois do desenho, o usuário cria alertas manuais nos objetos aprovados.

