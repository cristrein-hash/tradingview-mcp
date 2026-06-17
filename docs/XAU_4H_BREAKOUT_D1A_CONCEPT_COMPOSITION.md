# XAU 4H BREAKOUT / D1a — Concept Composition

**Data:** 2026-06-17 · **Tipo:** rodada de composição conceitual · **NOT_VALIDATION — hypotheses-only.**
**Escopo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a / DECISIVE_BREAKOUT. Sem Caminho B, sem mudar conceito.
**Gross R.** Read-only w.r.t. RAW/produção. Nenhuma plotagem, MCP/chart, Telegram, broker. Sem gates/thresholds novos.

---

## 1. Executive summary

Testamos mecanicamente se EMA-stack (V2), ATR-expanding (V3) e regime+D1a (V7) são **complementares** ou **interpolam** — montando 10 tiers (T0-T9) com composições de gates **já existentes** (zero threshold novo), engine causalmente auditado (0 SHIFT leaks em todos os tiers D1a).

**Achado robusto único (DA-confirmado):** **EMA-stack × ATR-expanding são genuinamente set-complementares** (jaccard 0.413; T1 tem 269 sinais exclusivos, T2 tem 172) e o **EMA-stack carrega informação PF-positiva real a alto N** (T0→T1: PF 1.55→1.82 **sem** colapsar N de 393→246). Essa é a única camada com edge ortogonal defensável.

**O resto é fronteira, não edge ortogonal.** Tudo downstream de T3 (D1a, ADX, slope; PF subindo 1.81→2.20) é **estatisticamente um blob**, consistente com a mecânica "cortar N → PF↑" num sistema de 30% WR cauda-dependente: qualquer filtro que remove N sobe PF se dropar marginalmente mais loser-R que winner-R. Exemplo direto: T3→T4 (+D1a) dropa um set **near-net-zero (+0.39R indep)** mas PF sobe 1.81→2.06 — lift quase puro de **denominador**, não informação nova.

**Micro-claims rejeitados como ruído:** "slope é prejudicial" (17 sinais, 7W/10L, +1.52R) e "ADX útil" (34 sinais, −3.19R) estão **dentro do ruído** — não sustentam conclusão; "slope harmful" seria confirmation bias (concorda com prior, mas n insuficiente).

**Veredito:** conceito **vivo e em investigação**. Esta rodada estabelece **uma** arquitetura robusta (EMA×ATR complementares + EMA como base de qualidade a alto N) e mostra que **empilhar 5-6 gates over-interpola** (N 393→88). Nada é edge validado. Próximo passo metodológico obrigatório: **pré-registrar o tier primário ANTES da próxima rodada** + custos net + bootstrap de PF-CI. **DA: PASS (hypotheses-only).**

---

## 2. Mentalidade de research

Investigação de **arquitetura de edge**, não busca de "estratégia final". Resultado ruim não invalida; bom não valida. Gross, in-sample, sem OOS/custos/visual/bootstrap. Os tiers filtram um sistema 30%-WR cauda-dependente, então **PF sobe mecanicamente** ao cortar N — a leitura deve normalizar por denominador, não tomar PF cru como qualidade.

---

## 3. Variantes testadas

T0 trigger · T1 +EMA stack · T2 +ATR exp · T3 +EMA+ATR · T4 T3+D1a · T5 full+D1a(=V7) · T6 full−ADX · T7 full−slope · T8 EMA+D1a · T9 ATR+D1a. (Gates existentes; D1a sempre CAUSAL `close_time≤bar_open`.)

---

## 4. Métricas por variante (gross, no-overlap)

| Tier | n | sumR | PF | avgR | WR | maxDD | streak |
|---|--:|--:|--:|--:|--:|--:|--:|
| T0 | 393 | +90.96 | 1.55 | 0.23 | 30% | -10.9 | 15 |
| T1 EMA | 246 | +82.03 | 1.82 | 0.33 | 32% | -12.4 | 16 |
| T2 ATR | 242 | +69.42 | 1.75 | 0.29 | 34% | -8.0 | 9 |
| T3 EMA+ATR | 154 | +49.62 | 1.81 | 0.32 | 34% | -9.3 | 13 |
| T4 T3+D1a | 122 | +49.74 | 2.06 | 0.41 | 35% | -9.45 | 12 |
| T5 full+D1a | 88 | +44.65 | 2.20 | 0.51 | 35% | -5.45 | 9 |
| T6 full−ADX | 106 | +48.20 | 2.18 | 0.45 | 34% | -8.45 | 12 |
| T7 full−slope | 101 | +43.48 | 2.05 | 0.43 | 37% | -5.45 | 8 |
| T8 EMA+D1a | 206 | +86.10 | 2.06 | 0.42 | 34% | -11.5 | 17 |
| T9 ATR+D1a | 170 | +51.37 | 1.80 | 0.30 | 34% | -10.8 | 9 |

