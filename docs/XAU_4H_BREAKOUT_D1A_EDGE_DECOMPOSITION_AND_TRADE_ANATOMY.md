# BREAKOUT / D1a — Decomposição do edge por regime + Anatomia dos trades

**Data:** 2026-06-16 · **Tipo:** análise read-only de artefatos existentes · **NOT_VALIDATION.**
**Foco exclusivo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a / DECISIVE_BREAKOUT. (Sem Caminho B, sem mudança de conceito, sem encerramento prematuro.)
**Não fez:** backtest novo, código, scanner/runtime/catalog/strategy_rules, RAW, MCP/chart, Telegram, broker, mover/deletar. Só agregou dados já existentes (sweep CSV + trades.jsonl) e leu prosa de summary.md. Só este relatório foi criado.
**DA:** executado via subagente ANTES da conclusão (hook `post_backtest_devils_advocate`) — feedback incorporado em todo o doc; síntese no §15.

---

## 1. Executive summary

No BREAKOUT/D1a, a leitura dos artefatos **sugere** (direção, não prova) que o **regime carrega mais peso que o trigger** — mas a decomposição precisa ser lida com 4 ressalvas duras (§3): tudo é **SLIM/in-sample**, o sweep é **seleção entre 22 configs**, os dois artefatos (sweep n=234 vs revalidação n=115) são **populações diferentes que não se explicam mutuamente**, e o **D1a não é reconstruível** do `trades.jsonl` (seus números são prosa de `summary.md`).

Leitura honesta por subcamada (toda direcional):
- **Núcleo aparente do edge:** **EMA-stack (close>EMA200 + EMA50>EMA200) + ADX≥20**. Combo `P` chega a +67.75R/PF1.36 (n=428) no sweep — quase o topo. O golden-cross (EMA50>EMA200) sozinho (`J`) já é forte (+66.28/PF1.27).
- **Camada de qualidade/seletividade:** **EMA50 slope + ATR expanding juntos** cortam N pela metade (428→234) e sobem PF 1.36→**1.64** (config `R_full_trend_regime`, a "adotada"). Mas **EMA50 slope sozinho é o PIOR gate** (`G`: +19.51/PF1.06/no_top10 −19.99) — só ajuda combinado.
- **htf_1d / D1a:** no **sweep**, `htf_1d_bullish` em cima do EMA-stack é **quase redundante** (P→S: n 428→427, PF 1.36→1.37 — close>EMA200 já captura o bias macro). Na **revalidação**, o `D1a` aparece **fortemente aditivo** (115→90, PF 1.48→1.86). **Tensão não resolvida** (artefatos diferentes; D1a é stricter que htf_1d; números D1a são prose-only).
- **Trigger sozinho:** fraco. Baseline sem regime (`A`): +32.84R mas **no_top10 −6.66R**, streak 31 → sem regime, depende inteiramente da cauda.

**Anatomia dos 115 (dump slim):** 9 target / 52 stop / 25 stop_be / 29 time_limit; +25.28R, WR 30.4%, PF 1.48. **Expectância carregada por ~9 targets + cauda de MFE** → **monumental-dependent**. Pior bolsão: chop_inflation_bear 2022 (−5.15R, WR18%, blow-off). Melhor: bull_recent 2024-26 (+16.42R).

**Não decidimos nada.** Conclusão central: *o regime parece ser a alavanca, o núcleo aparente é ADX+EMA-stack, slope+ATR é camada de seletividade, e D1a é candidato a refinamento macro — mas tudo é slim/in-sample/seleção e o D1a precisa de SHIFT1-audit em RAW antes de qualquer afirmação de "limpo/causal".* Subfiltros candidatos preservados como HYPOTHESIS_ONLY (§11), sem números.

---

## 2. Fontes lidas

