# INCIDENTE DE FONTE — NAS/SMC (DERIVED_ARTIFACT_BUG) — 2026-06-23

## Resumo
Conclusão errada: "NAS/SMC stale/unreliable" foi declarada a partir de um **derivado**
(`repro_recovery/raw_features_2020_2026.jsonl`) **sem auditar o RAW original primeiro** — violação do RAW-first
(`feedback_raw_data_lookup_order`). A auditoria do RAW original provou que **NAS/SMC/bubbles/RSI são autênticos no RAW**.
Classificação: **DERIVED_ARTIFACT_BUG**, não RAW_SOURCE_ISSUE.

## Fonte canônica (autoridade)
`/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_*.jsonl.gz` — captura **as-of-bar** (causal):
| indicador | campo RAW ORIGINAL |
|---|---|
| NAS TOP/BOTTOM (LONG/SHORT) | `pine_labels["NAS TOP BOTTOM DETECTOR"]` (buffer ≤500 labels, **tail = recentes**) |
| LuxAlgo SMC (BOS/CHoCH/EQH/EQL) | `pine_labels["Smart Money Concepts [LuxAlgo]"]` |
| Market Order Bubbles (buy/sell s/m/L) | `pine_shapes_bubbles["Market Order Bubbles"].activations_per_plot` (BUY=plot_0/2/4, SELL=plot_6/8/10) |
| RSI + divergências | `study_values["Relative Strength Index"]` → `RSI`, `Regular Bullish`, `Regular Bearish` |
| SVP (Session Volume Profile) | bloco `..._SVP_LUX_RAW.jsonl.gz` campo `session_vp` |

## A causa
O buffer de labels é ordenado **oldest→newest** (NAS x 2..501, SMC x 11..1384; cauda = era atual). O derivado
`raw_features_2020_2026` extraía `nas_recent`/`smc_recent` da **CABEÇA** do buffer (labels de 2018-19) em vez da
**CAUDA** (recentes as-of-bar). Prova: para o ep #5826 (2023, close ~1831) o derivado tinha NAS prices 1276-1313;
o RAW tail tem 1862/1865 (era 2023). Idêntico em todos os episódios spot-check.

## Evidência (spot-check, RAW vs derivado-stale)
| ep | close RAW | NAS RAW (era correta) | derivado (head/stale) | RSI-div RAW |
|---|---|---|---|---|
| 5826 | ~1831 | LONG 1862/1865 | LONG 1276/1275 | — |
| 4401 | ~1647 | LONG 1638/1633 | LONG 1314/1300 | — |
| 5627 | ~1895 | SHORT 1980/1989 + LONG 1913 | LONG 1284 | — |
| 4918 | ~1814 | LONG 1828/1808 | LONG 1180 | **Regular Bullish ✓** |

## Correção mínima (sem nova fonte)
- `l2_bpt_raw_indicator_extract.py` — lê o RAW replay original, ancora a barra por close-match (RAW autoridade),
  extrai NAS/SMC por **tail as-of-entry** (causal, filtrado à era atual), bubbles via `activations_per_plot`,
  RSI+divergência de `study_values`. Saída: `results/l2_bpt_raw_indicator_events.jsonl` (reliability=RAW_AUTHENTIC).
- `l2_bpt_causal_indicator_layer.py` — consome SÓ esse artefato RAW; **GUARD DURO** que recusa
  `raw_features_2020_2026` como fonte de indicador.
- **pine_labels NÃO é fonte nova** — já É parte do RAW. Chart/prints = ferramenta visual auxiliar, nunca fonte.

## REGRA PERMANENTE (vale para TODO indicador, não só NAS/SMC)
**Todo indicador — NAS, SMC, bubbles, RSI, SVP, OB/supply-demand — vem do RAW original replay, nunca de derivado**
(`raw_features_2020_2026`/repro_recovery/frozen/slim/packet). Antes de declarar qualquer indicador ausente/stale:
auditar o RAW original primeiro. Derivado nunca valida disponibilidade real.
