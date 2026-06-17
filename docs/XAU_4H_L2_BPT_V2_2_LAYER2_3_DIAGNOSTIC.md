# XAU 4H L2/BPT v2.2 — Camadas 2-3 Diagnostic (separação BOM vs NAO)

**Data:** 2026-06-17 · **Tipo:** DIAGNÓSTICO de separação (recall-first) · **NOT_VALIDATION / NOT_BACKTEST.**
**Sem PnL como validação, sem estratégia final, sem veto promovido, sem plotagem, sem MCP/chart, sem Telegram/broker/produção, sem SLIM.** RAW-only.

**Princípio:** recall primeiro → separação depois → performance só depois. **Regra dura:** nenhuma camada vira veto sem preservar o recall dos BOM_HIGH; medição em **nível de evento** (winner só é "perdido" se TODOS os candidatos dentro de ±2 barras dele forem cortados).

---

## 1. Executive summary

O Detector v2.2 gera **7763 candidatos** (2020-2026) e captura **17/17 GT BOM_HIGH** (backbone). Aplicando os **12 blockers causais canônicos** (de `L2_layer2_diagnostic_audit.py`, só diagnóstico) + tags de contexto causais à matriz completa, com recall medido em nível de evento:

- **7 camadas preservam 17/17** isoladamente (zero winners perdidos): `false_tipo_B_dump_direto`, `bear_flag`, `volume_fraco`, `no_absorption`, `no_polarity_defense`, `no_retest`, `overextended_entry`. São **redutores de densidade/ruído** seguros — não discriminadores BOM↔NAO.
- **4 camadas são PERIGOSAS** (matam ≥2 winners): `first_retomada` (mata **9/17**!), `BOS_fraco` (5), `bear_macro` (4), `cluster_BUY_climax` (2). Exatamente as que mais removem NAO também matam BOM → **jamais veto automático; só tag/human-review** (confirma o aprendizado antigo sobre `first_retomada`).
- **Conclusão honesta:** com o conjunto de contexto disponível no input v2.2 (bubbles, NAS, RSI, estrutura local, volume, ATR), **BOM e NAO NÃO são limpa­mente separáveis** por nenhuma camada mecânica isolada. As camadas servem para **reduzir ruído preservando recall**, não para separar winner de NAO. Isso aponta para as camadas **macro-estruturais ausentes do input** (at_D1_demand, macro-leg atlas, Custom OB demand/supply) como os prováveis discriminadores reais — **deferidas** (não estão no input congelado).
- **Redução de densidade segura (17/17 preservado):** união gulosa de camadas → **−41.1%** (7763→4575); ou pruning de fontes redundantes (`fractal_2_2`+`nivel_interno`+`topo_duplo`) → **−37%** (7763→4894). `fractal_3_3` é a **fonte sole-recall de 10/17 eventos** → backbone indrop­ável.

---

## 2. Detector v2.2 status

Candidate generator (não strategy). Recall 17/17 confirmado (`XAU_4H_L2_BPT_DETECTOR_V2_2_RECALL_AUDIT.md`). 1109 cand/ano. Lógica **não alterada** neste bloco — usado só como gerador. Input = RAW congelado (`/tmp/raw_features_2020_2026.jsonl`, cópia do safety pack) + 1D do `.gz`. Zero slim.

## 3. Candidate matrix

`results/l2_bpt_v2_2_candidate_matrix.csv` — **7763 linhas**, 1 por candidato. Campos: `candidate_id, ts, year, level, entry_close, source, variant, tipo, bos_mag_atr, label{BOM/NAO/UNKNOWN}, gt_id`, tags causais (`dist_pol_atr, sell_bub_10, large_sell_10, nas_near, nas_short_10, rsi, atr_pct`) + 12 flags `blk_*`. Label por proximidade ±2 barras ao Ground Truth.

Contagem: **GT_BOM_events=17** (71 candidatos-bar rotulados BOM), **NAO_events=8** (27 candidatos), **UNKNOWN=7665**. (NAO usado como **contraste**, não dataset completo — só 8 dos 10 NAO têm `entry_ts`.)