- `XAUUSD_4H_breakout_regime_filter_sweep.csv` (22 configs, agregado) + `regime_filter_test.py` (origem).
- `research/revalidation/XAUUSD_4H_BREAKOUT_CONTINUATION/v1/`: `trades.jsonl` (115), `report.json`, `summary.md`, `config.json`, `methodology.md`.
- `docs/XAU_4H_BREAKOUT_CONTINUATION_D1A_DEEP_DIVE.md`, `…PRE_BOTTOM_CATCHER…`, `…RESCUE_MASTER_INVENTORY`, `…IDEA_REVIEW`, BOOTSTRAP pós-L1, `catalog.json`, Pine #01, recheck:931 (legacy ref).

Computação própria: agregação do `trades.jsonl` (exit_reason/regime/ano/MFE/MAE) — leitura de dump existente, **não** backtest novo.

---

## 3. Limites metodológicos (ler antes de tudo)

1. **SLIM, não RAW.** Todo número é propriedade do **dump slim**, NÃO da estratégia. Proibição permanente `feedback_never_use_slim_features` (slim inflou Caminho B +185R→+18R RAW). Nada aqui passa de "slim-sugestivo".
2. **In-sample, sem OOS verificável.** O único walk-forward (W1+W2 carregam, W3 no-op) é **prosa de summary.md**, não reconstruível do `trades.jsonl`. Tratar como asserção não-verificada.
3. **Dois artefatos NÃO se conflam.** Sweep (agregado, n=234/+64.57R) e revalidação (`trades.jsonl`, n=115/+25.28R) são **runs/universos diferentes**. Anatomia de um **não explica** números do outro. Nunca misturar numa só narrativa.
4. **Config-label mismatch não resolvido.** `config.json` diz `S_full_trend_htf`; gates implementados + n=234 pertencem a `R_full_trend_regime`. Até reconciliar, atribuição por-config repousa em label não-verificado.
5. **D1a não é auditável daqui.** `trades.jsonl` **não tem** campo D1a/1D/htf por trade (o único "htf" é dentro de `config_id`). O split 90/25, "+32.2R/PF1.86", "remove 25 = −6.93R", "só 1 target removido" existem **só como prosa** em `summary.md`. Não verificável trade-a-trade.
6. **Poder estatístico baixo.** n=115 com **só 9 targets**; cells por-regime de 8-22 trades. Afirmações por-regime são **descritivas**, CIs largas o bastante para inverter sinal. Expectância repousa em ~5-10 trades (monumental-dependent) → jackknife/no_top10 obrigatórios antes de qualquer statement de expectância.
7. **`no_top10`/`no_top5` são probes de robustez, não claim de edge.** Cortam nos dois sentidos: se +25R/+64R vivem numa mão-cheia de monumentais, "o edge" pode ser 5-10 trades.

---

## 4. Sweep de 22 configs — tabela completa (agregado, in-sample, seleção)

Fonte: `XAUUSD_4H_breakout_regime_filter_sweep.csv`. Métricas **net @0.05R**. `best_r=3.95 / worst_r=−1.05` em TODAS (target 4R, stop 1R + custo). **Não há per-trade aqui.** Ordenado por total_net_r:

