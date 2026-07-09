# L1 SL V1 Scanner Reconciliation · Devil's Advocate

**2026-07-09.** DA da reconciliação do `scanner.py` para o SL oficial V1 (`zone_OB_low − 0.1ATR`). Read-only sobre dados; sem produção/runtime/chart. Output: `l1_sl_v1_scanner_reconciliation_result.json`.

## Source
`scanner.py` (edit V1) + `l1_approved34.json` (outcomes canónicos V1 do estudo-34) + `l1_FINAL_regime_gated.json` (FINAL-24). RAW via `scanner.build_series()`. **Zero SLIM/proxy.**

## Diff lógico (antes → depois)
`structural_sl(S,i)`:
- **antes:** `base = max(dz[1], sw6) if dz else sw6` → `max(zone_OB_low, swing6_low) − 0.1ATR` (SUPERSEDED).
- **depois:** `base = dz[1] if dz else sw6` → **`zone_OB_low − 0.1ATR` (V1 oficial)**; fallback swing6 só sem zona.
- Regra antiga preservada em comentário como SUPERSEDED. **Target inalterado: `entry + 3R`** (`TARGET_R=3.0`).

## Antes/depois (métricas)
| | antes (max-SL, doc) | depois (V1 oficial) |
|---|---|---|
| scanner-31 res | 17 TARGET / 13 STOP / 1 TIME | **15 TARGET / 14 STOP / 2 TIME** |
| scanner-31 sumR | +40.0R | **+34.2R** |
| scanner-31 WR / PF | — / 4.08 | **55% / 3.44** |
| monumentais (MFE≥6R) | 5/5 | **5/5 preservados** |

## Métricas pós-reconciliação
- **FINAL-24:** 24 · 18W/6L · 75% · **+45.2R** — INALTERADO (saved, sob V1).
- **Estudo-34:** 34 · 53% · **+35.2R** — INALTERADO (saved, sob V1).
- **Scanner-31 sob V1 (novo artifact):** 31 · 17W/14L · 55% · **+34.2R** · PF 3.44 · 5/5 monumentais. **Todos os 31 casam com o estudo-34 por unix-ts** (unmatched=0). Os 3 do estudo-34 fora dos 31 = exhaustion-blocked (`2023-10-23, 2024-04-10, 2025-04-01` = #26/#31/#47).

## Impacto
O número canónico do scanner-31 **sob o SL oficial V1 é +34.2R, NÃO +40.0R**. O +40R do doc estava sob a regra SUPERSEDED (max-SL, mais larga). V1 (zone_OB_low, mais apertado) resolve para +34.2R (15T/14S/2T). **Os 5 monumentais preservam-se sob V1.** As métricas APROVADAS (FINAL-24, estudo-34) não mudam (são saved, já sob V1).

## Causalidade / integridade
- V1 SL usa `demand_zone` (causal, bar i). Nenhum look-ahead adicionado. Outcomes do artifact = canónicos V1 do estudo-34 (match por unix-ts).
- **Cross-check forward-sim (first-touch, cap 200):** 29/31 batem; 2 diferenças TIME-vs-TARGET (`2024-08-12`, `2025-11-27`) = **diferença de HORIZONTE** (o cutoff TIME do estudo é mais curto que o meu sim de 200 barras; o trade acaba por tocar target depois). O artifact usa o outcome/R canónico TIME do estudo — **documentado, não é erro de dados.**

## Verdict: **PASS**
scanner.py alinhado a V1; FINAL-24 (+45.2R) e Estudo-34 (+35.2R) inalterados; scanner-31 tem artifact salvo e reproduzível sob V1 (+34.2R); divergências = 0. Regra de SL NÃO reaberta. Nenhum runtime/produção/chart/Telegram tocado.
