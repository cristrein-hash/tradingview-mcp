# XAU 4H L2/BPT v2.2 — Cross-Factor Diagnostic (BOM vs NAO vs UNKNOWN)

**Data:** 2026-06-17 · **Status:** `DIAGNOSTIC · NOT_STRATEGY · NOT_VALIDATION · RECALL_FIRST`
**Sem backtest/PnL, sem promoção de veto, sem plotagem, sem MCP/chart, sem Telegram/broker/produção, sem SLIM.** RAW-only. Recall medido em **nível de evento** (BOM perdido só se TODOS os candidatos do evento forem cortados).

---

## 1. Executive summary

Cruzamentos específicos de fatores sobre a matriz completa (7763 candidatos, 17 eventos BOM / 8 NAO). **136 combinações de 2 fatores** testadas: **34 SAFE (17/17)**, 28 BORDERLINE (15-16/17), 74 DANGEROUS (<15/17). 81 combinações de 3 fatores (shortlist).

- **Melhor redução preservando 17/17:** `overextended_entry + src_redundant + bear_flag` → **−61.8%** (7763→2965, ~424/ano), 4 frágeis preservados, NAOcut 2/8.
- **Fator único mais potente e seguro:** `src_redundant` (dropar fontes redundantes) — aparece em quase todas as top-SAFE; combina bem com `bear_flag`/`volume_fraco`.
- **Achado estrutural:** NAO **resiste** (só 2/8 eventos cortados mesmo a −62%). As combinações seguras reduzem **ruído UNKNOWN**, não separam BOM↔NAO. Confirma: discriminadores reais são macro-estruturais (deferidos, ausentes do input v2.2).
- **Confirmação metodológica:** `volume_fraco × overextended_entry` (2 camadas individualmente seguras) mata **GT13B e GT24** (15/17) → união NÃO preserva recall por composição. `nas_short_ge5` apesar de mediana NAO>BOM, é DANGEROUS como veto (mata BOM) — sinal de mediana ≠ filtro seguro.

## 2. Por que este bloco é mais específico

A pedido de Cris: nada de análise genérica multi-camada. Cada combinação é auditável com métricas explícitas (BOM preservado/perdido, NAO cut, UNKNOWN cut, densidade, frágeis, risco) e classe. Interações obrigatórias testadas nominalmente. Nenhuma vira veto.

## 3. Fatores disponíveis

**Disponíveis (campos reais da matriz, nenhum inventado):**
- `source` / `src_redundant` (fractal_2_2, nivel_interno, topo_duplo) · 12 blockers causais (`false_tipo_B_dump_direto, CHoCH_not_BOS, first_retomada, bear_flag, BOS_fraco, cluster_BUY_climax, bear_macro, volume_fraco, no_absorption, no_polarity_defense, no_retest, overextended_entry`).
- Derivados de tags reais: `nas_short_ge5` (NAS SHORT recente ≥5), `dist_pol_lt04` (dist-to-polaridade <0.4 ATR), `rsi_lt50`, `atr_pct_lt03`.

**INDISPONÍVEIS no input v2.2 (não inventados, marcados como ausentes):** `at_D1_demand`, `macro_leg_block`, `supply_overhead`, `Custom OB demand/supply`. Exigem extração 1D/estrutural → deferidos.

Sinais de mediana (contexto, não filtro): BOM tem **menos** NAS-SHORT (3 vs NAO 5), **maior** dist-pol (0.74 vs 0.37), **maior** RSI (59 vs 51), maior atr_pct.

## 4. 2-factor matrix

`results/l2_bpt_v2_2_cross_factor_matrix.csv` (136 linhas). Classes: 34 SAFE / 28 BORDERLINE / 74 DANGEROUS. Top SAFE 2-fatores por UNKNOWN cut: `overextended_entry+src_redundant` (−55.7%, UNKcut 4284), `src_redundant+bear_flag`, `volume_fraco+src_redundant`. Todas com `src_redundant` como núcleo.

## 5. 3-factor shortlist

`results/l2_bpt_v2_2_top_safe_combinations.csv`. Top SAFE 3-fatores (17/17, frágeis OK):

| Combo | −% | UNKcut | NAOcut |
|---|--:|--:|--:|
| overextended_entry+src_redundant+bear_flag | 61.8 | 4753 | 2 |
| src_redundant+dist_pol_lt04+bear_flag | 60.2 | 4639 | 2 |
| volume_fraco+dist_pol_lt04+bear_flag | 60.1 | 4617 | 2 |
| volume_fraco+src_redundant+bear_flag | 60.0 | 4612 | 2 |
| src_redundant+dist_pol_lt04+no_retest | 56.9 | 4379 | 2 |

## 6. Interações obrigatórias (Tarefa 5)

| Interação | BOM | NAOcut | UNKcut | frágeis | classe |
|---|:--:|--:|--:|:--:|---|
| 1. volume_fraco × overextended_entry | **15/17** | 1 | 3681 | ❌ (mata GT13B, GT24) | BORDERLINE |
| 2. volume_fraco × bear_flag | 17/17 | 1 | 2870 | ✅ | SAFE |
| 3. volume_fraco × no_retest | 17/17 | 1 | 2331 | ✅ | SAFE |
| 4. overextended × bear_context (bear_flag*) | 17/17 | 0 | 2578 | ✅ | SAFE |
| 5. no_polarity_defense × no_absorption | 17/17 | 0 | 214 | ✅ | SAFE (fraco) |
| 6. no_retest × false_tipo_B_dump_direto | 17/17 | 0 | 234 | ✅ | SAFE (fraco) |
| 7. bear_flag × nas_short_ge5 | **9/17** | 4 | 4937 | ❌ | DANGEROUS |
| 8. supply_overhead × cluster_BUY_climax | — | — | — | — | **UNAVAILABLE** (supply ausente) |
| 9. at_D1_demand_false × bear_macro | — | — | — | — | **UNAVAILABLE** (at_D1_demand ausente) |
| 10. fractal_3_3 × risk tag (intersecção alvo) | ver abaixo | | | | |

