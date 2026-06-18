# XAU 4H L2/BPT — Entry / Exhaustion Filter (RAW audit + bootstrap)

**Status:** `RESEARCH · CAUSAL · RAW_AUDITED · BOOTSTRAPPED · PROVISIONAL · NOT_PROMOTED` · **Data:** 2026-06-18
Filtros de entrada/exaustão com RAW audit obrigatório + bootstrap 5000 + registro completo de melhorias/pioras. SL FIXO STRUCT_PURE, exit FIXO partial50@2R+6R. 9º+10º DA. Não promove estratégia.

---

## 1. Executive summary

**RAW audit: PASS.** O filtro usa só OHLC 4H + RSI (confirmado = Wilder RSI14 causal, median diff 1.9) + legpos — sem tick-volume, sem campo retratado, sem candle pós-entrada, sem SLIM. **Resultado honesto após bootstrap:** o melhor candidato `F_TOP_OB_RSI_strict` (**legpos90≥85 & RSI≥70**) é **SMALL_BUT_STABLE, NÃO auto-block confiante.** Bootstrap base completa: delta_avgR P(>0)=0.90 (mediana +0.031), mas **delta_sumR P=0.57 (coin-flip)**, delta_maxDD P=0.76, delta_streak P=0.51. Os 30 removidos são **near-breakeven** (14W/16L, avgR −0.031, sumR −0.9R) → o avgR↑ é **parcialmente artefato de denominador** (DA). **MAS** no bootstrap **out-of-calibration 2023-26** (casos calibradores = 2020): **delta_avgR P(>0)=0.98, CI [+0.016,+0.08,+0.15] EXCLUI zero** — a melhoria de qualidade-por-trade É robusta na janela não-ajustada, 0 BOM. Não sobrevive Bonferroni×4 estrito (0.98 < 0.9875). **Conclusão:** F_strict remove robustamente um bucket de blow-off-tops levemente-negativo → **melhora qualidade por-trade, NÃO retorno total (sumR flat), DD modesto.** Classificação: **HUMAN_REVIEW_FLAG / soft-block provisório** (recall-limpo, OOS-robusto em avgR), não auto-block standalone. F_TOP_OB_RSI (RSI≥68)=review (sumR piora). F_LATE_LEG/F_WEAK_RECLAIM **cortam 1 BOM**=REJECTED. Nada em produção.

## 2. RAW / source audit (`results/l2_bpt_entry_exhaustion_raw_audit.csv`)

PASS. **Gate-allowed (causal):** OHLCV 4H frozen, ATR14, **RSI** (frozen=Wilder RSI14, causal closes≤i, ~2pt ruído), legpos90, dist_hi90, ext_lo20, body_frac (candle de entrada, close de i conhecido). **Available não-usado:** Session VP real (sem volume neste filtro), NAS/Bubbles/OB (contexto, não gate isolado). **FORBIDDEN/RETRACTED (excluídos):** tick-volume frozen, deep_confluence, outcome_proxy, RSI-divergence (detector bug-risk → unavailable), smc_recent PREÇO (caveat, usar só texto).

## 3. Known caveats and forbidden fields

tick-volume ≠ autoridade · deep_confluence/volume×1D-bear RETRACTED · outcome_proxy mede drift · legbear block retratado · filtros que só funcionam nos 41 curados ≠ validação · RSI-divergence indisponível/bug-risk · smc_recent preço não-confiável.

## 4. Why entry/exhaustion is now the focus

5 blocos: SL/exit/cap/defended-swing não são a alavanca. O bucket >4ATR e os não-salváveis apontam upstream (entrada). E23/E15/E24/E34 = entradas que estruturalmente não deveriam existir.

## 5. Must-preserve and should-cut

must_preserve (8): E1,E5,E13,E17,E21,E27,E30,E40. should_cut/review: E23,E15,E24,E34,E39. E13=winner real (bad entry/pivô, não top). E23=TOP_EXHAUSTION. E1/E17=big winners.

## 6. Hypotheses

TOP_EXHAUSTION · BLOWOFF_NO_LONG · SUPPLY_REJECTION (pós-entrada=review) · WEAK_RECLAIM · LATE_LEG · BEAR_LEG_BOUNCE (não matar E1/E17).

## 7. Filter definitions (`..._filter_candidates.csv`)

