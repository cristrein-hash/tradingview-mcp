# XAU 15M BigBeluga + NAS (Leonardo) — Perguntas operacionais (Fase 0)

**Objetivo:** confirmar a **regra real** que o Leonardo opera no mercado, antes de qualquer backtest. Sem isto, a análise corre risco de interpretar errado o setup. Respostas alimentam a Fase 2 (taxonomia) e o gate manifest futuro.
**Contexto:** estudo neutro; estratégia **não aprovada, não ativa**. Ver `XAU_15M_BB_NAS_LEONARDO_WORKFLOW_PROPOSAL.md` e `research/xau_15m_bb_nas_leonardo/manual_trade_table.csv`.

## 1. Entrada
1. Qual é a **condição exata** para entrar? (o que precisa estar verdadeiro no momento do clique)
2. Entra no **primeiro NAS** dentro da zona ou **espera um cluster**? Se cluster, **quantos** NAS no mínimo?
3. Entra **dentro** da zona, **na borda**, ou **no rompimento/reteste** da borda? (nos prints aparece "logo abaixo/acima da zona")
4. Há janela de tempo entre o NAS e a entrada? (ex.: entrar até X candles após o sinal)

## 2. Região BigBeluga
5. O que define uma **região BigBeluga válida** para operar? (toda zona vale? só as recentes? só as de certo tamanho?)
6. Importa o **tamanho/largura** da zona na decisão de entrar? Há zona "grande demais" que você evita?
7. Zona **fresca** (não testada) vs zona **já testada** muda sua decisão?

## 3. Reversão vs Continuação
8. Você opera **reversão** (contra o movimento que chegou) e **continuação** (pullback a favor da tendência) da **mesma forma**, ou são setups diferentes com regras diferentes?
9. Se diferentes: o que muda (entrada, stop, alvo, gestão) entre os dois?

## 4. Tendência / contexto
10. Como você **define a tendência**? Visual? Médias? Estrutura?
11. Em **qual timeframe** olha a tendência — M15, H1, 4H, diário? Usa mais de um?
12. Você **evita reversão contra tendência forte**? Como decide que está "forte demais"?

## 5. Quando NÃO entra
13. Quais condições fazem você **descartar** um setup que tem BB+NAS? (ex.: chegada muito impulsiva, tendência contrária forte, zona muito testada, horário)
14. O **movimento de chegada** à zona (velocidade/agressividade) influencia a decisão?

## 6. Stop
15. O stop fica **sempre** do outro lado da zona? Ou há outra regra (ATR, swing, pontos fixos)?
16. O stop vai **na borda** da zona ou **além** dela (com folga)? Quanta folga?

## 7. Alvo / saída
17. Como decide o **alvo**? Zona oposta? R fixo? Estrutura?
18. Usa **NAS oposto** como sinal de saída? (no Trade 05 a saída foi num cluster NAS LONG) — é regra ou caso a caso?
19. Usa **alvo parcial** / realização parcial?

## 8. Gestão de trades longos
20. Como você **segura** um trade que vira runner de vários dias? (os maiores R duraram >1–3 dias)
21. Move stop para breakeven / trailing? Com que critério?
22. O que te faz **sair antes** do alvo?

## 9. Pós-entrada / lateralização
23. Se o preço **entra na zona e lateraliza** sem ir a favor por N candles, o que você faz? (sai? reduz? espera?)
24. Quanto tempo "preso na zona" é aceitável antes de você considerar o setup inválido?
25. **NAS novos depois da entrada** mudam sua gestão? (confirmam, ou você ignora se o preço não desloca?)

## 10. Reentrada
26. Após ser **stopado**, você **reentra** na mesma zona/ideia? Sob quais condições?

## 11. NAS válido
27. O que é um **NAS válido** para você? Todo NAS conta, ou filtra por algo (direção, posição na zona, contexto)?
28. NAS **fora** da zona contam? E NAS **na direção oposta** ao seu trade?

## 12. Horários / sessões
29. Usa **filtro de horário/sessão**? (há uma nota nos prints: "sinal NAS veio entre 21:45 e 00") — isso é regra?
30. Há horários que você **evita** operar?

## 13. Timeframes superiores
31. Olha **H1 / 4H / diário** antes de entrar no M15? Para quê exatamente (tendência, zonas maiores, eventos)?
32. Usa **BigBeluga de timeframe maior** como confluência?

## 14. Amostra / curadoria (crítico para validade)
33. Os 15 winners e os losers dos PDFs são **todos** os trades de um período, ou são **exemplos selecionados**? (o doc dos losers diz que não contém todos)
34. Existe um **registro completo** (todos os trades, inclusive os medianos e os perdedores não destacados) que possamos usar? Sem isso não há winrate real.
35. Quais desses setups você **realmente operaria com dinheiro** hoje vs quais foram só **estudados/replay**?
36. Algum desses trades foi **replay** (e não realtime)? Quais?

## 15. Diferença estudo vs execução
37. Há alguma regra que você usa na prática que **não aparece** nas anotações dos PDFs?
38. Olhando os losers agora: o que você **faria diferente**? (isso já é uma hipótese de filtro)

---
_Fase 0 do workflow. Respostas confirmam a regra antes de catalogar/validar. Nada aqui ativa a estratégia._