\* supply indisponível → `bear_flag` como proxy declarado.

**#10 fractal_3_3 × tag (intersecção — só candidatos fractal_3_3 COM o risco):** cirúrgico, preserva backbone. SAFE: `× overextended_entry` (17/17, UNKcut 1180), `× volume_fraco` (1115), `× bear_flag` (571). DANGEROUS: `× first_retomada` (10/17), `× BOS_fraco` (12/17) — os killers matam BOM mesmo restritos ao fractal_3_3.

**Leitura estrutural:**
- volume/overextended/bear_flag/no_retest fazem sentido (entrada esticada, volume fraco, perna bear, sem retest = baixa qualidade) → **tag / soft warning / hard-veto-candidate**, nunca veto sozinho.
- nas_short e os 4 killers cortam NAO mas matam BOM → **só tag/human-review**.

## 7. Fragile BOM protection

`results/l2_bpt_v2_2_fragile_bom_protection.csv`. Os 4 frágeis (survivor único na base): **GT13B, GT17A, GT23, GT24**.
- **Todas as 34 combinações SAFE** preservam os 4 (0 LOST).
- O par BORDERLINE `volume_fraco × overextended_entry` mata exatamente **GT13B e GT24** → qualquer pruning futuro que toque `overextended_entry` junto de `volume_fraco` é proibido sem re-checar esses 2.
- Regra: nenhuma combinação avança sem coluna explícita de status frágil.

## 8. Melhores combinações seguras

1. **Cirúrgica (recomendada p/ análise):** `fractal_3_3 × overextended_entry` (intersecção) — 17/17, UNKcut 1180, só remove fractal_3_3 esticado. Mínimo risco.
2. **Equilíbrio:** `volume_fraco × bear_flag` — 17/17, UNKcut 2870, 2 fatores, frágeis OK.
3. **Agressiva:** `overextended_entry + src_redundant + bear_flag` — 17/17, **−61.8%**, frágeis OK (mas 3 fatores; mais complexa que a pruned base v1).

Nenhuma promovida a veto — candidatas a análise.

## 9. Combinações perigosas

`results/l2_bpt_v2_2_dangerous_combinations.csv`. Piores: `first_retomada+nas_short_ge5` (3/17, mata 14), `BOS_fraco+nas_short_ge5` (6/17), `first_retomada+BOS_fraco` (6/17), `bear_macro+nas_short_ge5` (6/17), `first_retomada+rsi_lt50` (6/17). **`first_retomada` e `nas_short_ge5` são os fatores tóxicos** — presentes em quase toda combinação DANGEROUS. **DO_NOT_USE como veto.**

## 10. O que parece estruturalmente relevante

- **src_redundant** (qualidade da fonte de polaridade) é o lever mais limpo: ruído concentra em topo_duplo/nivel_interno/fractal_2_2; `fractal_3_3` é backbone (sole-recall 10/17).
- **overextended_entry / dist_pol_lt04** (geometria da entrada vs polaridade) separam direcionalmente — BOM entra mais "aceito" acima da polaridade; entradas esticadas/coladas = mais ruído.
- **bear_flag / volume_fraco** (qualidade da perna/volume) reduzem ruído preservando recall.
- **NAO não é cortável** por estes fatores (resistência 6-8/8) → a distinção BOM↔NAO mora em camadas macro ausentes.

## 11. O que ainda falta

- Camadas macro-estruturais (at_D1_demand v2, macro-leg atlas, Custom OB demand/supply, supply_overhead) — **não no input v2.2**; exigem extração. São os prováveis discriminadores BOM↔NAO reais.
- Análise visual dos casos: (a) 2 winners mortos por volume×overextended (GT13B, GT24); (b) os 4 frágeis (margem de 1 survivor); (c) os 6-8 NAO que resistem a todo corte seguro (por que parecem BOM?).
- Thresholds derivados (`nas_short_ge5`, `dist_pol_lt04`, `rsi_lt50`) são **calibração** sobre 17/8 — não validados; tag-only.
- Nada de PnL/exit/gestão (fora de escopo).

## 12. DA appendix

- Nenhum PnL? ✅ · Nenhum backtest? ✅
- Recall BOM preservado nas combinações SAFE? ✅ 34 combos 17/17, event-level.
- 4 BOM frágeis checados? ✅ seção 7 + CSV; preservados em todas SAFE; GT13B/GT24 mortos só na borderline volume×overextended.
- Combinações perigosas não promovidas? ✅ classificadas DANGEROUS/DO_NOT_USE.
- Não inventou features? ✅ fatores indisponíveis marcados UNAVAILABLE, não fabricados.
- Não usou SLIM? ✅ · Não recomendou Caminho B? ✅ · Produção intacta? ✅.

**DA verdict: PASS — 136 combos 2-fatores + 81 3-fatores + 10 interações obrigatórias, recall event-level, frágeis protegidos, fatores tóxicos isolados, NAO-resistência documentada; nada promovido a veto; produção intacta.**

---

*Read-only. RAW-only. Diagnóstico (sem PnL/OOS). Outputs: este doc + `results/l2_bpt_v2_2_{cross_factor_matrix, top_safe_combinations, dangerous_combinations, fragile_bom_protection}.csv` + `_cross_factor_summary.json`. Script: `.../v1/cross_factor_diag.py`.*
