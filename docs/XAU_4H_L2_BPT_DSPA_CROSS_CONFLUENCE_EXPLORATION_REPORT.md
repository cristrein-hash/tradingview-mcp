# XAU 4H L2/BPT — DSPA CROSS-CONFLUENCE EXPLORATION REPORT

**2026-06-23.** Exploração cruzada AMPLA e disciplinada sobre a base 276. Diagnóstico; sem OOS/produção/promoção.
realR capado NUNCA árbitro (MFE uncapped só na avaliação). DA = PASS_WITH_LIMITATIONS (achou 1 miss meu valioso).

## O que foi testado
18 regras de confluência DECLARADAS (estruturais, não todas-combinações) em 5 famílias, com controles baked:
hypergeometric null + P1/P2 + Bonferroni (alpha 0.0028, 18 regras). Inventário (40+ features) + master matrix 276 construídos.
- **A bear-leg legitimacy** (5 regras) · **B supply interaction** (4) · **C reversal/runner capture** (5) · **D loser-cutting** (4) · **E recovery** (via métrica skipwin_recover).

## Resultado bruto: NENHUMA regra passa Bonferroni nem nominal 0.05
| status | n regras |
|---|---|
| STRONG_CANDIDATE | 0 |
| WEAK_REAL_STRUCTURE | 0 |
| CONDITIONAL_EVIDENCE | 2 (A2, A5) |
| OVERFIT_HULL_RISK (tiny-n) | 5 |
| DEAD_AS_PRIMARY_ALIVE_CONDITIONAL | 11 |

**Leads reais (n≥20):** A2 (bear + sweep/flush + reclaim) n=20 lift **1.53** p=0.116; A5 (LBB full) n=24 lift **1.44** p=0.139.
Sub-significativos (A2 precisaria n~29 p/ nominal). A família bear-leg-legitimacy é a única com lift recorrente real.

## O MISS que o DA achou — `svp_acc` (o lead mais forte, que eu over-gateei)
Minha regra A4 gateou `svp_acc` (SVP aceitando acima do VALOR, Família 6 da Camada 1) atrás de `bear` → colapsou (lift 0.99).
**Ungated, é o eixo mais forte do dataset:**
- `svp_acc` n=132, runner lift **1.28, p=0.0064**, captura **18/30 monumentais**, P1 28% / P2 38% (estável).
- **Sinal INDEPENDENTE:** `svp_acc SEM plain-accept` lift 1.31 p=0.047; `plain-accept (f3) SEM svp_acc` lift 0.78 p=0.91 (RUÍDO).
  ⇒ a aceitação-de-VALOR (volume profile) carrega o sinal; a aceitação plain de resistência é ruído. (Eu havia colapsado as duas em "accept".)
- Vive FORA do bear (`svp_acc & not bear` lift 1.41 p=0.028) — o bear-gate foi um erro de researcher-DOF.
- `svp_acc & st_up` (aceitação de valor + estrutura up): n=41 lift **1.50 p=0.035** P1 29%/P2 46%.
- **HONESTIDADE:** svp_acc p=0.0064 ainda FALHA o multiple-testing honesto (brute-force 56 cells, alpha 0.00089) e a Bonferroni-18.
  É o **CONDITIONAL lead mais forte, monumentais-rico — NÃO uma descoberta validada.**

## Famílias que NÃO acharam nada limpo
- **Supply interaction (B):** markup (B1 lift 0.97) e rejection (B2 loser_lift 1.08) não separam; B2 corta loser E runner proporcionalmente (sacrifica 24 runners + 7 monumentais).
- **Loser-cutting (D):** **0/86 loser-takes cortáveis limpos** — DA confirmou ABSÊNCIA real (nenhum combo SKIP com loser_lift≥1.3 & runner_lift≤0.6 & 0 monumentais existe), não artefato de threshold.

## Error map
| categoria | |
|---|---|
| SKIP_WINNERS recuperáveis (pelas take-rules condicionais) | 9/37 |
| SKIP_WINNERS ainda não | 28/37 |
| LOSER_TAKES cortáveis limpos | **0/86** |
| MONUMENTAIS total | 30/30 |
| MONUMENTAIS ameaçados por skip-rules | 9/30 |

## Comparação vs baselines
Nenhum lead supera materialmente os baselines de forma significativa. `svp_acc` (lift 1.28, 18/30 mon) supera o par
demand+acceptance (1.16) e o LBB original (1.45 mas n24 sub-sig) em cobertura+monumentais, e é mais limpo (ungated).

## Status final e o que preservar
- **`svp_acc` (acceptance above VALUE, ungated) = lead CONDITIONAL mais forte** — preservar como `WEAK_REAL_STRUCTURE/CONDITIONAL`, monumentais-rico (18/30), P1/P2 estável, mas falha MT honesto.
- **A2/A5 (bear-leg legitimacy) = CONDITIONAL secundário** preservado.
- **Loser-cutting = sem sinal limpo** (a 276, irredutível p/ corte).
- O resíduo é irresolvível p/ SIGNIFICÂNCIA a n=276; o ganho está em preservar svp_acc e refiná-lo, não em mais taxonomia.

## Candidato p/ próximo bloco (DA)
**Refinamento `svp_acc × structure` PRE-REGISTRADO como UMA hipótese** (próprio orçamento Bonferroni, p/ não ser descontado
como sobrevivente post-hoc de brute-force), testando explicitamente se remover o bear-gate generaliza. A2/A5 como secundário.
NÃO promover (calibração, não validação a 276). Sem OOS.

DA = PASS_WITH_LIMITATIONS. Outputs: `results/l2_bpt_dspa_cross_feature_inventory.csv`, `..._master_matrix_276.csv`,
`..._lead_ranking.csv`, `..._error_map.csv`, `..._confluence_da.csv`.
