# XAU 4H L2/BPT — Outcome/Anatomy Proxy Failure Audit

**Status:** `DIAGNOSTIC · PROXY_REFUTED · NOT_STRATEGY · NOT_VALIDATION` · **Data:** 2026-06-17
**RAW-only · sem filtro novo/backtest/promoção/plotagem/MCP/produção/SLIM.** A estratégia NÃO é descartada — o **proxy** é que falhou.

---

## 1. Executive summary

**O proxy de outcome/anatomy mede o bull drift do XAU 4H, NÃO edge L2/BPT.** Teste decisivo (lift vs base rate incondicional):

| métrica | TODAS as barras | candidatos base | lift |
|---|--:|--:|--:|
| % atinge +2 ATR em 36 bars | **67.3%** | 66.6% | **0.99×** |
| % atinge +3 ATR em 36 bars | **52.4%** | 52.6% | **1.00×** |

→ Um candidato L2 **não tem mais chance de "continuar"** que uma barra aleatória do dataset. Como 67% de QUALQUER barra vê +2 ATR em 36 bars (mercado em alta 2020-2026), rotular 66% dos candidatos como "continuation" é **a taxa-base, zero informação**. Isso explica por que BOM, NAO e UNKNOWN não se separam.

Além disso: **2965 candidatos = só 276 episódios estruturais** (média 10.7 sinais/episódio) → o número é inflado por **duplicação serial** dentro das pernas.

## 2. Por que o proxy falhou

1. **Mede movimento, não estrutura.** As classes dependem só de MFE/MAE/inval forward — nenhuma valida retest/reclaim/SL-viável/qualidade L2.
2. **Sem normalização por base rate.** Num ativo com drift de alta, "subiu depois" é o default. Faltou medir **lift** sobre a taxa incondicional (lift≈1.0× = nulo).
3. **Sem dedup por episódio.** Conta sinais seriais da mesma perna como eventos independentes (10.7/episódio).
4. **Janela fixa pega runup precoce dos NAO** antes da reversão → NAO parecem "good".

## 3. Definições atuais das classes (auditadas)

Todas do `outcome_anatomy.py`, janela 36 (12 p/ invalidação), **puro preço**:
- `STRONG_CONTINUATION`: MFE36≥3 ATR **e** MAE-antes-do-pico<1.0 ATR.
- `GOOD_CONTINUATION`: MFE36≥2 **e** MAE-antes<1.5.
- `WEAK_CONTINUATION`: 1≤MFE36<2.
- `STRUCTURE_INVALIDATED`: close<polaridade em ≤12 bars + MFE12<1 + MAE12≥1.5.
- `TOP_SWEEP_REVERSAL`: MFE36<1 **e** MAE36≥2.
- `CHOP`: MFE36<1 e MAE36<1. `FAILED_RECLAIM`: MFE36<1 e MAE36≥1. `NEEDS_VISUAL`: borda/insuf.
**Nenhuma mede estrutura L2** — só excursão de preço. Esse é o defeito raiz.

## 4. Cluster/duplicate analysis

`results/l2_bpt_episode_cluster_analysis.csv`: 2965 candidatos → **276 episódios** (gap>6 bars). cand/episódio: mediana 6, média 10.7, max 64. **181/276 episódios têm ≥1 STRONG/GOOD** (66% — = base rate, de novo). O verdadeiro N estrutural é ~276, não 2965.

## 5. UNKNOWN_STRONG: L2 real ou bull genérico?

Dos 1291 UNKNOWN STRONG/GOOD (`results/l2_bpt_unknown_strong_reclassification.csv`):
| reclass | n | % |
|---|--:|--:|
| GENERIC_BULL_FOLLOW_THROUGH | 658 | 51% |
| TRUE_L2_CONTINUATION_CANDIDATE | 479 | 37% |
| DUPLICATE_SIGNAL_IN_BULL_LEG | 154 | 12% |

(10% compartilham episódio com um BOM; 7% a ≤12 bars de um BOM.) → **maioria (51%) é continuação bullish genérica**, não setup L2; 12% são duplicatas de pernas já conhecidas.

## 6. BOM vs UNKNOWN_STRONG (`results/l2_bpt_unknown_strong_vs_bom.csv`)

| feature (mediana) | BOM | UNKNOWN_STRONG |
|---|--:|--:|
| dist_4h_supply_low_atr | **2.18** | 1.47 |
| supply_dist_from_polarity_atr | **2.76** | 1.96 |
| dist_4h_demand_top_atr | 2.34 | 1.86 |

→ BOM têm **supply mais distante / contexto mais limpo** que os UNKNOWN_STRONG. Logo "STRONG" no proxy ≠ BOM-like; os UNKNOWN_STRONG são, em mediana, mais colados ao supply (mais arriscados) — o proxy não vê isso.

## 7. NAO vs UNKNOWN_STRONG

NAO parecem "bons" no proxy porque: **MFE positivo antes de falhar** (a janela 36 captura o runup inicial); a **reversão estrutural/stop não é medida** (sem SL); a perna bear/supply que invalida não entra no proxy. Por isso 1/6 NAO virou GOOD e 3/6 ficaram NEEDS_VISUAL em vez de failure.

## 8. Nova taxonomia proposta (preliminar, aplicada)

- **TRUE_L2_CONTINUATION_CANDIDATE** (479) — demand-supporting/origin + supply não-perigoso + não-duplicata.
- **GENERIC_BULL_FOLLOW_THROUGH** (658) — sobe por drift, sem âncora L2.
- **DUPLICATE_SIGNAL_IN_BULL_LEG** (154) — sinal serial na mesma perna de um evento.
- **STRUCTURAL_RECLAIM_VALID / _WEAK** — a derivar com qualidade de retest/reclaim (próximo bloco).
- **TOP_OR_SUPPLY_RISK** — supply colado (US median 1.47 ATR).
- **UNKNOWN_NEEDS_VISUAL** — borda/ambíguo.

**Requisito para qualquer proxy futuro:** medir **lift sobre base rate** (não taxa absoluta) e **por episódio** (dedup serial), não por candidato.

## 9. O que ainda precisa de visual review

- Os 479 TRUE_L2_CONTINUATION_CANDIDATE (são L2 reais?).
- Os 6 NAO (por que não falham no proxy).
- GT17A (BOM frágil ambíguo).
- Amostra dos 276 episódios para confirmar a contagem estrutural real.

## 10. DA appendix

- Não tratou proxy como verdade? ✅ refutado por base-rate (lift 0.99×).
- Não criou filtro novo? ✅ só diagnóstico + reclass.
- Não promoveu UNKNOWN_STRONG como trade? ✅.
- Não descartou a estratégia por proxy ruim? ✅ — explicitado que o **proxy** falhou, não a tese.
- SLIM? ❌. Plotagem? ❌. Produção intacta? ✅. Caminho B? ❌.

**DA verdict: PASS — proxy REFUTADO (mede drift, lift≈1.0×; sem dedup por episódio; sem estrutura L2). UNKNOWN_STRONG = 51% bull genérico / 37% L2-candidate / 12% duplicata. Próximo proxy deve usar lift-vs-base-rate + por-episódio + qualidade estrutural. Estratégia não descartada; produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_outcome_proxy_failure_audit.csv`, `l2_bpt_episode_cluster_analysis.csv`, `l2_bpt_unknown_strong_vs_bom.csv`, `l2_bpt_unknown_strong_reclassification.csv`. Script: `/tmp/proxy_audit.py` (diagnóstico).*
