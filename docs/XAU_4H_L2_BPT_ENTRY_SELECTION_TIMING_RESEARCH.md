# XAU 4H L2/BPT — Entry Selection / Timing: resultado

**Status:** `RESEARCH · CAUSAL · RAW · HARD-RULE-FAILED · NOT_PROMOTED` · **Data:** 2026-06-18
Executa o pré-registro. Regra dura: bater long-random-casado-por-legpos (senão é drift). SL demand-anchored causal, exit partial50@2R+6R, classificação por tipo de saída. RAW, sem look-ahead, sem plotagem. DA dedicado.

---

## 1. Executive summary
**NENHUMA hipótese de entrada passou a regra dura.** Todas são direcionalmente positivas (delta +0.11..+0.19 vs baseline legpos-random, P 0.86–0.93) mas **NENHUMA clear Bonferroni×3 (exige P≥0.983)**. H2 (reclaim-timing) = **no-op confirmado** (touched_on_retest seleciona quase todo o conjunto). H1 (demand-backed) = maior delta mas **n=85, CI do baseline enorme [-0.08,+0.48], SL-entangled** (SCRATCH 2/85 é geometria do demand-SL, não edge). O delta +0.115 do ALL é **provável artefato do demand-SL/universo** (circular), não skill de entrada. **H3 (remoção topo/late) é o único que mexe o ponteiro (P0.93)** mas também não clear. **Conclusão: entry selection/timing é dead-end sob legpos-random — drift + geometria do demand-SL dominam.** Stop refinar entrada; o carregador de edge é o que já travamos (demand-SL + partial50 + F_STRICT top-removal).

## 2. Método (RAW, causal)
- Baseline: random long de **barras demand-backed** (com demanda 4H abaixo), casado pela distribuição de legpos-bucket de cada subset, **mesma mecânica demand-SL + partial50**. P(>rand)=fração de 2000 draws abaixo do avgR do subset.
- SL demand-anchored as-of-bar (repaint-auditado). Exit partial50@2R+6R. Classificação por TIPO DE SAÍDA.
- **Look-ahead evitado:** H2 corrigido pra causal (touched_on_retest em [i-WIN,i]; NÃO min-low-do-cluster que seria look-ahead). demand/legpos/swing todos ≤i. RAW (frozen + gz demanda RAW), sem SLIM.
- **Desvio do pré-registro (declarado):** o baseline pré-registrado era "random long matched by legpos" sem exigir demanda; usei universo **demand-backed** (necessário p/ demand-SL apples-to-apples). É um baseline MAIS FORTE (conservador) — responde uma pergunta demand-condicionada, não a pré-registrada exata.

## 3. Resultados (`results/l2_bpt_entry_sel_results.csv`)
| hipótese | n | avgR | WIN/STOP/SCR | baseline legpos-rand [5/50/95] | delta | P(>rand) |
|---|---|---|---|---|---|---|
| ALL_L2BPT(BOS) | 276 | +0.305 | 88/128/60 | 0.037/0.190/0.348 | +0.115 | 0.89 |
| H1_demand_backed≤2.5 | 85 | +0.378 | 38/45/2 | −0.082/0.184/0.477 | +0.194 | 0.86 |
| H2_reclaim_timing | 276 | +0.312 | 95/133/48 | 0.036/0.194/0.350 | +0.118 | 0.89 |
| H3_filter_kept(noF) | 245 | +0.329 | 81/116/48 | 0.016/0.178/0.341 | +0.151 | **0.93** |

Bonferroni×3 → exige P≥0.983. **Nenhuma alcança.**

## 4. Por hipótese (veredito)
- **H1 demand-backed:** maior delta (+0.194) mas n=85, baseline CI [-0.08,+0.48] engole o ponto; SCRATCH 2/85 = tautologia da geometria demand-SL (stop perto → printa +2R ou stopa, sem scratch), não evidência de edge. Lead frágil, só com amostra maior.
- **H2 reclaim-timing:** +0.118 ≈ +0.115 do ALL = **NO-OP** (quase todo rep já retesta a demanda). Lever morto, dropar.
- **H3 top/late filter:** P0.93, +0.151 — o único que mexe o ponteiro (consistente com F_STRICT positivo), mas não clear Bonferroni. Vale UMA confirmação em amostra independente, não promoção.
- **ALL +0.115:** provável artefato demand-SL/universo (subset e baseline usam a MESMA demanda → deveria diferenciar-se; o resíduo +0.115 a P0.89 é pequeno e não-confirmado). Não separável como edge de entrada.

## 5. P overstated (honesto)
O P(>rand) trata o avgR do subset como FIXO e só bootstrapa o baseline. O subset tem SE próprio (n=85-276, distribuição R fat-tail do +6R). Teste pareado/two-sided pioraria (mais overlap). **Os P reportados são otimistas — a significância real é menor.** Reforça o veredito de FAIL.

## 6. Recommendation
- **Parar de refinar entrada.** Entry selection/timing é dead-end sob legpos-random; drift + demand-SL dominam; timing é no-op.
- **Travar o carregador de edge já validado:** SL demand-anchored (risco/estrutura) + partial50 (exit) + F_STRICT top-removal (review flag). O valor do L2/BPT NÃO está num trigger esperto de entrada — é "long ouro em estrutura, com SL ancorado em demanda e remoção de topos", largamente drift + risk-shaping.
- **Se houver follow-up:** só H3-style top/late filtering, em amostra INDEPENDENTE, two-sided. Não perseguir H1/H2.

## 7. DA appendix
DA dedicado. Verdict: nenhuma hipótese passa a regra dura (Bonferroni×3); P0.86-0.93 = lead não resultado (não suavizar pós-hoc); P one-sided otimista (two-sided pior); H1 frágil/SL-entangled (SCRATCH 2/85 mecânico); H2 no-op confirmado; ALL +0.115 provável artefato demand-SL/circular; baseline demand-backed é conservador mas substituído (desvio declarado); **conclusão = entry selection dead-end, drift+demand-SL dominam, H3/top-removal único lever (não clear), parar de refinar entrada, travar demand-SL+partial50+F_STRICT como carregador**. Causal ✓ (H2 corrigido), RAW ✓, sem SLIM/look-ahead/plot/produção, nada promovido.

---

*Outputs: `results/l2_bpt_entry_sel_results.csv`. Script: `entry_selection.py`. Foundation: [[XAU_4H_L2_BPT_ENTRY_ATTRIBUTION_BOS_NOT_EDGE]]. Sem plotagem, sem produção, nada promovido.*
