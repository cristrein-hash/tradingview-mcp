# PREREGISTRO — Validação capitulation + rsi_momentum (foco LUCRO)

**Congelado em 2026-06-19 ANTES de qualquer cálculo deste bloco.** Escopo: XAU_4H_L2_BPT_BOS_CHOCH.
Não é engine global. Não promove. Não cria aggregator/decisão. Outcome só pós-hoc.

## Hipótese
- `hypothesis_id`: **L2BPT_CONFL_CAPITULATION_RSI_MOMENTUM_V1**
- `source`: Fase 2B.5 / commit `2a59b4f`
- `registry status`: PROMISING_IN_SAMPLE / REVIEW_ONLY

## Definições EXATAS (congeladas; reuso fiel da Fase 2B.5)
- **state(i,s)** (de `analyze_specialist_confluence.py`): `veto` se veto_count>0; senão `review_flag` se review_flag_count>0 E stance=='neutral'; senão a `stance` (= `net_read` do `specialist_out/<s>.jsonl`).
- **capitulation supportive** = `state(i,'capitulation')=='supportive'`.
- **rsi_momentum supportive** = `state(i,'rsi_momentum')=='supportive'`.
- **Regra da confluência** = capitulation supportive **AND** rsi_momentum supportive.
- **Fonte dos campos**: usa a **EVIDÊNCIA congelada** dos especialistas (net_read + veto/review_flag da `l2_bpt_specialist_ablation_ready_matrix.csv`), **NÃO** recomputa fator bruto. Sem retune.
- **Contexts permitidos**: TODOS (a célula vive em bottom_reversal_capitulation, bear_bounce, mid_range; não restringir).

## Dataset e janelas
- **Universo**: 276 episódios L2/BPT XAU 4H, 2020-2026, outcomes congelados (`l2_bpt_trade_qualification_outcomes.csv`, realR **capado +3.9R** para WIN_RUNNER).
- **Janelas temporais** (split por `datetime`): halves (2020→2022-12 / 2023-01→2026) e thirds (2020-2021 / 2022-2023 / 2024-2026).
- **Forma de validação**: sub-janelas / split temporal in-sample. **NÃO é OOS verdadeiro** (hipótese descoberta no conjunto completo). É o mais honesto sem dado novo; Opção B não rodada.

## Controles
capitulation sozinho · rsi_momentum sozinho · base universe (276) · base context-matched (mesmos Stage A da célula) · random-matched por contexto (null, 10k, seed 20260619) · NAS supportive (benchmark diagnóstico Fase 2B).

## Métricas PRIMÁRIAS (foco lucro)
1. **expectancy_R de-capada** (runner=+6R piso documentado; true≥). 2. **sumR de-capado**. 3. **profit factor**. 4. **frequência/n por janela**. 5. **maxDD aprox** (cum-R ordenado por datetime). 6. **max losing streak**. 7. vs **base context-matched**. 8. vs **random-matched** (percentil null).

## Métricas SECUNDÁRIAS
hit_2R · hit_3R(runner) · stop_first · scratch/time-stop · **avgR capado (só referência)** · Wilson CI 95% do hit_2R · drop-top2 · estabilidade por Stage A context.

## Critérios de decisão (LUCRO, não winrate)
- **PASS** (não exige ultra-winrate): expectancy_R/sumR/profit factor da célula **acima** da base context-matched **E** sinal presente em **≥2** das janelas temporais (não concentrado numa só) **E** **não some** ao tirar os 4 runners capados (drop-top2 / de-cap mantêm direção) **E** frequência preservada (não colapsa para n<5/janela útil).
- **FAIL**: depende de outliers (drop-top2 mata o sinal) · morre fora da janela de descoberta (concentrado em 1 janela) · mata frequência/lucro vs controles.
- **INCONCLUSIVE**: n insuficiente por janela (n<5) **OU** janelas divergem demais (sinal numa, oposto noutra) → sem poder estatístico para concluir; manter como candidato a OOS real com dado novo.

## Proibições deste bloco
sem aggregator · sem decisão TAKE/REVIEW/SKIP nova · sem promoção · sem PROMOTED/DECISIVE · sem retune · sem testar outras confluências/células · sem Opção B completa · sem SLIM · sem chart/MCP/plot · engine/decisions_merged/especialistas intocados.
