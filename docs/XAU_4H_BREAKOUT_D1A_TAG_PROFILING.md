# XAU 4H BREAKOUT / D1a — Tag Profiling (Winners vs Losers Anatomy)

**Data:** 2026-06-17 · **Tipo:** perfilamento por tags / anatomia · **NOT_VALIDATION — hypotheses-only.**
**Escopo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a. Sem Caminho B, sem mudar conceito, sem escolher versão final.
**Gross R.** Read-only w.r.t. RAW/produção. Sem gates/thresholds/filtros novos. Nenhuma plotagem, MCP/chart, Telegram, broker.

---

## 1. Executive summary

Anatomia por tags dos universos **T1 (trigger+EMA stack, n=246)** e **T8 (trigger+EMA+D1a, n=206)**, com tags derivadas só de campos já validados (regime_flags + D1a causal). Engine reusado (0 SHIFT leaks). **Re-rodado** porque os outputs anteriores não traziam `d1a_pass` nos tiers sem D1a (motivo registrado).

**Dois achados robustos (DA-aprovados, baseados em contagem exata ou n adequado):**
1. **O residual D1a-fail é "target-starved":** dos 41 trades T1 que falham D1a, **só 1 vira target (≈2%) vs 10% de base-rate** em T1. Fato de composição (contagem exata), não inferência de expectância.
2. **Dentro do D1a, ATR particiona qualidade:** T8 com ATR (n=89) PF **2.34** / DD-6.96 vs T8 sem ATR (n=117) PF **1.88** / DD-9.0 — n adequado; **hipótese a testar OOS** (split único, dados sobrepostos).

**Narrativas de cauda DESMENTIDAS pelo DA (n insuficiente — NÃO reportar como achado):**
- "D1a remove cluster net-negativo −4.48R": n=41, −0.11R/trade, CI atravessa zero → na verdade **residual sem edge positivo**, não "cluster perdedor".
- "ATR×D1a synergy": o cell ATR-sem-D1a tem n=32 (−0.04R/trade) = **info ~zero**; frame errado.
- PF individual dos premium (T4/T5/T6) = subconjuntos sobrepostos dos mesmos ~200 trades; decorativo, não evidência.

**Armadilha central (DA):** como **pct_d1a = 0.83** em T1, dizer "todo R positivo vive nos cells D1a" é em parte **identidade aritmética** (83% dos trades SÃO os cells D1a). A afirmação honesta é estreita: "o residual sem D1a (17%) não carrega edge positivo, em n pequeno" — **não** "o D1a gera o edge".

**Veredito:** conceito vivo. **T8 segue como candidato a base primária** (apoia-se em 206 trades reais). Exit-geometry (25% BE, time-limit como small winner) é **descritivo da config congelada**, não fato estrutural, e bloqueado atrás de MFE/MAE ausente. **DA: PASS (hypotheses-only).**

---

## 2. Mentalidade de research

Anatomia do edge, não validação/otimização/escolha final/descarte. Gross, in-sample, **round 3 sobre os mesmos dados** (~28 cells acumulados) → qualquer PF de cell isolado é decorativo. Linguagem ajustada ao n: claims de cauda (n<50) rebaixados a "underpowered".

---

## 3. Universos analisados

| Univ | Definição | n | sumR | PF | avgR | WR | maxDD | streak |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| A | T1 (EMA stack) | 246 | +82.03 | 1.82 | 0.33 | 32% | -12.4 | 16 |
| B | T8 (EMA+D1a) | 206 | +86.10 | 2.06 | 0.42 | 34% | -11.5 | 17 |
| C | T1 & D1a-fail | 41 | −4.48 | 0.77 | -0.11 | 22% | -7.0 | 8 |
| D | T8 & ATR | 89 | +41.98 | 2.34 | 0.47 | 35% | -6.96 | 10 |
| E | T8 & ¬ATR | 117 | +44.13 | 1.88 | 0.38 | 33% | -9.0 | 15 |
| F | Premium T4 / T5 / T6 | 122 / 88 / 106 | +49.7 / +44.7 / +48.2 | 2.06 / 2.20 / 2.18 | — | — | — | — |

---

## 4. Tags disponíveis e indisponíveis

**Disponíveis** (de campos validados): ema_stack_pass, close_gt_ema200, ema50_gt_ema200, ema50_slope_pass, atr_expanding_pass, adx_pass, **d1a_pass**, d1_close_gt_ema200, d1_ema50_gt_ema200, full_regime_pass, full_minus_adx_pass, full_minus_slope_pass, exit_reason, winner, duration_bars.
**Indisponíveis (não inventadas):** **MFE_R, MAE_R** (engine não computa). Toda hipótese sobre "BE saiu cedo de runners" / "quão longe foi a excursão" fica **bloqueada** até MFE/MAE.

---

## 5. T1 anatomy (por outcome)

