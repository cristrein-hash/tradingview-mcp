# MICRO-STRUCTURE LIQUIDITY ENGINE — RELATÓRIO DIAGNÓSTICO

**2026-06-22.** Bloco fechado. 62 (ensino). NÃO produção, NÃO 276/OOS, NÃO chart/MCP, NÃO promover.
Causal (join seguro 62/62; 84 features de proveniência verificada). Sem outcome/realR/exit_type como predicado.
3 agentes CEGOS (IDs opacos X01..X18), leitura de conjunto. Scripts: `microstructure_features.py`,
`microstructure_aggregate.py`.

## Resultado: **FEATURE_MISSING / MICROSTRUCTURE_NOT_CAPTURED** (com 1 separação parcial inútil-como-filtro)

A distinção micro-top-bad vs breakout/bottom-good **não é capturável** com as features causais de microestrutura
disponíveis. Pior: a leitura "trap/failed" **inverte** — marca winners como ruins e lê o bad central como bom.

### Casos centrais (consenso 3/3 dos agentes cegos, vs papel verdadeiro do Cris)
| trade | papel (Cris) | consenso agentes | lê como | separável? |
|---|---|---|---|---|
| **T17** | BAD micro-top | **BREAKOUT_ACCEPTANCE 3/3** | GOOD | ❌ NÃO |
| T24 | BAD micro-top | BREAKOUT_ACCEPTANCE 3/3 | GOOD | ❌ NÃO |
| T23 | BAD macro-bear accum | BREAKOUT_ACCEPTANCE 3/3 | GOOD | ❌ NÃO |
| T40 | BAD micro-top | split (MBR 1/3) | SPLIT | ❌ NÃO |
| **T20** | BAD micro-top | **FAILED_BREAKOUT 3/3** | BAD | ✅ (via below-VAL+reclaim<0, NÃO "micro-top") |
| **S12** | GOOD contrast | BREAKOUT_ACCEPTANCE 3/3 | GOOD | ✅ |
| T21, T22 | GOOD contrast | — | — | **CONTRAST_OUT_OF_WORKING_SET** (fora dos 62) |

### O filtro microestrutural DESTRUIRIA winners
- **Falsos-BAD em winners/anchors (5): S3, S15, S20, S24, S25** — a leitura "MICRO_TOP_TRAP/FAILED" dispara
  porque eles entraram PERTO/ATRAVÉS de supply (rompimento), exatamente o que um winner-breakout faz.
- Enquanto isso, **T17/T23/T24 (bad) leem como GOOD**. Ou seja, usar a leitura como gate INVERTERIA o resultado.

### Por que não separa (convergência dos 3 agentes — separability_note)
O mesmo vetor de entrada (`ABOVE_VAH + reclaim_body>0 + demand-supported + buy-flow + legpos alto`) precede
TANTO breakout-acceptance bom QUANTO micro-top-trap ruim. O único eixo que separa "trap" é proximidade de supply
(`sup_cat/dist_4h_supply_atr`) — mas isso marca os breakouts-através-de-supply (S15/S24, winners) como trap.
Em open-sky (has_overhead=0, ex. S29/S31) o blowoff-top e a acceptance são mecanicamente idênticos. **A
incapacidade é estrutural, não ruído** — confirma o disfarce de liquidez (Auction Theory) para T17 especificamente.

## Prior layers crosscheck (camadas anteriores sob microestrutura)
- **sup_cat/pol_cat + dist_supply**: único eixo que separa trap óbvio, MAS perigoso (mata breakouts-through-supply).
- **reclaim_body + va_state (SVP) / legpos / bubbles**: NÃO separam (compartilhados por good e bad).
- **drop20/rise20**: rende a única assinatura bad separável (FAILED_BREAKOUT de T20), mas não-segura como filtro.
- **D1 leg-state backbone / Bear-Leg Block v3**: contexto correto e ortogonal — v3 pega corrective raso, NÃO
  micro-top (T12/T25 leem como acceptance). Complementares, não substitutos.
- **entry-quality (refutado antes)**: RE-CONFIRMADO — good/bad estruturalmente idênticos no ponto de entrada.

## Conclusão honesta (sem mascarar negativo)
- **T17 = parcialmente irredutível PROVADO** por 3 agentes cegos independentes (3/3 leem como acceptance limpo).
  Não chamar de "totalmente irredutível" — é **feature-missing**: faltaria a sequência intrabar de varredura de
  micro-topo (high/low contíguo) que NÃO temos. Mas com o que é causal e disponível, não separa.
- **T20** tem assinatura FAILED_BREAKOUT separável (below-VAL + reclaim negativo) — registrar como lead, NÃO
  promover (também marca anchors S25/S35).
- **NÃO forçar regra de microestrutura.** Seria filtro que destrói winners (5 falsos-BAD) — pior que não-filtrar.
- T23 não tocado (continua classifier/hindsight). T32/S11 late-top residual aceito. S40 fatal-skip aceito.

## Próxima recomendação
Parar de perseguir o detector de micro-top (overfit garantido / inverte resultado). O caminho com retorno real
permanece: **macro reader (preserva bull) + Bear-Leg Block v3 (bloqueia corrective raso + bear-markdown) +
ACEITAR o resíduo T17/T24/T32 como custo**. Se um dia houver série OHLC contígua 2020-2026, reabrir só a
sequência intrabar de sweep/reclaim de micro-topo — única feature plausível ainda não testada.

Outputs: `results/l2_bpt_microstructure_feature_values_62.csv`, `..._agent_readings_62.csv`,
`..._target_check.csv`, `..._prior_layers_crosscheck.csv`, `..._da.csv`.
