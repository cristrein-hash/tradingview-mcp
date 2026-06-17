# XAU 4H BREAKOUT / D1a — Current State Synthesis

**Data:** 2026-06-17 · **Tipo:** síntese de estado (congelamento de raciocínio) · **NOT_VALIDATION — hypotheses-only.**
**Escopo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a / DECISIVE_BREAKOUT.
**Bloco:** **organização, zero execução** — nenhum backtest/workflow/agente/mineração/plotagem/MCP/RAW/script novo. Só este doc.

---

## 1. Executive summary

O BREAKOUT/D1a **não morreu**. Ao longo da sessão: o pipeline causal (D1a, EMA1D) foi resolvido; uma base primária candidata (**T8**) emergiu; a plotagem canônica foi resolvida; e a mineração RAW mostrou que **duas mecanizações ingênuas** da tese de entrada subperformaram **em expectância** — sem refutar a tese macro/auction-theory. A leitura visual do Cris não foi invalidada; ficou **mais sofisticada**: breakout é evento de validação/varredura de liquidez, a entrada imediata é frequentemente tardia, e a entrada de valor depende de estrutura, aceitação, demanda, supply overhead, regime e timing — não do candle de rompimento isolado.

**Tudo é hypotheses-only** (gross, in-sample/holdout, sem OOS verdadeiro, sem custos). Nada está pronto para live. Este doc congela o estado; não abre frentes.

---

## 2. Fatos provados

