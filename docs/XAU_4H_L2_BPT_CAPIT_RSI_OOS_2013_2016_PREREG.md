# PREREGISTRO — OOS REAL 2013-2016 capitulation + rsi_momentum (foco LUCRO)

**Congelado 2026-06-19 ANTES de qualquer teste OOS.** Escopo: XAU_4H_L2_BPT_BOS_CHOCH. Não é engine global.
Não promove. Outcome só pós-hoc. Aplica a hipótese congelada — NÃO procura nova célula/variante/threshold.

## Hipótese (idêntica à in-sample)
- `hypothesis_id`: **L2BPT_CONFL_CAPITULATION_RSI_MOMENTUM_V1** (status entrada: OOS_CANDIDATE / REVIEW_ONLY).
- Resultado in-sample 2020-2026 (sub-janelas): exp_decap +2.055R, sumR +34.9R, PF 8.94, maxDD −1.1R, streak 2, hit2R 65%.

## Definições EXATAS (congeladas; reuso fiel)
- **state(i,s)**: `veto` se veto_count>0; senão `review_flag` se review_flag_count>0 E stance=='neutral'; senão `stance` (=`net_read` do especialista).
- **capitulation supportive** = `state(i,'capitulation')=='supportive'`.
- **rsi_momentum supportive** = `state(i,'rsi_momentum')=='supportive'`.
- **Regra** = capitulation supportive AND rsi_momentum supportive.
- **Fonte dos campos:** evidência dos especialistas (prompts CONGELADOS `specialists/prompts/{capitulation,rsi_momentum}.md`) rodados sobre os 84-fatores OOS. SEM retune.
- **Contexts permitidos:** TODOS.

## Dataset OOS
- RAW XAU 4H **2013-02-01 → 2016-05-25** (5100 bars; gold BEAR; gz íntegro). **Zero overlap com 2020-2026.**
- De-cap = runner +6R (piso; realR capado +3.9R). Mesma convenção da in-sample.

## Métricas PRIMÁRIAS (lucro, não ultra-winrate)
expectancy_R de-capada · sumR · profit factor · frequência/n · maxDD · max losing streak · vs base OOS · vs context-matched/random-matched.

## Métricas SECUNDÁRIAS
hit_2R · hit_3R(runner) · stop_first · scratch · Wilson CI · drop-top2.

## Controles
base universe OOS · capitulation sozinho · rsi_momentum sozinho · random same-context · NAS supportive (benchmark, se gerado).

## Critérios de decisão
- **PASS (forte):** expectancy_R/sumR/PF da célula OOS **acima** da base/context-matched, **sem** depender de outliers (drop-top2 mantém), **com** frequência utilizável → pode subir a `AGGREGATOR_RULE_CANDIDATE` (NUNCA PROMOTED/DECISIVE sem autorização humana).
- **FRACO / n insuficiente:** manter `OOS_CANDIDATE` / `REVIEW_ONLY` ou marcar INCONCLUSIVE.
- **FAIL:** célula OOS abaixo dos controles, ou depende de outliers, ou mata frequência → `REJECTED` ou `CONTEXT_ONLY`.

## Pré-condição de fidelidade (gate de execução)
O teste OOS **só é válido** se os inputs OOS forem reproduzidos com fidelidade certificável — em especial **rsi e nas**, que alimentam diretamente a hipótese. Enquanto a reconstrução de raw_features estiver **<100% field-equivalent no rsi/nas (97.26%/97.66%)** e **sem referência congelada 2013-2016 para certificar decision-invariance**, e enquanto `--run-new-dataset` estiver **bloqueado/não-implementado**, o OOS **NÃO é executado** (resultado seria contaminado). Ver `results/l2_bpt_capit_rsi_oos_2013_2016_data_availability.csv`.

## Proibições
sem aggregator · sem TAKE/REVIEW/SKIP novo · sem promoção · sem PROMOTED/DECISIVE · sem retune · sem nova confluência/célula · sem Opção B como novo engine · sem SLIM · sem chart/MCP/plot · engine/decisions_merged/especialistas intocados.
