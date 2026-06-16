# L1 runtime — wiring com data_get_study_values_at_bar (2026-06-16) — DESTRAVADO

## O que mudou
- **`tv_read_adapter`**: snapshot agora traz `nas_series` e `rsi_series` (por bar, com timestamp) via `data_get_study_values_at_bar`.
- **`runtime_xau`**: `align_study_values(eval_t, prev_t, series)` alinha por **TIMESTAMP exato** (nunca índice/forming): NAS(eval), NAS(i-1=prev fechado), RSI(eval). `build_live_series` agora trunca o OHLCV até o eval_bar e injeta esses valores fechados; reusa `scanner.evaluate`. Persistência = fallback/debug.
- Só avalia se `nas_eval_source_time==eval_bar_time` E `nas_shift1_source_time==previous_closed_bar_time` E `rsi_eval_source_time==eval_bar_time`; senão `blocked_missing_closed_bar_study_values`.

## Validação live
`alignment_status: ok`. eval_bar=10:00 (fechado): nas_eval=0.749, rsi=(58.67,56.50). nas_shift1=1.042 do 06:00 (bar fechado anterior). forming=14:00 ignorado. **`blocked_missing_closed_bar_study_values` eliminado.** state=no_candidate (regime BEAR — correto). notify.sent=False.

## Fixtures (test_wiring.py) PASS
T1 forming + séries com ordem embaralhada/índice deslocado → alinha por TIME; NAS SHIFT1 do prev fechado (2.2), RSI do eval, forming(9.99) IGNORADO. T2 sem o time do eval → bloqueia. T3 só forming → bloqueia (anti-índice).

## DA PASS/FAIL
alinhamento por timestamp (não índice) **PASS** · NAS SHIFT1 do bar anterior fechado **PASS** · RSI do eval_bar **PASS** · forming rejeitado **PASS** · scanner/runtime mesmos gates **PASS** (scanner.evaluate) · thresholds congelados **PASS** · SL estrutural/target 3R **PASS** · vol_entry_z ausente **PASS** · regime_B_v3 ausente live **PASS** · Telegram bloqueado **PASS** · broker intocado **PASS** · chart restaurado **PASS**.

## Status: runtime = OPERACIONAL-CAPABLE
O runtime agora avalia a config aprovada completa sobre o bar FECHADO (study-values causais por timestamp). Emite `operational_candidate` quando regime BULL + base-rule + RSI gate + stack v1 + NAS SHIFT1≥1.31 passam. Hoje retorna `no_candidate` apenas porque o regime live está BEAR (correto, não bug). Telegram só dispararia em operational + allowlist + não-dedup; este bloco foi dry-run.

_Mudança no caminho live (runtime/adapter). scanner não foi alterado. Telegram não enviado. Broker intocado. Scheduler horário inalterado._