## 4. BOM vs NAO comparison

`results/l2_bpt_v2_2_gt_nao_comparison.csv` — 71 BOM + 27 NAO candidatos com tags completas.

Sinais direcionais (small-n, hypotheses-only):
- **Source:** BOM cand dominados por `fractal_3_3` (56/71); NAO cand mais espalhados em `topo_duplo` (9/27) e `fractal_3_3` (16/27). `topo_duplo` levemente NAO-leaning.
- **Tags de contexto** (sell_bub_10, nas_short_10, dist_pol_atr, rsi) **não separam** BOM de NAO de forma limpa no event-level — overlap alto. Nenhuma vira gate.

## 5. Layer diagnostics (event-level recall)

`results/l2_bpt_v2_2_layer_diagnostic.json`. "BOMkept/BOMlost" = eventos GT (de 17); "NAOrm" = eventos NAO removidos (de 8); "UNKcut" = candidatos UNKNOWN cortados (densidade).

| Camada | BOMkept | BOMlost | NAOrm | UNKcut | Papel recomendado |
|---|--:|--:|--:|--:|---|
| false_tipo_B_dump_direto | 17 | 0 | 0 | 0 | tag (já é o único veto duro v2.2) |
| no_absorption | 17 | 0 | 0 | 0 | tag |
| no_polarity_defense | 17 | 0 | 0 | 214 | **hard_veto_candidate** |
| no_retest | 17 | 0 | 0 | 234 | **hard_veto_candidate** |
| overextended_entry | 17 | 0 | 0 | 1775 | **hard_veto_candidate** |
| bear_flag | 17 | 0 | 0 | 1028 | **hard_veto_candidate** |
| volume_fraco | 17 | 0 | 1 | 2154 | **hard_veto_candidate** (melhor single) |
| CHoCH_not_BOS | 16 | 1 | 0 | 893 | human_review_reason |
| cluster_BUY_climax | 15 | 2 | 0 | 905 | reject as veto / tag |
| bear_macro | 13 | 4 | 3 | 1570 | reject as veto / tag |
| BOS_fraco | 12 | 5 | 3 | 3259 | reject as veto / tag |
| first_retomada | 8 | **9** | 5 | 4128 | **reject as veto** (mata winners) / human-review |

> "hard_veto_candidate" = preserva 17/17 isoladamente E corta ruído — **candidato a veto, ainda NÃO promovido** (Tarefa 3: nenhum blocker vira veto sem prova; classificado como reason/tag até validação independente).

## 6. Reason Atlas v2

`results/l2_bpt_v2_2_reason_atlas_v2.csv` — colunas `reason_id, description, preserved_BOM_count, cut_NAO_count, cut_UNKNOWN_count, recommended_role, confidence, notes`. Confidence = **low** em todas (GT BOM events=17, NAO events=8 — small-n; calibração, não validação — `feedback_calibration_vs_validation_45_groups`).

Roles: 5 `hard_veto_candidate`, 2 `tag` puros, 1 `human_review_reason`, 4 `reject as veto`. Mecânico-tag vs human-review-reason separados conforme Tarefa 3.

## 7. Density analysis

**Por que ~1109/ano:** `fractal_3_3` sozinho = **4223/7763 (54%)** dos candidatos; banda de entrada larga (low≤level+0.8ATR, close≥level−0.7ATR) + aceitação mínima (1 close) + 6 fontes de polaridade ⇒ muitos triggers.

Recall por fonte (sole-recall = eventos que SÓ aquela fonte captura):

| Source | candidatos | sole-recall events | papel |
|---|--:|--:|---|
| **fractal_3_3** | 4223 | **10/17** | backbone — indrop­ável |
| topo_duplo | 1832 | 0 | redundante; levemente NAO-leaning (ruído) |
| nivel_interno | 915 | 0 | quase-só-ruído (2 BOM cand, 0 sole) |
| swing_high_simples | 671 | 0 | redundante (GT27 também por outra fonte) |
| fractal_2_2 | 122 | 0 | quase-só-ruído (0 BOM cand) |