| config | gates | n | totR | avgR | PF | WR | streak | no_top5 | no_top10 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **S_full_trend_htf** | adx20+close>ema200+ema50>ema200+htf_1d | 427 | **68.8** | 0.161 | 1.37 | .258 | 22 | 49.05 | 29.30 |
| T_minimal_trend_htf | close>ema200+ema50>ema200+htf_1d | 565 | 68.65 | 0.122 | 1.28 | .246 | 30 | 48.9 | 29.15 |
| **P_adx20+ema_stack** | adx20+close>ema200+ema50>ema200 | 428 | 67.75 | 0.158 | 1.36 | .257 | 22 | 48.0 | 28.25 |
| J_ema50_above_ema200 | ema50>ema200 | 572 | 66.28 | 0.116 | 1.27 | .245 | 30 | 46.53 | 26.78 |
| F_atr_expanding | atr_expanding | 434 | 65.27 | 0.150 | 1.36 | .279 | 18 | 45.52 | 25.77 |
| **R_full_trend_regime** *(adotada)* | adx20+close>ema200+ema50>ema200+ema50_slope+atr_expanding | **234** | 64.57 | **0.276** | **1.64** | .286 | **16** | 44.82 | 25.07 |
| V_robust | adx18+ema50>ema200+htf_1d+breakout_exp | 362 | 55.64 | 0.154 | 1.35 | .251 | 19 | 35.89 | 16.14 |
| C_adx20 | adx20 | 613 | 55.36 | 0.090 | 1.20 | .251 | 21 | 35.61 | 15.86 |
| Q_adx22+ema_stack | adx22+close>ema200+ema50>ema200 | 378 | 54.23 | 0.144 | 1.33 | .251 | 20 | 34.48 | 14.73 |
| M_range_expanding | range_expanding | 436 | 52.75 | 0.121 | 1.29 | .264 | 21 | 33.0 | 13.25 |
| U_anti_chop | no_chop_10+breakout_exp+atr_expanding | 350 | 52.54 | 0.150 | 1.35 | .274 | 20 | 32.79 | 13.04 |
| D_adx22 | adx22 | 542 | 50.06 | 0.092 | 1.21 | .249 | 20 | 30.31 | 10.56 |
| E_adx25 | adx25 | 418 | 50.0 | 0.120 | 1.27 | .254 | 23 | 30.25 | 10.5 |
| O_htf1d_bullish | htf_1d | 692 | 49.71 | 0.072 | 1.17 | .234 | 26 | 29.96 | 10.21 |
| B_adx18 | adx18 | 676 | 49.45 | 0.073 | 1.17 | .240 | 20 | 29.7 | 9.95 |
| K_no_chop_10 | no_chop_10 | 792 | 44.81 | 0.057 | 1.13 | .236 | 31 | 25.06 | 5.31 |
| N_htf12h_bullish | htf_12h | 706 | 40.85 | 0.058 | 1.13 | .234 | 26 | 21.1 | 1.35 |
| I_close_above_ema200 | close>ema200 | 690 | 40.15 | 0.058 | 1.13 | .235 | 27 | 20.4 | 0.65 |
| A_baseline_no_regime | {} (trigger só) | 834 | 32.84 | 0.039 | 1.09 | .231 | 31 | 13.09 | **−6.66** |
| L_breakout_expansion | breakout_exp | 583 | 31.63 | 0.054 | 1.12 | .232 | **39** | 11.88 | −7.87 |
| H_close_above_ema50 | close>ema50 | 780 | 21.48 | 0.028 | 1.06 | .228 | 29 | 1.73 | −18.02 |
| G_ema50_slope_pos | ema50_slope | 677 | 19.51 | 0.029 | 1.06 | .220 | 29 | −0.24 | **−19.99** |

(maxDD não está no CSV; `streak` = max_losing_streak.)

---

## 5. Decomposição dos gates de regime (direcional, NÃO causal)

⚠️ As 22 configs **não são um fatorial limpo** (diferem em N e combos); o que segue é **comparação direcional entre configs**, não atribuição causal isolada.

