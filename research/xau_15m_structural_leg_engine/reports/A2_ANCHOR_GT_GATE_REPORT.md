# A2 GT GATE — REPORT + RELATÓRIO DE FALHAS SEM MAQUIAGEM (2026-07-09)
# STATUS: `BLOCKED_A2_GT_GATE`

Script: `a2_anchor_gt_gate.py` · Result: `results/a2_anchor_gt_gate_result.json` · looks no
`claims_ledger.csv`. Spec A2 v1.1 §9. Baseline a bater: F1.5 = PLT 6/10 · DM 4/11.

## PASSO 1 — dente automático (seleção r vs PLT/DM, 3 looks, sem contingência)
| r | PLT | DM | passa (≥9/10 e ≥10/11)? |
|---|---|---|---|
| **4** | **8/10** | **7/11** | NÃO |
| 6 | 7/10 | 4/11 | NÃO |
| 8 | 4/10 | 1/11 | NÃO |

**Melhora MATERIAL sobre F1.5 (6/10·4/11 → 8/10·7/11) mas fasquia NÃO atingida → BLOCKED, sem
expansão de grid (pré-registado).** Tendência monótona para r menor: a escada vive numa escala ≤4 ATR
— r<4 é exploração NÃO autorizada (grid fechado); fica como facto para decisão do Cris.
Misses r=4 — PLT: 2025-08-28 11:45 · 2025-09-11 10:15; DM: 2025-09-05 · 2025-09-15 · 2025-09-22 ·
2025-10-15.

## PASSO 3 — leitura ÚNICA (report-para-decisão-do-Cris, corrida com o MELHOR r=4, declarado —
nada congelado; consome os 13 BULL-2026 antes reservados, por ordem explícita)

### 42 VELA DE FUNDO — cobertura CAUSAL no instante da marca
`COVERED 11/42 (26%)` = 10 por região-fundo ativa + 1 por converted_support ·
`NEAR_MISS 10/42` (banda a ≤0,7 ATR) · `LATE_ONLY 18/42` · `MISS 3/42`
(2025-10-15 09:00 · 2025-11-04 23:00 · 2026-03-24 13:00).
Composição das 11 cobertas: 7 por regiões BULL_PULLBACK, 3 por RANGE_BOTTOM, 1 converted —
**(correção DA final #1) NÃO é recall condicional por família** (a família da marca coberta é
atribuída pela região que a cobriu = tautologia de construção); os falhados concentram-se em
MACRO_BEAR 0/14 e MACRO_BULL 0/11 (fundos em preço virgem).
**(DA final #5) Idade das regiões cobridoras: 2/10 COVERED_BOTTOM têm 200+ dias** (cobertura de
banda com 7 meses ≈ coincidência de preço) — cobertura estratificada por idade obrigatória em
qualquer v2. Base-rate (sonda DA, barras aleatórias): covered-análogo 4,0% / late 7,4% /
serviceable-análogo 11,4% vs observado 26,2/42,9/69,0% ≈ lift ~6× (caveat: null não extreme-matched;
lift real menor).
**(DA final #4) Passo 1 com null e densidade:** mining-null verbatim F1.5 (sonda DA, 200 trials,
offset ±3-10d): r=4 obs 15 hits vs null mediana 1, q95 3, **P=0,000** — a melhora não é acaso.
Density-adjusted: F1.5 10/74=0,135 · A2 r=4 15/92=0,163 (+21% por candidato; parte do salto de
recall vem de +24% candidatos) · **A2 r=6 11/44=0,250 (melhor precisão com 40% menos candidatos)**.

