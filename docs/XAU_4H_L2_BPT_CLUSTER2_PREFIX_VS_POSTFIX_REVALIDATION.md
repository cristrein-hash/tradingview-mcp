# XAU 4H L2/BPT — CLUSTER 2: PRE-FIX vs POST-FIX REVALIDATION — 2026-06-23

Revalidação das leituras do Cluster 2 (macro negativo) sobre o backbone CAUSAL (commit 1267c8d) vs a versão
PRE-FIX contaminada. Base: `results/raw_rebuild_cluster2_postfix/*` vs `raw_rebuild_cluster2/*` (histórico).
SANITY_PROBE — diagnóstico, não gate.

## Placar por episódio (audit pós vs pré)
| EP | sub | pré-fix | pós-fix | mfe_R / exit | nota |
|----|---|---|---|---|---|
| 5826 | A | CONFIRMED | **CONFIRMED** | 16.73R runner | washout construtivo |
| 1623 | A | REFUTED | **CONFIRMED** | 0.31R stop | "comprador ausente/base incompleta" bateu o stop |
| 4401 | B | REFUTED | **REFUTED** | 10.31R monster | wall virou fuel (reader hedgeou via anchor-warning) |
| 3825 | B | INSUFFICIENT | **CONFIRMED** | 0.96R stop | "rejeição em curso" rolou exato |
| 1522 | C | REFUTED | **MODIFIED** | 5.65R runner | direção certa, upside sub-pesado |
| 1873 | C | CONFIRMED | **CONFIRMED** | 1.2R stop | trap mais limpo (div bearish) |
| 5627 | C | REFUTED | **REFUTED** | 5.96R runner | causal melhorou calibração (hedge), direção ainda erra |
| 1775 | C | INSUFFICIENT | **CONFIRMED** | 0.53R stop (−110/40b) | "ainda capitulando, sem CoC" → queda mais profunda |
| 3949 | D | CONFIRMED | **CONFIRMED** | 6.62R runner | open-sky washout |
| 3929 | D | CONFIRMED | **CONFIRMED** | 0.05R stop (−38/20b) | push-into-wall rejeitado |

Pré-fix **4C/4R/2INSUF** → pós-fix **7C/1M/2R**. **Melhora marcada de calibração** — o backbone causal +
re-leitura recuperaram 1623, 3825, 1775 (de REFUTED/INSUFFICIENT → CONFIRMED) e 1522 (→MODIFIED). Os 2 REFUTED
residuais (4401, 5627) são exatamente os WALL-próximos que correram, onde o reader já hedgeava.

## Classificação de LENTES (pós-fix)
| Lente | Status |
|---|---|
| **weekly-negativo NÃO é veto** (5826 16.73R, 3949 −0.6657 correu 6.62R) | **POSTFIX_CONFIRMED** |
| **geometria preço×supply é o eixo SOB macro casado** (3949 SUPPLY_FAR runner vs 3929 SUPPLY_BLOCKS stop, mesmo dia) | **POSTFIX_CONFIRMED (prova mais limpa; agora SEM look-ahead)** |
| 5826 vs 1623 — desempate por esforço de volume real (reclaim-com-comprador vs grind-sem) | **POSTFIX_CONFIRMED** |
| 4401 vs 3825 — ambos rotulados wall; só 3825 (rejeição-em-curso) parou; 4401 correu | **POSTFIX_MODIFIED** (forma da rejeição > rótulo wall) |
| 1522 vs 1873 — maturidade do flush (absorvido→runner vs trap-formado-com-div) | **POSTFIX_CONFIRMED** |
| 5627 — supply causal mais longe (1.87 não 0.84) | **POSTFIX_MODIFIED** (calibração melhor; direção ainda erra → STILL_INSUFFICIENT sem VA de volume) |
| acceptance textual enganosa → ler pela forma (sub-bloco D) | **POSTFIX_CONFIRMED** |
| compression-runner vs washout-runner (1522 absorção lenta vs 5826 reclaim explosivo) | **POSTFIX_CONFIRMED** |
| entry-red-bar / esforço-comprador-ausente = trap (1873, 3929, 3825) | **POSTFIX_CONFIRMED** |
| **supply-WALL-próximo ⇒ fade como REGRA** (4401/5627 correram) | **QUARANTINED_PENDING_VOLUME_VA** |

## Veredictos-chave
- **3949 vs 3929 (geometria):** CONFIRMADO LIMPO, agora **sem look-ahead** — outcome split 6.62R vs 0.05R por
  geometria de supply com todo o resto idêntico (mesmo dia/macro/cascade/SMC). Esta é a **prova causal** de que
  geometria-preço×supply é eixo real, não artefato. (Pré-fix já sugeria, mas estava contaminado.)
- **weekly-negativo = trap: QUEBRADO** (confirmado causal).
- **Wall pole:** o fix **afia a fronteira** em vez de salvá-la — as wall-calls confiantes com conjunção (3825,
  1873, 3929) confirmam/param; os 2 refutados (4401, 5627) são onde o reader hedgeou (anchor-warning, mais-cego).
  O que separa wall-fade de wall-fuel é a **CONJUNÇÃO** (proximidade × push-into/rejeição × esforço-comprador-ausente
  × div-bearish), e o fechamento definitivo exige o **VA de VOLUME (BLOCKED)**.

## Síntese
A revalidação causal **melhorou** o Cluster 2 (7/10 CONFIRMED) e **purificou** a evidência mais forte (geometria
3949/3929 agora sem look-ahead). Lentes confirmadas pós-fix; "supply-WALL ⇒ fade" segue QUARANTINED_PENDING_VOLUME_VA.
Nada vira regra/gate/score.
