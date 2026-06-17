# XAU 4H BREAKOUT / D1a — Entry Mining Results (RAW substrate + multi-agent + stop-width)

**Data:** 2026-06-17 · **Tipo:** mineração de entrada · **NOT_VALIDATION — hypotheses-only.** · **Gross R.**
**Escopo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a. Sem Caminho B, sem mudar conceito.
**Fonte:** RAW replay `.gz` ONLY (extractor auditado in-memory; **zero slim** — `feedback_never_use_slim_features`).

---

## 1. Executive summary (honesto, inclui correções)

Testamos a tese visual do Cris (breakout = validação, não gatilho; valor na entrada do retrace à demanda; SL estrutural) **mecanizada e medida rigorosamente** sobre um substrato RAW de 1038 eventos de validação (333 no-overlap para independência), com 14 agentes diversificados + verificação adversarial + 5 Devil's Advocates.

**⚠️ Enquadramento (correção Cris 2026-06-17): NÃO é "tese refutada".** O que subperformou foi uma **implementação ingênua específica** — (1) esperar QUALQUER retrace em 24b; (2) SL estrutural simples mantendo +4R; (3) **sem distinguir** tipo de demanda, supply overhead, aceitação/rejeição, timing, regime. A tese/filosofia **segue hipótese aberta**; o fenômeno visual é real.

**Resultado central — as versões CRUAS não batem o baseline em expectância (não a tese):**
1. **"Esperar qualquer retrace à demanda em 24b" (cru) subperformou.** **61.3% dos breakouts nunca recuam** em 24 barras — muitos são winners (runaways). A versão crua **abandona-os**: entrada-no-retrace = WR 22%, +16.6R vs entrada-no-rompimento +46.8R. **NÃO** refuta esperar um retrace *bem qualificado* (tipo de demanda, aceitação/rejeição, timing).
2. **"SL estrutural simples + +4R" subperformou em expectância.** Sobe WR 37.5%→**55%** (holdout 61%), recupera 24/75 losers — **mecânico** (stop largo sempre sobe WR, baixa R-multiple). `avgR` a risco-fixo **cai 0.39→0.19**; stop curto faz **~2× o dinheiro/risco**; holdout flat. **NÃO** refuta SL estrutural *com target redimensionado*.

**O único lead honesto que sobreviveu:** **H3 regime** = no rompimento, `close>EMA200 AND atr_expanding` (sem ADX). WR 37.5%, +46.8R, holds out (TRAIN 35% → HOLDOUT 41%). Modesto, WR-only, n=120 (46 holdout) — **lead, não edge.**

**Correção honesta:** o "+292.8R swing" que reportei (retrace-entry vs current na sub-amostra dos retraced) era **CIRCULAR** — nos eventos que recuam, o stop curto é batido por construção. O DA havia avisado; eu propaguei. **Descartado.**

**Meta-aprendizado (não-óbvio):** a assimetria tight-stop +4R/1R do breakout **já é R-eficiente**; a alavanca não é entry-timing nem stop-width isoladamente — é **(a) seleção de regime (H3)** e **(b) target dimensionado ao risco** (não +4R sobre 4 ATR), que é o **único gate ainda não medido**. **DA: as duas IMPLEMENTAÇÕES ingênuas subperformaram (tese segue aberta); progresso real precisa de pré-registro + OOS + custos, NÃO mais p-hacking dos 333 eventos.**

---

## 2. Substrato (RAW-only)

`results/entry_anatomy.jsonl` (gitignored, regenerável): 1 linha/evento de validação (close>swing10[i-1] + bullish + body≥0.5 + rsi>ma), **construído 100% do RAW** via extractor auditado in-memory. Cruza contexto canônico (SMC / Custom OB demand-supply / NAS / Bubbles / RSI+div / volume) + EMA/ADX/D1a + forward path. Outcomes: current (tight SL), `bk_struct_sl` (structural SL, mesma entrada), `alt_demand_entry` (retrace entry). Builder: `build_entry_anatomy.py` (py_compile OK).

---

## 3. Mineração multi-agente (Fase 2, workflow)