- **Base sem regime (`A`):** +32.84R / PF1.09 / **no_top10 −6.66** / streak 31. → **trigger sozinho é fraco e cauda-dependente.**
- **Golden-cross `EMA50>EMA200` (`J`):** +66.28 / PF1.27 — **o single-gate mais forte por total_R.** É o lifter macro principal.
- **ATR expanding (`F`):** +65.27 / PF1.36 / WR .279 — forte e melhora PF/WR. Filtro de "mercado vivo".
- **ADX≥20 (`C`):** +55.36 / PF1.20 — lifta PF da base (1.09→1.20). Some ao stack sobe PF (T→P: +adx, PF 1.28→1.36, N 565→428).
- **close>EMA200 sozinho (`I`):** fraco (+40.15 / PF1.13). Mas é a "porta" do bias macro que os stacks usam.
- **EMA50 slope sozinho (`G`):** **PIOR** (+19.51 / PF1.06 / no_top10 −19.99). **Só ajuda combinado** (dentro de `R` contribui pra cortar N e subir PF).
- **htf_1d sozinho (`O`):** modesto (+49.71 / PF1.17). **Em cima do EMA-stack é quase redundante** (P→S: N 428→427, PF 1.36→1.37) — close>EMA200 já captura o bias diário.
- **breakout_expansion (`L`):** **prejudica** (no_top10 −7.87, streak 39 = pior streak). Não usar isolado.

**Síntese (hipótese):**
| Papel | Gates |
|---|---|
| **Carregam edge** | EMA50>EMA200 (golden-cross), ATR expanding, ADX≥20 |
| **Camada de qualidade/seletividade** (cortam N, sobem PF combinados) | EMA50 slope + ATR expanding (juntos → R: PF 1.64, N 234) |
| **Quase redundante** sobre o EMA-stack | htf_1d (e, por extensão, a ideia do D1a — ver §6) |
| **Limpam ruído mas fracos isolados** | close>EMA200, no_chop, range_expanding |
| **Perigosos/contraproducentes isolados** | EMA50 slope, close>EMA50, breakout_expansion |

- **Combinação mínima que preserva ~máximo do edge:** `P` = **ADX + EMA-stack** (+67.75 / PF1.36 / n=428) — ~98% do total_R do topo com o dobro de N de `R`.
- **Trade-off de seletividade:** `R` (adotada) troca N (428→234) por PF (1.36→1.64) e DD/streak menores (16). É **escolha de qualidade**, não de total_R (S/P têm total_R maior).

---

## 6. O que realmente parece carregar o edge

1. **O regime, não o trigger** — confirmado direcionalmente pelo salto base→stack (no_top10 −6.66 → +28). **Máximo que se pode dizer:** "configs com gate de regime pontuaram melhor que a base sem regime, neste sweep slim — direção, não prova." Não atribuir o edge a 1 gate.
2. **Núcleo = golden-cross + ATR-expanding + ADX.** Os três aparecem nas configs de topo e cada um, isolado, supera a base.
3. **slope + atr_expanding = seletividade**, não edge-fonte (slope isolado é o pior gate).
4. **D1a é candidato a REFINAMENTO macro, não núcleo provado.** No sweep, o análogo htf_1d é quase redundante sobre o EMA-stack; na revalidação o D1a parece forte — **tensão não resolvida** entre artefatos. Não declarar D1a "núcleo" nem "limpo/causal".

---

## 7. Anatomia dos 115 trades (dump slim — descritivo)

| | valor |
|---|---|
| n / sumR / avgR / WR / PF | 115 / +25.28R / +0.220 / 30.4% / 1.479 |
| exit_reason | **target 9 · stop 52 · stop_be 25 · time_limit 29** (29 right-censored) |
| MFE_R | max **5.99**, mediana ~1.0 |
| MAE_R | min **−3.23**, mediana ~−0.93 |

**Por regime (descritivo, cells pequenas):**
| regime (ano) | n | sumR | avgR | WR | PF |
|---|---:|---:|---:|---:|---:|
| bull_recent (2024-26) | 40 | **+16.42** | +0.410 | .375 | 2.03 |
| bull_pre_covid (2019) | 14 | +7.46 | +0.533 | .357 | 1.93 |
| covid_rally (2020) | 10 | +3.63 | +0.363 | .200 | 1.83 |
| chop_macro (2023) | 10 | +1.82 | +0.182 | .300 | 1.61 |
| pre_covid (2016-18) | 22 | +2.09 | +0.095 | .318 | 1.22 |
| chop_post_covid (2021) | 8 | −1.00 | −0.125 | .125 | 0.80 |
| **chop_inflation_bear (2022)** | 11 | **−5.15** | −0.468 | .182 | 0.26 |