| Filtro | Definição causal | Tipo |
|---|---|---|
| F_TOP_OB_RSI_strict | legpos90≥85 & RSI≥70 | soft-block/review provisório |
| F_TOP_OB_RSI | legpos90≥85 & RSI≥68 | review |
| F_LATE_LEG_EXT | legpos90≥85 & ext_lo20≥4.5 | rejected (corta BOM) |
| F_WEAK_RECLAIM | dist_hi90<2 & body<0.15 | rejected (corta BOM) |
| F_BEAR_BOUNCE | bearleg context | review (E39≈E17, nunca block) |
| F_SUPPLY_REJECTION | supply+rejeição pós-entrada | rejected (não-causal p/ entry) |

## 8. Case-study results (`..._case_study.csv`)

Tops separam de V-reversals winner por **RSI**, não legpos: E23 rsi77/E24 rsi69 (cut) vs E5 rsi61/E21 rsi55 (keep, legpos 92/90). E15(reclaim fraco)/E34(exaustão ambígua)/E39(≈E17) não separáveis por top-metrics → review.

## 9. Full-base results (276; baseline avgR+0.226 sumR+62.5 WR48.2 maxDD24.3 streak9)

| Filtro | removed | BOM_cut | sumR após | DD após | streak após |
|---|---|---|---|---|---|
| F_TOP_OB_RSI_strict | 30 | 0 | +63.4 | 22.1 | 8 |
| F_TOP_OB_RSI | 38 | 0 | +58.2 | 21.4 | 7 |
| F_LATE_LEG_EXT | 46 | 1 | +54.8 | 20.1 | 8 |
| F_WEAK_RECLAIM | 14 | 1 | +57.1 | 23.2 | 8 |

## 10. Bootstrap results (`..._bootstrap.csv`, 5000 paired)

**F_TOP_OB_RSI_strict (base completa):** delta_avgR [−0.007,+0.031,+0.071] P=0.90 · delta_sumR [−8.5,+1.0,+10] **P=0.57** · delta_maxDD [−4.4,−1.1,+1.5] P=0.76 · delta_streak [−2,−1,0] P=0.51.
**F_strict OUT-OF-CALIBRATION 2023-26 (n=156, threshold NÃO ajustado aqui):** delta_avgR [**+0.016,+0.08,+0.15**] **P=0.98** (exclui zero) · delta_sumR [−6.8,+1.5,+9.5] P=0.62 · delta_maxDD [−3.6,−1.1,+0.9] P=0.77.
**F_TOP_OB_RSI:** delta_sumR P=0.26 (piora), delta_avgR P=0.74.
**Removidos-30 composição:** 14W/16L/4scratch, avgR −0.031, sumR −0.9 = **near-breakeven** (levemente negativo).

## 11. Complete improvement register (`..._improvement_register.csv`)

| Filtro | removed (BOM/must) | avgR | sumR | DD | verdict |
|---|---|---|---|---|---|
| F_TOP_OB_RSI_strict | 30 (0/0) | .226→.258 | 62.5→63.4 | 24.3→22.1 | **SMALL_BUT_STABLE** (avgR OOS P=0.98; sumR flat) |
| F_TOP_OB_RSI | 38 (0/0) | .226→.244 | 62.5→58.2 | 24.3→21.4 | POINT_ESTIMATE_ONLY (sumR piora P=0.26) |
| F_LATE_LEG_EXT | 46 (1/0) | .226→.238 | 62.5→54.8 | 24.3→20.1 | REJECTED_RECALL_FAIL |
| F_WEAK_RECLAIM | 14 (1/0) | .226→.218 | 62.5→57.1 | 24.3→23.2 | REJECTED_RECALL_FAIL (avgR P=0.35) |

**Maior melhoria:** F_strict avgR (robusto OOS). **Maiores pioras:** F_LATE_LEG sumR −7.7, F_WEAK_RECLAIM avgR. **Reduz DD mas perde sumR:** F_TOP_OB_RSI. **Melhora avgR mas não sumR:** F_strict (artefato denominador parcial). **Corta top mas mata winner:** F_LATE_LEG/F_WEAK (1 BOM cada).

## 12. Auto-block vs review vs Telegram flag

