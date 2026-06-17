# XAU 4H BREAKOUT/D1a × L2/BPT — Metrics Only

**Data:** 2026-06-17 · **Tipo:** extração de métricas concretas (sem plotagem) · **NOT_VALIDATION — hypotheses-only.**
**Fonte:** dump per-evento `results/l2_bpt_events_full.jsonl` (gerado pelo teste anterior, mesmos params; **metrics-only, sem backtest/RAW/slim novo**). Gross R, **sem custos**. Sem MCP/plot/Telegram/produção.

---

## 1. Executive summary

Métricas concretas comparáveis de **A) entrada imediata T8** vs **B) retorno à polaridade (SL P−1ATR causal)** vs **C) retest com reclaim**, no-overlap (176 eventos), gross.

**Quadro honesto:**
- **Full-universe ~equivalente em sumR**, mas perfis diferentes: imediata +82.4R (n=176, WR 45.5%, **maxDD −9.1**); retest +74.6R (n=141 fills, WR 34.8%, **maxDD −7.0**, **misses 35**). Retest = menos trades, WR menor, DD menor, mesma expectância por trade (avgR 0.53 vs 0.47).
- **Achado novo (pareado, mesmos 141 eventos que retornam):** o **retest faz +74.6R vs +15.6R da imediata** — quando o preço volta ao nível, comprar o retorno bate fortemente perseguir o rompimento. **MAS** o total da imediata é **carregado pelos 31 runaways** (eventos que nunca retornam): +66.8R que o retest não captura.
  - ⚠️ Caveat de seleção: os 141 eventos "que retornam" são, por construção, os de **pullback** — adversos à entrada imediata. Parte da vantagem do retest aí é seletiva, não pura.
- **Complementaridade por regime (year breakdown):** em **anos de tendência forte (2020, 2025)** a imediata domina (runaways): 2025 imm **+22.2** vs retest **+6.6**. Em **anos de chop/transição (2022, 2023)** o retest iguala/supera: 2023 retest **+8.5** vs imm **−0.7**.

**Veredito:** nenhum domina; são **complementares** (retest nos pullbacks/chop, imediata nos runaways/tendência forte). O retest **não melhora o baseline em expectância full-universe**, mas **reduz DD** e **domina condicionalmente** nos eventos que retornam. Reclaim corta N demais. Tudo hypotheses-only, gross, sem custos. **DA já auditou este teste nesta sessão (artefato PF~5 corrigido); enquadramento honesto mantido.**

---

## 2. Fontes e outputs usados

`results/l2_bpt_events_full.jsonl` (577 eventos T8, 176 no-overlap; dump do `run_l2bpt_breakout_test.py`, params lockados). Métricas computadas por `compute_l2_bpt_metrics.py` (read-only do dump). Outputs: `l2_bpt_metrics_only_summary.json` + `l2_bpt_metrics_only_tables.csv` (tracked). **Nenhuma lógica alterada; nenhum threshold novo.**

---

## 3. Tabela principal (no-overlap, gross, R4 primário)

| Grupo | n | WR | sumR | avgR | medR | PF | maxDD | streak | tgt | stop | time |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **A immediate T8 (R4)** | 176 | 45.5% | +82.4 | 0.468 | −0.25 | 1.97 | −9.1 | 7 | 26 | 82 | 68 |
| A immediate (R3) | 176 | 47.7% | +81.1 | 0.461 | −0.12 | 2.00 | −8.6 | 5 | 41 | 78 | 57 |
| **B l2_touch_fix1 P−1ATR (R4)** | 141 | 34.8% | +74.6 | 0.529 | −1.0 | 1.82 | −7.0 | 7 | 36 | 90 | 15 |
| B (R3) | 141 | 37.6% | +64.9 | 0.460 | −1.0 | 1.75 | −6.3 | 7 | 48 | 86 | 7 |
| **C l2_reclaim_fix1 (R3)** | 24 | 33.3% | +4.6 | 0.191 | −1.0 | 1.32 | −9.0 | 9 | 5 | 14 | 5 |

**TRAIN/HOLDOUT (R4):** A imediata TRAIN +39.5 / HOLDOUT +42.9 (estável). B retest TRAIN +37.0 / HOLDOUT +37.6 (estável). **stop_be=0** (BE desligado neste teste limpo — declarado).

---

## 4. Comparação entrada imediata vs retest

- **Total (full-universe):** imediata +82.4R (176) ≈ retest +74.6R (141, misses 35). Empate prático em sumR.
- **DD:** retest melhor (−7.0 vs −9.1). **WR:** imediata melhor (45.5% vs 34.8%). **avgR:** retest levemente melhor (0.53 vs 0.47, por risco maior/1ATR).
- **Custos:** NÃO considerados (gross). Stop 1ATR é mais robusto a custo que o tight 0.5ATR da imediata.

## 5. Runaways perdidos (esperar o retest)

