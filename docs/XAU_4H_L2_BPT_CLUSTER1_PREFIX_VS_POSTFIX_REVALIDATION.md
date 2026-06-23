# XAU 4H L2/BPT — CLUSTER 1: PRE-FIX vs POST-FIX REVALIDATION — 2026-06-23

Revalidação das leituras do Cluster 1 sobre o backbone CAUSAL (anchor as-of por timestamp real, commit 1267c8d)
vs a versão PRE-FIX contaminada por look-ahead. Base: `results/raw_rebuild_cluster1_postfix/*` (pós-fix) vs
`results/raw_rebuild_cluster1/*` + audit antigo (pré-fix, histórico). SANITY_PROBE — diagnóstico, não gate.

## Placar por episódio (audit pós vs pré)
| EP | pré-fix | pós-fix | mfe_R / exit | nota |
|----|---|---|---|---|
| 4918 | CONFIRMED | **CONFIRMED** | 19.79R runner | causal afiou (demanda 0.02ATR + RSI35+div) |
| 1661 | CONFIRMED | **CONFIRMED** | 0.0R stop | trap/wall held |
| 5701 | AMBIG/CONFIRMED | **CONFIRMED** | 0.42R stop | supply-wall held |
| 6887 | REFUTED | **REFUTED** | 0.0R stop | "fuel" mas parou |
| 7426 | ACERTOU/MODIFIED | **MODIFIED** | 4.61R scratch | extensão, sem runner |
| 8878 | REFUTED | **REFUTED** | 18.78R monster | wall-stall mas disparou |
| 8923 | CONFIRMED | **CONFIRMED** | 0.58R BE | climax RSI82 |
| 8940 | CONFIRMED | **MODIFIED** | 4.96R BE | direção certa, runner modesto |
| 4926 | REFUTED | **REFUTED** | 18.03R monster | wall/sem-edge mas correu |

Pré-fix 5C/3R/1M → **pós-fix 4C/2M/3R**. **Estável** — os 3 REFUTED (4926/6887/8878) e os CONFIRMED de
inversão-de-regime (4918/1661/5701/8923) coincidem. O fix não mudou as conclusões load-bearing; só rebaixou 8940
CONFIRMED→MODIFIED e deu ao 4926 uma leitura oposta mais confiante (que segue REFUTED).

## Classificação de LENTES (pós-fix)
| Lente | Status |
|---|---|
| Regime/weekly-sign inverte significado (4918 cascade-1+div vs 1661 cascade-3 trap) | **POSTFIX_CONFIRMED** |
| RSI-position / blow-off (8923 RSI82 climax; 8878 RSI não-extremo) | **POSTFIX_CONFIRMED** |
| supply-as-FUEL (distante + forma) direção correta (8940; 6887 REFUTED=parou 0R) | **POSTFIX_MODIFIED** (8940 direção certa exit fraco; 6887 não — direção errada) |
| bottom_turn condicionado ao regime (4918 com macro_broken+demanda; vs casos sem) | **POSTFIX_CONFIRMED** |
| timing/apex (8923 chase climático) | **POSTFIX_CONFIRMED** |
| **supply-colado/geometria-wall ⇒ fade/sem-edge** (4926, 8878 = wall + correram monster) | **QUARANTINED_PENDING_VOLUME_VA** |
| 4918 vs 4926 como par discriminável | **POSTFIX_REFUTED** (são gêmeos-runner, não opostos; a discriminação por geometria de wall falha) |

## 4918 vs 4926 — veredito honesto
A leitura pós-fix os chamou OPOSTOS (4918 absorção-no-piso / 4926 wall-sem-edge). O outcome diz **GÊMEOS**:
ambos monster runners (+19.79R e +18.03R) no dia seguinte. O fix **melhorou o 4918** (CONFIRMED contrarian
limpo) mas **piorou a calibração do 4926** (trocou "não-sei" pré-fix por "oposto-confiante" que falha). O eixo
que separaria de verdade (aceitação acima do VALUE-AREA DE VOLUME) está **BLOCKED** — por isso a discriminação
4918/4926 fica **QUARANTINED_PENDING_VOLUME_VA**, não resolvida por geometria de supply.

## Síntese
A revalidação causal **não destruiu** as lentes do Cluster 1 — confirmou as load-bearing (regime, RSI, bottom_turn
condicionado) e reconfirmou a **quarentena** do "supply-colado ⇒ fade" (over-fade runners). O 4918/4926 segue como
o caso-limite cujo árbitro real é o VA de volume bloqueado. Nada vira regra/gate/score.
