# RANGE V2 — SAÍDA DE BEAR (prereg selado 2026-08-28 ANTES de correr; aprovado Cris "APROVADO V2")
Causa-raiz do estudo V1: stable-BEAR em latch (sai só com 5 rawS consecutivos não-BEAR) manteve BEAR
6 semanas num range real; cont falso nesses dias. Candidata V2 ataca SÓ o mecanismo de saída.

## Candidata ÚNICA (predicados existentes, zero thresholds novos além do N selado)
UNLOCK: se cur=="BEAR" e, no dia i: (a) NENHUM bl=True nos últimos N_UNLOCK=10 dias
(bl = DC[j] < min(DL[j-15:j-2]), o mesmo predicado de entrada em BEAR — negação simétrica) E
(b) DC[i] >= E50[i] (fecho de volta na média) ⇒ cur="RANGE" imediato. BULL continua a exigir as suas
condições normais. Override dd6% INTOCADO (DA: não é culpado). N_UNLOCK=10 = 2×Kbear, fixado agora.

## GT v2 (correções do DA, seladas antes de olhar resultados)
- ATR-d REAL do resample diário do motor (TR/atrd), não aproximação 6×TR4h.
- Critério: net<=40% da largura em K=30 barras 4H (componente vivo do V1) E largura<=4 ATR-d REAL.
- Duração mínima de segmento RANGE = 12 barras 4H (2 dias); segmentos menores viram TREND (anti-flicker).

## Medição
bacc por barra vs GT-v2 + null persistente (mesma fração, 300 reps) · deteção/lag por segmento ·
jul-ago/2026 descritivo (não pontua) · censo A1/A2 relabel (exploratório) · jackknife semestral ·
side-effect do motor: ordem patched-primeiro (bug V1 não se repete). DA obrigatório. Veredito=Cris.

## VEREDITO PÓS-EXECUÇÃO (28/08, DA a97315e)
V2 MORRE. (1) cond_b (fecho>=E50) = ZERO dias em julho (gap −1.1 a −3.1 ATR-d; E50 desce devagar num
range 20% abaixo do pico) — candidata estruturalmente incapaz, ganho real ~4 dias (05-08/08). (2) Premissa
FALSIFICADA: o rawS cru disse BEAR todo o julho (caminho bef: DC<E50); o latch custou ~5 dias, não 6
semanas — o diagnóstico do DA V1 estava errado e a medição dia-a-dia corrigiu-o. (3) GT-v2 rotula julho
como só 11% RANGE — o árbitro mecânico (net 5 dias) não codifica o range multi-semana que o Cris viu.
CONCLUSÃO ESTRUTURAL: 2 candidatas + 2 GTs falharam porque a tarefa "range = f(OHLC diário)" está mal
posta — descarta zonas/liquidez/choch por TF que definem o range real (erro nº7 anti-miopia).
CAMINHO HONESTO (aguarda Cris): (a) GT humano — Cris rotula os ranges vividos (padrão catalog_manual_
tags_20260707) e só depois se mede qualquer detetor; e/ou (b) range como estado MULTI-CAMPO do reader/E0
existente (consumir, nunca reconstruir), não rótulo de um indicador OHLC. NÃO gastar V3 contra GT mecânico.
