# XAU 15M BigBeluga + NAS (Leonardo) — dataset manual de estudo

## O que é
`manual_trade_table.csv` é um **dataset manual** extraído dos PDFs do Leonardo (`Analise 15M BB + NAS.pdf`, `Analise Losers .pdf`) — 15 winners + 4 losers selecionados.

## O que NÃO é
- **NÃO é validação estatística** nem prova de edge.
- **NÃO é base rate:** é uma **amostra curada** (winners destacados + losers selecionados). O doc dos losers afirma explicitamente não conter todos. **Não calcular winrate/expectancy a partir daqui.**

## Como foi preenchido (proveniência)
- Valores numéricos (entry/stop/risk/result/R, ranges de zona, barras/duração) vêm do **texto das anotações** dos PDFs → `confidence=HIGH_numeric_text`.
- `zone_width_points` calculado dos ranges quando o texto os fornece; senão `UNKNOWN`.
- Classificações de leitura (reversal/continuation, trend_alignment, entry_location_in_zone) são **inferência** → marcadas `INFERRED` / `confidence=MEDIUM`.
- Campos sem dado claro = **`UNKNOWN`** (não inventados). Todos com `needs_manual_review=yes` (pendente confirmação visual nos prints + Leonardo).
- Losers (L02–L05) são qualitativos: não trazem entry/stop/R numéricos nos PDFs → numéricos `UNKNOWN`.

## Limitações conhecidas
- Localização exata da entrada na zona, retestes, tempo-na-zona e comportamento pós-entrada **ainda não extraídos dos prints** (exigem leitura visual página a página) → `UNKNOWN`, a preencher na Fase 1.b.
- Direção enviesada (11 short / 4 long). Reversão vs continuação não confirmado pelo Leonardo (Fase 0).

## Próximos passos
- **Fase 0:** respostas de `docs/XAU_15M_BB_NAS_LEONARDO_QUESTIONS.md` (regra real).
- **Fase 1.b:** completar campos visuais (`entry_location_in_zone`, `retests_pre_entry`, `time_inside_zone_before_entry`, `post_entry_behavior`) lendo os prints.
- **Fase 2:** taxonomia em buckets (continuation_with_trend / reversal_countertrend / immediate_break_loser / false_defense_loser / long_duration_runner / …).
- **Fase 3:** classificar variáveis em mechanical / semi-mechanical / human-review-only / unavailable.
- **Backtest:** só depois de gate manifest + mapping RAW (XAU 15M RAW, close-only-causal/SHIFT1). Não rodar antes.

## Campos do CSV
trade_id · source_pdf · page · winner_loser · direction · entry · stop · risk_points · result_points · r_multiple · zone_type · zone_high · zone_low · zone_width_points · nas_count · nas_direction · trend_alignment · reversal_or_continuation · entry_location_in_zone · bars_to_exit · duration_text · duration_hours_if_known · retests_pre_entry · time_inside_zone_before_entry · post_entry_behavior · failure_type_if_loser · exit_reason · notes · confidence · needs_manual_review
