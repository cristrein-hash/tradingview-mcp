# Daily Strategy Research Review — Parcial
Data: 2026-04-30
Período analisado: eventos de 2026-04-29 a 2026-04-30
Status: relatório parcial, amostra ainda insuficiente para alteração de regra.

## 1. Resumo executivo

O sistema D1/D2 está operacional. Até este ponto, foram registrados 52 eventos de pesquisa e 80 outcomes D2. Em nível de evento único, há 20 eventos com algum outcome avaliado.

Resumo por evento:
- mostly_favorable: 11
- mostly_adverse: 6
- mixed: 1
- unclear_or_noise: 1
- insufficient_data: 1

Leitura provisória:
- A amostra sugere que há valor em medir reações futuras por MFE/MAE e não apenas por acerto/erro.
- Ainda não há amostra suficiente para alterar strategy_rules.json.
- Outcomes 1–60 devem ser interpretados com cautela porque o D2 ainda estava agressivo em should_adjust_strategy.
- Outcomes após o patch conservador do D2 são mais confiáveis para propostas futuras.

## 2. Estado do sistema

Correções feitas hoje:
- Telegram deixou de disparar por menções negativas ou genéricas a QUASE_VALIDO.
- Telegram deixou de disparar por frases como "bloqueio crítico de RSI".
- D2 foi ajustado para manter should_adjust_strategy=false por padrão.
- D2 só deve sugerir ajuste formal com evidência recorrente em múltiplos eventos independentes.

## 3. Estatísticas gerais D2

Outcomes brutos:
- favorable_reaction: 30
- adverse_reaction: 17
- insufficient_data: 22
- unclear: 5
- sideways_noise: 4
- invalidation_confirmed: 2

Direções:
- long: 68
- short: 8
- unknown: 4

Observação:
A amostra está enviesada para eventos long. Não concluir ainda sobre performance de shorts.

## 4. Resultado por ativo

BTCUSD:
- mostly_favorable: 1
- insufficient_data: 1
Leitura: promissor, mas ainda com pouca amostra.

ETHUSD:
- mostly_favorable: 1
- mostly_adverse: 2
Leitura: short em supply funcionou, longs em demand durante queda forte falharam. Evitar afrouxar RSI genericamente em ETH.

US500:
- mostly_favorable: 1
Leitura: caso forte com cluster BigBeluga + LONG NAS100 + RSI ~33, mas amostra insuficiente para regra.

USDJPY:
- unclear_or_noise: 1
- mostly_adverse: 1
Leitura: baixa confiança; houve evento de teste contaminando a amostra.

XAGUSD:
- mostly_favorable: 2
Leitura: promissor, mas precisa mais casos.

XAUUSD:
- mostly_favorable: 3
- mostly_adverse: 2
Leitura: reage bem com confirmação, mas pune entrada antecipada ou contra momentum/macro.

XPTUSD:
- mostly_favorable: 3
- mostly_adverse: 1
- mixed: 1
Leitura: promissor para hipótese de sweep/reentry, mas primeiro toque pode sofrer MAE relevante.

## 5. Hipóteses provisórias

1. Reentry pós-sweep
Zonas demand podem funcionar melhor após varredura/invalidação falsa seguida de candle de força, especialmente em XPTUSD.

2. US500 com cluster denso
Em US500, RSI levemente acima de 30 pode ser aceitável quando há cluster BigBeluga denso + sinal LONG NAS100 dentro da zona. Ainda não alterar regra.

3. ETHUSD em queda forte
Long em demand sem RSI extremo, sem bubbles e sem candle fechado de rejeição é fraco. O filtro conservador protegeu.

4. XAUUSD
A confirmação local é crítica. Entradas antecipadas geram MAE/invalidação; entradas com confirmação têm melhor reação.

## 6. Propostas de ajuste

Nenhuma proposta aprovada.

Amostra insuficiente para alteração de:
- strategy_rules.json
- operational_prompt.md

Qualquer proposta deve passar por D4 formal e aprovação humana.

## 7. Próximas ações

- Continuar acumulando D1.
- Rodar D2 em lotes pequenos.
- Separar outcomes pré-patch e pós-patch.
- Monitorar especialmente:
  - QUASE_VALIDO explícito;
  - reentry pós-sweep;
  - US500 com cluster BigBeluga;
  - ETHUSD long contra queda forte;
  - ruído em USDJPY.
