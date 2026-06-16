# Plotagem CANÔNICA L1 NEW_ONLY (25) — revisão visual (2026-06-16, v2)

Plotados os **25 NEW_ONLY** (regime_l1_v4) como **`long_position` nativo do TradingView** no chart 4H, para revisão visual. Substitui a v1 (vertical_line+texto — ERRADO, descartado).

## Formato canônico (convenção `alert-bridge/draw_xau_4h_trades.py`)
Por entrada:
- **entry** = close do bar candidato.
- **SL = ESTRUTURAL** = low da zona de demanda Custom OB tocada (ou swing low dos últimos 10 bars se sem OB) **− 0.1×ATR**.
- **TARGET = +3R** = entry + 3 × (entry − SL).
- `long_position` com `stopLevel`/`profitLevel` em **TICKS** (mintick XAU = 0.01), `point`=entry, `point2`=(entry+20 bars, target).
- label curto `#<candidate_id>` (azul, fonte 10) acima do target — sem poluição.

## Resultado
- **25 NEW_ONLY encontrados?** SIM (25/25).
- **25 plotados?** **SIM — 25 long_position, 0 skipped.**
- **Símbolo/timeframe:** PEPPERSTONE:XAUUSD / **240** (confirmado).
- **Chart:** deixado em **240** (revisão visual exige 4H).
- **Dados insuficientes:** nenhum (todos com entry/SL estrutural/target calculados de dados reais; risco>0 em todos).
- **Desenhos pré-existentes:** `draw_list` = 0 → nada seu foi apagado. Não usei `draw_clear`.
- **Telegram:** nenhum. **Broker:** intocado. **Runtime/scanner/scheduler/gates/RAW:** não tocados.

## Detalhe por trade
Entry / SL estrutural / target(3R) / risco / fonte-do-SL por candidato em `l1_new_only_plotting_result.json` (campo `trades`).

## Próximo passo
**Sua revisão visual** dos 25 long_position no 4H: avaliar se o SL estrutural + alvo 3R fazem sentido em cada entrada, com atenção aos 2 em regime BEAR antigo (2022-05-27, 2022-05-30). Decide manter regime_l1_v4 live ou tightenar.

_Helper: `plot_new_only.py` (read-only sobre dados; só desenha long_position). NÃO calcula winner/loser; é visual._