| grupo | n | avgR | medianR | pct_atr | pct_d1a | pct_adx |
|---|--:|--:|--:|--:|--:|--:|
| target | 25 | 4.0 | 4.0 | 0.52 | **0.96** | 0.72 |
| stop | 98 | -1.0 | -1.0 | 0.45 | 0.81 | 0.71 |
| stop_be | 62 | 0.0 | 0.0 | 0.50 | 0.81 | 0.48 |
| time_limit | 61 | **+1.31** | +1.40 | 0.53 | 0.85 | 0.64 |
| winners | 78 | +2.34 | +2.15 | 0.50 | 0.89 | 0.68 |
| losers | 168 | -0.60 | -1.0 | 0.48 | 0.81 | 0.62 |

- **Targets quase sempre D1a-aligned** (0.96 vs base 0.83) — robusto direcionalmente.
- **Time_limits são small winners** (+1.31R) → com o cap +4R / stop 24-bar, muitas saídas por tempo são trends parciais. **Descritivo da config congelada**, não fato estrutural.
- **25% terminam em BE** (62/246, avgR 0) — descritivo da regra BE@+1R; "saiu cedo de runner" **não testável sem MFE/MAE**.

---

## 6. T8 anatomy (por outcome)

| grupo | n | avgR | pct_atr | pct_adx |
|---|--:|--:|--:|--:|
| target | 24 | 4.0 | 0.50 | 0.75 |
| stop | 79 | -1.0 | 0.37 | 0.71 |
| stop_be | 50 | 0.0 | 0.46 | 0.50 |
| time_limit | 53 | +1.30 | 0.47 | 0.64 |
| winners | 69 | +2.43 | 0.45 | 0.70 |
| losers | 137 | -0.60 | 0.42 | 0.62 |

**T8 vs T1 (efeito do D1a):** targets 24 vs 25 (~iguais); stops 79 vs 98 (−19); winners 69 vs 78 (−9). **D1a corta predominantemente stops e mantém targets** — porém parte do "−19 stops" é base-rate (stops são 40% vs targets 10%; qualquer corte acerta ~4× mais stops). **O sinal honesto:** o residual D1a-fail converte em target muito menos (≈2% vs 10%).

---

## 7. T1-only / análise de corte D1a

Universo C (T1 & D1a-fail, n=41): sumR −4.48, PF 0.77, WR 22%, **1 único target (≈2%)**.
- ⚠️ **DA:** −4.48R/41 = −0.11R/trade, CI ~[−0.6,+0.5] **atravessa zero** → reportar como **"residual sem edge positivo"**, NÃO "cluster perdedor".
- Robusto (contagem): **target-starvation** (1/41 ≈ 2% vs 10% base) — este é o fato limpo.

---

## 8. EMA × ATR × D1a intersections (partição de T1=246)

| cell | n | sumR | PF | avgR | tgt | stop | be | time |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| EMA_only (¬ATR,¬D1a) | 9 | -3.20 | 0.20 | -0.36 | 0 | 4 | 4 | 1 |
| EMA_ATR (ATR,¬D1a) | 32 | -1.28 | 0.92 | -0.04 | 1 | 15 | 8 | 8 |
| EMA_D1a (¬ATR,D1a) | 117 | +44.13 | 1.88 | 0.38 | 12 | 50 | 27 | 28 |
| EMA_ATR_D1a (ATR,D1a) | 88 | +42.38 | 2.37 | 0.48 | 12 | 29 | 23 | 24 |

**Leitura honesta (DA):**
- Os cells **sem D1a** (9+32=41) têm n minúsculo **por construção** (só 17% dos trades não têm D1a). −1.28R/32 e −3.20R/9 = **info ~zero** — NÃO concluir "ATR sem D1a é fraco".
- **Comparação defensável** = dentro do D1a: **EMA_ATR_D1a (PF 2.37, n=88) vs EMA_D1a (PF 1.88, n=117)** → ATR particiona qualidade. **Hipótese**, split único sobre dados sobrepostos.

**Respostas (com caveats):**
- ATR complementa D1a ou redundante? Dentro do D1a, ATR sobe PF 1.88→2.37 (hipótese). Fora do D1a, dados insuficientes.
- D1a complementa ATR ou só corta N? Concentra a população lucrativa (target-starvation do residual), mas "gera edge" é overclaim (identidade aritmética 83%).
- EMA+ATR+D1a base forte ou estreita? PF 2.37 mas n=88 — **estreita**; premium, não base ampla.
- T8 sem ATR ainda tem valor? Sim (PF 1.88, n=117) — base mais larga.
- T8 com ATR mais explosivo ou só seletivo? Mais seletivo + DD menor (-6.96 vs -9.0); "explosivo" não verificável sem MFE.

---

## 9. Premium vs core

