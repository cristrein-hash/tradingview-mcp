# MCP tool `data_get_study_values_at_bar` (2026-06-16) — fonte exata de study-value por bar

## O que resolve
Faltava uma fonte EXATA e causal do `NAS_DISTANCE`/RSI do **bar FECHADO** (a `data_get_study_values` só dá a data-window = bar em formação). A nova tool lê a **série indexada por bar** do study via `study.data().valueAt(barIndex)` (mesmo motor do `getPineShapes`): slot 0 = time, slots 1+ = cada plot na ordem → retorna **valor do plot + timestamp por bar**.

## Arquivos (servidor MCP — additivo, não altera tools existentes)
- `src/core/data.js`: `getStudyValuesAtBar({study_filter, count})` → `{studies:[{name,last_index,bars:[{bar_index,time,values}]}]}`.
- `src/tools/data.js`: tool `data_get_study_values_at_bar` (args study_filter, count≤50; default 3).
- `node --check` OK em ambos.

## Validação (chart live 240, via _MCP fresh)
`data_get_study_values_at_bar(study_filter="NAS", count=4)` →
| time | bar | NAS_DISTANCE |
|---|---|---|
| 2026-06-16T02:00 | 296 | 0.444 |
| 2026-06-16T06:00 | 297 | **1.042** (último FECHADO típico) |
| 2026-06-16T10:00 | 298 | 0.749 |
| 2026-06-16T14:00 | 299 | 0.577 (forming/projeção) |

→ Entrega NAS_DISTANCE por bar **com timestamp** → permite alinhar exatamente ao bar fechado e ao bar fechado anterior (SHIFT1). RSI idem via `study_filter="Relative Strength"`.

## ⚠️ Nota de convenção (crítica p/ o wiring)
O **study series** e o `data_get_ohlcv` podem diferir em **1 bar** (a series inclui um bar mais recente — convenção de time open/close difere entre as APIs). **O wiring DEVE alinhar por TIME** (não por índice/offset): runtime calcula `eval_bar_time`/`previous_closed_bar_time` (close-guard) e pega na series os bars com `time == eval_bar_time` (NAS atual fechado) e `time == previous_closed_bar_time` (SHIFT1). A tool fornece o time por bar → match robusto, independente da convenção.

## Status / próximo passo
- **Tool CRIADA e validada.** Destrava a Opção A. Não restaurei/reiniciei o servidor MCP da sessão (código novo é carregado pelo subprocess fresco do `tv_read_adapter`; o server da sessão segue o antigo até reinício — sem impacto no runtime).
- **Próximo bloco (wiring → operacional):** o `tv_read_adapter` chama `data_get_study_values_at_bar` e devolve, alinhados por time, `nas_eval`(bar fechado) + `nas_shift1`(anterior) + `rsi_eval`; o `runtime_xau` usa esses valores fechados (dispensa a persistência de NAS) e deixa de bloquear em `blocked_missing_closed_bar_study_values`. Exige Pre-Change Discipline + DA + validação de paridade vs scanner.

_Mudança additiva no servidor MCP. Produção (receiver/scheduler/runtime) NÃO alterada por este bloco. Sem Telegram. Sem broker._