- **Path que captura BOM mas gera ruído demais:** `fractal_3_3` (recall alto E 54% do ruído — não dá para dropar, só filtrar por cima).
- **Paths quase-só-ruído:** `fractal_2_2`, `nivel_interno`.

## 8. Safe reductions preserving recall

Todas mantêm **17/17 BOM** (event-level):
1. **Single melhor:** `volume_fraco` → −28% (7763→5609), remove 1 NAO event. Mais simples.
2. **Pruning de fontes redundantes** (`fractal_2_2`+`nivel_interno`+`topo_duplo`) → **−37%** (7763→4894). Limpo, sem blocker.
3. **União gulosa de camadas 17/17-preserving** (`volume_fraco, bear_flag, no_retest, no_polarity_defense, false_tipo_B_dump_direto, no_absorption`) → **−41.1%** (7763→4575), remove 1 NAO event.

⚠️ **Achado metodológico:** a união *naive* das 7 camadas zero-BOM (incluindo `overextended_entry`) derruba **2 winners** (15/17) — camadas que isoladamente preservam recall podem, combinadas, matar winner. Por isso a redução segura usa a **união gulosa verificada** (recall re-checado a cada adição), não a soma. **≥15/17 (gate mínimo) é atingível com −57%, mas perde 2 winners → não recomendado** sob a regra dura "não cortar winners antes de justificar".

## 9. What remains unknown

- **Camadas macro-estruturais ausentes do input v2.2** (provavelmente os discriminadores BOM↔NAO reais): `at_D1_demand` v2, macro-leg / atlas block, Custom OB demand/supply, supply overhead, bear-control/top-distribution estrutural, first_retomada estrutural. Existem nas fontes do pack (`L2_BPT_AT_D1_DEMAND_DESIGN_V2.md`, `L2_BPT_MACRO_LEG_*`, `L2_BPT_REASON_ATLAS_v1.csv`) mas **exigem extração 1D/estrutural** → **deferidas**.
- NAS `x` field não é estritamente bars_ago (memory `feedback_nas_long_short_never_top_bottom`) — usado só como tag aproximada, nunca gate.
- n pequeno (17 BOM / 8 NAO events) → tudo **calibração**, não validação. Promoção de qualquer veto exige set independente.
- Performance (PnL/exit/gestão) **não medida** por design — fora do escopo deste bloco.

## 10. DA appendix

- Recall 17/17 preservado na base? ✅ gerador não alterado; medição event-level.
- Nenhuma camada virou veto prematuro? ✅ "hard_veto_candidate" = candidato, classificado tag/reason; nenhum promovido.
- Nenhum PnL chamado validação? ✅ zero PnL/outcome/target/stop neste bloco.
- NAO como contraste, não dataset completo? ✅ 8 eventos NAO como contraste; small-n declarado.
- SLIM não usado? ✅ RAW congelado + 1D do `.gz`.
- Produção intacta? ✅ receiver/cloudflared/xau-l1-cycle/broker/pause-flag não tocados.
- Caminho B não recomendado? ✅.
- Nenhum backtest de performance / nenhuma plotagem? ✅.

**DA verdict: PASS — separação diagnóstica executada em nível de evento; 7 camadas seguras de densidade identificadas, 4 perigosas isoladas; BOM↔NAO não separáveis mecanicamente com o contexto disponível (aponta camadas macro deferidas); recall 17/17 preservado; nada promovido a veto; produção intacta.**

---

*Read-only. RAW-only (zero slim). Diagnóstico (sem PnL/OOS). Outputs: este doc + `results/l2_bpt_v2_2_{candidate_matrix.csv, gt_nao_comparison.csv, reason_atlas_v2.csv, layer_diagnostic.json}`. Script: `/tmp/l2_layer23_diag.py` (regenerável; blockers verbatim de `L2_layer2_diagnostic_audit.py`).*