**SHIFT audit:** todos T4-T9 = 0 same-day / 0 close_time_gt_bar_open / 0 missing → causal limpo.

---

## 5. Overlap entre V2/V3/V7/Tiers (sinais independentes; base T0=914; tiers ⊆ T0)

| Análise | Resultado |
|---|---|
| EMA(T1) × ATR(T2) | T1_only 269 · T2_only 172 · common 310 · **jaccard 0.413** |
| T1→T3 (+ATR) | dropa 269 = **66W / 203L** (indep +43.46R) |
| T2→T3 (+EMA) | dropa 172 = 52W / 120L (+22.12R) |
| T3→T4 (+D1a) | dropa 56 = 13W / 43L (**+0.39R = near-net-zero**) |
| T4→T5 (+ADX+slope) | dropa 57 = 15W / 42L (−0.97R) |
| ADX (T6 keeps 34 que T5 dropa) | 34 = 7W/27L (−3.19R) |
| slope (T7 keeps 17 que T5 dropa) | 17 = 7W/10L (+1.52R) |

membership_n: T0 914 · T1 579 · T2 482 · T3 310 · T4 254 · T5 197 · T6 231 · T7 214 · T8 501 · T9 346.

> ⚠️ **Caveat metodológico (DA):** o overlap usa outcomes **independentes** (sem no-overlap), então o sumR dropado é **limite superior de custo de oportunidade**, não R realizado pelo engine. Direção válida; não citar "+43R deixados na mesa" como realizado.

---

## 6. Complementaridade vs interpolação

- **Complementar (real):** EMA × ATR — conjuntos de sinais genuinamente diferentes (jaccard 0.41), cada um com exclusivos substanciais. EMA sobe PF mantendo N (não é só "trade-less").
- **Interpolação (mecânica):** todo o trajeto T3→T4→T5→T6→T7 (PF 1.81→2.20) acompanha exatamente o decaimento de N (154→88). Num sistema 30%-WR, cortar N **sempre** sobe PF se dropar mais losers. T3→T4 (+D1a) é o caso-prova: set dropado net-zero, PF sobe só por denominador.
- **Risco de interpolação excessiva: ALTO.** N colapsa 393→88; a tabela inteira é majoritariamente uma fronteira N↓/PF↑. Os tiers T3-T7 são **um blob estatístico** (n=88-154, ~11-32 targets; PF-SE grande, dominado por cauda).

**Resposta às perguntas obrigatórias (com caveats DA):**
1. **V2&V3 complementares?** Sim — parcialmente (jaccard 0.41). Único achado ortogonal robusto.
2. **EMA+ATR melhora qualidade ou corta edge?** Mantém PF (~1.81), corta majoritariamente losers, mas **downstream é denominador**.
3. **D1a melhora T3 ou corta demais?** PF 1.81→2.06, mas set dropado near-net-zero (+0.39R) → **lift de denominador, não info nova clara**. Modesto.
4. **Full regime (T5) agrega além de T3+D1a (T4)?** PF 2.06→2.20 marginal, N 122→88; **mesmo blob estatístico**.
5. **ADX útil ou redundante?** Remove −3.19R em 34 sinais = **dentro de ruído**; "mildly useful" no máximo.
6. **Slope útil ou instável?** Remove +1.52R em 17 sinais = **ruído**; "slope harmful" **não sustentado** (confirmation bias).
7. **Melhor base primária?** **T1 (EMA stack)** — único com PF-lift real a alto N (n=246, PF 1.82).
8. **Melhor camada premium?** Indistinguível entre T4-T7 (blob); tentativamente T6/T4 — mas **não escolher da fronteira sem bootstrap**.
9. **Interpolação excessiva?** Sim — caveat central.
10. **Melhor equilíbrio N/PF/DD/streak/estabilidade?** Na fronteira: T1/T8 (alto N) vs T5/T6 (baixo N, DD menor). Não há vencedor estatístico — **pré-registrar antes de decidir**.

---

## 7. Winners cortados / losers cortados

- EMA e ATR (T1→T3, T2→T3) cortam **majoritariamente losers** (66W/203L; 52W/120L) — bom ratio, mas é o esperado de qualquer filtro num sistema 30%-WR.
- D1a (T3→T4) corta 13W/43L mas o set é **net-zero** (+0.39R) — remove cluster near-BE.
- ADX/slope cortam sets pequenos dentro do ruído.

---

## 8. Estabilidade anual

