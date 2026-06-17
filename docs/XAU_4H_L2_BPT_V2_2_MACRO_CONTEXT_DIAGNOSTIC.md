# XAU 4H L2/BPT v2.2 PRUNED_BASE_V2 — Macro-Structural Context Diagnostic

> 🚨 **UNTRUSTED — visual reality mismatch. Do not use these macro-context results for strategy decisions until mapping is reconciled against chart/GT examples, including 4H OB Demand.** (Marcado 2026-06-17.) Causa provável: tolerâncias estreitas (0.5·ATR) e ausência de medição de **demanda 4H relevante abaixo / origem da perna** — só foi medido "inside/near". O `at_D1_demand=0/17` é artefato de threshold/semântica, NÃO conclusão. Reconciliação em `XAU_4H_L2_BPT_MACRO_CONTEXT_VISUAL_RECONCILIATION_AUDIT.md`.

**Status:** `UNTRUSTED / NEEDS_VISUAL_RECONCILIATION` · ~~`DIAGNOSTIC`~~ · **Data:** 2026-06-17
**RAW-only · sem backtest/PnL, sem promoção de veto, sem plotagem, sem MCP/chart, sem Telegram/broker/produção, sem SLIM.** Recall em nível de evento.

---

## 1. Executive summary

Enriqueci a PRUNED_BASE_V2 (2965 candidatos, 17/17 BOM) com camadas macro-estruturais **derivadas do RAW, causais**: Custom OB v11 DEMAND/SUPPLY 4H (as-of-bar), `supply_overhead` 4H, e `at_d1_demand` v2 (guarda causal 1D). **Achado central — honesto:** as camadas macro disponíveis **NÃO separam BOM de NAO**. Os dois grupos partilham o mesmo perfil macro (supply acima, sem demanda 1D). Em particular:
- **`at_d1_demand` = 0/17 BOM e 0/6 NAO** (0/39 candidatos-BOM). Insight estrutural: entradas L2/BPT são **reclaims acima de polaridade/supply, NÃO bounces de demanda 1D** — a estratégia não é demand-reclaim.
- **`supply_overhead`** presente em **11/17 BOM e 5/6 NAO** → domina ambos; não discrimina (levemente NAO-leaning, small-n).
- Custom OB demand (inside/near) é esparso em ambos (BOM 4/17 inside, 1/17 near).

**Conclusão:** o discriminador BOM↔NAO **não está na presença/ausência destas zonas macro** — está provavelmente em camadas mais finas (qualidade/frescor do reclaim, qual supply é rompido, momentum), ainda não medidas. macro_leg não foi derivado (só 5 linhas manuais no pack = REFERENCE_ONLY; não inventado).

## 2. Base usada

`results/l2_bpt_v2_2_pruned_base_v2.csv` — **2965 candidatos, 17/17 BOM, 6 NAO** (GT04A, GT06A, GT06B, GT12, GT14_NAO, GT19A). RAW-only (frozen input + RAW gz). Confirmado antes da análise.

## 3. Disponibilidade das camadas macro

| Camada | Fonte canônica | RAW? | Causal | SHIFT | Status |
|---|---|:--:|:--:|---|---|
| **at_D1_demand** | `pine_boxes` "Custom OB Detector v11" text=DEMAND, 1D gz; def v2 canônica (`L2_BPT_AT_D1_DEMAND_DESIGN_V2.md`) | sim | sim | guarda `d1_record_used` = max `replay_current_date ≤ entry_time` | **NEEDS_DERIVATION_FROM_RAW → DERIVADO** |
| **supply_overhead** | Custom OB v11 SUPPLY 4H acima do preço | sim | sim (as-of-bar) | n/a | **DERIVADO** |
| **Custom OB demand/supply (4H)** | Custom OB v11 boxes 4H (240m gz) | sim | sim (as-of-bar) | n/a | **DERIVADO** |
| **macro_leg** | `L2_BPT_BLOCKS_1_TO_5_MACRO_LEG_RAW_BREAKDOWN.csv` (5 linhas manuais) | não | não | — | **REFERENCE_ONLY** (não derivado — sem invenção) |

77/2965 (2.6%) candidatos sem alinhamento 4H OB (bordas/gap 2023-01-01→03) → flag `feature_availability`.

## 4. Metodologia de alinhamento

- Candidato → `ts_epoch` (frozen input, = bar time 4H) → snapshot do 240m gz com `ohlcv[-1].time == ts` → boxes Custom OB **as-of aquele bar** (causal; última snapshot do bar vence).
- `entry_price` = `entry_close` do bar 4H (campo da fonte; close-only-causal; não recomputado).
- **at_d1_demand v2:** `d1_record_used` = record 1D com maior `replay_current_date ≤ ts` (lookahead-free). DEMAND vivas desse record. `at_d1_demand = inside_d1_demand OR near_from_above` (`near_from_below` excluído por def). `ATR_D1` = ATR14 de dailies **fechadas** antes do entry. Tolerância diagnóstica 0.5·ATR_D1 (calibração reportada, não threshold final).
- 4H: `inside_demand/supply`, `near_demand` (≤0.5·ATR_4H), `supply_overhead` = SUPPLY com low>preço dentro de 3·ATR_4H.

## 5. BOM vs NAO macro context (event-level: camada presente em ≥1 candidato do evento)

| Camada | BOM (/17) | NAO (/6) | leitura |
|---|--:|--:|---|
| at_D1_demand | **0/17** | **0/6** | null — entradas não são demand-bounce |
| inside_custom_ob_demand | 4/17 | 2/6 | esparso, sem separação |
| near_custom_ob_demand | 1/17 | 2/6 | esparso, NAO-leaning |
| supply_overhead | 11/17 | 5/6 | domina ambos; NAO-leaning (small-n) |
| inside_custom_ob_supply | 3/17 | 1/6 | esparso |

