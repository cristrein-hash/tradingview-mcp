# XAU 4H L2/BPT — Opção B: DATASET STATUS (amostra independente bear→bull)

**Status:** `DATASET REGISTERED · 2013-2016 ARCHIVED (PASS) · 2016-2017 COLLECTING · LOCAL RAW RETAINED` · **Data:** 2026-06-18
Registro/status dos datasets RAW independentes coletados para a validação do L2/BPT Trade Qualification Engine fora do bull 2020-2026. Source-of-truth = gz externo + manifest + sha. Foundation: [[XAU_4H_L2_BPT_OPTION_B_BEAR_VALIDATION_PLAN]].

## Bloco 1 — BEAR 2013-2016 (✅ coletado + arquivado + validado)
| campo | valor |
|---|---|
| range real | 2013-01-31T23:59:59Z → 2016-05-25T01:59:59Z |
| bars | 5100 (5076 ts únicos, 24 dup ~0.47%, 0 out-of-order) |
| qualidade | 0 JSON inválido, 0 `_error`, 6/6 fontes 5100/5100 |
| fontes | ohlcv, study_values, pine_boxes, pine_labels, pine_shapes_bubbles, pine_lines |
| indicadores | Custom OB Detector, LuxAlgo SMC, NAS Top Bottom, Market Order Bubbles, RSI, Volume |
| gz (source-of-truth) | `/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_2013-02-01_to_2016-05-25.jsonl.gz` (68.6 MB) |
| manifest | `/Volumes/GUTS_ LACIE/TradingData/manifests/XAUUSD_240m_replay_2013-02-01_to_2016-05-25_manifest.txt` |
| sha256 original | `349c2b69e5cbf59965309581b0ebad0cdb95cf01df13a811e38c9d3f3ac3b713` |
| sha256 gz | `6175e11fa4be57f3c66c4f9a6a1f8a8511995004a1410fc9a6a6d034469f201e` |
| integridade | `gzip -t` OK · roundtrip sha256 == original ✓ |
| local RAW | `alert-bridge/logs/backtests/XAUUSD_240m_replay_2013-02-01_to_2016-05-25.jsonl` (558 MB) — **RETIDO (delete pendente de autorização)** |
| regime | gold BEAR 2013-2015 + crash abr/2013 + fundo dez/2015 + início recuperação 2016 |

## Bloco 2 — TRANSIÇÃO/BULL inicial 2016-2017 (🔄 coletando — Parte 2)
Range alvo: 2016-05-25 → 2017-12-31. Mesmo padrão de coleta/arquivamento. Status/qualidade serão anexados ao concluir (hard-stop se falhar qualidade).

## Registro
- Registry: `docs/data/dataset_registry.json` (regenerado por `scripts/build_dataset_registry.py` a partir dos manifests).
- Audit: `results/l2_bpt_option_b_dataset_audit.csv`.
- **Source-of-truth = gz externo** (cold storage). Produção NÃO depende do HD externo.
- **Pendência:** local RAW retido nos 2 blocos; deletar só após gz+sha+roundtrip+manifest validados E aprovação explícita do Cris.

---
*Status documental. Sem produção/plotagem/SLIM/cross-asset. Local RAW retido.*