**Por ano:** positivo em 2017/19/20/23/24/25/26; negativo em 2016/18/21/22; **2025 carrega +12.6R (n=23)** e bull_recent carrega o resultado. **Expectância concentrada** — ~9 targets + cauda de MFE; **monumental-dependent**. MFE máx 5.99R (target capado em 4R → alguns correriam mais).

> ⚠️ Por-regime e por-ano são **descritivos**. Com 8-22 trades por cell e 9 targets totais, CIs invertem sinal. Não tratar ranking de regime como propriedade estável.

---

## 8. Anatomia dos 25 D1a-rejects (⚠️ prose-only — NÃO reconstruível daqui)

**Limite duro:** `trades.jsonl` **não carrega** flag D1a nem campos 1D. Não consigo reconstruir os 25 rejects trade-a-trade. O que segue é **transcrição do que `summary.md` documenta** (asserção não-verificável aqui), não medição própria:

- D1a (1D fechado, no-lookahead) → **90 keep / 25 reject**; keep +32.20R, PF 1.86; rejects somam **−6.93R**; **só 1 target** entre os 25 (8/9 targets preservados).
- Walk-forward (prosa): W1 2016-2020 +9.55→+13.15; W2 2020-2023 −2.52→+0.81 (PF cruza 1.0); **W3 2023-2026 +18.24→+18.24 (no-op)** — não degrada a janela recente.
- Visual review dos 25 (prosa): **~20/25 rejeições "corretas"** (topo/exaustão/contexto); **5 falsos-positivos** com R+ nomeados: #3 +0.76, #8 +2.08, #10 +0.96, #20 +4.00, #21 +0.67 (total +8.48R deixados na mesa) — event-driven (Fed pivot Nov-2021, CPI Nov-2022)/não-replicáveis; só #10 candidato replicável. Decisão registrada: não criar exceção.
- Residual após D1a: **chop_inflation_bear −2.82R** (n=7 keep) — o **regime label** (não o stop) parece o carrier do prejuízo de 2022.

**Padrão comum alegado nos rejects:** breakouts contra/sem direção macro 1D (tops/exaustão). **Não verificável** sem 1D por trade. Visual review = **calibração, não validação** (`feedback_calibration_vs_validation_45_groups`).

---

## 9. Targets vs Stops

Do dump (descritivo): **9 targets (+4R)**, **52 stops (−1R)**, 25 stop_be (~0R), 29 time_limit (mistos, 25% dos trades).
- **Targets:** MFE alto (alguns >4R, capados); concentrados em bull_pre_covid/covid_rally/bull_recent (regimes trending). 8/9 preservados pelo D1a (prosa) → targets tendem a estar alinhados ao macro.
- **Stops:** dominam pre_covid e chop. **`trades.jsonl` não traz ADX/EMA/D1 por trade** → **não consigo** dizer "qual gate cada stop tinha". Não inventar.
- **stop_be (25):** BE@+1R move stop pro entry → infla "não-perda" sem ser win. Cuidado ao contabilizar WR/PF (be_moved interage).
- **time_limit (29 = 25%):** fato estrutural relevante — um quarto dos trades sai por tempo (24 bars). "Apertar/soltar o time-stop ajuda" = **não testado**.

---

## 10. Blow-off / fragilidade de stop / casos críticos

