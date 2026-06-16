# Re-derivação L1 sob regime_l1_v4 (2026-06-16) — research / NOT_VALIDATION

Diagnóstico após unificar `scanner.py` para usar **`regime_l1_v4`** (= regime que roda ao vivo no `runtime_xau.py`), resolvendo o split-brain (scanner usava `regime_B_v3`, declarado morto).

- `rederive_regime_l1v4.py` — reusa o **mesmo gate** da `scanner.py` (import, sem duplicar lógica), varre todos os bars do RAW canônico sob `regime_l1_v4`, compara com o set antigo (`rebuild_v3/trades.jsonl`, gerado sob `regime_B_v3`).
- `rederive_regime_l1v4.json` — output.

## Resultado (in-sample, NÃO é prova de edge)
| | valor |
|---|---|
| set antigo (regime_B_v3) | 38 candidatos |
| set novo (regime_l1_v4) | **63 candidatos** (59 operational, 4 blocked_exhaustion) |
| preservados | **38/38** |
| removidos | **0** |
| novos sob regime live | **+25** |

- **#1/#11/#36/#38** (preservados, não-RSI-blocked): seguem `operational_candidate` ✅
- **#3/#15/#18/#32** (RSI-blocked): seguem `blocked_exhaustion` (RSI gate é regime-independente) ✅

## Leitura crítica (Devil's Advocate)
`regime_l1_v4` é **mais permissivo** que `regime_B_v3` para este universo: **+25 candidatos novos (+66%)** que o regime antigo bloqueava. **Consequência:** os números históricos do set de 38 (FULL-38 +14.9R, KEEP-19 +32.6R) **NÃO representam o regime que roda ao vivo** — há 25 bars de outcome desconhecido. Os números antigos continuam **research/in-sample**; o set de 63 também é in-sample e **não foi avaliado em R** (isso exige gate manifest + RAW OOS, próximo passo). Nada aqui prova edge.
