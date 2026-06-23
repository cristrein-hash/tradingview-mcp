# XAU 4H L2/BPT — CLUSTER 1 CONTINUATION/FUEL REREAD — 2026-06-23

Segunda rodada DIRECIONADA (não genérica) sobre a fraqueza central do Cluster 1 (4918/4926 = irmãos monster
runners; over-fade de continuação). Estrutura: 3 papéis cegos independentes (Continuation/Fuel Reader +
Fade/Wall Challenger + Judge/Integrator, outputs `agent_*.md` + dossiê), VA real incluída, freeze antes do
outcome. SANITY_PROBE — diagnóstico, NÃO regra/gate/score.

## Pergunta viva
Quando dois trades são irmãos estruturais/continuação legítima com VA construtiva, o que faz o 2º parecer
perigoso? Como distinguir supply-as-WALL de supply-BEING-CONSUMED sem criar gate?

## Processo
- Pacote: `results/cluster1_continuation_fuel_reread/reading_packet_BLIND.md` (VA real, causal, sem outcome).
- Pareceres cegos: `agent_continuation_fuel_reader.md` (steelman fuel) + `agent_fade_wall_challenger.md` (steelman wall).
- Integração: `reader_dossier_FROZEN.md` (Judge, sem voto-maioria; variável arbitral).
- Freeze hash: **dbd7c8b** (antes do outcome).
- Audit: `phase3_audit_FROZEN_vs_outcome.md`. Visual: `visual_post_audit_review.md`.

## Variável proposta (congelada, cega): VALUE-MIGRATION PHASE (lead vs lag)
Valor subindo SOB um movimento cuja última barra ainda estende (corpo no topo) = **consumido/fuel**; valor subindo
PARA um movimento gasto cuja última barra parou (give-back/wick/EQH, teto recém-chegado) = **wall**. Os mesmos
escalares (dist_poc grande, ACCEPTING_ABOVE, VAH migrou, supply perto) ocorrem nas DUAS fases → só a relação
temporal arbitra (leitura, não gate). Cascade-up = pré-condição.

## Audit result (contra outcome)
| ep | classificação cega | mfe_R / exit | audit |
|---|---|---|---|
| 4918 | INSUFFICIENT(origem) | 19.79 runner | HONEST_RESIDUAL (variável absteve no maior runner) |
| 4926 | HONEST_RESIDUAL(consumption-lean) | 18.03 runner | MODIFIED_LENS (lean confirmado, costura-lag refutada) |
| 8878 | SUPPLY_WALL | 18.78 WIN_HELD | **REFUTED_LENS** (wall correu) |
| 8940 | VA_ACCEPTANCE_EXPANSION | 4.96 BE | **REFUTED_LENS** (lead limpo correu MENOS) |
| 6887 | SUPPLY_CONSUMPTION | 0.00 STOP | **REFUTED_LENS** (lead/consumido parou) |

**A variável value-migration-phase é REFUTADA — anti-correlacionada com o outcome:** ambos LAG/WALL (8878, 4926)
correram ~18R; ambos LEAD limpos (8940, 6887) falharam; absteve no maior runner (4918). Leu geometria PRÉ-impulso
como exaustão PÓS-impulso → sinal invertido. Em bull forte, near-supply + give-back + POC-compression é
**spring-load que dispara**, não wall.

## Novas variáveis encontradas / refutadas / insuficientes
- **Nova confirmada:** NENHUMA (CONFIRMED_NEW_VARIABLE = 0).
- **Refutada:** `value-migration-phase` (lead/lag) — re-narração da mesma geometria estática sob moldura temporal;
  o próprio dossiê admite que os escalares são idênticos nas duas fases; o outcome falsifica.
- **Insuficiente/irredutível:** o separador runner-vs-stop NÃO existe nas features de entry desta rodada (consistente
  com a auditoria rabbit-hole: entry sem edge, substrato auction-irredutível).

## Status obrigatório de 4918/4926
- **4926 → MODIFIED_AS_CONTEXT_DEPENDENT**: o over-fade FOI corrigido (a leitura de consumo, não mais "over-extension
  confiante", foi vindicada por um runner de 18R), MAS o separador que distinguiria fuel-de-wall no entry NÃO foi
  achado — fica STILL_INSUFFICIENT para a separação. Melhora de processo, não de poder discriminante.
- **4918 → HONEST_RESIDUAL**: leitura de origem correta, mas a variável absteve no maior runner (19.79R).

## Impacto no manual / Cluster 3
- Manual: a lente `value-migration-phase` entra como **REFUTED** (não vira regra). A lente "over-fade de continuação
  em bull forte" é confirmada como **irredutível no entry** (negativa honesta).
- **Cluster 3:** o eixo continuation/fuel-vs-wall segue SEM separador no entry; isso é informação para Cris decidir
  se Cluster 3 muda a pergunta (ex. exit/gestão em vez de seleção no entry), NÃO executado aqui.
