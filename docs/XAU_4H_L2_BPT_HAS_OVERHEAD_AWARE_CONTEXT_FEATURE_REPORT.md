# HAS_OVERHEAD-AWARE CONTEXT FEATURE — RELATÓRIO DIAGNÓSTICO

**2026-06-21.** Diagnóstico. Sem outcome como predicado. C fora do fit. Engine/decisions/produção intocados.
Spec c9f2a20. Thresholds principled DECLARADOS (não ID-fit; sem re-tuning para passar âncoras).

## Provenance (gate de segurança)
`supply_broken_before`/`rejected_before` confirmados CAUSAIS: janela `range(i-12, i+1)` inclusive, nunca >i
(`_before_entry`). Sem look-ahead. Externas não usadas nesta feature.

## A/B/C
A(bull cortado)=26 · B(bear aceito)=18 · C(ambíguo, FORA do fit)=18.

## Distribuição dos estados composite
- **A:** VALID_OVERHEAD_SUPPLY_RISK 15 · NO_OVERHEAD_BULLISH 6 · MARKUP_BREAKING_SUPPLY 3 · SUPPLY_COLADA 2.
- **B:** VALID_OVERHEAD_SUPPLY_RISK 16 · NO_OVERHEAD_BULLISH 1 · MARKUP 1.
- **C:** VALID_RISK 11 · NO_OVERHEAD 5 · SUPPLY_COLADA 2.

## Comparação vs dist_supply puro
| método | A_recall(bull) | B_block | bal |
|---|---|---|---|
| dist_supply puro (<2.33) | 0.73 | 0.89 | **0.81** |
| HAS_OVERHEAD composite | 0.35 | 0.89 | **0.618** |

**O composite É PIOR no agregado** (bal 0.618 < 0.81) e na recall de A (0.35 < 0.73).

## Anchor check
- **preserve: composite 7/18 (PIOR que dist_supply puro 9/18)** — falha T34/T35/S20/S24-S27/T41/S35-S37.
- **block: composite 2/2 (MELHOR que puro 1/2)** — agora bloqueia S40 corretamente.

## Robustez
full bal 0.618 · **shuffle-null P(null≥real)=0.070 (NÃO-significativo a 0.05)** · 2020-23 bal 0.549 · 2024-26 bal 0.731 (B late n=3, frágil). n=44.

## Diagnóstico da falha (estrutural, honesto)
**15/26 do A-set caíram em VALID_OVERHEAD_SUPPLY_RISK** porque a regra exige `supply_broken_before=1` para
MARKUP — mas estes 15 bull-winners têm `broken_before=0` (entram com supply próxima SEM break registrado na
janela de 12 bars). O composite **consertou 2 lados** (no-overhead: 6 A→NO_OVERHEAD_BULLISH; block: S40/T40
→ 2/2) **mas regrediu o lado close-supply-bull** que o dist_supply puro pegava.

## CONCLUSÃO: CANDIDATO FRACO / EVIDÊNCIA INSUFICIENTE (n=44)
- O `has_4h_supply_overhead` é gate **NECESSÁRIO** (prova: resolve no-overhead/ATH + block side) **mas NÃO suficiente**.
- O sinal positivo para **close-supply bull-run NÃO é `broken_before`** (raro nestes winners) — provável é **MOMENTUM/trend** (close-supply + momentum forte = markup) ou **posição no frame D1**. Hipótese para próximo bloco, **NÃO testada aqui para evitar ID-fit** (re-tunar até âncoras passarem seria overfit).
- shuffle-null não-significativo + held-out frágil → **calibração, não validação**. Nada promovido.

## Próximo passo recomendado (não-agora)
Revisar a regra MARKUP: `has_overhead=1 + dist<markup + MOMENTUM_forte → MARKUP` (momentum desambigua close-supply,
NÃO broken_before), com mais dados / held-out independente. Manter has_overhead como gate. Sem re-tuning aos 44 IDs.
