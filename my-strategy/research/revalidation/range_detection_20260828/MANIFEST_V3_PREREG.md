# RANGE V3 — GT HUMANO + candidata contenção/sweeps (prereg selado 2026-08-28 ANTES de correr; "TOCA FICHA")
Árbitro = gt_human.json (5 períodos Cris, 51a2b42). Honestidade declarada: fora dos períodos NÃO é tudo
TREND (Cris rotulou os ranges CLAROS); FP fora dos períodos é reportado com essa reserva, e a comparação
v5/Layer1/candidata usa o MESMO árbitro (justo entre si). AUTO-CRÍTICA declarada: o %dentro p5-p95 da
verificação é parcialmente tautológico (percentis contêm 90% por construção) — a candidata NÃO usa
contenção percentil; usa os dois invariantes NÃO-tautológicos dos 5 períodos:
  (i) oscilação: o fecho cruza o MEIO da janela repetidamente (trend não cruza);
  (ii) bordas que rejeitam: extremos além da banda que fecham de volta sem aceitação (trend aceita).

## Candidata ÚNICA V3 (diária causal, params selados AGORA, zero sweeps)
Janela W=15 dias. mid = (maxH+minL)/2 da janela. Por dia i:
  cross = nº de cruzamentos do fecho pelo mid na janela
  fsw = nº de sweeps FALHADOS de borda (2 lados): extremo do dia fura o max/min dos 15 dias anteriores
        E fecho volta para dentro em <=3 dias E sem aceitação (nenhum fecho além de 0.5×ATRd do extremo)
  vote_RANGE = cross>=3 E fsw>=1
FSM: entra RANGE após 2 dias consecutivos de vote; sai por ACEITAÇÃO (fecho > hi_janela+0.5 ATRd ou
< lo_janela−0.5 ATRd) ou cross<2 por 3 dias consecutivos. Estados: RANGE / NAO-RANGE (a candidata não
opina BULL/BEAR — é um DETETOR DE RANGE dedicado, compõe com v5/Layer1 em vez de os substituir).

## Medição (selada)
Por período GT: detetado? lag (dias desde início). Por barra dentro dos períodos: recall. Fora: FP rate
(com a reserva acima). Baselines: v5 atual e Layer1 (rótulo==RANGE) no MESMO árbitro. Null persistente
mesma fração ON (300 reps). Jackknife = leave-one-period-out (5 folds). DA obrigatório. Veredito=Cris.
Se prestar: NADA vai a live — próximo passo seria shadow no forward_labeler (campo range_v3) por ordem.

## VEREDITO PÓS-EXECUÇÃO (29/08, DA a7f5a9d) — MORRE, com BUGS_CRITICOS
1. Saída por ACEITAÇÃO do FSM = dead code (hi inclui o próprio dia ⇒ condição impossível; 0/68 saídas
   em 2 anos) — o manifest selado NÃO foi o que correu. Estado arrasta-se para dentro de breakouts.
2. Null por PERÍODO mata o headline: V3 está ON 54% do tempo; janelas aleatórias com a mesma fração
   detetam >=4/5 períodos com lag<=8d em 82% das reps. bacc 0.62 < null p95 0.662 < v5 0.63 < Layer1 0.65.
3. Overcall em trend: 23 dias de "RANGE" dentro da parabólica fev/2026 (+5.8 ATRd) + 2 blocos em quedas >4 ATRd.
4. R2 = doença estrutural do mid-ROLANTE pós-level-shift (mid contaminado pelos lows do range anterior).
SOBREVIVE: GT humano + null-por-período como árbitro canónico p/ qualquer V4; voto cru honesto em trend
(8% falso-voto — o dano era do FSM bugado); diagnóstico "range ancorado, não rolante" para o caso R2.
NÃO vai a shadow. Decisão de V4 (FSM corrigido + banda ANCORADA) = Cris.
