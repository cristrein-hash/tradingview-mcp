# RANGE V4 — banda ANCORADA (prereg selado 2026-08-28; aprovado Cris "DEPOIS FAZ V4 SIM")
ÚLTIMA candidata desta família (declarado). Corrige os 2 defeitos provados do V3:
(A) FSM exit dead-code → aceitação agora medida contra banda ANCORADA na entrada (possível de disparar);
(B) mid rolante contaminado pós-breakout (doença R2) → janela do voto ANCORA no último LEVEL-SHIFT.

## Candidata única (diária causal; params herdados do V3 onde existem, 1 regra nova de âncora)
LEVEL-SHIFT (aceitação estrutural): fecho > max(DH janela W anterior) + 0.5×ATRd ou simétrico abaixo.
Janela do voto = dias desde o último level-shift, capada a W=15, mínimo 5 dias.
vote_RANGE = cross>=3 (fechos × mid da janela ancorada) E fsw>=1 (sweeps falhados 2 lados, iguais ao V3).
FSM: entra após 2 votes consecutivos; NA ENTRADA fixa banda hi0/lo0 = max/min da janela ancorada.
SAI por: fecho > hi0+0.5×ATRd OU fecho < lo0−0.5×ATRd (aceitação REAL, banda fixa) OU cross<2 por 3 dias.
Sem outros knobs. Zero sweeps de parâmetros.

## Medição (idêntica ao V3 + as armas do DA V3, seladas)
Árbitro = gt_human.json. recall/FP-fora/bacc + por período (det/lag/cobertura) + fração ON do tempo +
NULL POR PERÍODO (300 reps, episódios ON realocados: p de >=4/5 com lag mediano <= o real) + null
persistente por barra + episódios ON dentro de cada período (flicker) + blocos FP >=5d listados com net
ATRd (overcall em trend = desqualificante, limiar 30% dos dias-em-bloco em |net|>=3 ATRd) + jackknife
leave-one-period-out. Baselines v5/Layer1 já medidos (results_v3). DA obrigatório. Veredito = Cris.
Se falhar: família OHLC-mecânica ENCERRADA; range passa para o lane reader/E0 multi-campo.

## VEREDITO PÓS-EXECUÇÃO (28/08, DA a7bf890) — MORRE; FAMÍLIA ENCERRADA conforme prereg
Execução LIMPA (FSM exit dispara 51/71; causalidade PASS por teste de prefixo; overcall corrigido 11%).
Mas: null-por-período p=0.73 (o acaso com o mesmo orçamento ON reproduz o perfil de deteção em 73% das
reps); bacc 0.602 < v5 0.63 < Layer1 0.65; R2 estruturalmente indetetável (2 level-shifts internos em 13d
consomem o warm-up); banda fixa sai cedo nos ranges longos (EXIT dentro do GT em R4/R1) e re-entrada
quase impossível (fsw exige sweep fresco). Família OHLC-mecânica ENCERRADA — 4 candidatas, 4 mortes
limpas. Range passa ao lane reader/E0 multi-campo quando o Cris ordenar.
REGISTO (hipótese, não evidência): combo R1 lag<=8 + R3 lag=0 (os 2 períodos cegos p/ v5+Layer1) tem
p=0.199 — cross+fsw ancorado pode servir como FEATURE dentro do reader para ranges curtos/recentes.