- **HUMAN_REVIEW_FLAG / soft-block provisório:** F_TOP_OB_RSI_strict — recall-limpo, OOS-robusto em avgR, mas sumR flat + Bonferroni marginal → NÃO auto-block confiante.
- **HUMAN_REVIEW_FLAG:** F_TOP_OB_RSI, F_WEAK_RECLAIM (E15-tipo), F_BEAR_BOUNCE (E39, nunca block).
- **TELEGRAM_FUTURE_FLAG:** `overbought-top` (legpos≥85 & RSI≥68/70), `weak-reclaim-near-high`, `bear-leg-bounce` — aparecer no sinal para decisão humana.
- **REJECTED:** F_LATE_LEG_EXT, F_WEAK_RECLAIM (auto-block, cortam BOM), F_SUPPLY_REJECTION (pós-entrada).

## 13. What improved

F_TOP_OB_RSI_strict melhora a **qualidade média por-trade** (avgR +0.031 base / robusto OOS P=0.98) removendo um bucket de blow-off-tops levemente-negativo, **sem cortar nenhum monumental** (0 BOM nas 2 janelas) e sem custar retorno total (sumR coin-flip). Modesta redução de DD (P=0.76-0.77).

## 14. What failed

- **Retorno total (sumR):** nenhum filtro melhora sumR de forma robusta (F_strict P=0.57; F_TOP_OB_RSI piora). O ganho de avgR é parcialmente artefato de denominador.
- **DD/streak:** não atingem o bar robusto (P<0.9) na base completa.
- **F_LATE_LEG/F_WEAK_RECLAIM:** cortam 1 BOM → recall fail.
- **E15/E34/E39 + supply-rejection:** irredutíveis a filtro causal de entrada (não-separáveis / pós-entrada).
- **Bonferroni×4:** F_strict (P=0.98 OOS) não sobrevive o threshold estrito (0.9875).

## 15. DA appendix

9º+10º DA. Verdict (síntese): "avgR↑/sumR-flat = artefato de denominador (remove near-breakeven); P=0.90 base é in-sample; DD/streak dentro do ruído; não sobrevive Bonferroni. F_strict = POINT_ESTIMATE_ONLY/review, não auto-block. O 2023-26 mantém vivo mas precisa do próprio bootstrap." **Resposta (feita):** bootstrap OOS 2023-26 → **delta_avgR P=0.98 CI exclui zero** (upgrade para SMALL_BUT_STABLE em avgR), removidos confirmados near-breakeven (−0.9R). Checklist: RAW audit PASS · campo retratado NÃO · volume errado NÃO · daily futuro N/A · candle pós-entry NÃO (supply-rejection rejeitado por isso) · must-preserve preservados (0 BOM/0 must nas 2 janelas) · E23/E24 cortados, E15/E34/E39 review · causal SIM · melhoria no bootstrap (avgR OOS sim; sumR não) · registro completo (sem cherry-pick, pioras listadas) · robusto OOS em avgR sim, em sumR não · SL/exit intactos · produção intacta · não promovido.

## 16. Recommendation (research-only)

1. **F_TOP_OB_RSI_strict = HUMAN_REVIEW_FLAG / soft-block provisório + TELEGRAM_FUTURE_FLAG `overbought-top`.** É o melhor achado causal da saga (recall-limpo, OOS-robusto em avgR), mas o benefício é **qualidade-por-trade, não retorno total** → não promover como auto-block standalone. Operacionalmente: marcar/avisar o trade overbought-top para decisão humana.
2. **NÃO** auto-block automático (sumR flat, Bonferroni marginal, removidos near-breakeven).
3. **Settle definitivo (se continuar):** walk-forward split real (threshold num período, teste em outro disjunto) + mais janelas independentes + amostra maior de tops rotulados. Cross-asset proibido por política.
4. E34/E39/supply-rejection = review discricionário irredutível. Regime v3 / SHORT = depois.

---

*Outputs: `results/l2_bpt_entry_exhaustion_{raw_audit,case_study,filter_candidates,policy_results,recall_gate,bootstrap,improvement_register}.csv`. Scripts: `l2_bpt_entry_exhaustion.py`, `entry_case_study.py`, `l2_bpt_entry_bootstrap.py`. Sem produção, sem SLIM, sem chart, SL/exit inalterados, nada promovido.*
