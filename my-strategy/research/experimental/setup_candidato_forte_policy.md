# SETUP_CANDIDATO_FORTE — Política Operacional Experimental

Status: experimental / revisão humana  
Substitui operacionalmente: QUASE_VALIDO / INTRADAY_QUASE_VALIDO

## 1. Objetivo

Criar uma camada intermediária entre SETUP_VALIDO e SETUP_EM_OBSERVACAO para evitar perda de oportunidades assimétricas reais.

SETUP_CANDIDATO_FORTE significa:

- oportunidade forte para revisão humana;
- não é entrada automática;
- não altera risco;
- não executa ordem;
- deve ir para Telegram;
- deve ser medida em D1/D2 por MFE, MAE, R:R e outcome posterior.

## 2. Hierarquia operacional

SETUP_VALIDO:
- setup completo segundo regras principais;
- execução sempre manual.

SETUP_CANDIDATO_FORTE:
- oportunidade assimétrica forte;
- faltam uma ou duas confirmações formais;
- merece revisão humana imediata;
- não é entrada automática.

SETUP_EM_OBSERVACAO:
- contexto interessante;
- ainda insuficiente para Telegram na maioria dos casos.

NO_TRADE:
- não operar;
- tese inválida, ruído, bloqueio crítico ou ausência de estrutura.

## 3. Regra central

SETUP_CANDIDATO_FORTE não exige checklist perfeito.

Ele existe para capturar casos em que a assimetria operacional é boa, mesmo sem todos os elementos exigidos para SETUP_VALIDO.

O foco é:

- zona/linha relevante;
- direção clara;
- stop técnico claro;
- R:R >= 2:1;
- confluências suficientes;
- revisão humana.

## 4. Critérios mínimos obrigatórios

Classificar como SETUP_CANDIDATO_FORTE somente se TODOS forem verdadeiros:

1. Ativo está na watchlist operacional.
2. Há zona ou linha operacional relevante:
   - AUTO_CLAUDE_;
   - AUTO_CLAUDE_DYNAMIC_;
   - BB/BigBeluga 4H, 1H, 30M ou 15M;
   - linha dinâmica de invalidação, breakout, breakdown, reentry, LTA/LTB local.
3. Preço está tocando, entrando, reagindo ou muito próximo da zona/linha.
4. Direção operacional está clara:
   - long;
   - short;
   - breakout;
   - breakdown;
   - reentry.
5. Existe stop técnico claro.
6. R:R estimado é >= 2:1.
7. Não há janela macro vermelha imediata.
8. Há pelo menos 3 confluências fortes.

## 5. Confluências fortes

Contam como confluência forte:

- RSI em extremo;
- RSI recém saindo de extremo;
- divergência Regular Bull/Bear;
- CHoCH/BOS na direção;
- sweep/reentry;
- sinal NAS100 LONG/SHORT dentro ou na borda da zona;
- rejeição clara em candle fechado;
- cluster Market Order Bubbles;
- zona 15M/30M nested dentro de 1H/4H;
- toque em linha dinâmica de invalidação/reentry/breakout;
- contexto HTF favorecendo direção;
- price action esticado chegando em supply/demand;
- recuperação forte após sweep;
- falso rompimento retornando para dentro da zona.

## 6. O que NÃO é obrigatório

Para SETUP_CANDIDATO_FORTE, não exigir obrigatoriamente todos ao mesmo tempo:

- RSI extremo exato no candle atual;
- Bubbles;
- NAS100 signal fresco;
- CHoCH/BOS já confirmado;
- divergência perfeita.

Esses elementos aumentam confiança, mas não são todos obrigatórios se houver 3 ou mais confluências fortes e R:R >= 2:1.

## 7. Bloqueios obrigatórios

Não classificar como SETUP_CANDIDATO_FORTE se houver:

- sem stop técnico claro;
- R:R < 2:1;
- macro vermelha imediata;
- range tight sem direção;
- apenas toque seco de zona;
- nenhuma confirmação estrutural;
- direção indefinida;
- leitura MCP falhou ou símbolo/timeframe não confiável;
- zona muito distante sem chance operacional;
- risco de notícia iminente;
- setup depende apenas de esperança de reversão.

## 8. Telegram

Quando houver SETUP_CANDIDATO_FORTE, Telegram deve avisar:

🟠 [CLAUDE] <ATIVO> <TF> — SETUP_CANDIDATO_FORTE — REVISÃO HUMANA

A conclusão deve conter:

SETUP_CANDIDATO_FORTE. Revisão humana; não é entrada automática.

## 9. Output obrigatório do Claude

Quando reavaliar qualquer alerta, Claude deve preencher:

Classificação:
Direção:
R:R estimado:
Gatilho faltante:
Candidato forte:
Motivo candidato forte:

Valores esperados:

Candidato forte: SIM
ou
Candidato forte: NÃO

Se SIM:
- explicar as confluências;
- indicar stop técnico;
- indicar R:R;
- dizer claramente que não é entrada automática.

## 10. Relação com QUASE_VALIDO

QUASE_VALIDO e INTRADAY_QUASE_VALIDO ficam obsoletos como linguagem operacional.

Para logs antigos, podem continuar existindo como histórico.

Para novas respostas, usar SETUP_CANDIDATO_FORTE.

Não usar mais:
- QUASE_VALIDO;
- INTRADAY_QUASE_VALIDO;
- quase válido experimental.

Usar:
- SETUP_CANDIDATO_FORTE;
- Candidato forte: SIM/NÃO.

## 11. Pesquisa D1/D2

Todo SETUP_CANDIDATO_FORTE deve ser medido em D2.

Métricas principais:
- MFE;
- MAE;
- R:R teórico;
- outcome_label;
- would_have_helped;
- would_have_hurt;
- se virou SETUP_VALIDO depois;
- se Telegram foi útil ou ruído.

## 12. Aprovação humana

SETUP_CANDIDATO_FORTE não altera strategy_rules.json.

Qualquer promoção futura para regra definitiva exige:
- amostra recorrente;
- relatório D3;
- proposta D4;
- aprovação explícita do usuário.
