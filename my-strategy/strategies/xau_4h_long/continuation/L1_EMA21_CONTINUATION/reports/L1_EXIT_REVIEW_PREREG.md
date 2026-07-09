# L1 EMA21 4H LONG Continuation — EXIT REVIEW · PRÉ-REGISTRO

**Versão:** 1.0 · **Data:** 2026-07-09 · **Status:** `PREREG_ONLY_NOT_TESTED`
**Escopo:** definir, ANTES de qualquer teste numérico novo, o desenho completo da revisão de saída (exit) da L1. Este documento **não** executa a revisão. Só inspeções read-only (métricas já aprovadas + leitura read-only das extensões de TP que o Cris marcou no chart) foram feitas para o escrever.

> **Regra dura herdada:** SL **NÃO** é reaberto aqui (oficial = V1 `zone_OB_low − 0.1ATR`, Cris 2026-07-03). Entrada, seleção e gating **NÃO** mudam. Só se revê a **gestão de saída** sobre o conjunto de trades já selecionado.

---

## 1. Objetivo

Determinar se uma regra de saída **causal (sem lookahead)** captura os runners de continuação em macro-regime BULL — que o alvo fixo `+3R` decapita — **sem degradar a base aprovada** (WR, PF, DD, streak, monumentais). A hipótese operacional do Cris: *"em macro-regime BULL, gestão de exit correspondente à tendência"* — deixar correr o que a estrutura sustenta, cortar o que ela nega, tudo decidível na barra, ao vivo.

O árbitro do "alvo ideal" é **o próprio Cris**: ele estendeu no chart 14 das 24 operações da FINAL-24 para mostrar o TP estrutural que teria capturado. Essas extensões são o **ground-truth do teto de captura** — não um alvo a otimizar, mas a referência do que uma saída causal deveria conseguir aproximar.

---

## 2. Baseline OBRIGATÓRIO — V1 APENAS

Toda comparação da revisão usa **exclusivamente** a base sob SL oficial V1 (`zone_OB_low − 0.1ATR`), target fixo `+3R`:

| Conjunto | N | W/L | WR | sumR | PF | Notas |
|---|---|---|---|---|---|---|
| **FINAL-24** (regime-gated, primário) | 24 | 18/6 | 75% | **+45.2R** | — | saved, sob V1 |
| **Scanner-31 V1** (secundário) | 31 | 17/14 | 55% | **+34.2R** | 3.44 | 15 TARGET / 14 STOP / 2 TIME · 5/5 monumentais |
| **Estudo-34** (terciário) | 34 | — | 53% | **+35.2R** | — | saved, sob V1 |

🚫 **PROIBIDO** usar o antigo baseline **+40.0R** do scanner-31: estava sob SL SUPERSEDED (`max(zone_OB_low, swing6_low) − 0.1ATR`, mais largo). Sob V1 o número correto é **+34.2R**. Qualquer delta da revisão mede-se contra estes três números V1, nunca contra +40R.

---

## 3. Unidade de análise

Cada trade = 1 episódio (entrada única, SL V1 único, uma saída). A revisão corre **em cada conjunto separadamente — nunca misturados**:

- **Primário: FINAL-24** — é o conjunto aprovado e o que o Cris anotou no chart. Decisão de aceitação/rejeição assenta aqui.
- **Secundário: Scanner-31 V1** — universo operacional reproduzível pelo `scanner.py`; testa se o ganho de exit sobrevive fora do conjunto curado (inclui os 14 STOP e 2 TIME).
- **Terciário: Estudo-34** — sanity de consistência (inclui os 3 exhaustion-blocked que o scanner exclui).

Um resultado só conta se **replicar direção do efeito no primário E no secundário**. Divergência entre eles = achado inconclusivo, reportar como tal.

---

## 4. Hipótese

**H1:** O alvo fixo `+3R` limita sistematicamente o ganho em BULL porque corta runners de continuação cujo MFE excede muito 3R.

**Evidência de suporte (ground-truth do chart, read-only, `l1_cris_tp_extensions.json`):** dos 24 da FINAL-24, o Cris estendeu **14** (todos winners); os 6 losers e 4 winners ficaram em 3R.

| bucket | trades | R_ideal (Cris) |
|---|---|---|
| ficou em 3R (4 W + 6 L) | #1,4,8,9 · #2,3,6,12,13,14 | 3.0 |
| estendido moderado (3.5–6R) | #5,7,15,16,21,22,23 | 3.57–5.40 |
| estendido runner (9–21R) | #10,11,17,19,20 | 9.07–21.51 |
| estendido monumental | **#18 → 60.77R** · #24 → 10.44 | — |