- **chop_inflation_bear 2022 (n=11, −5.15R, WR18%, PF0.26):** pior bolsão. `summary.md` (prosa): entries com close_1D ~**+3.18 daily-ATR acima da EMA200** (blow-off) e ~+9.5 ATR_4H da swing_high (chasing breakout esticado); 0 targets; stop 0.5ATR "pequeno demais" pra expansão pós-entrada.
- **Confound (DA):** não dá pra atribuir o prejuízo ao **multiplicador de stop** especificamente. O residual "−2.82R após D1a" sugere que o **regime/período** (2022, um bolsão único) é o carrier, não o stop. **NÃO generalizar "0.5ATR é frágil"** — é observação de 2022, não propriedade.
- **MAE min −3.23R:** há trades que foram a −3.23R de excursão adversa (com stop nominal −1R, indica gaps/expansão intrabar ou medição de MAE sobre o range) — sinal de que o risco realizado pode exceder 1R em expansão. Vale **estudo** (não conclusão).

---

## 11. Subfiltros candidatos preservados (HYPOTHESIS_ONLY — SEM números)

Inspirados nos trades perdedores que deveriam corrigir → **se quantificados agora, viram overfit in-sample garantido**. Nenhum testado; nenhum com R atrelado.

| Subfiltro | Ideia | Marca |
|---|---|---|
| Cap de extensão diária | bloquear entry se close_1D − EMA200_1D > k·ATR_1D (anti blow-off 2022) | HYPOTHESIS_ONLY · NEEDS_RAW_MAPPING · NEEDS_PRE_REGISTRATION |
| Distância da EMA / da swing | bloquear "chasing" (entry muito longe da swing_high/EMA) | HYPOTHESIS_ONLY · NEEDS_VISUAL_REVIEW |
| ATR-expansion excessiva | distinguir expansão saudável de climática | HYPOTHESIS_ONLY · DO_NOT_TEST_YET (risco de cortar bull_recent) |
| SL estrutural (vs low−0.5ATR) | swing/zone-based em vez de 0.5ATR | HYPOTHESIS_ONLY · NEEDS_VISUAL_REVIEW |
| Time-stop tuning | 29/115 saem por tempo (24 bars) | HYPOTHESIS_ONLY · NEEDS_PRE_REGISTRATION |
| Regime D1 mais limpo (D1a stricter) | reconciliar D1a vs htf_1d (por que diverge §6) | HYPOTHESIS_ONLY · NEEDS_RAW_MAPPING · NEEDS_SHIFT1_AUDIT |

`DO_NOT_TEST_YET`: ATR-expansion-excessiva (provável corte de bull_recent, o regime que carrega o edge).

---

## 12. Relação com a L1 EMA21 CONTINUATION refinada

- **L1 = pullback-and-go, anti-extensão** (ret5/ext_ema/zone_w/dist_zone, volume baixo, RSI exhaustion gate). **BREAKOUT = impulso/rompimento, pró-momentum** (corpo forte, ATR expandindo). **Opostos no eixo respiro↔rompimento.**
- A L1 **rejeita** extensões; o BREAKOUT possivelmente **captura parte** delas → **ortogonais/complementares**, não competidores.
- **D1a pode servir de macro-contexto para o BREAKOUT, NÃO para a L1** (a L1 já tem regime_l1_v4 D-1).
- **NÃO** misturar automaticamente o **RSI gate da L1** no BREAKOUT: na L1 o RSI é **anti-exhaustion**; no BREAKOUT o RSI é **pró-momentum** (RSI>MA). Semânticas opostas.
- O **SL estrutural da L1** pode **inspirar** gestão do BREAKOUT (vs `low−0.5ATR`), mas **não aplicar sem estudo** (§11).
- Encaixe natural: **futura L2 breakout separada** do motor L1 (módulo próprio), não fusão.

---

## 13. O que ainda NÃO sabemos

