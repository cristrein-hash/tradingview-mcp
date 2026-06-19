# DECISÃO METODOLÓGICA — OOS 2013-2016 RSI/NAS direto do study_values (Rota A)

**2026-06-19.** Escopo: XAU_4H_L2_BPT_BOS_CHOCH. Aplica a hipótese CONGELADA capit+rsi em OOS real; não
procura nova. Autorizada pelo Cris a **Rota A**.

## Por que a reconstrução raw_features (rsi/nas) foi bloqueada
`reconstruct_raw_features.py` reproduz OHLC/volume/bubbles 100%, mas o rsi/nas dependem de **atribuição
por snapshot** sujeita à ambiguidade de **dup-capture (stall do replay)**: 2+ snapshots com o mesmo
último-bar-time → fidelidade rsi 97.26% / nas 97.66% no fidelity gate de 2020-2026. Sem referência
congelada 2013-2016, **não há como certificar decision-invariance** — e rsi é o input direto da hipótese.

## Por que usar study_values direto é aceitável (e superior aqui)
- `study_values` (RSI, NAS) estão **5100/5100** no RAW OOS — o valor do indicador é capturado nativamente
  por snapshot, não precisa de atribuição lossy.
- Extração direta: `build_oos_rsi_nas_from_study_values.py` — para cada snapshot, o **último bar de `ohlcv`**
  é o bar corrente; o RSI/NAS daquele snapshot é o valor disponível **no fechamento** desse bar. Dedup por
  bar_time = **keep-last** (manifest: dup_ts 24 ~0.47%).
- Resultado: **5076 bars únicos, 0 RSI ausente.** Comparado à reconstrução, o rsi direto **difere em apenas
  1 de 5073 bars** (99.98% concordância) — i.e., para 2013-2016 a reconstrução já era quase perfeita, e a
  Rota A remove qualquer resíduo no sinal da hipótese.

## Diferença metodológica vs in-sample 2020-2026
- In-sample: rsi veio do `raw_features_2020_2026.jsonl` **congelado** (referência SHA 9fac96b9).
- OOS: rsi vem **direto do study_values** (Rota A), e os demais campos (OHLC/bubbles/nas_recent/smc_recent)
  da reconstrução (100% nos campos não-rsi). O `raw_features` OOS é a reconstrução **com o campo `rsi`
  patchado** pelos valores diretos. **Declarado como diferença metodológica.** Não altera o pipeline 2020-2026.
- Barras diárias OOS: derivadas por **agregação de sessão 22:00 UTC** do 4H (mesma convenção de `time` do
  in-sample `XAU_1D_bars.jsonl`). Limitação: SMA diária no **início de 2013** tem histórico curto (a coleta
  começa 2013-01-31) → contexto diário degradado nas primeiras ~50 sessões; documentado.

## Riscos
- nas_recent/smc_recent ainda vêm da reconstrução (não patchados) — **não são inputs da hipótese capit+rsi**, então irrelevantes para ela; relevantes só se outros especialistas forem usados.
- Daily-from-4H ≈ daily real (ambos fecham 22:00 UTC) mas não idêntico; afeta SMA/regime diário marginalmente.
- Edge de SMA diária no início de 2013.

## Controles obrigatórios (quando o OOS for aplicado)
base universe OOS · capitulation sozinho · rsi_momentum sozinho · random same-context · NAS supportive (se gerado). Métrica primária = LUCRO (expectancy/sumR/PF), não ultra-winrate.

## Alinhamento causal (exigência)
- RSI/NAS atribuídos ao bar pelo **timestamp do último ohlcv** (= bar que o snapshot fecha).
- **Proibido** usar forming/future bar: o valor nunca é atribuído a um bar futuro; entry = close do bar i (causal).
- Duplicatas: keep-last determinístico.
- Auditoria: `results/l2_bpt_oos_2013_2016_rsi_nas_alignment_audit.csv`.

## Status
**OOS pipeline unlocked conditionally** após a auditoria de alinhamento causal (PASS). Inputs base OOS
gerados e fiéis: `raw_features` (rsi Rota A), `1D_bars`, universo L2 (3798 candidatos raw). **Pendente**
(build sensível à fidelidade, não fabricado): stages 5-11 (pruning + 84-fatores), evidência dos 2
especialistas (agentes, prompts congelados), outcomes, e então aplicação da regra congelada + controles.
