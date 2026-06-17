# XAU 4H L2/BPT — UNKNOWN Triage Plan

**Status:** `TRIAGE/PLANNING · NOT_STRATEGY · NOT_VALIDATION · NO_EDGE_CLAIMED` · **Data:** 2026-06-17
**RAW-only · sem novo backtest/PnL/filtro/promoção/plotagem/MCP/produção/SLIM.** Unidade = **episódio**.

> Honestidade central: os **buckets mecânicos NÃO separam os UNKNOWN** (todos ~40% ≈ base rate). O entregável real deste bloco é uma **amostra controlada outcome-blind (41 episódios) + uma taxonomia de labels humanos** — não um edge.

---

## 1. Executive summary

255 episódios UNKNOWN (de 2965 candidatos → 276 episódios; 15 BOM, 6 NAO, 255 UNKNOWN). Outcome por episódio (stop estrutural, +2R): **WR 42.0%, avgR +0.21 — vs base rate random-long 40%/+0.16 (lift 1.05×)**. Nenhum bucket estrutural mecânico separa além do ruído. Dois/três buckets que "separam" são **circulares** (definidos sobre o próprio outcome) → marcados como grupos-de-seleção, não achados. **Conclusão:** só **rotulagem humana/visual cega** pode transformar UNKNOWN em classes úteis; preparei a amostra e a taxonomia para isso.

## 2. Por que UNKNOWN é grande demais

- **2965 candidatos = só 276 episódios** (média 10.7 sinais/perna): o gerador v2.2 é permissivo e dispara em série dentro de cada perna → inflação por duplicação.
- **283 candidatos UNKNOWN foram absorvidos em episódios BOM** no dedup (gap≤6) — ou seja, boa parte dos "UNKNOWN perto de BOM" já some na agregação por episódio; só **4 episódios UNKNOWN** ficam a ≤12 bars de um BOM.
- O gerador captura qualquer reclaim-like; num ativo em drift de alta, isso vira muita continuação genérica.

## 3. O que falta para medir UNKNOWN

1. **Labels humanos/visuais** numa amostra (o sistema não mede estrutura visual).
2. **Classificação por episódio** (já aplicada aqui), não por candidato.
3. Separar TRUE_L2_SETUP / GENERIC_BULL_FOLLOW_THROUGH / BAD_TOP_ENTRY / WEAK_RECLAIM / DUPLICATE_SIGNAL / NEEDS_CONTEXT.
4. Confirmação visual de: polaridade correta · retest real · reclaim verdadeiro (aceitação vs sweep) · demanda/supply útil · entrada R-viável · perna madura/tardia.
5. **Macro-leg / auction context** — ainda não existe mecanicamente (só 5 linhas manuais no pack; REFERENCE_ONLY).

O que o sistema **não sabe medir hoje:** qualidade/aceitação do reclaim, maturidade da perna, se o supply é fresco/rompido, contexto macro-leg — tudo o que distingue um L2 real de "preço subiu".

## 4. Buckets de UNKNOWN (`results/l2_bpt_unknown_triage_buckets.csv`)

| bucket | tipo | n | WR | avgR |
|---|---|--:|--:|--:|
| HIGH_OUTCOME_BOMlike | **SELECTION (circular)** | 62 | tautológico | +2.0 |
| LOW_OUTCOME_NAOlike | **SELECTION (circular)** | 27 | tautológico | −1.0 |
| TOP_SWEEP_RISK | **SELECTION (circular)** | 15 | tautológico | −0.87 |
| SUPPLY_PRESSURE (≤1ATR) | estrutural | 51 | 43.1% | +0.13 |
| CLEAN_SKY | estrutural | 82 | 41.5% | +0.23 |
| DEMAND_SUPPORTED | estrutural | 155 | 42.6% | +0.23 |
| NO_DEMAND_SUPPORT | estrutural | 56 | 46.4% | +0.30 |
| DUPLICATE_DENSE_LEG (≥8) | estrutural | 103 | 47.6% | +0.33 |
| SINGLE_CLEAN_SIGNAL (≤2) | estrutural | 71 | 38.0% | +0.12 |

