# FULL 276 — MACRO READER + BEAR-LEG BLOCK v3 — RELATÓRIO DIAGNÓSTICO

**2026-06-22.** Bloco fechado. Diagnóstico na POPULAÇÃO completa 276. Sem produção, sem AGG_v2, sem OOS, sem
SLIM, sem chart/MCP, sem promoção. Causal: daily/weekly/regimeB shift D-1; 4H as-of-bar. outcome/realR APENAS
em avaliação. Scripts: `full276_macro_bear_v3.py`, `full276_eval.py`, `full276_confluence.py`.

## 1. Escopo e travas
Diagnóstico apenas. **SMOKE PASS: pipeline 276 reproduz o gate v3 committado nos 62 = 62/62** (provenance da
reimplementação validada). Audit população: n=276, cronológico, 0 duplicados, 0 leg UNKNOWN, realR 276/276.

## 2-3. Macro Reader + Bear-Leg Block v3 aplicado — resultado cronológico
| | allow | WR | sumR | avgR | PF | maxDD | L-streak |
|---|---|---|---|---|---|---|---|
| baseline (sem gate, 276) | 276 | 49.3% | **+84.2** | 0.30 | 1.58 | 18.7 | 7 |
| **Macro+Bear v3 (allowed)** | **195** | 50.3% | **+75.5** | 0.39 | 1.75 | 15.2 | 8 |

**O gate REDUZ o sumR (84.2→75.5)** enquanto melhora modestamente PF (1.58→1.75) e maxDD (18.7→15.2).
Bloqueia 81 (62 bear-markdown + 18 corrective + 1 range-chop). Por leg: BULL n=106 WR46%, RANGE n=52 WR58%.

## 4. Layer ablation (o bear-markdown é o custo)
| config | allow | WR | sumR | PF | maxDD | L-streak |
|---|---|---|---|---|---|---|
| macro_reader_only | 276 | 49.3 | 84.2 | 1.58 | 18.7 | 7 |
| +bear_markdown | 214 | 50.0 | **75.3** | 1.68 | **19.1** | **9** |
| +range_chop | 213 | 50.2 | 76.4 | 1.70 | 19.1 | 8 |
| +corrective | 195 | 50.3 | 75.5 | 1.75 | **15.2** | 8 |

`+bear_markdown` **derruba sumR e piora DD/streak** (bloqueia 12 winners incl. monumentais +3.9/+3.54/+3.32R).
`+corrective` ajuda só o DD. ⇒ reconcilia com a memória **legbear-block RETRATADO no 276**.

## 5. Error analysis
- winners bloqueados: 38 (sumR perdido **+52.8R**), incl. 3 monumentais.
- losers preservados: 97 (−100.6R) = o resíduo micro-top/late-top aceito (não-separável).

## 6. Confluência exaustiva — verificação conjunta (Tarefa 4)
**(a) Sinais PRÉ-ESPECIFICADOS dos 62 → TODOS NULOS no 276:** clean_sky lift +0.007, sup_cat CLEAN_SKY −0.019,
no-near-supply +0.037, legpos90≥80 −0.025, rsi_1d≥65 +0.026. **Não estabilizam na população = eram ID-fit.**

**(b) Melhor confluência exaustiva 1/2/3-way:** `bub_buy_sell_ratio<=1 AND leg==MACRO_BULL_LEG AND
supply_blocks_2ATR>=1` → 21 trades, 20 losers (precisão 0.952, lift +0.455). Permutation p=0.020, temporal
P1 0.92/P2 1.0, dispara todo ano. **PARECIA robusto — mas a DA REJEITOU:**
- termos isolados ~nulos: ratio≤1 **+0.046**, BULL **+0.040**, supply_blocks **−0.010 (NEGATIVO)**; a precisão
  é **fabricada por encolhimento de interseção = HULL over-especificado**.
- **18/21 têm ratio==0** ⇒ efetivamente 1 feature ("no-buy-bubbles", tick-volume **não-confiável**).
- permutation null **mediana +0.378, max +0.503 > real +0.455** ⇒ ruído puro atinge isto; p=0.020 borderline,
  **não passa Bonferroni cross-arc**; n efetivo ~15 episódios seriais (Wilson CI precisão [0.77,0.99]).
- **look-ahead não-verificado** em bub/OB (classe repintável, SHIFT1 não confirmado) = UNTRUSTED (caso A1').
- **re-descobre o RETRATADO** `volume×1D-bear` (tick-volume artifact) + `legbear-block` no 276.

## 7. Comparação baseline vs confluence
`results/l2_bpt_full276_macro_bear_v3_vs_confluence.csv` — o "+candidate" mostra ΔsumR+20/ΔPF+0.45/ΔDD−5.5
**mas é REJEITADO como hull overfit**. ⇒ **NO_PROMOTABLE_CONFLUENCE_FOUND.**

## 8. DA (`..._da.csv`)
PASS em escopo/n/joins/smoke/permutation/baseline-honesto; **FAIL_candidate em id-fit + multiple-testing**;
PARTIAL em features-causais (bub/OB SHIFT1 não confirmado). Veredicto candidato: **OVERFIT_REJECT**.

## 9. Conclusão
- **Gate base na população 276 = `BASELINE_WEAK`** — reduz sumR, bloqueia winners/monumentais, melhora só
  PF/DD marginalmente. O ganho dos 62 era artefato de teaching-set curado (não-representativo).
- **`NO_PROMOTABLE_CONFLUENCE_FOUND`** — os sinais parciais dos 62 são nulos no 276; a melhor confluência
  exaustiva é hull overfit re-descobrindo achados já retratados.
- **`NEEDS_NEW_FEATURES`** — nenhuma feature/confluência atual separa losers de winners na população com
  robustez real. Re-confirma: o resíduo é auction-irredutível com o feature set atual.

## 10. Próximos passos recomendados
- NÃO operacionalizar o gate bear-leg na população (BASELINE_WEAK).
- NÃO promover o candidato (hull; precisaria 1º auditar SHIFT1 de bub/OB, depois OOS/cross-asset EUR/USOUSD).
- Reabrir só com **nova informação estrutural** (OHLC contíguo/geometria) ou **volume REAL (Session VP)** no
  lugar de tick-volume, conforme memória. Permutation + Bonferroni cross-arc = guarda canônica daqui pra frente.