**NAO é small-n (6) — contraste, não prova estatística.** Nenhuma camada separa de forma limpa. supply_overhead é o sinal direcional mais forte (e ainda assim presente na maioria dos BOM).

## 6. Fragile BOM protection

| Frágil | at_D1_demand | demand_ob | supply_overhead | n_surv | status |
|---|:--:|:--:|:--:|--:|---|
| GT13B | 0 | 0 | 1 | 1 | protected_case |
| GT17A | 0 | 0 | 1 | 1 | protected_case |
| GT23 | 0 | 0 | 1 | 4 | protected_case |
| GT24 | 0 | 0 | 1 | 1 | protected_case |

**Todos os 4 frágeis têm `supply_overhead=1` e nenhum contexto de demanda.** Implicação crítica: **um veto por `supply_overhead` mataria os 4 frágeis** (e 11/17 BOM no total) → `supply_overhead` **NÃO pode virar veto**; no máximo soft_warning. `at_d1_demand` como gate positivo mataria 17/17 → proibido.

## 7. UNKNOWN contextual ranking

`results/l2_bpt_v2_2_pruned_base_v2_unknown_ranking.csv` (2912 UNKNOWN). Buckets contextuais (NÃO trade signals):

| bucket | n | critério |
|---|--:|---|
| UNKNOWN_NAO_LIKE | 2165 | supply_overhead/inside_supply presente (perfil dominante) |
| UNKNOWN_BOM_LIKE | 185 | contexto de demanda sem supply overhead |
| UNKNOWN_LOW_PRIORITY | 490 | sem contexto macro forte |
| UNKNOWN_NEEDS_VISUAL | 72 | sem alinhamento OB / contexto ambíguo |

⚠️ **Caveat forte:** como BOM ≈ NAO ≈ UNKNOWN no perfil macro (supply dominante, demanda esparsa, at_d1=0), estes buckets têm **baixíssimo poder discriminativo** e **não predizem BOM**. O rótulo "BOM_LIKE" reflete "localização mais limpa" (demanda sem supply), não semelhança validada com winners. Nenhum UNKNOWN promovido a trade.

## 8. Reason Atlas macro v3

`results/l2_bpt_v2_2_reason_atlas_macro_v3.csv`. Roles: at_D1_demand → tag (null, não usar como gate); supply_overhead/inside_supply → soft_warning (NAO-leaning, mas mata BOM se veto); custom_ob_demand → tag; macro_leg → `do_not_use(REFERENCE_ONLY)`. Confidence = **low** (BOM ev=17, NAO ev=6). Causal status declarado por camada. **Nenhum hard_veto promovido.**

## 9. Achados robustos

- **at_d1_demand é estruturalmente irrelevante** para L2/BPT (0/17 e 0/6): a estratégia entra em reclaim acima de polaridade, longe de demanda 1D. Insight de design forte e causal.
- **supply_overhead é o contexto modal** de ambos BOM e NAO (entram abaixo de supply prévio — coerente com reclaim/continuação).
- A derivação macro é **causal e auditável** (guarda 1D, boxes as-of-bar).

## 10. Achados fracos

- Nenhuma camada macro **separa** BOM de NAO (overlap alto; NAO small-n).
- O ranking de UNKNOWN é fraco (perfis sobrepostos).
- Tolerâncias (0.5 ATR) = calibração sobre 17/6, não validadas.

## 11. O que ainda falta

- **Discriminadores mais finos:** qualidade/frescor do reclaim, qual supply específico é rompido (idade/força do box), momentum no rompimento, distância ao supply imediato vs macro.
- macro_leg como feature causal (hoje só 5 linhas manuais) — exigiria um classificador de perna macro causal (design pendente, não inventar).
- Validação independente (set fora dos 17/6) — tudo aqui é calibração.

## 12. Próximas análises possíveis (sem escolher pelo usuário)

- Medir **qualidade do supply rompido** (idade/largura/n toques do box) BOM vs NAO.
- Caracterizar os 6 NAO restantes individualmente (visual/estrutural) vs os 17 BOM.
- Derivar macro_leg causal (perna macro) se desejado, com pré-registro.
- Extrair momentum/aceitação pós-reclaim como camada fina.

## 13. DA appendix

- PRUNED_BASE_V2 preservada? ✅ 2965, 17/17.
- Nenhum SLIM? ✅ RAW gz + frozen input.
- Macro-camadas causais? ✅ guarda 1D + boxes as-of-bar.
- D1 usa SHIFT correto? ✅ `d1_record_used` = max replay_current_date ≤ entry_time.
- Custom OB não interpretado genericamente? ✅ "Custom OB Detector v11 — Alert", text DEMAND/SUPPLY, high/low reais.
- macro_leg não inventado? ✅ REFERENCE_ONLY (5 linhas manuais).
- NAO small-n com caveat? ✅ contraste, não prova.
- UNKNOWN não promovido? ✅ buckets, nenhum trade.
- Nenhum hard veto criado? ✅ atlas só tag/soft_warning.
- Nenhum backtest/PnL/plotagem? ✅. Produção intacta? ✅. Caminho B? ❌ não recomendado.

**DA verdict: PASS — macro-camadas derivadas causalmente, BOM↔NAO NÃO separáveis por elas (at_d1=0/0, supply domina ambos), frágeis protegidos, nada promovido a veto/estratégia; produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_v2_2_pruned_base_v2_macro_context.csv`, `_unknown_ranking.csv`, `l2_bpt_v2_2_reason_atlas_macro_v3.csv`. Script: `.../v1/macro_context_enrich.py` (regenerável do RAW gz; py_compile OK).*
