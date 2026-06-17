# XAU 4H L2/BPT PRUNED_BASE_V2 — Outcome / Anatomy Labeling

**Status:** `MECHANICAL_PROXY · NOT_BACKTEST · NOT_VALIDATION · PARTIALLY_CALIBRATED` · **Data:** 2026-06-17
**RAW-only (frozen OHLC) · sem estratégia/catalog/produção/Telegram/broker/L1/SLIM/plot/pruning novo.** MFE/MAE são análise **post-hoc** (entrada não usa futuro).

---

## 1. Executive summary

Mediu-se forward anatomy (MFE/MAE em ATR, janelas 6/12/24/36) dos 2965 candidatos. **Calibração é PARCIAL e honesta:**
- **BOM: 13/17 em continuation** (9 STRONG + 4 GOOD) ✅ — o labeling captura bem o lado winner.
- **NAO: só 2/6 em failure** (3 NEEDS_VISUAL, 1 até GOOD_CONTINUATION) ✗ → **`calib_ok = False`**. O proxy **NÃO é confiável como detector de NAO** (NAO não se separam mecanicamente; n=6).
- **Conclusão:** o labeling é **confiável no lado continuation (BOM), não confiável no lado failure (NAO)**. UNKNOWN: ~1291 continuation, ~839 noise/invalidated, 404 visual — **indicativo, não verdade** no lado failure.

## 2. Por que este bloco era necessário

Antes de mais filtros, era preciso saber **o que há dentro dos 2965**. Sem outcome/anatomy, qualquer filtro adicional era cego.

## 3. Fonte/base

PRUNED_BASE_V2 (2965; 39 candidatos-BOM/17 eventos, 14/6 NAO, 2912 UNKNOWN). OHLC do input congelado (causal). Tags de `demand_supply_quality` + `candidate_matrix`. **Nota:** `overextended_entry`/`bear_flag`/`src_redundant` aparecem 0% em todo cruzamento **porque a base V2 já os excluiu** (não é sinal, é construção).

## 4. Métricas de forward anatomy

Por janela W∈{6,12,24,36}: `mfe_atr`, `mae_atr`, `cret_atr`, atingiu +1/2/3/4 ATR, caiu −1/−2 ATR, `inval` (close<polaridade). Mais: `mae_before` (adverso antes do pico MFE), `t_mfe`. **Proxy mecânico, não SL/target real** (v2.2 não tem SL → sem R final).

## 5. Calibração BOM/NAO

| Grupo | continuation | failure | ambíguo | veredito |
|---|--:|--:|--:|---|
| BOM (17) | **13** (9 STRONG+4 GOOD) | 1 (STRUCTURE_INVALIDATED) | 3 NEEDS_VISUAL | ✅ confiável |
| NAO (6) | 1 (GOOD) | **2** (STRUCTURE_INVALIDATED) | 3 NEEDS_VISUAL | ✗ **não confiável** |

→ **calib_ok=False.** Continuation-side calibrado; failure-side falha (esperado: NAO não se distinguem de BOM por anatomia simples). Fragile BOM: GT13B STRONG, GT23 STRONG, GT24 GOOD, **GT17A NEEDS_VISUAL** (→ fila visual).

## 6. Classificação dos UNKNOWN

`results/l2_bpt_pruned_base_v2_unknown_classification.csv` (2912):
| classe | n |
|---|--:|
| STRONG_CONTINUATION | 864 |
| GOOD_CONTINUATION | 427 |
| WEAK_CONTINUATION | 370 |
| STRUCTURE_INVALIDATED | 801 |
| NEEDS_VISUAL_REVIEW | 404 |
| TOP_SWEEP_REVERSAL | 38 |
| FAILED_RECLAIM | 8 |

**~1291 continuation forte/boa · ~839 noise/invalidated · 404 visual.** ⚠️ Dado calib_ok=False, o lado failure (STRUCTURE_INVALIDATED, TOP_SWEEP) é **indicativo, não verdade** — não promover nem podar com base nisso.

## 7. Cruzamento com demand/supply

`STRONG/GOOD` (n=1324): supply≤1ATR 31% · demand_supporting 52% · nas_short≥5 54%.
`TOP_SWEEP_REVERSAL` (n=38): supply≤1ATR 13% · demand_supporting 32% · nas_short≥5 60%.
`FAILED_RECLAIM` (n=8): demand_supporting 62%.
→ **demand_supporting_retest** é mais comum em continuation (52% vs 32% em top-sweep) — consistente com o esperado, mas fraco. supply≤1ATR **não** concentra failure aqui (top-sweep tem MENOS supply-perto, 13%) — contradiz a hipótese supply-near=loser; small-n (38/8). CHOP=0 (a base não tem chop puro).

## 8. Cruzamento com Reason Atlas

`overextended`/`bear_flag` = 0% (excluídos pela base). `nas_short≥5` é alto em todas as classes (54-60%) → **não discrimina**. As tags fortes da base não separam anatomy — reforça que o discriminador real ainda falta (macro/visual).

## 9. Grupos de alta prioridade visual

`results/l2_bpt_pruned_base_v2_visual_review_queue.csv`: (a) **GT17A** (BOM frágil, anatomy ambígua); (b) os 6 NAO (calibração falhou — entender por que não parecem failure); (c) 1 BOM STRUCTURE_INVALIDATED; (d) amostra dos 864 UNKNOWN STRONG_CONTINUATION (parecem winners — checar se são L2/BPT reais ou continuations genéricas).

## 10. O que ainda não sabemos

- Outcome **real** (sem SL/target confiável → só anatomy proxy). Não é backtest.
- Por que os NAO não parecem failure por anatomia (looked-good-then-reversed após a janela? ambíguos?) — **visual**.
- Se os 864 UNKNOWN STRONG são setups L2/BPT válidos ou continuations genéricas capturadas pelo gerador permissivo.
- calib_ok=False → **não confiar no lado failure**; não podar com isto.

## 11. DA appendix

- Não chamou proxy de backtest final? ✅ `MECHANICAL_PROXY / NOT_BACKTEST / NOT_VALIDATION`.
- SLIM? ❌. MFE/MAE usaram futuro só para análise posterior, não para entrada? ✅ (entrada = close do bar, forward = i+1..i+W).
- BOM/NAO usados para calibrar? ✅ — e calibração reportada como **PARCIAL/False** honestamente.
- UNKNOWN promovidos? ❌. Filtro final criado? ❌. Plotagem? ❌. Produção intacta? ✅. Caminho B? ❌.

**DA verdict: PASS — anatomy medida; BOM continuation confirmada (13/17), NAO failure NÃO confirmada (2/6, calib_ok=False) → labeling confiável só no lado continuation; UNKNOWN mapeado como indicativo; nada promovido/podado; produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_pruned_base_v2_outcome_anatomy.csv`, `_outcome_anatomy_summary.json`, `_unknown_classification.csv`, `_visual_review_queue.csv`. Script: `outcome_anatomy.py` (py_compile OK). Proxy mecânico, não validação.*
