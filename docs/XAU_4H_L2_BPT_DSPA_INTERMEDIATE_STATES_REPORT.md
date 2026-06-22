# XAU 4H L2/BPT — DSPA CAMADA 4: INTERMEDIATE STATES REPORT

**2026-06-23.** Aggregation / Intermediate State Reading. Base única 276. Diagnóstico/calibração. Sem produção/OOS/
promoção. realR capado NUNCA árbitro (MFE uncapped só na avaliação). DA = PASS_WITH_LIMITATIONS.

## 1. Join seguro (Tarefa 1)
276/276 em todas as fontes (dspa_path, macro_engine, indicator_v2, decisions/prior, macro_phase, uncapped-EVAL-only).
bear_leg refined parcial (n=29 = universo bear_leg, por design). `l2_bpt_dspa_aggregation_coverage.csv`.

## 2. Distribuição dos 9 estados intermediários
MARKUP_THROUGH_SUPPLY 90 · STRUCTURAL_RISK_SL_PROBLEM 51 · LEGITIMATE_BEAR_BUY 37 · BULL_PULLBACK_CONTINUATION 32 ·
SUPPLY_REJECTION_TRAP 28 · BEAR_PULLBACK_TRAP 23 · UNKNOWN_CONFLICT 13 · REVERSAL_RUNNER 2.
Confidence: high 130 / med 100 / low 46.

## 3. Avaliação diagnóstica (outcome SÓ aqui) — base runner 26% / loser 61% / 30 monumentais
| state | n | runner% | rLift | loser% | lLift | monum |
|---|---|---|---|---|---|---|
| **LEGITIMATE_BEAR_BUY** | 37 | **38** | **1.45** | 54 | 0.89 | **6** |
| **BEAR_PULLBACK_TRAP** | 23 | **13** | **0.50** | 65 | 1.07 | **0** |
| MARKUP_THROUGH_SUPPLY | 90 | 27 | 1.02 | 58 | 0.95 | 14 |
| SUPPLY_REJECTION_TRAP | 28 | 25 | 0.96 | 71 | 1.17 | 1 |
| REVERSAL_RUNNER | 2 | 50 | 1.92 | 0 | 0 | 0 |
| BULL_PULLBACK_CONTINUATION | 32 | 25 | 0.96 | 62 | 1.03 | 2 |
| STRUCTURAL_RISK_SL_PROBLEM | 51 | 27 | 1.05 | 65 | 1.06 | 7 |
| UNKNOWN_CONFLICT | 13 | 8 | 0.29 | 62 | 1.01 | 0 |

## 4. As perguntas-chave
**LEGITIMATE_BEAR_BUY vs BEAR_PULLBACK_TRAP — DISTINGUÍVEIS (real, fino).** 38% vs 13% runner (Fisher contraste
p=0.045; concentração LBB p=0.064 — quase). **SOBREVIVE P1/P2 (39%/37% vs trap 12%/17%)** = estrutural, não
single-period (o ponto mais credível do DA). LBB captura **6 monumentais**, trap **0**. **Esta é a distinção do
resíduo que o v1 sub-reader-7 NÃO conseguiu** (30.4% vs 23.7% sobrepostos) — agora separa via path features
(sweep/flush/acceptance) + convergência. **MAS dominada pelo par `demand_defended`(95%)+`acceptance_above`(92%);** as
8 evidências extras adicionam incremento REAL mas pequeno (par sozinho bear+demand+accept = n76 30% p=0.205 → convergência
estreita p/ n37 38%). Carriers internos `flush_V`(n12)/`sweep_low_reclaim`(n4) pequenos demais p/ confiar. NÃO promovível.
**MARKUP_THROUGH_SUPPLY vs SUPPLY_REJECTION_TRAP — FRACO.** markup runner 27%≈base; rejection loser-lift 1.17. Modesto.

## 5. Correção de mislabel (potencial, não policy)
skip-winner recovery potential 15 (runner em SKIP-engine, DSPA take-leaning) · loser-take cut potential 12.
TAKE-leaning agregado n=161 runner 29% lift 1.12 **null_p=0.107** (não-forte no agregado; o valor está nos estados
específicos, não no agregado). UNKNOWN_CONFLICT corretamente low-edge (8%, lift 0.29).

## 6. Quais prior layers agregaram vs redundantes (DA)
- **Backbone (decisivas frequentes):** acceptance (F3/F6), momentum, supply, structure (F4), macro_phase.
- **Cor condicional (raras, alta especificidade, nunca veto-redundante):** bearleg-refined (23), bottom_turn (13), smc (9), capit (8), bubbles (7) — adicionam cor a poucos LBB/REVERSAL, raramente decisivas isoladas.
- **Sub-exploradas (FALHA a corrigir):** só **9 das 30** path features consumidas (estados categóricos); os 21 sub-features
  numéricos (`f4_CHoCH`, `f1_sweep_depth`, `f2_velocity`, `f6_dist_poc`, `f5_range_pos_1d`) IGNORADOS — informação descartada.

## 7. Falhas principais
(1) LBB pair-dominado (demand+acceptance carregam a maior parte do sinal-base; convergência adiciona pouco). (2) n fino
(37/23) — p≈0.06, não edge validada. (3) 21/30 path features ignoradas. (4) state→support authored pelo assistant
(risco de design-fit nos carriers pequenos flush_V/sweep, mitigado pela estabilidade P1/P2). (5) MARKUP/REJECTION fraco.

## 8. Conclusão (NÃO automation-ready, NÃO feature-dead, NÃO human-endpoint)
Primeira separação REAL (ainda que fina e estrutural) do legitimate-bear-buy vs trap — o resíduo que tudo antes falhou.
Causal, sem outcome leak, multi-fatorial genuíno, prior layers como evidência condicional (não veto). Intermediário apenas;
NÃO convertido em TAKE/SKIP. **Próximo bloco (DA):** stress da separação LBB com permutation null (par vs convergência completa,
banda de confiança, quantificar o incremento das 8 evidências sobre o par); SE o incremento não separa de ruído a n=37,
a leitura honesta é "demand+acceptance em bear leg" é o sinal inteiro e a taxonomia 9-estados está over-specified —
então explorar os 21 path features numéricos ignorados ANTES de mais taxonomia. Tudo DENTRO dos 276, sem OOS/promoção.

DA = PASS_WITH_LIMITATIONS (sem outcome leak; multi-fatorial real; separação real-mas-fina; prior layers condicionais).
Outputs: `results/l2_bpt_dspa_intermediate_states_276.csv`, `..._intermediate_evidence_276.jsonl`,
`..._aggregation_coverage.csv`, `..._aggregation_da.csv`.
