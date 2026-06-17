# XAU 4H L2/BPT v2.2 — PRUNED BASE V2 (base seletiva, recall 17/17 preservado)

**Status:** `CANDIDATE_BASE · NOT_STRATEGY · NOT_VALIDATION · RECALL_PRESERVED_17_17 · DENSITY_REDUCED_61_8_PERCENT · WORKING_BASE_FOR_DEEPER_CONTEXT_ANALYSIS`
**Data:** 2026-06-17 · RAW-only · **sem backtest/PnL, sem estratégia, sem promoção de veto, sem plotagem, sem MCP/chart, sem Telegram/broker/produção, sem SLIM.**

---

## 1. Executive summary

Formalizada a base seletiva **L2_BPT_V2_2_PRUNED_BASE_V2** = regra `overextended_entry + src_redundant + bear_flag` (união: prune se qualquer um dispara). Reproduzida exatamente: **7763 → 2965 candidatos (−61.8%)**, ~424/ano, **recall 17/17 BOM preservado** (event-level), 4 frágeis intactos, `fractal_3_3` backbone preservado (2592). NAO 8/8→6/8. É **base de candidatos** para análise de contexto mais profunda — não estratégia, não validação, não mede edge.

## 2. Por que a base V2 foi aprovada

O cross-factor diagnostic (commit `477f59a`: 136 combos de 2 fatores + 81 de 3 + 10 interações obrigatórias) identificou esta combinação como a **maior redução de ruído preservando 17/17**. Cris a aprovou como nova base de trabalho, mais enxuta que a V1 (−41%) mas ainda ampla. Pruning aqui = limpar a base, **não** decidir trades.

## 3. Regra V2

**Prune (remove) o candidato se** `overextended_entry == 1` **OR** `src_redundant` (source ∈ {fractal_2_2, nivel_interno, topo_duplo}) **OR** `bear_flag == 1`. Caso contrário, **kept**. Reproduzível: `.../v1/build_pruned_base_v2.py` (py_compile OK), lê `results/l2_bpt_v2_2_candidate_matrix.csv`.

## 4. Comparação P0/P1/P2/P3

| Versão | Regra | Candidatos | −% | /ano | Recall | NAO | UNKcut | Complexidade | Risco |
|---|---|--:|--:|--:|:--:|:--:|--:|---|---|
| **P0** | original | 7763 | 0 | 1109 | 17/17 | 8/8 | 0 | — | — |
| **P1** v1 | união gulosa 6 blockers | 4575 | 41.1 | 654 | 17/17 | 7/8 | 3151 | média | baixo |
| **P2** v2 ✅ | overext+src_redundant+bear_flag | **2965** | **61.8** | **424** | **17/17** | 6/8 | 4753 | baixa (3 fatores) | baixo (frágeis OK) |
| P3 ref | volume_fraco × bear_flag | 4857 | 37.4 | 694 | 17/17 | 7/8 | 2870 | mínima | baixo |
| P3 ref | fractal_3_3 × overextended (∩) | 6563 | 15.5 | 938 | 17/17 | 8/8 | 1180 | mínima | mínimo |

P3 = referência apenas (não escolhidas). V2 corta mais ruído com 3 fatores simples.

## 5. Recall BOM 17/17

`results/l2_bpt_v2_2_pruned_base_v2_gt_recall.csv` — todos os 17 com `captured_in_pruned_v2=yes`. Comparação por evento: capturado em original / v1 / v2. **Nenhum BOM perdido** (regra de hard-stop no script: se algum BOM caísse, V2 não seria formalizada). Min survivors = **1** (eventos frágeis).

## 6. Proteção dos 4 BOM frágeis

GT13B, GT17A, GT23, GT24 = **preservados** (cada um com ≥1 candidato survivor). ⚠️ A combinação borderline `volume_fraco × overextended_entry` mata **GT13B e GT24** — por isso `volume_fraco` **não** entra na regra V2; só `overextended_entry` (que isolado e nesta tríade preserva os 4). Qualquer extensão futura da regra deve re-checar esses 4 explicitamente.

## 7. NAO / UNKNOWN

- **NAO antes:** 8/8 capturados. **Depois:** 6/8 (cortados **GT07, GT17B**; permanecem GT04A, GT06A, GT06B, GT12, GT14_NAO, GT19A).
- **UNKNOWN:** cortados **4753**, remanescentes **2912**.
- **Por que ainda não separa BOM↔NAO:** mesmo a −61.8%, só **2/8 NAO** são cortados → V2 reduz **ruído UNKNOWN**, não resolve a separação BOM↔NAO. Os 6 NAO remanescentes passam pelos mesmos filtros de qualidade local que os BOM. Os discriminadores reais provavelmente exigem **camadas macro-estruturais ainda INDISPONÍVEIS** no input v2.2: `at_D1_demand`, `supply_overhead`, `Custom OB demand/supply`, `macro_leg`. Detalhe em `results/l2_bpt_v2_2_pruned_base_v2_nao_unknown.csv`.

## 8. Source/path density

`results/l2_bpt_v2_2_pruned_base_v2_source_density.csv`. `src_redundant` zera topo_duplo/nivel_interno/fractal_2_2 na base. `fractal_3_3` permanece **2592** (backbone, sole-recall de 10/17 — **nunca removido**). swing_high_simples remanescente parcial. A base V2 é dominada por fractal_3_3 + parte de swing_high_simples.

## 9. Explicação dos fatores

