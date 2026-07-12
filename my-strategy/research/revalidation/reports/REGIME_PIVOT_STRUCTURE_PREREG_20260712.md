# PRÉ-REGISTO — FEATURES ESTRUTURAIS DE PIVOT + DECOMPOSIÇÃO A/B (mecanismo novo)

> Escrito 2026-07-12 ANTES de rodar (prompt Cris/Claude-chat). STATUS: `PREREG_FROZEN`.
> Diagnóstico assumido: features atuais = deslocamento em janela fixa (informação esgotada —
> dial soma-zero provado no harness anterior). O que falta = ESTRUTURA (sequência de pivots).

## Métrica e barra
- Métrica ÚNICA: balanced accuracy vs GT congelado `REGIME_GT_CRIS_4H_20260712.json`
  (sha be4a9d6f…, bordas ±3d excluídas). P&L FORA do loop.
- **Barra a bater: balanced 73,4 na metade CEGA 2023-26** (baseline K5/K5/dd6). Não o 64,1 agregado.
- Split: desenho 2020-22 → congela (regra: max balanced in-sample) → teste cego 2023-26.
- Alvo realista declarado: 75-85 (dois humanos não concordam 100% em fronteiras).

## Definição CAUSAL de pivot (anti-repaint — risco central declarado)
- Pivot HIGH no bar i (4H): `H[i] > H[i−k..i−1]` e `H[i] > H[i+1..i+k]` — **confirmado apenas no
  FECHO do bar i+k** (`confirmed_at = open(i+k)+14400`). Pivot LOW espelhado.
- Um pivot NUNCA é revisto após confirmado. Feature no instante t usa SÓ pivots com
  `confirmed_at ≤ t` (close-only-causal, mesma convenção do fix ovr_at).
- DA lookahead-only OBRIGATÓRIO no código ANTES de qualquer medição.

## Features estruturais (ordinais) no instante t
Sobre os últimos N/2 highs e N/2 lows confirmados ≤ t:
- comparações consecutivas de highs: HH / LH / EQH (igual se |Δ| ≤ ε·ATR14_4H do pivot mais recente)
- comparações consecutivas de lows: HL / LL / EQL
- `score = (#HH+#HL) − (#LH+#LL)` sobre as N comparações
- veto de igualdade: `#EQH+#EQL ≥ 2` → RANGE (ataca o recall RANGE 53,1)
- distância à última perna confirmada em ATR: REPORTADA apenas (não entra na regra — declarado)

## Variantes (fechadas)
- **V1 (Hipótese 1, estrutural puro 3-classes)**: BULL se score ≥ S · BEAR se score ≤ −S ·
  senão RANGE; veto de igualdade → RANGE.
- **V2 (Hipótese 2, decomposição A/B)**: A (direcional?) = |score| ≥ S E sem veto de igualdade;
  B (direção, só se A=sim) = rótulo direcional do baseline se ele disser BULL/BEAR, senão
  sinal do score. A=não → RANGE.
- Comparação: V0 = baseline atual (3-classes state machine).

## Grelha (FECHADA — não se acrescenta depois)
`k ∈ {3, 5}` × `N ∈ {4, 6}` × `S ∈ {2, 3}` × `ε ∈ {0.5, 1.0}` = 16 combos × 2 variantes = 32 linhas.

## REVISÃO r2 (ordem Cris 2026-07-12 — "NÃO ACEITO O RESULTADO... parâmetros não discriminam estrutura MACRO. REVISAR MEDIÇÃO")
Diagnóstico da falha r1: escala. Fractal k=3/5 gera 190-312 pivots/ano; a janela "bear gigante"
(ago/20→abr/21, ~8-10 swings a olho) continha **129 pivots k=5** — com N=4-6 comparações a memória
estrutural era ~1 semana. r1 mediu MICRO-estrutura, não a estrutura macro do GT. RESULTADO r1
INVALIDADO COMO TESTE DA HIPÓTESE (não do código — causalidade DA 6/6 mantém-se).
Grelha r2 (FECHADA, pivots à escala macro; resto igual — N/S/ε/V1/V2):
- **zigzag-ATR causal** (mesma máquina de ciclos do A2/15M): perna confirmada quando o preço
  reverte ≥ `R·ATR14_4H` do extremo; pivot = o extremo; `confirmed_at` = fecho da barra que
  confirma a reversão; nunca revisto. `R ∈ {4, 6, 10}`.
- **fractal largo**: `k ∈ {12, 24}` (2/4 dias por lado; confirmação atrasa k barras — declarado).
= 5 definições de pivot × N{4,6} × S{2,3} × ε{0.5,1.0} × {V1,V2} = 80 linhas. Barra/split/DA/regras
idênticos ao r1. DA obrigatório no código novo (zigzag) ANTES de medir.

## Regras
- Reportar a CURVA completa (recall/falsos por estado), não escolher ótimo sem mostrar ao Cris.
- Detector atual INTOCADO. NADA commitado sem ordem do Cris.
- Falhou a barra no cego → falhou; nova hipótese = novo pré-registo (baliza não se move).
- Dados: RAW only (raw_4h_ohlc.jsonl, extração verificada do HD GUTS LACIE).