neg_years (de 11): T0/T1/T2/T3/T4/T8 = **2**; T5/T6/T7 = 3; T9 = 4. Os tiers de alto N (T1/T8) têm **menos anos negativos** que os premium de baixo N (T5/T6/T7). 2020/2024/2025 carregam; 2022 fraco em todos. **Concentração de carry** = risco (DA top-3).

---

## 9. Melhor base primária candidata

**T1 (EMA stack)** — hipótese: é a camada com edge ortogonal defensável (PF 1.55→1.82 mantendo N=246, 2 anos negativos). Alternativa de alto N com D1a: **T8 (EMA+D1a, n=206, PF 2.06)** — mas o lift do D1a pode ser denominador. Ambas HYPOTHESIS_ONLY.

---

## 10. Melhor camada premium candidata

**Indistinguível estatisticamente** entre T4 (T3+D1a, PF 2.06, n=122), T5 (full+D1a, PF 2.20, n=88), T6 (full−ADX, PF 2.18, n=106). T6 mantém mais N que T5 a PF ~igual (ADX removível sem perda). **Não promover** — são o mesmo blob; precisa bootstrap + custos.

---

## 11. O que ainda NÃO sabemos

- Se algum PF-gap (1.8↔2.2) sobrevive a **bootstrap de PF-CI** (provável blob único T3-T7).
- Se sobrevive **net de custos** (com n=88-122 e ~11 targets, 0.2-0.4R/trade apaga o edge).
- Se o carry **2020/2024/2025** é estrutural ou poucos trades grandes (visual pendente).
- Se EMA×ATR complementaridade se mantém **OOS / sub-janelas**.
- Reconciliação **visual** + ADX/ATR/EMA recomputados vs TV.

---

## 12. Próximos passos dentro BREAKOUT/D1a

- **Pré-registrar o tier primário** (candidato: T1 base; premium a decidir) ANTES da próxima rodada — parar o frontier-mining.
- **Net de custos + slippage** sobre o tier pré-registrado.
- **Bootstrap PF-CI** para testar o blob T3-T7.
- Estabilidade **sub-janela / OOS**; checar concentração 2020/2024/2025.
- Plotagem canônica de um subconjunto (T1 ou D1a-rejects) para visual review.
- Estudo SL/exit (geometria +4R).

(Cris decide. Caminho B não recomendado.)

---

## 13. Devil's Advocate (subagente, incorporado)

DA executado ANTES da conclusão (hook). **Veredito: conceito sólido, continuar; mas a tabela de tiers é majoritariamente uma fronteira mecânica N↓/PF↑ — só EMA×ATR é complementaridade real.**

| Pergunta | Risco | Síntese |
|---|---|---|
| Metodologia overlap (independente vs no-overlap) | MED | direção válida; sumR dropado = limite superior, não realizado |
| Selection bias (18 configs total) | **HIGH** | T8/T6/drop-slope = frontier-mining; ranking instável; CIs largas |
| slope/ADX micro-claims (17/34 sinais) | HIGH/MED | ruído; "slope harmful" = confirmation bias |
| PF 1.8↔2.2 distinguível? | — | T3-T7 = **um blob**; PF acompanha N |
| "Trade-less = PF↑" mecânico? | MED-HIGH | parcialmente lands; EMA é real, D1a/ATR/regime são denominador |
| Gross/sem OOS/n baixo | HIGH | nada > hipótese sem net+bootstrap+walk-forward+visual |

**Maior armadilha:** ler a fronteira monotônica N↓/PF↑ como edge ortogonal por gate. **Correções aplicadas:** PF cru desmistificado (denominador); slope/ADX micro-claims marcados ruído; só EMA×ATR como achado robusto; pré-registro exigido.

### Checklist DA do bloco
- ✅ Nenhum threshold novo · ✅ D1a CAUSAL mantido · ✅ Nenhum filtro promovido como final · ✅ Métricas boas NÃO chamadas validação · ✅ Métricas ruins NÃO chamadas invalidação · ✅ Overlap analisado antes de concluir · ✅ Interpolação excessiva considerada (caveat central) · ✅ V2/V3/V7 comparadas por estabilidade+overlap, não só PF · ✅ Nenhuma plotagem · ✅ Nenhum MCP/chart · ✅ Nenhum Telegram/broker · ✅ L1 intacta · ✅ Caminho B não recomendado.

**DA verdict: PASS (hypotheses-only).**

---

*Read-only w.r.t. RAW e produção. Gross R, in-sample, sem OOS/custos/visual/bootstrap. Outputs em `results/` (bulk trades.jsonl + plot_ready.csv gitignored; overlap.csv + summary.json + summary.md tracked). Nenhuma plotagem.*