- **D1a causal resolvido.** Regra `latest_closed_daily = daily.close_time ≤ bar_open_4h`; trade-level SHIFT audit = **0 leaks** (same_day=0, close_time_gt_bar_open=0).
- **A regra ORIG vazava o D1.** A regra estilo-produção (`open_time < bar_open` / `t < bar_time`) seleciona o daily do mesmo dia em formação em **83.3%** das barras 4H intraday (provado em 15.434 barras). Segura só em live (arquivo exclui `today`); um backtest vazaria.
- **EMA1D causal criada.** Dataset RAW 1D 2012-2026 (3584 barras), EMA50/EMA200, warmup-ready 2013-04 (estável antes do breakout 2016).
- **T8 = base primária candidata.** Trigger + EMA stack + D1a: n=206, +86.1R, PF 2.06 (gross, no-overlap a parte).
- **D1a corta majoritariamente stops e preserva targets.** T1→T8: stops 98→79, targets ~24-25 (efeito real, com a ressalva de base-rate; o sinal limpo é o residual D1a-fail ser *target-starved*: 1/41 ≈ 2% vs 10% base).
- **ATR particiona qualidade dentro do D1a.** T8 com ATR: PF 2.34 (n=89); T8 sem ATR: PF 1.88 (n=117).
- **Plotagem canônica resolvida.** 153 trades T8 (targets + stops/stop_be) plotados como 306 shapes (long_position + label #id, verde/vermelho), verificado por `draw_list`. Sem clear/screenshot/troca de símbolo.
- **Fato estrutural robusto (n alto):** **61.3% dos breakouts nunca recuam à demanda em 24 barras** — muitos são os winners (runaways).

---

## 3. Fatos NÃO provados

- A estratégia **não está validada**. Nenhum setup pronto para live.
- **SL estrutural simples não provou edge** (sobe WR mecanicamente, baixa `avgR`).
- **Retrace simples à demanda não provou edge** (versão crua perde os runaways).
- **SHORT inversion ainda é apenas insight visual/paralelo** — nenhum short simulado de verdade.
- **Todas as métricas são hypotheses-only** — gross, in-sample/holdout, sem OOS, sem custos, sem bootstrap, sem visual review sistemático.
- O lead H3 (`close>EMA200 & atr_expanding`) é **modesto e WR-only** (não é edge provado).

---

## 4. Refutações LIMITADas (não "a tese morreu")

- Refutada a versão ingênua **"esperar qualquer retrace à demanda em 24 barras"** (regra bruta).
- Refutada a versão ingênua **"apenas trocar para SL estrutural mantendo +4R"** (lógica simplificada).
- **Isto NÃO refuta** a tese macro/auction-theory de que o breakout é evento de liquidez/varredura e a entrada imediata é frequentemente tardia. O fenômeno visual é real; o que falhou foram mecanizações cruas que **não distinguiam** tipo de demanda, supply overhead, aceitação/rejeição, timing e regime.
- ⚠️ Correção registrada (Cris 2026-06-17): não confundir **entrada ruim** com **conceito ruim**, nem **stop ruim** com **trigger ruim**.

---

## 5. Tese madura atual

**BREAKOUT não é entrada final. BREAKOUT é validação / evento de liquidez / deslocamento.**
A entrada madura depende de:
- **aceitação** acima do breakout **ou rejeição**;
- **qualidade da base de demanda** abaixo;
- **supply overhead** (resistência no caminho);
- **regime 4H / D1**;
- **energia real** (não expansão enganosa);
- **timing do pullback**;
- **relação risco/target** (target dimensionado ao risco);
- **anatomia da perna**, não só o candle de rompimento.

---

## 6. Arquitetura conceitual atual

| Camada | Estado |
|---|---|
| **Core candidate** | **T8** = Trigger (T1-T4) + EMA stack + D1a causal |
| **Energy tag** | ATR expanding (particiona qualidade dentro do D1a) |
| **Premium tag** | full regime / T5 / T6 / V7 (PF ~2.2; estatisticamente um blob, não distinto) |
| **Entry problem** | **ainda não resolvido** (entrada imediata é tardia; retrace cru perde runaways) |
| **Exit/SL problem** | **ainda não resolvido** (tight +4R/1R é R-eficiente; SL estrutural simples baixa avgR) |
| **Short inversion** | insight visual paralelo — **não abrir agora** salvo ordem do usuário |

---

## 7. Pontos de atenção (riscos)

- **overfit** e **p-hacking** (já houve muitos cortes sobre os mesmos 333 eventos no-overlap);
- **excesso de bifurcações**;
- usar **resultado ruim para matar hipótese cedo**;
- usar **resultado bom para validar cedo**;
- confundir **entrada ruim com conceito ruim**;
- confundir **stop ruim com trigger ruim**;
- métricas circulares (ex.: o "+292.8R swing" descartado: retrace ⇒ stop curto batido por construção).

---

## 8. Plot sets pendentes (já criados, NÃO plotados aqui)

Listados em `my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/v1/results/tag_profiling_plot_sets.md`:
- T8 targets;
- T8 losers / stops;
- T1 winners cortados por D1a;
- T1 losers cortados por D1a;
- T8 + ATR;
- T8 sem ATR;
- premium (T5) losers;
- biggest winners;
- biggest losers.

(Apenas T8 targets + T8 losers/stops foram plotados na sessão; os demais permanecem pendentes de revisão visual.)

---

## 9. Decisões pendentes do usuário

A tese de entrada madura (§5) ainda **não está mecanizada**. Como avançar — revisão visual dos plot sets, organização da tese de entrada, ou pausar BREAKOUT — é decisão do Cris. Não há próximo passo escolhido aqui.

**Próximo passo aguarda decisão do usuário.**

---

## 10. Devil's Advocate (auto-checklist do bloco)

- ✅ Não abriu nova frente.
- ✅ Não recomendou Caminho B.
- ✅ Não recomendou SHORT como próximo.
- ✅ Não recomendou OOS/cross-asset como próximo.
- ✅ Não invalidou a tese macro (refutações marcadas como limitadas, §4).
- ✅ Não chamou hypotheses-only de validação (§3 explícito).
- ✅ Não executou nada (zero backtest/workflow/agente/plot/MCP/RAW/script).
- ✅ Produção intacta (verificada read-only).

---

*Síntese read-only. Nenhuma execução, nenhuma plotagem, nenhum RAW/slim tocado. Congela o estado atual do BREAKOUT/D1a para retomada sob direção do usuário.*