- Se o edge sobrevive em **RAW** (tudo é slim).
- Se sobrevive **OOS** (pós-2026-06).
- Se a vantagem do regime sobrevive à **correção de seleção** (22 configs, sem Bonferroni).
- **Se o D1a é de fato causal/no-lookahead** — precisa **SHIFT1-audit em RAW** (precedente A1' SUPERTREND: "causal-by-construction" colapsou 88%→46%). Hoje é **asserção de design, não propriedade verificada**.
- Por que o **D1a (revalidação) diverge do htf_1d (sweep)** em impacto — artefatos diferentes, não reconciliados.
- A anatomia **por-gate dos stops/targets** (trades.jsonl não traz ADX/EMA/D1 por trade).
- Se a expectância sobrevive a **jackknife/no_top10** no nível do dump de 115 (monumental-dependent).

---

## 14. Próximos blocos possíveis (dentro de BREAKOUT/D1a)

- **C — Separação de conceito / manifest preliminar (read-only):** isolar o núcleo (trigger + ADX + EMA-stack + slope/atr-seletividade + D1a) num gate manifest desacoplado do canal recheck/rótulo catalog.
- **D — Relação fina BREAKOUT vs L1:** sobreposição temporal (quantos bars disparariam juntos/separados), confirmar ortogonalidade.
- **E — Estudo conceitual de SL/exit:** `low−0.5ATR` vs SL estrutural, time-stop (29/115), MAE −3.23R — conceitual, sem teste.

(O Cris decide qual, quando. Sem recomendação de família externa.)

---

## 15. Apêndice — Devil's Advocate (subagente, incorporado)

DA executado via subagente antes da conclusão. Veredito do DA: **a postura honesta é "sinal slim in-sample, viés de seleção, lookahead-não-auditado, monumental-dependente; leads promissores pendentes de RAW + SHIFT1 + OOS"** — alinhado à postura SUSPENSO-de-OFICIAL, não promoção. Correções aplicadas:

| Ponto DA | Como foi incorporado |
|---|---|
| Slim ≠ propriedade da estratégia | §3.1 + números rotulados "dump slim" em todo o doc |
| Sweep e revalidação não se conflam | §3.3 + §5/§7 mantidos separados; tensão §6 explicitada |
| D1a não reconstruível / prose-only | §3.5 + §8 inteira marcada prose-only |
| "Causal-by-construction" ≠ verificado | §6.4 + §13: NEEDS_SHIFT1_AUDIT, precedente A1' |
| Regime = edge é overstated | §5/§6: "direcional, não causal", claim máximo declarado |
| 0.5ATR frágil = não-generalizável | §10: confound regime/período, não generalizar |
| n=115/9 targets → poder baixo | §3.6 + §7 marcado descritivo; monumental-dependence |
| Subfiltros viram overfit se quantificados | §11: HYPOTHESIS_ONLY, sem números, 1 DO_NOT_TEST_YET |
| Não virar "não validado" em validado NEM em worthless | §1/§13: leads preservados como hipótese, não refutados nem provados |

**Checklist do bloco:**
- ✅ Nenhum backtest novo (só agregação de dump existente).
- ✅ Sweep tratado como seleção in-sample/hipótese, não validação.
- ✅ D1a tratado como hipótese causal não-provada (prose-only, NEEDS_SHIFT1_AUDIT).
- ✅ Nenhum dado ausente inventado (split D1a e per-gate dos stops marcados não-reconstruíveis).
- ✅ MFE/MAE analisados só porque **existem** no trades.jsonl.
- ✅ Nenhum subfiltro promovido; todos HYPOTHESIS_ONLY.
- ✅ Sem conclusão precipitada; sem decisão final.
- ✅ Caminho B não recomendado.
- ✅ L1 descrita corretamente (anti-extensão vs pró-momentum; RSI semântica oposta).
- ✅ Nada operacional tocado.

**DA verdict: PASS.**

---

*Read-only. Nenhum backtest novo; nenhum código/scanner/runtime/catalog/strategy_rules/RAW/scheduler/broker/Telegram/MCP tocado. Todos os números são in-sample/SLIM/agregado conforme §2-3. Nenhuma decisão final de descarte ou promoção.*
