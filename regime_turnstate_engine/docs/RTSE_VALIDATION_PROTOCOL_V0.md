# RTSE_VALIDATION_PROTOCOL_V0 — Protocolo de Validação

**Status:** PLANNING. Documentação only. Como provamos (ou refutamos) que o RTSE vale. Inclui a Fase 0 harness-probe (endurecimento #4).

---

## 1. Métrica primária — latência × falso-positivo vs `true_reversals_M8`
**Régua:** `research/xau_15m_bb_nas_leonardo/true_reversals_M8.csv` — 414 pivôs (205 BOT / 209 TOP), zigzag ATR M=8, 8 blocos / 3 anos (2024:137, 2025:196, 2026:81). **É RÉGUA, NUNCA feature.**

**Protocolo exato:**
1. Detector roda forward → lista de eventos `(ts, tipo, confidence)`, só com info ≤ ts.
2. Para um limiar de confiança `c`: um disparo é **TP** se existe pivô M8 do mesmo tipo na janela `[pivot_t, pivot_t+W]` (só dá pra disparar AO OU APÓS o pivô, causalmente). Disparo sem pivô na janela = **FP**.
3. Para cada pivô casado: **latência = barras do pivô até o 1º disparo qualificado**. Pivô sem disparo = **miss (perda de recall)**.
4. Varre `c` → curva: **precisão, recall, latência mediana + p90, FP rate, clustering de FP**, separado **BOT/TOP** e **por-bloco/ano/regime** (nunca só agregado).
5. Entrega por profile = um ponto na curva (ex.: scalp = FP-budget alto → recall 55% / latência 3 barras; swing = FP apertado → recall 35% / latência 9 barras).

## 2. ⛔ Fase 0 — HARNESS PROBE (endurecimento aceito #4, antes da construção pesada)
Antes de construir as 6 camadas: rodar o harness latência×FP medindo **só o que JÁ EXISTE** (regime v5 atual + baselines triviais) contra o M8. **Sem detector novo, sem re-cabear estratégia.**
- **Pergunta make-or-break barata:** algum sinal causal atual (v5) bate o lagged-MA na curva latência/FP?
- Se **NEM o v5 bate o trivial** → a premissa inteira é frágil → re-escopar ANTES de investir nas camadas. Front-load do veredito.
- Saída: a primeira curva latência/FP real do projeto + sanity do harness (reproduz 414/205/209).

## 3. Sensibilidade multi-M (correção do Cris aceita)
- `primary_label = M8` (ancorado na leitura validada do Cris).
- `sensitivity_labels = M6, M10, M12`.
- Pergunta dupla: "detectamos rápido o M8?" **E** "o detector continua útil quando a definição de reversão muda (M6/M10/M12)?" Se não sobrevive à troca de M → frágil.

## 4. Baselines obrigatórios (tem que bater TODOS em Pareto)
- regime v5 puro
- MA cross lagged (EMA50/200)
- swing-break simples
- RSI causal oversold/overbought
- random / null casado por frequência
Se não bate esses → **não há detector**. Se só empata com v5 → **só consolidação arquitetural, NÃO edge novo** (declarar, não inflar — `RTSE_CANON_V0` §3 anti-oracle / não-inflar).

## 5. Testes obrigatórios (validação mora nos dados — SEM OOS)
- **Null permutation** (shuffle/circular-shift; ou randomiza tempos de disparo preservando contagem) — bater null p<α (barra do programa: swept/bottom-power p=0).
- **Jackknife por episódio** (dropar cada um dos 8 blocos) — não pode colapsar; pega a armadilha "2026 carrega tudo".
- **Por ano** (2024/2025/2026; 2026 = ano-vigia, bottom-power não confirmou nele — honestidade).
- **Por regime** (bull/range/bear; BEAR onset = caso duro e valioso; v5 BEAR concord 0,75 é honestamente imperfeito por causa do bounce fev-mar = corretamente não-bear).
- **Por volatilidade** e **por sessão** (NY/Asia/EU).
- **Feature ablation** (remover cada feature → quanto a curva piora).
- **Bonferroni / null-of-the-max** em qualquer grid de threshold/janela (a célula E3 morreu aqui, p=0,92).
- **Robustez ±20%** em todo param. Params **espelhados do v5, NÃO fitados** às estratégias (anti-circularidade, como o 4H regime gate fez).

## 6. Red-team anti-look-ahead (gate de TODA fase — bug nº1)
Cada feature responde, sob auditoria do RTSE Lookahead Red-Team Agent:
- a info existia no close da barra? · foi shift1? · usa confirmação futura escondida? · usa pivot futuro? · usa label M8 como input? · usa zona hindsight? · usa top/bottom humano? · usa resultado do trade?
Falhou UMA → **descartada**. Teste mecânico: injetar barra futura sintética → estados passados têm que ser **byte-idênticos**.

## 7. Critério de promoção
≥12/15 do `reference_backtest_methodology_checklist` para "validated context"; a curva tem que bater todos os baselines sob null+jackknife. Default `recorded_context` até sign-off (Fase 7).

## 8. Critérios de FALHA explícitos (quando MATAR / re-escopar)
- v5 não bate lagged-MA na Fase 0 → premissa frágil, re-escopar.
- RTSE só empata v5 na Fase 2 → entregar como consolidação, **não** vender como edge.
- Curva colapsa em jackknife-episódio ou num único ano → beta/concentração, não sinal.
- Qualquer feature falha red-team → descartada (não "ajustada").
- Edge some quando M muda (M6/M10/M12) → frágil.
- n<30 por célula sustentando um claim → anedótico, sem promoção.