### Hipótese central — **EXPLORATORY_POSTHOC, NOT_FOR_DECISION (rótulo exigido pelo DA final #2)**
Métrica "entry-serviceable" NÃO pré-registada (inventada após ver 18/42); constantes do LATE
(|Δt|≤8h, |Δpx|≤1,0 ATR) improvisadas fora da spec (violação declarada de "nada improvisado");
"utilizável para reteste" NÃO verificado (ninguém checou reteste na janela 10-38h nem sobrevivência
da região). Vale como HIPÓTESE para o Cris, nunca como resultado.
**18/42 = LATE_ONLY: a região é criada PELA PRÓPRIA queda, known_at 16-36 barras depois do low
(latência GLOBAL das regiões, não das 18 LATE — DA final #7).**
A pergunta do gate ("o fundo aconteceu numa região JÁ conhecida?") tem resposta maioritariamente NÃO
— os teus fundos genuínos são maioritariamente PREÇO VIRGEM (capitulações/pullbacks fundos), não
retestes de âncoras pré-existentes. MAS o teu próprio catálogo diz que a ENTRY vive 1,5-59h DEPOIS
do fundo, no retest — ou seja, **a região LATE é exatamente a âncora que serviria a entry**: fundo
forma → região confirma (lat. p50 16 barras = 4h) → entry no reteste posterior (janela 10-38h).
O canal anchor-only não prevê o fundo; ancora a ENTRY. Métrica correta para F2 = "entry-serviceable":
LATE + COVERED = 29/42 (69%) têm região utilizável para reteste posterior. (Modo lag-curto 1,5-2,2h
continua estruturalmente inalcançável — declarado na spec.)

### 50 círculos (secundário)
COVERED 10/50 · NEAR 14 · LATE 21 · MISS 5 — mesmo padrão.

### 4 INVALIDO — FRACO: rejeitados só 1/4
3/4 tinham região-fundo ativa a conter o preço (o bounce raso em BEAR toca bandas antigas). **A camada
de regiões SOZINHA não rejeita os teus negativos** — a rejeição pertence ao ESTADO (LEG_DOWN/ACTIVE,
filtro capitulation) em F2. Registado sem desculpa.

### Precision / FP (r=4)
698 regiões-fundo · GT-touched 16 → **precision_gt 0,023** · 6,4 fundos/sem (GT ~0,7/sem) ·
FP 0,89/dia · traps pos96 36 · **retested→invalidated 92-98%** (o trap dominante do F2 confirmado).

## Diagnóstico por causa (FASE 5, miss a miss no result json)
- **Escala** (dominante no passo 1): melhora monótona até à borda do grid (r=4); degraus da escada
  ≤4 ATR. → decisão Cris: abrir r={2,3} como looks novos declarados, ou aceitar 8/10·7/11.
- **Largura de banda**: 10/42 NEAR_MISS a ≤0,7 ATR da borda — alargar banda converteria vários, mas
  é look novo + custo em precision (declarado, NÃO feito).
- **known_at tarde**: NÃO é defeito para o teu workflow de entry-no-retest (ver achado central);
  é defeito só para "prever o fundo" — pergunta que o A2 não se propõe responder.
- **Contexto/negativos**: INVALIDO 1/4 — regiões não carregam estado de perna; rejeição = F2.
- **Pullback detection/reclaim**: sem evidência de defeito (PLT 8/10 com matcher estrito).

## Ponte losers ≤10 (C6 obrigatória)
Precision_gt 0,023 e retested→invalidated 92-98% ⇒ **o ledger de regiões sozinho está a ~30-70× da
fasquia; F2 (estado da perna + capitulation filter + seleção dentro do reteste) tem de fechar o gap.**
Regiões = condição necessária (69% entry-serviceable), nunca suficiente.

## GT QUEIMADO (DA final #3 — consequência escrita)
O passo 3 correu com r=4 escolhido A OLHAR para o GT (gate1 BLOCKED ⇒ nada congelado; declarado).
**Todos os números do passo 3 = `NOT_FOR_DECISION` para seleção futura**: qualquer A2 v2 (r={2,3},
banda, idade) será avaliada sobre GT JÁ LIDO — 42 FUNDO (incl. 13 BULL-2026), 50 círculos e os
4 INVALIDO (já lidos 2×: BURN_F2 + esta leitura; a futura "rejeição" deles em F2 será in-sample
storytelling, não validação). Abrir r<4 = fit-de-parâmetro-ao-GT declarado (alerta do DA #5).
`no_entry_on_confirmation` = invariante ESTRUTURAL (first_valid_bar = conf+1 por construção), não
check falível — declarado (DA final #6); a proteção real é a ausência de camada de entry + exclusão
da barra de confirmação (essas SÃO checks falíveis, testados no guard).

## Confirmação negativa
Sem entry · sem backtest · sem indicadores · holdout consumido SÓ nesta leitura única por ordem
explícita · todos os looks no ledger · STOP após este gate.
