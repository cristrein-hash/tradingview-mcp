# L1 runtime — seleção da última barra 4H FECHADA (2026-06-16)

## Bug corrigido
`data_get_ohlcv` inclui o bar EM FORMAÇÃO (realtime) como último. O runtime agora **seleciona a última barra 4H fechada** (`now ≥ bar_time+14400`), exclui o forming, e avalia/persiste só barras fechadas. Logs: `returned_last_bar_time`, `eval_bar_time`, `previous_closed_bar_time`, `forming_bar_excluded`.

- Live agora: `returned_last=10:00 (forming)` → `eval_bar=06:00 (FECHADA)`, `forming_bar_excluded=True`. **Não retorna mais o `blocked_bar_not_closed` cego.**

## Descoberta crítica (honesta): study-values também são do forming
`data_get_study_values` (RSI/NAS corrente) corresponde ao **bar em formação** (último retornado), NÃO ao eval_bar fechado. Usar o NAS/RSI do forming para o bar fechado seria **look-ahead**. Por isso, quando há forming excluído, o runtime bloqueia com **`blocked_missing_closed_bar_study_values`** (preciso). Só avalia quando o último bar retornado JÁ é o fechado (study-values alinham) + NAS SHIFT1 do bar fechado anterior existe.

## Validação (fixtures `test_closed_bar.py`)
- **T1 forming:** eval_bar = penúltima (fechada), `forming_bar_excluded=True`, estado `blocked_missing_closed_bar_study_values`, forming NÃO persistido. PASS.
- **T2 todas fechadas + NAS i-1 no histórico:** avalia o eval_bar fechado; **NAS SHIFT1 = i-1 (2.0), não o atual (5.0)**; persiste o eval_bar fechado. PASS.
- **T3 todas fechadas, sem histórico:** `blocked_missing_nas_shift1`. PASS.
- Reuso de `scanner.evaluate` (mesmos gates), SL estrutural + target 3R do scanner. NAS nunca recomputado/aproximado.

## DA PASS/FAIL
eval_bar fechada ✓ · forming ignorada ✓ · NAS SHIFT1 de i-1 fechado ✓ · NAS atual não usado como SHIFT1 ✓ · scanner/runtime mesmos gates ✓ · SL estrutural igual ✓ · target +3R igual ✓ · vol_entry_z ausente ✓ · regime_B_v3 ausente live ✓ · Telegram bloqueado ✓ · broker intocado ✓ · chart restaurado ✓ (benigno).

## STATUS: runtime = PARCIAL (seleção de barra fechada CORRIGIDA; operacional ainda bloqueado)
A seleção da barra fechada está correta. **Operacional ainda bloqueado** porque os study-values (RSI/NAS) do snapshot são do bar em formação, não do eval_bar fechado — bloqueio preciso (`blocked_missing_closed_bar_study_values`), não-look-ahead. **Fix real p/ operacional (bloco futuro):** alinhar a leitura dos study-values ao bar fechado — opções: (a) scheduler/leitura no fechamento do bar (não +5min depois, quando o forming já domina o data window); (b) tool MCP de histórico per-bar de study-value; (c) confirmar se o indicador NAS só plota em barstate.isconfirmed (então o study-value corrente já seria o do bar fechado). Até lá, runtime causalmente seguro + não-operacional + sem Telegram.

_Produção intacta. Telegram não enviado. Broker intocado._
