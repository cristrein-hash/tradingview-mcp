# XAU 4H L2/BPT v2.2 — PRUNED BASE V1 (base seletiva, recall 17/17 preservado)

**Data:** 2026-06-17 · **Status:** `CANDIDATE_BASE · NOT_STRATEGY · NOT_VALIDATION · RECALL_PRESERVED_17_17`
**Sem backtest/PnL, sem estratégia final, sem veto definitivo promovido, sem plotagem, sem MCP/chart, sem Telegram/broker/produção, sem SLIM.** RAW-only.

---

## 1. Executive summary

Criada a base seletiva **L2_BPT_V2_2_PRUNED_BASE_V1** = **P1 (união gulosa de camadas seguras)**: **7763 → 4575 candidatos (−41.1%)**, **recall 17/17 BOM_HIGH preservado** (re-verificado em nível de evento após combinar camadas), backbone `fractal_3_3` intacto (2581 candidatos). NAO captured cai de 8/8 → 7/8 (1 evento NAO removido como subproduto — não é objetivo). É uma **base de candidatos para análise futura**, não estratégia nem validação.

## 2. Por que o pruning foi aprovado

O Detector v2.2 é recall-maximizing (1109 cand/ano, 54% só de `fractal_3_3`). O diagnóstico Camadas 2-3 mostrou que ~40% do ruído pode ser cortado sem perder nenhum BOM conhecido. Cris aprovou explicitamente o primeiro passo: **eliminar ~40% do ruído preservando 17/17**. Pruning aqui = limpar a base para análise mais profunda depois (camadas macro-estruturais), **não** decidir trades.

## 3. Regras usadas (camadas seguras, 17/17 individual + combinação re-verificada)

União gulosa verificada (cada adição re-checa recall 17/17): **`volume_fraco`, `bear_flag`, `no_retest`, `no_polarity_defense`, `false_tipo_B_dump_direto`, `no_absorption`**. Um candidato é **pruned** se disparar QUALQUER uma. `fractal_3_3` (sole-recall de 10/17) nunca removido.

## 4. Regras proibidas (cortam BOM — jamais veto automático)

`first_retomada` (mata 9/17), `BOS_fraco` (5), `bear_macro` (4), `cluster_BUY_climax` (2). E `overextended_entry`: embora preserve 17/17 **isolada**, foi **excluída da união** porque, combinada, derrubava 2 winners → confirma a regra "não assumir que união preserva recall".

## 5. Comparação P0/P1/P2/P3

| Versão | Candidatos | %corte | Recall BOM | NAO captured | Fontes | Nota |
|---|--:|--:|:--:|:--:|---|---|
| **P0** original | 7763 | 0% | 17/17 | 8/8 | 5 fontes | base v2.2 |
| **P1** união gulosa segura ✅ | **4575** | **−41.1%** | **17/17** | 7/8 | 5 fontes (fractal_3_3 backbone) | **ESCOLHIDA** |
| P2 source-prune | 4894 | −37.0% | 17/17 | 7/8 | só fractal_3_3+swing_high_simples | mais simples; alternativa |
| P3 interseção conservadora | 6508 | −16.2% | 17/17 | 8/8 | 5 fontes | menos agressiva (remove só o que P1 E P2 removem) |

Todas preservam 17/17. P1 corta mais ruído mantendo todas as fontes; P2 é mais simples mas descarta fontes inteiras; P3 é fallback conservador.

## 6. Base escolhida

**P1** — preserva 17/17, corta mais ruído (−41%), não depende de camada perigosa, mantém `fractal_3_3` (backbone). Nomeada **L2_BPT_V2_2_PRUNED_BASE_V1**.

## 7. Recall BOM

**17/17 eventos preservados** (`results/l2_bpt_v2_2_pruned_base_v1_gt_recall.csv`). Margem fina em 4 eventos (GT13B, GT17A, GT23, GT24 ficam com **1 candidato survivor** cada) — registrado como sensibilidade: qualquer pruning futuro deve re-checar especialmente esses 4.

## 8. NAO captured

Antes 8/8 → depois **7/8** (1 evento NAO removido como subproduto do `volume_fraco`). Redução de NAO **não é objetivo** deste bloco; NAO segue como contraste, não dataset.

## 9. Densidade antes/depois

| | candidatos | cand/ano |
|---|--:|--:|
| Antes (P0) | 7763 | ~1109 |
| Depois (P1) | 4575 | ~654 |

Fontes na base: `fractal_3_3` 2581 (backbone), + topo_duplo/nivel_interno/swing_high_simples/fractal_2_2 (reduzidas pelos blockers, não removidas).

## 10. Limitações

- Base ainda **NÃO é estratégia nem validação** — só candidate set mais limpo.
- Camadas usadas são **redutores de ruído**, não discriminadores BOM↔NAO (os discriminadores reais — at_D1_demand, macro-leg atlas, Custom OB demand/supply — seguem **deferidos**, ausentes do input v2.2).
- n pequeno (17 BOM / 8 NAO events) → calibração, não validação (`feedback_calibration_vs_validation_45_groups`).
- 4 eventos com survivor único = margem frágil.
- Sem PnL/exit/gestão (fora de escopo).

## 11. Próximas análises possíveis sobre a base pruned

- Extrair camadas macro-estruturais (at_D1_demand v2, macro-leg atlas, Custom OB) e medir separação BOM↔NAO sobre os 4575.
- Caracterizar os 7665→remanescentes UNKNOWN: clustering por contexto.
- Recall-gate permanente antes de qualquer censo/backtest sobre a base.
- Só então: definir exit/gestão e medir performance (bloco separado, com autorização).

## 12. DA appendix

- Preservou 17/17 BOM? ✅ event-level.
- Revalidou recall após combinar camadas? ✅ união gulosa re-checa a cada adição; `overextended_entry` excluída por quebrar recall combinada.
- Não removeu `fractal_3_3` indevidamente? ✅ backbone 2581 preservado.
- Não promoveu pruning a estratégia? ✅ status `CANDIDATE_BASE / NOT_STRATEGY`.
- Não usou PnL? ✅. Não chamou de validação? ✅ `NOT_VALIDATION`.
- Não usou SLIM? ✅ RAW congelado. Não plotou? ✅. Não tocou produção? ✅.
- Caminho B não recomendado? ✅.

**DA verdict: PASS — base seletiva P1 criada, recall 17/17 re-verificado pós-combinação, backbone preservado, nada promovido a estratégia/veto/validação, produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_v2_2_pruned_base_v1{.csv, _removed.csv, _gt_recall.csv, _summary.json}`. Script: `.../v1/build_pruned_base_v1.py` (regenerável da matriz de candidatos).*
