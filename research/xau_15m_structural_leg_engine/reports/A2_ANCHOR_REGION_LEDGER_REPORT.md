# A2 ANCHOR REGION LEDGER — REPORT (2026-07-09)

Script: `a2_anchor_region_ledger.py` · Result: `results/a2_anchor_region_ledger_result.json` ·
Ledgers completos: `results/a2_regions_r{4,6,8}.jsonl` + `results/a2_events_r{4,6,8}.jsonl` (append-only).
Spec: `XAU_15M_A2_ANCHOR_ONLY_SPEC_20260709.md` v1.1 (congelada pré-código; DA pré-código aplicado).

## O que foi construído
Máquina simétrica de ciclos 15M price-only sobre as 49.804 barras CLOSED do F0 (RAW HD, sha-verified):
flip por threshold r_cycle·ATR15 → publica região no FECHO da barra de confirmação (known_at=t+900);
bandas por heranças congeladas (0,1/0,7 ATR); topo rompido por close → `converted_support` (evento
versionado — tese dos 35 prints); invalidação por close através; retestes REGISTADOS (entry NÃO
existe); contexto = macro v5 verbatim; warmup 400 barras; GT ausente do builder (guard mecânico).

## Números por r (grid pré-registado {4,6,8})
| r | regiões | fundos/sem | converted_support | latency p50/p90 (barras) | traps pos96 |
|---|---|---|---|---|---|
| 4 | 1.396 | 6,4 | 666/698 topos | 16 / 36 | 36 |
| 6 | 732 | 3,4 | 343/366 | 27 / 59 | 5 |
| 8 | 456 | 2,1 | 211/228 | 40 / 85 | 0 |

- `no_entry_on_confirmation` computado e TRUE em 100% das regiões (guard asserido).
- **Trap real medido** (métrica exigida pelo DA pré-código): retested→invalidated =
  92-98% conforme contexto/r — o reteste de região-fundo é maioritariamente seguido de quebra;
  qualquer F2 terá de discriminar DENTRO do reteste (não bastará tocar a banda).

## Confirmação negativa
Sem entry · sem indicadores · sem backtest · sem GT na construção · sem produção/Telegram/broker/chart.