**Os buckets estruturais NÃO separam:** todos 38–48% em torno do base rate 40% (CI ~±8–19pts em n=27–155 → dentro do ruído). Inversões aparentes (NO_DEMAND 46% > DEMAND 42.6%; DENSE 47.6% > SINGLE 38%) são **ruído**, não evidência contra a tese L2. `DENSE_LEG` mais alto é provável **survivorship de drift** (mais sinais disparam numa perna que já subia). Membership é **não-exclusiva** → WRs não somam nem comparam como estratos ortogonais.

## 5. Amostra visual proposta (`results/l2_bpt_unknown_visual_sample_plan.csv`)

**41 episódios, OUTCOME-BLIND** (correção do DA: selecionar/mostrar outcome contamina o rótulo humano). Estratificada **só por estrutura pré-trade**: supply_pressure≤1ATR (12), clean_sky (12), demand_supported (10), no_demand_support (10), dense_leg (10), single_clean (10), near-BOM (4) → dedup 41. Cada linha traz `selection_stratum` + `visual_question` + features estruturais; **sem coluna de outcome**. Objetivo: ~50 episódios controlados, não milhares; o humano rotula sem ver o desfecho.

## 6. Taxonomia de labels humanos (`results/l2_bpt_unknown_label_taxonomy.csv`)

10 labels com definição + o-que-observar + consequência: TRUE_BPT_LONG · ACCEPTABLE_BPT_LONG · WEAK_BPT_LONG · BAD_TOP_ENTRY · BEAR_LEG_TRAP · GENERIC_BULL_MOVE · DUPLICATE_OF_BETTER_ENTRY · NO_CLEAR_POLARITY · NO_RECLAIM_ACCEPTANCE · NEEDS_SECOND_REVIEW.

## 7. Como usar os labels depois

- Cris rotula os 41 (cego ao outcome) → só então cruzar label×outcome para ver se os labels humanos separam (o que o mecânico não conseguiu).
- Se TRUE_BPT_LONG ≫ GENERIC_BULL_MOVE em outcome → confirma que o discriminador é estrutural-visual e vira base para uma camada de qualidade.
- Os labels viram ground-truth para treinar/auditar o próximo detector estrutural (recall-gate primeiro).

## 8. O que NÃO deve ser concluído ainda

- UNKNOWN **não tem edge demonstrável** (≈ base rate) — não é "lado bom" da base.
- Buckets mecânicos **não separam** — não filtrar com eles.
- Buckets circulares **não são achados**.
- Nada de estratégia/filtro/promoção; n pequeno; in-sample.

## 9. DA appendix

DA executado (general-purpose) — vereditos aplicados:
- Buckets circulares = **FATAL como achado** → relabelados SELECTION_GROUP/tautológico. ✅ corrigido.
- Buckets estruturais não separam (ruído ~base rate). ✅ reportado.
- Inversões = ruído; dense_leg = survivorship de drift. ✅ flag.
- **Amostra visual contaminada por outcome = FATAL p/ rotulagem** → regenerada **outcome-blind**, estratificada por estrutura. ✅ corrigido.
- Absorção dedup (283) é outcome-blind (gap temporal). ✅.
- Não tratou UNKNOWN como edge? ✅. Filtro novo? ❌. Estratégia? ❌. Plotou tudo? ❌. SLIM? ❌. Outra frente? ❌. Produção intacta? ✅.

**DA verdict: PASS — triagem por episódio entregue; buckets mecânicos NÃO separam (≈base rate), circulares marcados; amostra de 41 episódios outcome-blind + taxonomia de labels prontas para rotulagem humana cega. Nenhum edge alegado; produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_unknown_triage_buckets.csv`, `l2_bpt_unknown_triage_episodes.csv`, `l2_bpt_unknown_visual_sample_plan.csv` (outcome-blind), `l2_bpt_unknown_label_taxonomy.csv`. Script: `unknown_triage.py` (py_compile OK).*