35/176 (20%) **nunca retornam**; desses **31 são imm_R4 winners** (runaways perdidos pelo retest) e **4 losers** (top-losses evitados). Custo de esperar = perder 31 runaways para evitar 4 losers.

## 6. Losers evitados

Só 4 (os não-retornos que eram losers da imediata). A maioria dos não-retornos é winner (runaway).

## 7. Paired comparison (141 eventos que retornam, R4)

| Grupo | n |
|---|--:|
| E — imediata perde / retest ganha | 6 |
| F — imediata ganha / retest perde | 6 |
| G — ambos ganham | 43 |
| H — ambos perdem | 86 |
| (F-ext) sem-fill mas imm ganhou (runaway) | 31 |

- **imm_sumR nos 141 pareados = +15.6** vs **retest_sumR = +74.6.** Nos eventos que retornam, o retest é **muito melhor** (a imediata é chopada pelo pullback) — **mas é população de pullback (seleção)**.
- E≈F (6=6): quando discordam (≈12 eventos), é simétrico; concordam em 129/141.

## 8. Year breakdown (R4, sumR · imediata vs retest)

| Ano | imediata | retest | quem ajuda |
|---|--:|--:|---|
| 2017 | +9.2 | +10.6 | retest |
| 2018 | +4.4 | +6.0 | retest |
| 2019 | +13.5 | +8.6 | imediata |
| 2020 (covid) | +11.5 | +6.0 | **imediata (runaways)** |
| 2021 | −3.5 | −2.3 | ~ |
| 2022 (chop) | +3.3 | +6.0 | retest |
| 2023 (chop) | −0.7 | +8.5 | **retest** |
| 2024 | +17.8 | +19.5 | retest |
| 2025 (trend) | +22.2 | +6.6 | **imediata (runaways)** |
| 2026 | +3.5 | +3.0 | ~ |

**Padrão:** tendência forte (2020, 2025) → imediata domina (runaways); chop/transição (2022, 2023) → retest domina. **Complementaridade por regime.**

---

## 9. Respostas às 10 perguntas

1. **Retest melhora em expectativa ou só visual?** Full-universe: ~empate em sumR, **menor DD**; condicional (eventos que retornam): retest muito melhor (+74.6 vs +15.6), mas parte seleção (pullback). Não domina uniformemente.
2. **Winners perdidos por esperar:** 31 runaways.
3. **Losers evitados por esperar:** 4.
4. **Sem fill:** 35/176 (20%).
5. **SL P−1ATR R-viável?** **Sim** (141 fills, avgR 0.53, PF 1.82, DD −7.0). O estrutural-base não era (abortava ~tudo).
6. **Reclaim melhora ou corta N?** **Corta N demais** (141→24) e enfraquece (PF 1.82→1.32).
7. **Anos onde retest ajuda:** 2017, 2018, 2022, **2023**, 2024 (chop/transição).
8. **Anos onde retest piora:** 2019, **2020**, **2025** (tendência forte — perde runaways).
9. **Imediata ainda melhor baseline?** Como baseline simples R-viável que captura runaways: ligeiramente (sumR maior, mas DD maior, WR maior). **Sem vencedor claro** — complementares.
10. **Sets para plotagem futura:** ver §10.

---

## 10. Sets recomendados para futura plotagem (NÃO plotados)

- **31 runaways** (não-retorno, imm_R4 win) — ver o que se perde ao esperar.
- **Grupo E (n=6)** imediata-perde/retest-ganha + **Grupo F (n=6)** imediata-ganha/retest-perde — os casos de discordância.
- **Divergência 2025** (imediata +22.2 >> retest +6.6) — ver runaways de tendência forte.
- **2023** (retest +8.5 vs imediata −0.7) — ver retest ajudando em chop.
- l2_touch_fix1 fills (`results/l2_bpt_breakout_trades.jsonl`).

---

## 11. Devil's Advocate

DA já spawnado neste teste L2/BPT (previu/confirmou o artefato PF~5; SL look-ahead corrigido). Esta é extração metrics-only do mesmo dump — sem novo backtest/regra.
- ✅ Nenhuma plotagem/MCP/chart. ✅ Nenhuma regra/threshold novo. ✅ Nenhum SLIM (dump derivado de RAW). ✅ Métricas boas NÃO chamadas de validação; ruins NÃO de invalidação. ✅ Retest NÃO promovido (complementar, não superior). ✅ Imediata NÃO descartada (baseline R-viável). ✅ Caveat de seleção (eventos retornam = pullback) explícito. ✅ Custos/gross declarado (não considerados). ✅ Caminho B não recomendado; SHORT não aberto. ✅ Produção intacta.

**DA verdict: PASS — métricas concretas; complementaridade por regime; nenhum vencedor declarado; hypotheses-only.**

---

*Read-only metrics extraction. Gross, sem custos, in-sample/holdout (não OOS). Outputs: `l2_bpt_metrics_only_{summary.json,tables.csv}` (tracked); dump `l2_bpt_events_full.jsonl` (gitignored). Nenhuma plotagem.*