8 lentes diversificadas (SMC · demand-geometry · volumetria/bubbles · NAS · regime · short-inversion · SL/exit · novel) → verificação adversarial → síntese. **32 achados → 5 survivors → 0 confirmados** sob gate adversarial (independência + não-circularidade + holdout). Zero confirmados = disciplina funcionando (nenhum edge fabricado).
- **H3** (close>EMA200 & atr_expanding): único filtro de entrada causal honesto, holds out.
- **H4** (`mae_R≥−0.5`): **look-ahead** (outcome-conditioned) → só diagnóstico ("o stop curto custa caro"), nunca filtro.
- **Short lead** (`inside_supply_zone` em sweeps-de-topo): 0.525/0.522 vs base-short 0.496 — minúsculo, estável, só proxy.
- **Negativos:** H2 (buy bubble) abaixo da base no train = overfit-holdout; H1 CHoCH marginal/repaint.

---

## 4. Stop-width isolation (gate prioritário do DA — entrada fixa, só o SL muda)

| H3 set, no-overlap (n=120) | WR | sumR | avgR |
|---|--:|--:|--:|
| **TIGHT SL** (low−0.5ATR) | 37.5% | +46.8R | **0.39** |
| **STRUCTURAL SL** (demand_low−0.5ATR) | **55.0%** | +22.7R | 0.19 |
| TRAIN tight / struct | 35.1% / 51.4% | +34.2 / +11.3 | 0.46 / 0.15 |
| HOLDOUT tight / struct | 41.3% / 60.9% | +12.5 / +11.4 | 0.27 / 0.25 |

- 24 de 75 tight-losers recuperam sob structural SL — **cosmético de WR**.
- Risco structural mediano **4.08 ATR** vs tight 2.02 ATR (~2×) → R-units não comparáveis; comparar `avgR`.
- **Veredito DA:** o stop curto **não é o problema**; é R-eficiente. SL estrutural troca WR por qualidade-por-risco e perde.

---

## 5. O que aprendemos / o que NÃO é

- A tese **visual** (chart) está certa sobre o *fenômeno* (breakout esticado em topo, retrace à demanda, runaways em bull). Mas as **mecanizações ingênuas** não viram edge: esperar perde os runaways; alargar o stop perde expectância.
- **A edge residual é seleção de regime** (H3), não timing/stop.
- A assimetria +4R/1R com stop curto é eficiente — qualquer alargamento de stop exige **target redimensionado** para não destruir o R:R.

---

## 6. Próximo gate (pré-registrado — NÃO rodar ad-hoc no mesmo dado)

**Gate único (DA):** SL estrutural **+ target dimensionado ao risco** (ex.: +1.5R/+2R, ou target à resistência/supply estrutural — **não** +4R sobre 4 ATR), pré-registrado em split fresco, **julgado em `avgR` a risco-fixo** vs o tight 0.39 OOS. Se não bater 0.39 fora da amostra → o stop curto nunca foi o problema, e o foco volta à **seleção de regime + a frente SHORT** (sweep-de-topo).
- Disciplina: já fizemos muitos cortes nos 333 eventos → mais tuning in-sample = overfit. Progresso real agora exige **OOS/cross-asset + custos + bootstrap**.
- **Frente SHORT** (paralela): sweep-de-topo (`inside_supply` / nas_short / supply overhead) → sim short real (entry/stop/target), não proxy.

---

## 7. Devil's Advocate (5 spawns, incorporados)

DA1 (substrato): exigiu simular a entrada-alternativa (feito). DA2 (Candidato B): "+292.8R é circular; 61% nunca recuam; naive-wait refutada". DA3 (stop-width): "stop curto não é o problema; avgR cai; WR é mecânico". Workflow verify: 0 confirmados. **Todas as correções aplicadas; nenhuma métrica boa chamada de validação; nenhuma ruim chamada de invalidação final — conceito preservado como investigação, próximo gate definido.**

**DA verdict: PASS (hypotheses-only; duas IMPLEMENTAÇÕES ingênuas subperformaram em expectância — tese segue hipótese aberta; H3 lead modesto).**

---

*Read-only w.r.t. RAW/produção. Gross, in-sample/holdout (não OOS verdadeiro), sem custos. Substrato RAW-only (zero slim). Nenhuma plotagem nesta fase. Outputs: `results/entry_anatomy_orientation.json` (tracked), `entry_anatomy.jsonl` (gitignored). Builder + workflow versionados.*
