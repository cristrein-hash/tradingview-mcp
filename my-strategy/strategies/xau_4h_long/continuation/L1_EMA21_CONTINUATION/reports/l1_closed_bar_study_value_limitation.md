# L1 runtime — limitação de study-values do bar FECHADO (HARD STOP documentado, 2026-06-16)

## Pergunta
Existe fonte EXATA, causal e in-scope para RSI/NAS_DISTANCE do **eval_bar fechado** (e NAS do bar fechado anterior, SHIFT1), sem usar valores do bar em formação?

## Evidência por fonte (5 investigadas)
1. **Pine / `data_get_study_values`** — lê `dataSource.dataWindowView().items()` (`src/core/data.js:381`). A data window reflete o **último bar (forming em realtime)**. **= valor do bar EM FORMAÇÃO, não do fechado.** Confirmado no código + empírico (returned_last=10:00 forming vs eval_bar=06:00). **NÃO usável** (look-ahead).
2. **MCP — tool de histórico de study-VALUE por bar** — **NÃO EXISTE.** Só há `data_get_pine_shapes` (ativações de `plotshape()/plotchar()` por bar = sinais NAS top/bottom), que **não** entrega o plot `NAS_DISTANCE_FROM_EMA_ATR`. O motor TEM `study.data().valueAt(barIndex)` (usado internamente pelo getPineShapes, `src/core/data.js:497`), mas **não está exposto** para valores de plot — exporia exigiria mudar `src/` (fora do escopo deste bloco).
3. **RAW canônico** — último bar **2026-06-09T22:00** (7 dias stale); **não cobre** o bar fechado live (06:00 hoje). Exato porém **stale** → não-live.
4. **Event store (`indicator_signals.jsonl`)** — NAS XAU 240 = **7 eventos esparsos** (só top/bottom), **sem `NAS_DISTANCE` no payload**. Não é série per-bar. **NÃO usável.**
5. **Estado persistente próprio** — capturaria o `data_get_study_values` corrente, que é **forming** → persistir forming como se fosse closed = aproximação proibida. **NÃO usável.**

## Veredito: HARD STOP (por falta real de fonte exata in-scope, não preguiça)
Não há fonte exata, causal e dentro do escopo (runtime/adapter) para o `NAS_DISTANCE`/RSI do bar fechado. O runtime **já bloqueia corretamente** com `blocked_missing_closed_bar_study_values` (não-look-ahead, sem Telegram). **Nada foi forçado/aproximado.**

## Menor mudança necessária (bloco futuro, com autorização — toca fora do escopo deste)
**Opção A (recomendada — mais robusta): nova tool MCP `data_get_study_values_at_bar`** em `src/core/data.js` + `src/tools/data.js`, espelhando o padrão **provado** `study.data().valueAt(barIndex)` do getPineShapes, retornando o valor do plot (NAS_DISTANCE/RSI) no bar fechado **com timestamp** → o adapter alinha por `source_bar_time == eval_bar_time`. Pequena, cirúrgica, exata.
**Opção B: Pine alert no fechamento** (`barstate.isconfirmed`) emitindo NAS_DISTANCE/RSI/OB do bar fechado no payload → receiver → event store → runtime lê (causal). Toca Pine/alert infra.
**Opção C: runtime Python puro sobre RAW atualizado** — exige re-coleta RAW contínua (replay), não-live por design.

## DA PASS/FAIL
study-values têm timestamp/alignment? **FAIL (é o achado)** — data window = forming, sem bar-alignment para o fechado. · forming rejeitado? **PASS** (runtime bloqueia). · scanner/runtime mesmos gates? **PASS** (inalterado). · thresholds mudaram? **PASS (não)**. · gate removido? **PASS (não)**. · Telegram bloqueado? **PASS**. · broker intocado? **PASS**. · hard stop por falta real de fonte? **PASS** (5 fontes com evidência empírica).

## Status
runtime = **PARCIAL** (causalmente seguro, não-operacional). Config aprovada vive no **scanner (gate autoritativo)**. Operacional live depende da Opção A/B acima.

_Nenhum código alterado neste bloco (runtime já seguro). Produção intacta. Sem Telegram. Sem broker._
