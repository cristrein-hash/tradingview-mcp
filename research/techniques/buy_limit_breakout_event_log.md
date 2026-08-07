# TÉCNICA: Buy-Limit-Breakout em Evento (BLBE) — Forward Log

**Estatuto:** CANDIDATO EM ESTUDO (não aprovado, não rejeitado). Árbitro = forward com N≥5-6 eventos,
risco controlado, avaliação por dados e não por euforia de amostra-1. (Cris 2026-08-07)

## Definição estrita (condições OBRIGATÓRIAS — sem estas, não é a técnica, é chase)
1. **Alinhamento de tendência:** buy-limit/stop ACIMA do topo SÓ em uptrend confirmado (espelho short só
   em downtrend). NUNCA contra a tendência dominante.
2. **Catalisador real:** só em evento macro agendado (NFP, CPI, FOMC, PCE). Não em topo qualquer.
3. **Entrada por CONFIRMAÇÃO, não predição:** a ordem só enche se o mercado ROMPE o nível — não se
   adivinha a direção do número.
4. **Risco definido e PEQUENO:** ≤0,5% da conta. O whipsaw/fakeout VAI acontecer — o size protege.
5. **Nível da ordem + SL pré-definidos ANTES do evento** (sem ajustar no calor).

## Modo de falha conhecido (a vigiar no forward)
- **Fakeout/whipsaw:** rompe para cima, enche a ordem, REVERTE → SL. É o cenário mais comum de perda em
  breakouts de NFP. A técnica só é boa se os winners pagarem os múltiplos fakeouts.
- **Slippage no fill:** spike violento pode encher muito acima do nível → entry pior, RR degradado.

## Métricas a acumular (painel honesto, por evento)
| # | data | evento | tendência | nível ordem | SL | fill? | slippage | resultado (R) | outcome | nota |
|---|------|--------|-----------|-------------|----|----|----------|---------------|---------|------|
| 1 | 2026-08-07 | NFP | UP | ~acima 4327 | ~4307? | SIM | ? | +? (WIN, ouro +60) | WIN | payroll gold-positive; trend-aligned; Cris confirmou funcionou. SIZE/entry exato a preencher. |

## Regra de decisão (prereg)
- **APROVAR** só se, ao fim de N≥5-6 eventos: expectância líquida > 0 com risco 0,5%, e os winners
  sobrevivem aos fakeouts (não é 1 win a mascarar 4 perdas). 
- **REJEITAR** se o whipsaw come a maioria ou se depende de acertar a direção do número (=aposta).
- Amostra-1 (hoje) NÃO valida — é o 1º ponto do forward.

## Vieses a guardar contra (lição do próprio Cris)
- **Viés de resultado:** "deu certo = é seguro" é a mesma lógica que reforçou os shorts de reversão que
  custaram -4,2%. Uma vitória não reescreve o risco. Ver memory:project_trade_log_20260807_chase_be_exit.
- Registar TODOS os usos, incluindo os que não enchem e os que dão SL — sem cherry-pick.
