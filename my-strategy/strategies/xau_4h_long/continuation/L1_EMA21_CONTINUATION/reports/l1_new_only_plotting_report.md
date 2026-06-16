# Plotagem L1 NEW_ONLY (25) — revisão visual manual (2026-06-16)

Plotados os **25 candidatos NEW_ONLY** (admitidos pelo regime_l1_v4, ausentes no regime_B_v3) no chart 4H, para sua revisão visual. Fonte: `l1_old_vs_new_regime_comparison.csv` (filtro `status==NEW_ONLY`). Outcome **UNKNOWN** — plotagem é para olhar no chart, não conclusão estatística.

## Resultado
- **25 NEW_ONLY encontrados?** SIM (25/25).
- **25 plotados?** **SIM (25/25, 0 com dado ausente).**
- **Símbolo/timeframe:** PEPPERSTONE:XAUUSD / **240** (confirmado antes e depois).
- **Chart:** deixado em **240** (revisão visual exige 4H; NÃO restaurado a outro TF).
- **Telegram:** nenhum. **Broker:** intocado. **Produção/runtime/scheduler/scanner/gates:** não tocados.

## Formato canônico usado
Como os NEW_ONLY **não têm entry/stop/target** no CSV (vieram do regime, não de um trade com exit policy), **não inventei preço de trade**. Por candidato:
- **`vertical_line`** no candle de entrada (preço-âncora = close real do bar).
- **label `text`**: `NEW_ONLY #<id> L <regime_old>->BULL` ancorada no high real do bar (×1.004).
- LONG. Sem Long Position (sem stop/target definidos). Desenhos existentes **não** foram apagados/movidos.

## Os 25 (id · data · regime_B_v3 antigo → regime_l1_v4)
Todos LONG, todos 4H, todos `operational_candidate` sob regime_l1_v4. Sob o regime antigo: 18 TRANSITION, 2 BEAR (2022-05-27, 2022-05-30 — long em regime de baixa antigo, atenção), 2 BULL (2026-01-15, 2026-01-20 — eram BULL mas caíram fora dos 38 por cooldown/TZ), 3 sem entrada daily (2020-12-06, 2022-05-29, 2025-11-09). Lista completa + `rsi_vs_ma` por candidato no CSV.

## Dados insuficientes
Nenhum. Os 25 foram localizados no RAW canônico e plotados. (Não havia entry/stop/target a usar — por isso marcador simples, conforme regra.)

## Próximos passos
**Revisão visual manual sua** no chart 4H: avaliar se os NEW_ONLY parecem continuações válidas ou ruído (especialmente os 2 em regime BEAR antigo). Isso informa a decisão de manter regime_l1_v4 live ou tightenar para aproximar o regime_B_v3. Nenhuma classificação automática winner/loser foi feita.

_Helper: `plot_new_only.py` (read-only sobre dados; só desenha). Resultado bruto: `l1_new_only_plotting_result.json`._