Média R_ideal dos 14 estendidos = **13.2R**; máximo **60.8R** (#18). O teto de captura que o 3R descarta é grande e concentrado num punhado de episódios — perfil clássico de runner. **H1 é plausível e o alvo da revisão é fechar essa lacuna causalmente.**

**H0 (nula a bater):** nenhuma regra causal de saída melhora sumR ajustado a risco (sumR e sumR/DD) vs `+3R` sem piorar WR/streak/DD de forma inaceitável. A revisão tem de **rejeitar H0 com margem**, não por optimização.

---

## 5. Alternativas de saída (A–E) — todas causais, decididas na barra

Cada alternativa é **totalmente especificada** antes de correr. Todas partilham: entrada = close da barra i; SL inicial = V1 (`zone_OB_low − 0.1ATR`); avaliação **on bar close** (nunca intrabar look-ahead); nenhuma usa MFE/pivots futuros.

### A — Fixo +3R (baseline / controlo)
- Trigger: `high ≥ entry + 3·risk`. · Timing: primeiro toque. · SL: fixo V1. · Sem parciais. · Gap: se abrir ≥ target, preenche no open. · Time-cap: cutoff canónico do estudo. **É o controlo — reproduz o baseline.**

### B — Let-run (sem alvo, saída só por SL/estrutura)
- Trigger de saída: **só** SL V1 OU flip de regime (ver E) — sem teto de lucro. · Timing: close. · SL: fixo V1 (variante B2: SL sobe para breakeven após +1R close-confirmed). · Time-cap: mesmo cutoff. · Mede o **teto bruto** de deixar correr — referência superior de captura.

### C — Trailing por EMA21 / candle-close
- Após atingir **+1R** (close-confirmed), SL passa a trailar: `max(SL_atual, min(EMA21_da_barra, low_da_barra_anterior − buffer))`. · Só sobe, nunca desce. · Saída: close abaixo do trailing. · Fonte: `EMA21` já no `scanner.py` (causal, bar i). · Gap-down abaixo do trail: sai no open. · Sem alvo fixo (teto = estrutura).

### D — Trailing por swing / V_stair
- Após +1R close-confirmed, SL trai para **último swing-low confirmado** (pivô estrutural já fechado — `swing_N` do scanner, nunca pivô futuro). · Só sobe. · Saída: close abaixo do último swing-low válido. · Variante D2: combina com step-degrau (sobe SL a cada novo HH close-confirmed). · É a que mais se aproxima do que o Cris descreve como "seguir a tendência".

### E — Flip de regime / estrutura (macro-exit)
- Saída quando o **regime BULL** que autorizou a entrada deixa de valer: `regime_l1_v4` sai de BULL na barra (close-confirmed) OU BOS de baixa (close abaixo do último higher-low estrutural). · Fonte: `regime_l1_v4` + estrutura, ambos já causais no scanner. · Pode combinar-se como **overlay** sobre B/C/D (E não é mutuamente exclusiva — testar E-standalone e E como camada de veto de saída).

**Matriz mínima a correr:** A (controlo), B, B2, C, D, D2, E-standalone, e as combinações C+E, D+E. Cada uma nos 3 conjuntos. Nenhuma combinação adicional "à mão" depois de ver resultados (ver §6).

---

## 6. Proibições anti-hindsight (dureza máxima)

1. **Nunca usar MFE (ou qualquer máximo futuro) para escolher a saída.** MFE só entra como *métrica de diagnóstico ex-post* (runner-capture-ratio), nunca como trigger.
2. **Nenhum pivô/estrutura futura.** Trailing só usa pivôs **já fechados** na barra de decisão.
3. **Nenhum trigger visual / discricionário.** As extensões do Cris no chart são ground-truth de *referência*, **não** regra executável — a regra tem de ser computável de campos causais.
4. **Não alterar entrada, SL inicial (V1), nem a seleção/gating.** Só muda a gestão de saída.
5. **Nenhuma optimização de threshold sobre os mesmos 24/31/34.** Os parâmetros de cada alternativa (buffer, ativação +1R, swing_N) são fixados **neste prereg** com os valores já usados no scanner; não se varre grelha nos conjuntos de avaliação.
6. **Nenhum "best-of-many" sem penalização exploratória.** A matriz de §5 é fixa e pequena. Se se reportar a melhor, reporta-se **quantas foram testadas** e aplica-se penalização (o "vencedor" não pode ser declarado edge sem sobreviver null/DA).
7. **Nenhuma regra impossível ao vivo** (intrabar peek, saída no exato topo, snapshot de futuro). Tudo decidível no close da barra corrente.

---

## 7. Métricas obrigatórias (por alternativa × conjunto)

Painel completo, sempre:

- **n · sumR · WR · PF · avgR · medianR**
- **maxDD (em R) · pior streak de perdas**
- **# saídas > 3R** (quantos runners a regra deixou passar do teto antigo)
- **# winners-do-baseline que voltaram a ≤ 0** (dano: trades que eram +3R e a nova saída estragou)
- **runner-capture-ratio** = `sumR_capturado / sumR_ideal_Cris` nos 14 estendidos (quão perto do ground-truth)
- **tempo-em-trade** (barras médias; custo de exposição)
- **pior excursão adversa depois de +3R** (quanto devolveu quem passou do alvo)
- **impacto nos 5 monumentais** (MFE≥6R — a regra preserva-os? amplia-os?)
- **vs-baseline:** Δ em sumR, sumR/DD, WR, streak vs A(+3R) — com sinal e no primário E secundário

---

## 8. Critérios de ACEITAÇÃO

Uma alternativa é candidata a promoção **apenas se, no primário FINAL-24 E no secundário Scanner-31 V1, simultaneamente:**

1. **sumR** ≥ baseline `+3R` **com margem material** (≥ +15% no primário) **E** sumR/DD ≥ baseline (não compra R com DD).
2. **# winners-do-baseline revertidos a ≤0 ≤ 1** (não destrói vencedores certos — regra do Cris: não sacrificar o pássaro na mão).
3. **pior streak** não piora além de +1 vs baseline.
4. **maxDD** não piora além de +20% em R vs baseline.
5. **5/5 monumentais preservados** (nenhum monumental cortado abaixo do que fazia em 3R).
6. Sobrevive a **null de saída** (permutação/shuffle da regra de trail vs saídas aleatórias com mesmo perfil de exposição) — o ganho não é sorte de sequência.

---

## 9. Critérios de REJEIÇÃO

Rejeita-se (ou marca-se RISK_CONTROL_ONLY, não edge) se qualquer:

- Ganho de sumR vem **só de 1–2 episódios** (ex.: #18) e desaparece jackknife-1 → **fragilidade concentrada**, não edge.
- **> 1 winner-do-baseline** vira ≤0 (viola §8.2).
- Streak/DD pioram acima dos limites §8.3–8.4.
- Efeito presente no primário mas **ausente/invertido no secundário** → inconclusivo.
- Só passa por optimização/best-of-many sem sobreviver penalização e DA.
- Depende de qualquer campo não-causal (falha §6).

---

## 10. Devil's Advocate obrigatório (bloco seguinte)

Antes de **qualquer** relatório de resultado da revisão de saída, correr o Devil's Advocate como spawn real via Agent tool (hook `post_backtest_devils_advocate` obrigatório), focado em:
1. O ganho é **hindsight-de-exit** disfarçado? (trailing calibrado a estes 24?)
2. **Concentração**: quanto do Δ vem do #18 (60R) e top-3? jackknife.
3. **Null de saída**: bate saídas aleatórias com mesma exposição?
4. **Dano oculto**: winners revertidos, streak, DD, tempo-em-trade.
5. **Causalidade byte**: variante leaky (com pivô futuro) prova que a versão causal não peeka.
6. **Primário vs secundário**: replica ou só curou os 24?

Sem DA PASS, não há relatório de resultado.

---

## 11. Outputs futuros (nomes reservados, ainda NÃO criados)

- `reports/l1_exit_review.py` — harness da matriz A–E × 3 conjuntos (fail-loud, causal, saved).
- `reports/l1_exit_review_result.json` — painel completo por alternativa × conjunto.
- `reports/L1_EXIT_REVIEW_REPORT.md` — relatório curto (só após DA PASS).
- `reports/L1_EXIT_REVIEW_DA.md` — devil's advocate do bloco.

Ground-truth já salvo (este bloco): `reports/l1_cris_tp_extensions.json` + `reports/l1_read_cris_tp_extensions.py`.

---

## 12. Status

- **STATUS:** `PREREG_ONLY_NOT_TESTED`
- **PRODUÇÃO:** `NOT_AUTHORIZED`
- **SL:** não reaberto (V1 oficial mantido)
- **NEXT_STEP:** `WAIT_FOR_CRIS_TO_AUTHORIZE_EXIT_REVIEW_EXECUTION`

Nada foi commitado nem pushed. Nenhum runtime/produção/Telegram/plotagem tocado neste bloco (a leitura das extensões foi read-only via MCP).
