# XAU 4H BREAKOUT/D1a × L2/BPT — Entry Test

**Data:** 2026-06-17 · **Tipo:** teste de entrada (retorno à polaridade) + expansão criativa · **NOT_VALIDATION — hypotheses-only.**
**Fonte:** RAW replay `.gz` ONLY (extractor auditado in-memory; **zero slim**). Gross R, sem custos. Sem MCP/plot/Telegram/produção.

---

## 1. Executive summary

Testei a tese do Cris (**breakout = validação; entrada de valor = retorno à polaridade do nível rompido**, Pattern #1) sobre eventos **T8** (trigger + EMA stack + D1a), RAW-only, com a polaridade = `swing_high_10[i]` (nível rompido). Comparei **entrada imediata** vs **retorno à polaridade** (touch / reclaim) sob 3 regimes de SL.

**Resultado honesto (DA-corrigido):**
- **O retorno à polaridade acontece em 80% dos eventos** (nível raso é retestado com frequência — só ~31 runaways perdidos, vs 61% de não-retorno no retrace-profundo). Isso é real e favorável à *espera*.
- **MAS o "PF~5" da primeira rodada era ARTEFATO** — combinava (a) **look-ahead** (SL usava o low da própria barra de toque ao preencher intrabar) + (b) **R-floor 0.3ATR** (stop minúsculo num nível-ímã). O DA previu; a correção confirmou.
- Com **SL causal estrutural** (base da consolidação `swing_low_10`, sem floor): **quase tudo aborta** (n=2, ambos losers) — o fundo estrutural fica > 1.5 ATR abaixo → **R-inviável**.
- Com **SL fixo realista** (`P − 1.0·ATR`, causal): a entrada-no-retorno fica **≈ equivalente à entrada imediata** (avgR ~0.46, PF ~1.75-1.82, holds out) — **não melhora**.

**Veredito:** a tese **não é refutada** (o fenômeno do retest é real e R-viável com stop 1ATR), **mas a mecanização honesta do retorno à polaridade NÃO entrega a melhora de edge esperada** com estas definições de SL. O ganho aparente foi artefato. **O ponto não-resolvido é a definição causal do SL** (tight = trapaça/look-ahead; base estrutural = profundo demais; 1ATR = equivalente). **DA: previu e confirmou (artefato).** Hypotheses-only.

---

## 2. Bootstrap / memória 24h recuperada

Confirmado (sem conflito memória×repo): D1a causal (close_time≤bar_open, 0 leaks); EMA1D causal (RAW 1D 2012); T8 base candidata; D1a corta stops/preserva targets; ATR particiona qualidade; plotagem canônica resolvida; **mecanizações ingênuas (retrace profundo + SL estrutural simples) subperformaram em expectância — não a tese**; "+292.8R" circular descartado; **SLIM proibido (RAW única fonte)**; L2/BPT/Reason Atlas = Pattern #1 do Cris (retest à polaridade), RESEARCH_CORE nunca validada (L2 v1 refutada → L2 v2 defs → SMC Unified pré-reg LOCKED não-implementado).

---

## 3. Hipótese normal

Breakout/D1a valida; entrada no **retorno ao nível de polaridade** (= `swing_high_10` rompido, resistência→suporte), com reclaim e SL estrutural — não no candle de rompimento.

## 4. Dados / fonte RAW

RAW 4H 2016-2026 (3 blocos contíguos), interpretado pelo extractor auditado **in-memory** (zero slim). EMA/ADX/ATR (eng), D1a (EMA1D causal). 15187 barras, **577 eventos T8**, **176 no-overlap**.

## 5. Definições L2/BPT usadas (canônicas reusadas, NÃO novas)

Polaridade = `swing_high_10[i]`. Buffers L2 v2/SMC Unified (decididos c/ Cris 2026-06-06/07): retest tol 0.15·ATR, reclaim buf 0.1·ATR, body≥0.5, R-ceiling 1.5·ATR. **Nenhum threshold novo inventado.**

---

## 6. Teste normal (FASE 1, no-overlap, gross)

| Entrada | SL | R3 n | WR | avgR | PF | HOLDOUT avgR | Leitura |
|---|---|--:|--:|--:|--:|--:|---|
| **IMMEDIATE** | low−0.5ATR | 176 | 47.7% | **0.46** | **2.0** | 0.50 | baseline limpo, holds out |
| l2_touch | retest-low−0.1ATR, floor 0.3ATR | 131 | 62.6% | 1.49 | 4.97 | 1.33 | **ARTEFATO** (look-ahead + floor) |
| l2_touch | **estrutural** (base consolidação) | **2** | 0% | −1.0 | 0 | — | **R-inviável** (fundo > 1.5ATR) |
| **l2_touch_fix1** | **P−1.0ATR (realista, causal)** | 141 | 37.6% | **0.46** | 1.75 | 0.41 | **≈ imediata** (R4: avgR 0.53, PF 1.82) |
| l2_reclaim_fix1 | P−1.0ATR | 24 | 33% | 0.19 | 1.3 | 0.64 | fraco, n pequeno |

**Respostas (FASE 1):**
1. **L2/BPT melhora a entrada?** Não em expectância — l2_touch_fix1 ≈ imediata (avgR ~0.46 ambos). O "melhora" só apareceu na versão-artefato.
2. **Retorno à polaridade > entrada imediata?** Em WR/PF, **não** sob SL honesto; em R-multiple, equivalente.
3. **Reclaim melhora ou reduz fills?** Reduz drasticamente (141→24) e enfraquece (PF 1.82→1.3) — o filtro reclaim corta para um subset pequeno/fraco.
4. **SL estrutural fica R-viável?** **NÃO** (base da consolidação > 1.5ATR → aborta ~tudo). Só o SL fixo 1ATR é viável.
5. **+2R/+3R/+4R muda a lógica?** Marginal; R4 levemente melhor em avgR/PF na l2_touch_fix1.
6. **Runaways perdidos ao esperar?** 31 (de 35 não-retornos eram immediate-R4 winners).
7. **Losers de topo evitados?** 4 (poucos).
8/9. Trades atuais ruins→no-trade / bons perdidos: a espera troca ~31 runaways por 4 losers evitados — **assimetria desfavorável** isolada, compensada só pelo fato de 80% retornar (fills mantidos a expectância igual).

---

## 7. Exploração criativa causal (FASE 2)

Gates causais sobre a entrada-no-retorno (not_inside_supply, atr_expanding, fresh_demand, not_nas_short, combos) — **todos `HYPOTHESIS_ONLY`**. Sob o SL estrutural honesto, **todos resultaram n=0** (a base já abortava por R-ceiling). Na versão-artefato anterior tinham n=4-25 (ruído, descartado pelo DA). **Nenhuma hipótese criativa promovida; nada conclusivo.**

---

## 8. Entrada imediata vs retorno à polaridade

Sob execução honesta (SL fixo 1ATR causal), **equivalentes em expectância** (avgR ~0.46, PF ~1.8-2.0). O retorno não bate a imediata; a imediata não bate o retorno. A diferença aparente anterior era 100% geometria de SL minúsculo + look-ahead.

## 9. Runaways perdidos vs losers evitados

80% retornam → só 35/176 nunca retornam; desses, **31 runaways perdidos : 4 top-losses evitados** (assimetria desfavorável de esperar isoladamente). É a métrica mais honesta do custo da espera.

## 10. SL / target / R-viability

- SL minúsculo (retest-low floored) = look-ahead/artefato. SL estrutural (base) = R-inviável (>1.5ATR). SL fixo 1ATR = viável mas equivalente à imediata. **A definição causal do SL é o crux não-resolvido.**
- Target: a assimetria +4R/1R da imediata permanece R-eficiente; nas versões L2 viáveis, R4 ≈ melhor mas sem vantagem sobre a imediata.

---

## 11. Achados sólidos
- O retest da polaridade (nível rompido) ocorre **80%** das vezes (raso, frequente).
- A **entrada imediata em T8** é R-viável e estável: PF 2.0, avgR 0.46, holds out (a config mais limpa até agora).
- O **PF~5 do L2_touch era artefato** (look-ahead + floor) — confirmado por correção causal.

## 12. Achados fracos
- l2_touch_fix1 (retorno + SL 1ATR) ≈ imediata (sem melhora).
- l2_reclaim_fix1 fraco (n=24, PF 1.3).

## 13. Achados refutados (limitadamente)
- Refutado: a versão **com SL minúsculo floored** (artefato/look-ahead).
- Refutado: a versão **com SL = base estrutural da consolidação** (R-inviável, >1.5ATR).
- **NÃO refutado:** a tese macro (retorno à polaridade é fenômeno real, R-viável com stop fixo) — só não entregou edge superior com estas SLs.

## 14. Hipóteses preservadas
- **A definição causal do SL para a entrada-no-retorno** é o problema central em aberto (tight=trapaça, base=profundo, 1ATR=equivalente) — pode existir um SL causal intermediário/estrutural-mais-fino que diferencie.
- Target/gestão dimensionados (a imediata é eficiente; talvez o retorno precise de gestão própria).
- SMC Unified Rebuild v0 (S1/S2/S3 com SL R-bounded próprio) como mecanização alternativa não testada aqui.
- SHORT-inversion: parado (insight paralelo).

## 15. Plot sets recomendados (NÃO plotados)
- l2_touch_fix1 R4 fills (em `results/l2_bpt_breakout_trades.jsonl`) — para revisão visual do retorno à polaridade vs imediata.
- Os 35 eventos sem-retorno (runaways) — para ver visualmente o que se perde ao esperar.
- (Nada plotado neste bloco.)

## 16. Devil's Advocate (auto-checklist + DA spawn incorporado)

O DA foi spawnado neste teste e previu o artefato; a correção causal confirmou.
- ✅ Nenhum SLIM como source-of-truth (RAW-only). ✅ RAW não alterado. ✅ L2/BPT não inventado por nome (Pattern #1 + L2 v2/SMC Unified). ✅ Polaridade causal (`swing_high_10[i]`). ✅ Reclaim/SL sem futuro (SL fix = `swing_low_10`/`P−1ATR`, conhecidos no evento; **look-ahead da v1 corrigido**). ✅ Daily não-forming (D1a causal). ✅ Nenhuma hipótese criativa promovida (FASE2 n=0/ruído). ✅ Imediata vs retest comparadas no MESMO set. ✅ Runaway loss (31:4) reportado como headline. ✅ R-viability central. ✅ Gross/custos caveat. ✅ Nenhuma plotagem/MCP/Telegram/broker. ✅ L1 intacta. ✅ Caminho B não recomendado. ✅ SHORT não aberto.

**DA verdict: PASS — tese suportada em direção (retest real, R-viável), NÃO em magnitude; PF~5 = artefato; entrada-no-retorno ≈ imediata sob execução honesta. Hypotheses-only.**

---

*Read-only. RAW-only (zero slim). Gross, sem custos, in-sample/holdout (não OOS). Outputs: `results/l2_bpt_breakout_test_summary.json` (tracked) + `l2_bpt_breakout_{trades.jsonl,plot_ready.csv}` (gitignored). Nenhuma plotagem.*