**1. overextended_entry** — entry close > polaridade + 1.0·ATR (entrada esticada acima do nível). *Remove ruído:* entradas longe da polaridade têm pior R estrutural / são FOMO. *Isolado preserva 17/17* (os BOM entram tipicamente ≤1ATR acima — mediana dist_pol 0.74). *Combinado precisa recall-check* porque com volume_fraco mata GT13B/GT24. **Role:** density reducer / structural reason. **Confidence:** média (calibração 17/8). **Limitation:** threshold 1.0ATR não validado OOS.

**2. src_redundant** — source ∈ {fractal_2_2, nivel_interno, topo_duplo}. *Lever mais limpo:* essas fontes têm **sole-recall 0** (nenhum BOM só elas capturam) e geram ~54% do ruído combinado. *fractal_3_3 permanece intacto* (backbone, sole-recall 10/17). **Role:** source-pruning. **Confidence:** alta (estrutural, não threshold). **Limitation:** assume estabilidade do mapeamento de fontes do detector v2.2.

**3. bear_flag** — nos 15 bars antes do pivot, existe ≥1 candle bear com range ≥1ATR e pavio superior ≥60% (bandeira de baixa / rejeição). *Corta ruído:* contexto de perna bear forte degrada o setup de reclaim. *NÃO confundir com `bear_macro`* (este usa close diário < SMA200_D e **mata 4/17 BOM** → perigoso); `bear_flag` é **local e preserva 17/17**. **Role:** risk tag / structural reason. **Confidence:** média. **Limitation:** lookback 15 fixo; small-n.

## 10. Fatores proibidos / perigosos

**NÃO usar como veto** (cortam BOM): `first_retomada`, `nas_short_ge5`, `BOS_fraco`, `bear_macro`, `cluster_BUY_climax`.
- `first_retomada + nas_short_ge5` mata **14/17** BOM. `first_retomada` mata 9/17 sozinho.
- `nas_short` pode ter valor como **tag / human-review reason** (BOM tem mediana NAS-SHORT menor que NAO), mas **nunca como veto** (variância mata BOM).
- **Borderline (NÃO base):** `volume_fraco × overextended_entry` = 15/17, mata GT13B + GT24. Registrado apenas como borderline.

## 11. Por que V2 é melhor que V1

- Corta mais ruído: −61.8% vs −41.1% (2965 vs 4575), preservando o mesmo 17/17.
- Regra mais simples: 3 fatores (vs 6 na união gulosa V1).
- Inclui `src_redundant` (lever estrutural mais limpo) + `overextended_entry` (geometria de entrada) — fatores com leitura estrutural clara, não só blockers de qualidade.
- Mantém backbone fractal_3_3 e os 4 frágeis.

## 12. Limitações

- **Não é estratégia, não é validação, não mede edge.** Só candidate set mais limpo.
- Não separa BOM↔NAO (6/8 NAO permanecem) — discriminadores macro deferidos/indisponíveis.
- Margem frágil: 4 eventos com survivor único.
- Thresholds (overextended 1.0ATR, bear_flag 15b) = calibração sobre 17/8, não validados OOS.
- Sem PnL/exit/gestão.

## 13. Status correto

**L2_BPT_V2_2_PRUNED_BASE_V2** = `CANDIDATE_BASE · NOT_STRATEGY · NOT_VALIDATION · RECALL_PRESERVED_17_17 · DENSITY_REDUCED_61_8_PERCENT · WORKING_BASE_FOR_DEEPER_CONTEXT_ANALYSIS`. **Catalog/strategy_rules/produção NÃO atualizados** (exigem autorização explícita).

## 14. Próximas análises possíveis sobre V2 (sem recomendar execução automática)

- Extrair camadas macro-estruturais (at_D1_demand v2, macro-leg atlas, Custom OB demand/supply, supply_overhead) e medir separação BOM↔NAO sobre os 2965.
- Análise visual dos 6 NAO remanescentes (por que sobrevivem aos filtros de qualidade) e dos 4 frágeis.
- Caracterizar os 2912 UNKNOWN remanescentes por contexto.
- Recall-gate permanente antes de qualquer censo/backtest sobre a base.
- Só então (bloco separado, com autorização): exit/gestão e performance.

## 15. DA appendix

- Regra reproduziu 2965? ✅ exato (7763→2965, −61.8%).
- 17/17 BOM preservados? ✅ event-level, hard-stop no script.
- 4 frágeis preservados? ✅ GT13B/GT17A/GT23/GT24.
- Recall rechecado após combinação? ✅.
- fractal_3_3 preservado? ✅ 2592.
- overextended_entry não usado com combinação que mata BOM? ✅ (volume_fraco fora da regra).
- first_retomada / nas_short_ge5 viraram veto? ❌ não — proibidos (seção 10).
- volume_fraco × overextended_entry só como borderline? ✅.
- Não promoveu estratégia / não mediu PnL / não chamou validação? ✅✅✅.
- SLIM? ❌ não. Plotagem? ❌ não. Produção tocada? ❌ não. Caminho B? ❌ não recomendado.

**DA verdict: PASS — V2 formalizada e reproduzida exatamente; recall 17/17 event-level; frágeis e backbone preservados; fatores perigosos isolados; nada promovido a estratégia/veto/validação; produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_v2_2_pruned_base_v2{.csv, _removed.csv, _gt_recall.csv, _summary.json, _nao_unknown.csv, _source_density.csv}`. Script: `.../v1/build_pruned_base_v2.py` (regenerável da matriz de candidatos).*