- **Core:** T1 (n=246), T8 (n=206) — base ampla, n real.
- **Premium:** T4/T5/T6 (n=88-122, PF ~2.06-2.20) — **subconjuntos sobrepostos**, PF individual decorativo (DA: ~28 cells, sem correção).
- **Premium melhora real ou só reduz N?** Em parte denominador (concept_composition já mostrou). A única melhora com n decente é ATR-dentro-de-D1a (D vs E).
- **Premium deve ser estratégia separada?** Indefinido — candidato a **priority label / review filter**, não estratégia única. Decisão exige pré-registro + bootstrap.

---

## 10. Year / regime / concentração

- T1/T8: 2 anos negativos (de 11); premium (T5/T6) 3. 2020/2024/2025 carregam; 2022 fraco.
- Pré-2020 vs pós-2020: pós carrega (ex. T8 ~ pós-2020 domina).
- **Concentração 2025/2019/2020** registrada — **não invalida**, mas é risco a checar (visual + sub-janela).

---

## 11. Subideias preservadas

- **ATR como tag de qualidade dentro do D1a** (D vs E, PF 2.34 vs 1.88) — hipótese OOS.
- **Target-starvation do residual D1a-fail** (fato de composição) — usar para entender o que D1a remove.
- **T8 como base primária ampla** (n=206) — candidato a pré-registro.
- **Time_limit como small-winner** + 25% BE — sinais para o **estudo SL/exit** (precisa MFE/MAE).
- Todas HYPOTHESIS_ONLY; nenhuma promovida.

---

## 12. Plot sets recomendados (NÃO plotados)

Gerados em `results/tag_profiling_plot_sets.md` (10 listas com count + por-que-plotar + pergunta visual). Destaques: T8 targets (24), T8 stops, **T1 winners cortados por D1a** (~9), T1 losers cortados por D1a, T8+ATR targets, T8-sem-ATR winners/losers, premium losers, biggest winners/losers (MAE indisponível → plotar para ver contexto). Para `CANONICAL_TRADE_PLOTTING.md` em bloco futuro autorizado.

---

## 13. O que ainda NÃO sabemos

- Se o split ATR-dentro-de-D1a (2.34 vs 1.88) sobrevive **OOS / bootstrap**.
- **MFE/MAE** de winners/losers/BE/time_limit (engine não computa) → exit-geometry não interpretável.
- Se a concentração 2020/2024/2025 é estrutural ou poucos trades.
- Reconciliação **visual** (nada plotado).
- Se as tags se mantêm net de custos.

---

## 14. Próximos blocos dentro BREAKOUT/D1a

- Plotagem canônica dos sets selecionados (visual review).
- **Estudo SL/exit** (com MFE/MAE — exige extensão do engine) → testar BE@1R / +4R / 24-bar.
- Relação fina BREAKOUT × L1.
- Refinamento **com pré-registro** (tier primário T8) + bootstrap PF-CI + custos net.

(Cris decide. Caminho B não recomendado.)

---

## 15. Devil's Advocate (subagente, incorporado)

| Pergunta | Risco | Síntese |
|---|---|---|
| "−4.48R cluster" (n=41) | **HIGH** | −0.11R/trade, CI cruza zero → residual sem edge, não cluster perdedor |
| "ATR×D1a synergy" (n=32) | **HIGH** | −0.04R/trade = info ~zero; frame errado; usar split D vs E (89/117) |
| Conditioning bias (pct_d1a 0.83) | **HIGH** | "R vive nos cells D1a" = identidade aritmética (83%) |
| "D1a corta stops não targets" | MED | parte base-rate; sinal honesto = target-starvation (2% vs 10%) |
| Multiple comparisons (~28 cells) | HIGH | PF de cell isolado decorativo |
| 25% BE / time-limit winner | MED-HIGH | descritivo da config congelada, não fato estrutural; precisa MFE/MAE |

**Achados robustos a reportar:** (1) target-starvation do residual D1a-fail (contagem); (2) ATR particiona qualidade dentro do D1a (89/117, hipótese OOS). **Demovidos a underpowered:** cluster −4.48R, ATR-sem-D1a, PFs premium individuais, exit-geometry como estrutural.

### Checklist DA do bloco
- ✅ Nenhum threshold novo · ✅ Nenhum filtro novo promovido · ✅ Dados existentes + re-run justificado (d1a_pass ausente) · ✅ Tags ausentes (MFE/MAE) marcadas, não inventadas · ✅ Métricas boas NÃO chamadas validação · ✅ Métricas ruins NÃO chamadas invalidação · ✅ Premium não promovido só por PF · ✅ Interpolação/conditioning considerados · ✅ Plot sets criados, NÃO plotados · ✅ Canonical plotting referenciado · ✅ Nenhum MCP/chart · ✅ Nenhum Telegram/broker · ✅ L1 intacta · ✅ Caminho B não recomendado.

**DA verdict: PASS (hypotheses-only).**

---

*Read-only w.r.t. RAW e produção. Gross R, in-sample, sem OOS/custos/visual/MFE-MAE/bootstrap. Outputs em `results/tag_profiling_*` (tracked). Re-run do engine justificado (d1a_pass ausente nos tiers não-D1a). Nenhuma plotagem.*
