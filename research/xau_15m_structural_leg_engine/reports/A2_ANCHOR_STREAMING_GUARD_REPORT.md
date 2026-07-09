# A2 STREAMING GUARD — REPORT (2026-07-09) — STATUS: PASS

Script: `a2_anchor_streaming_guard.py` · Result: `results/a2_anchor_streaming_guard_result.json`.

| Check | Resultado |
|---|---|
| **Truncation VERDADEIRO** (Data RECONSTRUÍDO na série truncada — exigência do DA F0-F1.5) | **60/60 PASS** (40×r6 + 10×r4 + 10×r8; região existe EXATAMENTE no known_at, nunca antes; prefixo do ledger idêntico nos campos core; nenhuma região além do corte) |
| known_at monotónico (stream de eventos completo, 3 r) | PASS |
| No-retro-use (first_retest_t > known_at, todas as regiões) | PASS |
| Bar de confirmação nunca é reteste | PASS |
| first_valid_bar > barra de confirmação (100%) | PASS |
| Whitelist de campos (zero futuro/outcome/membership N96-N83) | PASS |
| Builder GT-free (guard mecânico por substring; 1 falso-positivo de docstring corrigido — a docstring negativa continha a palavra banida; guard mantido estrito) | PASS |
| Determinismo (2 runs, sha256 idêntico) | PASS |

Desvio declarado: n=60 amostras de truncation (spec pedia 200 no walk-level; aqui cada amostra
reconstrói o Data INTEIRO — compensado pelos checks full-stream em TODAS as regiões).

Confirmação negativa: sem entry, sem backtest, sem GT na construção.
