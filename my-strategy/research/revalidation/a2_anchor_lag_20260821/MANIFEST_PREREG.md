# A2 ANCHOR-LAG — MANIFEST + PREREG (selado 2026-08-21, ordem Cris "FAZ RESEARCH DA ÂNCORA DO A2")

## Problema (medido no forward, não inventado)
A2 (pullback raso ≤2 ATR) disparou 0× em 21 sinais forward (05-21/08). Hipótese da limitação conhecida
(feedback_a1a2_leg_anchor_lag_limitation): o gatilho exige swing-low fractal CONFIRMADO (M_FRAC=3 → +3
barras após o fundo) + MB3 (fecho > high anterior) na barra CORRENTE (ei==N-1) — num pullback raso o
bounce resolve-se antes da confirmação, o MB3 chega "antigo" e o detect descarta.

## Dados (canónicos, verificados no dataset_registry ANTES de ler)
RAW 15M replay .gz do HD via raw_reader.series_flat (leitor canónico obrigatório) — 8 blocos ativos
2024-05-25→2026-05-25 (~47k barras). Regime gate OFF no replay (estuda-se a MECÂNICA do detetor, não o
gating; declarado). Detetor = a1a2_runtime.detect REAL importado (zero reimplementação).

## Perguntas seladas
Q1 — Quantos sinais A2 a mecânica atual produz em 2 anos de história? (0-baixo = confirmação estrutural.)
Q2 — GT mecânico de pullbacks rasos: fundos com depth∈[1.0,2.0] ATR (mesmas janelas HH_WIN/HH_GAP/PB_WIN
     do detetor). Para cada um: o MB3 confirmou a tempo? Quantas barras fundo→gatilho? bounce_pct no
     gatilho? Onde exatamente morre (sem-fractal / MB3-antigo / bounce-corrido)?
Q3 — DUAS variantes seladas (multiplicidade=2, sem varrimento):
     V1: M_FRAC 3→2 SÓ no ramo raso (fractal confirma 1 barra mais cedo).
     V2: gatilho RCL (reclaim EMA21: C>EMA e C>C[-1]) em vez de MB3 SÓ no ramo raso.
     Métricas por variante: nº A2 capturados · outcome 3R SL-first (matemática aprovada, SL low-real
     −0.1ATR) · painel completo · bounce_pct na entrada.
Null (para Q3): por fundo raso capturado, 300 entradas aleatórias na mesma janela TRIG_WIN com o MESMO
SL — WR-null 3R; a variante tem de bater o null (senão "qualquer entrada no dip raso ganha", não a regra).
Sub-janelas: por semestre. Sem OOS/cross-asset (trava dura).

## Vereditos possíveis (selados)
V-candidata SUPORTADA se: captura ≥15 A2 em 2 anos E WR-3R > WR-null do próprio conjunto E sumR>0 E
nenhum semestre catastrófico (≤−5R). Resultado positivo NÃO vai a produção: vira proposta A2.1 c/ painel
p/ aprovação do Cris + forward próprio. Negativo = A2 documenta-se como estruturalmente não-capturável
por esta família de gatilhos (e morre a expectativa, que também é valor).
A1 (o que está aprovado e a pagar) fica INTOCADO em qualquer cenário.
Claims só via claims_ledger.jsonl. DA obrigatório antes do relatório.
