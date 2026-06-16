# Deep Dive — Estratégias XAU 4H pré-Bottom-Catcher

**Data:** 2026-06-16 · **Tipo:** análise/reconstrução read-only · **NOT_VALIDATION.**
**Escopo:** esgotar a revisão das famílias XAU 4H **antes** de avançar para o conceito Bottom Catcher / Caminho B. Mesmo rigor do deep dive F4+F5 (commit 5a3aae9).
**Não fez:** backtest, execução de scanner, alteração de código/catalog/strategy_rules/runtime/scheduler, Telegram, broker, MCP/chart, RAW, mover/deletar. Só este relatório foi criado.
**Famílias-alvo:** (1) Caminho A reversal a6 · (2) reversal a6_a7 · (3) A1 BALANCE · (4) A1' SUPERTREND / L5 · (5) XAUUSD_4H_BREAKOUT_CONTINUATION. Caminho B aparece **só como contraste**, não reanálise.

---

## 1. Executive summary

As 5 famílias se separam em **3 destinos** distintos:

- **Reversal a6 / a6_a7** (linhagem V1.4g-RWS): **REVERSAL_LONG** (fundo/pullback-em-uptrend), **ortogonal à L1 continuation**. Métricas fortes (a6_a7: n=177, WR 67.2%, +142.2R, walk-forward 3/3) **MAS** derivadas de **SLIM** (proibido como validação), **nunca passaram pelo look-ahead audit de 2026-06-06**, e o exit depende de **SMC BOS (repinta → SHIFT1)**. São o candidato reversal **mais maduro fora do Caminho B** → **`REVALIDATION_CANDIDATE` (após Caminho B; precisa RAW + lookahead audit + gate manifest).** a6 é predecessor → `KEEP_REFERENCE`.
- **A1 BALANCE e A1' SUPERTREND (= L5)**: ambas **`REJECTED_DO_NOT_REOPEN`** — **INVALIDADAS empiricamente por look-ahead** em 2026-06-06. A1 BALANCE: 68%→18% WR (anchor vaza outcome futuro). A1' SUPERTREND: 88%→46% WR (regime daily do mesmo dia). KEEP_REFERENCE como caso-escola.
- **XAUUSD_4H_BREAKOUT_CONTINUATION**: **sub-arquétipo distinto** (DECISIVE_BREAKOUT, **≠ pullback-continuation da L1**). Rótulo `ACTIVE_CANDIDATE` no catalog é **enganoso** (não deployado; recheck legacy dormant) → `CONTAMINATED_LEGACY / KEEP_REFERENCE`. A revalidação v1 (D1a) é metodologicamente a mais cuidadosa das 5 (regime-segmentada + walk-forward + visual review) **mas em SLIM, in-sample, sem OOS** → o filtro D1a é `REVALIDATION_CANDIDATE / NEEDS_RAW_BACKTEST + NEEDS_OOS`.

**Conclusão de priorização:** **nenhuma das 5 desloca o Caminho B do P0.** A única com valor independente vivo e ortogonal à L1 é a linhagem reversal **a6_a7** — mas ela compete no mesmo espaço (reversal/bottom 4H LONG) que o Caminho B, que é o candidato canônico já versionado e clean no lookahead audit. Recomendação: **seguir para o gate manifest do Caminho B**; reavaliar a6_a7 **depois**, como segunda lógica reversal.

**DA:** PASS (ver §17). Nenhuma classificada por nome sem gate real; nenhum in-sample/slim chamado de validação; look-ahead de A1/A1'/L5 explicitado; regime_B_v3 e vol_entry_z não ressuscitados; a6/a6_a7 não confundidas com F4+F5; L1 descrita com a config refinada correta; Caminho B só contraste; produção intacta.

---

## 2. Fontes lidas (read-only)

| Família | Fontes |
|---|---|
| a6 | `candidates/xau_4h_reversal_v1_4g_rws_a6/` (README, plot_script.py, 3 jsonl) + memory `project_xau_4h_reversal_v1_4g_rws_a6` |
| a6_a7 | `candidates/xau_4h_reversal_v1_4g_rws_a6_a7/v14g_rws_a6_a7_2016_2026.jsonl` (177) + memory `project_xau_4h_reversal_v1_4g_rws_a6_a7` |
| A1 BALANCE | memory `project_caminho_a_v3_A1_BALANCE_OFICIAL` (INVALIDADA) + `project_lookahead_audit_2026_06_06` |
| A1' SUPERTREND / L5 | memory `project_caminho_a_v3_A1_PRIME_SUPERTREND_OFICIAL` (INVALIDADA) + lookahead audit + `project_caminho_a_padroes_visuais_5_layers` (L5) |
| BREAKOUT_CONTINUATION | `catalog.json` (entrada 96-114), `research/experimental/xauusd_4h_long_breakout_continuation_regime_filtered.md` (packet), `research/revalidation/XAUUSD_4H_BREAKOUT_CONTINUATION/v1/` (summary/config/report/methodology) |
| Contexto | BOOTSTRAP pós-L1 (2026-06-16), MASTER_INVENTORY, IDEA_REVIEW, REEVALUATION_PLAN, LEGACY_KNOWLEDGE_INDEX, F4+F5 DEEP_DIVE, L1 module (STRATEGY/scanner), project_authority/ |

**Não usado como validação:** SLIM features e métricas in-sample (citadas só como histórico, marcadas como tal).

---

## 3. Tabela mestre

| Família | Nome real | Arquétipo | TF/Dir | Universo | Métricas (natureza) | Look-ahead audit? | Fonte de dados | Relação c/ L1 | Veredito |
|---|---|---|---|---|---|---|---|---|---|
| **a6** | V1.4g-RWS-A6 | REVERSAL_LONG | 4H LONG | V1 trigger union T1-T6 | n=182 WR65.4% +137.2R (in-sample/SLIM) | ❌ não | SLIM 4H | ortogonal (reversal) | **KEEP_REFERENCE** (predecessor de a6_a7) |
| **a6_a7** | V1.4g-RWS-A6-A7 | REVERSAL_LONG | 4H LONG | idem + A7 anti RSI-bear-div | n=177 WR67.2% +142.2R WF 3/3 (in-sample/SLIM) | ❌ não | SLIM 4H | ortogonal (reversal) | **REVALIDATION_CANDIDATE** (após B; NEEDS_RAW + NEEDS_LOOKAHEAD_AUDIT + NEEDS_GATE_MANIFEST) |
| **A1 BALANCE** | Caminho A v3 A1 BALANCE | reversal/natural-bull (anchored em B) | 4H LONG | CB amplo + anchor B-winner | ORIG 68%/+122.6R → **clean 18%/+12R/streak9** | ✅ INVALIDADA | (anchor B outcome) | — (refutada) | **REJECTED_DO_NOT_REOPEN** / KEEP_REFERENCE (caso-escola) |
| **A1' SUPERTREND / L5** | Caminho A v3 A1' SUPERTREND v1 | trend-following supertrend | 4H LONG | supertrend-active days | ORIG 88%/+75R → **SHIFT1 46%/+20R/DD−11R** | ✅ INVALIDADA | (daily mesmo-dia) | — (refutada) | **REJECTED_DO_NOT_REOPEN** / KEEP_REFERENCE (caso-escola) |
| **BREAKOUT_CONTINUATION** | XAUUSD_4H_BREAKOUT_CONTINUATION | DECISIVE_BREAKOUT (≠ pullback) | 4H LONG | close>swing_high(10) + regime gate | revalid v1 SLIM: n=115 WR30.4% +25.3R PF1.48; D1a→90/+32.2R/PF1.86 (in-sample/SLIM) | parcial (D1a é causal; base slim) | SLIM 4H | sub-arquétipo distinto | **CONTAMINATED_LEGACY / KEEP_REFERENCE**; D1a = REVALIDATION_CANDIDATE / NEEDS_RAW + NEEDS_OOS |

---

## 4. Deep dive — Caminho A reversal a6 (V1.4g-RWS-A6)

**1. Identidade real.** Nome: V1.4g-RWS-A6. Arquétipo **REVERSAL_LONG** (long em pullback/fundo dentro de uptrend, FundedNext-oriented). 4H, LONG. Universo = **V1 trigger union T1-T6** (V0 BEST variant, `risk_atr≥0.887`, `n_triggers≤2`, 1163 trades 2016-2026). Status correto: **OFICIAL em memory mas predecessor de a6_a7** (substituída mesmo dia). **Linhagem DISTINTA da L1** (continuation) **e da F4+F5** (continuation) **e de A1/BALANCE** (anchored em B). É a linhagem "reversal V1".

**2. Hipótese original.** Capturar reversões long em pullback dentro de uptrend, com agressão compradora retomando (bubble_buy) e sem RSI weakness / sem supply distante demais. Resolve o que a L1 não faz: **entradas de reversão/fundo**, não continuação.

**3. Processo de construção.** V1 → V1.3 (swing10 stop + BOS exit) → V1.4g (+bubble_buy + NOT range_middle) → V1.4j (+weekly regime — **REJEITADA**, cortou monumentais) → **V1.4g-RWS-A6** (refinamento empírico A6 via 3 subagents, gate duro "preservar 100% ≥5R/≥10R"). Absorvido pela L1: **nada** (famílias distintas). Parte que virou ideia futura: SHORT espelho, DCA/scaling entry.

**4. Gates reais.**

| Gate | Condição exata | Campo | TF | SHIFT1? | Lookahead | Status |
|---|---|---|---|---|---|---|
| V1 trigger union | T1-T6 + `risk_atr≥0.887` + `n_triggers≤2` | main_state | 4H | causal 4H | baixo | KEEP (precisa re-deriv RAW) |
| Bubble | `bubble_buy_recent==True` | bubbles | 4H | repinta→checar | médio (mapping) | REUSABLE c/ mapping validado |
| NOT range_middle | `abs(supply_dist−demand_dist)/2 > 0.5·ATR14` | SMC zones | 4H | repinta | médio | REUSABLE |
| RWS | rejeita se `rsi_above_ma_4h==False` AND `supply_dist>2·ATR14` | RSI+SMC | 4H | causal-ish | baixo-médio | KEEP |
| A6 (+NAS rescue) | rejeita se `buy_burst≥3` AND `large_buy_in_win8==0`, EXCETO `nas_recent_short_bars==0` | bubbles+NAS | 4H | repinta | médio | REUSABLE (mapping) |
| Stop | `swing_low(10)−1·ATR14` | OHLC | 4H | causal | nenhum | KEEP |
| Exit | next **SMC BOS bearish** 4H; fallback 100 bars | SMC | 4H | **repinta → SHIFT1 obrigatório** | **alto se não SHIFT1** | CONTAMINATED até auditar |

**5. Indicadores/features.** EMA implícito no V1; RSI (RWS, causal); Market Order Bubbles (filtro entrada — mapping a validar); Custom OB/SMC zones (range_middle, supply/demand dist); NAS (rescue A6 — mapping); ATR14 (stop/risk); swing_low(10) (stop); SMC BOS (exit — repinta). Útil ainda: RWS, swing stop, A6 conceito; **bubbles/NAS exigem re-validação de mapping**; **SMC BOS exit exige SHIFT1**.

**6. Estudos/backtests/métricas.** Backtest 2016-2026 sobre **SLIM** (`/Volumes/.../slim_features/XAUUSD/4H/`): n=182, WR 65.4%, +137.2R, avg +0.75R, streak 4, DD 4.4R, WF 3/3, 15/15 ≥5R + 4/4 ≥10R preservados. **Natureza:** in-sample + **SLIM** (proibido como validação) + exit SMC-dependente. **NÃO é validação** (slim, sem RAW, sem lookahead audit).

**7. Trades relevantes.** 5 trades cortados por A6 (2 losers eliminados + 1 winner real +1.32R perdido + 2 marginais). Monumentais ≥10R: 2017-12-21 (+11.58), 2020-02-18 (+11.62), 2020-07-20 (+11.63), 2025-10-10 (MFE 12.1R). Não aparecem na L1 (família distinta).

**8. Comparação c/ L1.** Hipótese oposta (reversal vs continuation); regime: L1 usa regime_l1_v4 BULL D-1, a6 não usa regime gate (V1.4j weekly foi rejeitada); exit: a6 = SMC BOS dinâmico vs L1 = +3R fixo; SL: ambos estruturais ATR-buffered. **L1 NÃO cobre reversão** → a6 é **complementar, não redundante**. Único e potencialmente útil. Mas o espaço reversal/bottom já é ocupado pelo Caminho B (mais maduro/clean).

**9-12.** Riscos: SLIM, mapping bubbles/NAS desatualizado, SMC BOS exit sem SHIFT1, nunca lookahead-audited. Aprendizado: A6 (burst suspect + NAS rescue) e RWS são filtros cirúrgicos de losers preservando monumentais. **Veredito: `KEEP_REFERENCE`** (predecessor; o vivo é a6_a7). Próxima ação: nenhuma isolada — usar como base do a6_a7.

---

## 5. Deep dive — Caminho A reversal a6_a7 (V1.4g-RWS-A6-A7)

**1. Identidade.** V1.4g-RWS-A6-A7. **REVERSAL_LONG** 4H. Universo = a6 + camada A7. Status: **OFICIAL ATUAL da linhagem reversal V1 em memory**, **não migrada** ao novo core, **não lookahead-audited**, métricas SLIM.

**2. Hipótese.** a6 + filtrar topos: rejeitar quando há **cluster de RSI bear divergences** (exaustão sistemática que precede topos macro). Tese: ≥2 bear divs em 20 barras 4H = exaustão.

**3. Construção.** Sobre a6, A7 derivada de observação visual do Cris nos prints + validação empírica (losers têm 3.6× mais bear divs em janela 10-20). Adotada 2026-06-03 mesmo dia que a6.

**4. Gates reais.** Todos os de a6 **+ A7:** `REJEITAR se count(rsi_div_bearish_event in last 20 4H bars) ≥ 2`. Campo: rsi_div_bearish (4H, derivado de RSI — causal se computado só de barras fechadas). SHIFT1: não-aplicável (feature 4H intrínseca), **mas precisa confirmar que rsi_div_bearish_event não repinta**. Status A7: **REUSABLE** (causal-plausível), pendente confirmação de cálculo.

**5. Indicadores.** = a6 + RSI bear divergence detector (novo). Papel: filtro anti-topo. Mapping não dependente de bubbles → menor risco.

**6. Estudos/métricas.** n=177, WR 67.2% (+1.8pp vs a6), +142.2R (+5R), streak 4, DD 4.4R, **WF 3/3** (W1 65.7%/W2 65.5%/W3 70.9%), 15/15 ≥5R + 4/4 ≥10R preservados, ~16 trades/ano. A7 corta **5 trades, TODOS losers** (cirúrgico). **Natureza:** in-sample + **SLIM**. **NÃO é validação.** Dataset: `candidates/.../v14g_rws_a6_a7_2016_2026.jsonl` (177 — persistido no repo ✓).

**7. Trades relevantes.** 5 cortados por A7 (100% losers: 2017-01-18, 2017-03-28, 2022-08-10, 2023-07-19, 2025-01-13, todos com n_bear_div_20≥2). Monumentais preservados 4/4.

**8. Comparação c/ L1.** Igual a a6 — reversal ⟂ continuation L1. Complementar. **Diferença operacional vs L1:** a6_a7 não tem scanner=runtime, não tem chart-management, não tem NAS SHIFT1 causal via per-bar tool, está em SLIM. A L1 está muito mais avançada em readiness; a6_a7 está em estado de pesquisa.

**9. Riscos.** **SLIM** (todas as métricas); **nunca lookahead-audited** (a linhagem reversal V1 NÃO estava na lista do audit 2026-06-06, que pegou A1'/A1 BALANCE/B v1.5 — risco residual de que features SMC/bubble/NAS tenham vazamento não detectado); **SMC BOS exit repinta**; mapping bubbles/NAS pode estar desatualizado (BUY=plot_0/2/4, SELL=plot_6/8/10 — confirmar no dataset). **Sobreposição com Caminho B** (ambos reversal/bottom 4H LONG) — risco de redundância/competição de slot.

**10. Aprendizados.** A7 (anti RSI-bear-div cluster) é um filtro de exaustão **reaproveitável e potencialmente aplicável à L1** (a L1 já tem RSI exhaustion gate `rsi_vs_ma≤−9.35`, mas A7 é um sinal *temporal/cluster* diferente — vale comparar). Filtro derivado de print visual + validado empiricamente = bom padrão.

**11. Veredito: `REVALIDATION_CANDIDATE`** + `NEEDS_RAW_BACKTEST` + `NEEDS_LOOKAHEAD_AUDIT` + `NEEDS_GATE_MANIFEST`. É o candidato reversal mais maduro fora do Caminho B, mas **prioridade abaixo do Caminho B**.

**12. Próxima ação.** Não reabrir agora. Quando o Caminho B fechar, avaliar a6_a7 como **segunda lógica reversal** — exige re-derivação RAW + lookahead audit (ORIG vs SHIFT1) + gate manifest + confirmar exit SMC causal. Visual review já parcialmente feito (prints).

---

## 6. Deep dive — A1 BALANCE (Caminho A v3) — 🔴 INVALIDADA

**1. Identidade.** Caminho A v3 A1 BALANCE. Reversal/natural-bull **ancorada em winners do Caminho B v1.5**. 4H LONG. Universo: bar CB amplo (`close>max(high[-5:])`, `range/ATR≥0.8`, `body_pct≥0.4`) **ancorado** em winner-B nos últimos 30 bars. Status: **INVALIDADA 2026-06-06**.

**2. Hipótese.** Long de continuação bull "auto-regulada por regime" via ancoragem em winners do Caminho B (B opera em fundo → A opera na retomada). Tese de ortogonalidade A+B.

**3. Construção.** Promovida OFICIAL 2026-06-05 (WR 74%, +122.6R, escopo 2020-2024). **Auditada e refutada 2026-06-06.**

**4. Gates reais + o bug.** Trigger CB + **anchor `bsw∈(0,30]`** (winner-B nos últimos 30 bars) + `bubble_buy_5≥1` (mapping **SUPERSEDED**). **🔴 LOOK-AHEAD ESTRUTURAL:** o anchor usa o **timestamp do TRIGGER** do trade B — mas saber que aquele trigger foi *winner* só existe **após o exit (50-200 bars depois)**. Cada entry A1 consultava **outcome futuro**. Stop −1.5ATR, target +15R, sem BE, time 72.

**5. Indicadores.** CB body/range, ATR, bubbles (mapping superseded), **anchor em outcome de B (a fonte do vazamento)**. Nenhum reaproveitável sob a forma atual.

**6. Métricas.** ORIG 68%/+122.6R/streak2 → **POST+SHIFT1 (clean) 18%/+12R/streak9/DD−9R**. Δ −110.6R (−90%). **90% do edge era artefato.** REFUTADO.

**7. Trades.** Os winners reportados eram em grande parte os que o anchor "sabia" terem dado certo no futuro. Sem valor causal.

**8. Comparação c/ L1.** Não comparável como edge — refutada. A L1 não usa anchor em outcome (gates causais close-only). Lição reforça por que a L1 é construída close-only-causal.

**9. Riscos/contaminação.** Look-ahead em **outcome** (classe distinta do A1'); mapping bubbles antigo; promoção 2026-06-05 sobre dados contaminados.

**10. Aprendizado.** **Ancorar em outcome de outra estratégia = look-ahead** mesmo quando o regime classifier é clean (SHIFT1 sozinho não corrigiu). Hooks `pre_approval_guard.py` + `post_backtest_devils_advocate.py` instalados para impedir recorrência.

**11. Veredito: `REJECTED_DO_NOT_REOPEN`** (+ `KEEP_REFERENCE` como caso-escola de look-ahead em outcome).

**12. Próxima ação.** Não tocar. Não reabrir salvo hipótese **nova** sem anchor-em-outcome.

---

## 7. Deep dive — A1' SUPERTREND / L5 (Caminho A v3) — 🔴 INVALIDADA

**1. Identidade.** Caminho A v3 A1' SUPERTREND v1 = **L5** (camada "supertrend" do framework "5 layers + 8 padrões"). Trend-following para regime **supertrend-ativo** (11.4% do histórico). 4H LONG. Status: **INVALIDADA 2026-06-06**.

**2. Hipótese.** Operar long em supertrend bull massivo (regime raro mas muito lucrativo), com entrada não-climática (sem absorção compradora excessiva).

**3. Construção.** v1 (inviável)/v2 (sem edge)/v3 (overfit)/v4 (WR baixo) → "v1 OFICIAL" 2026-06-05 (88% WR, +75R). **Refutada 2026-06-06.**

**4. Gates reais + o bug.** Regime supertrend-ativo (weekly_gain_12wk≥8% + slope_20_pct_1D≥0.15 + gain_30d≥4%) + bar verde + dist_MA20≤1.5ATR + bb_sell_5≤2 (mapping **superseded**) + dedup≥3. Filtro qualidade: Branch1 (dist_MA50≥0.3ATR + slope_1D≤0.40 + bb_buy_5≤5) OR Branch2 (body≥0.5 + lwr≥0.2 + bb_buy_5≤5). **🔴 LOOK-AHEAD:** `is_supertrend(ds)` usa **close diário / slope / weekly do MESMO dia `ds`** — info só disponível ao fechamento daily (~22:00 UTC), consultada em bars 4H das 04/08/12/16 UTC. Stop −1.5ATR, target +3R, sem BE, time 24.

**5. Indicadores.** Regime daily/weekly (a fonte do vazamento), MA20/MA50 4H, bubbles (mapping superseded), body/lower-wick, ATR. **A definição de regime supertrend exige SHIFT1 (D-1) para ser causal.**

**6. Métricas.** ORIG 88%/+75R/DD−1R → **SHIFT1 (limpo) 46%/+20R/DD−11R**. 19 trades "ONLY ORIG" (winners) eram artefato; 13 "ONLY SHIFT1" (losers) seriam executados em produção. REFUTADO na forma promovida.

**7. Trades.** Winners infláveis pelo look-ahead de regime. Sem valor causal na forma v1.

**8. Comparação c/ L1.** Conceito diferente (trend-following em supertrend vs pullback-continuation). A L1 já é close-only-causal com regime_l1_v4 (D-1 SHIFT1). L5 só faria sentido **reconstruída do zero com regime SHIFT1**.

**9. Riscos.** Look-ahead em **regime daily** (classe do A1'); mapping bubbles antigo; robustness ±20% e "regime gate redundante" de 2026-06-05 = **inválidos** (sobre dados contaminados).

**10. Aprendizado.** Features daily/weekly consultadas em bar 4H **exigem SHIFT1** (D-1) — convenção canônica do audit. Supertrend é regime real e raro; uma L5 futura precisa de classifier SHIFT1 desde o início.

**11. Veredito: `REJECTED_DO_NOT_REOPEN`** (na forma v1) + `KEEP_REFERENCE` (caso-escola). Reabertura só como **L5 nova com regime SHIFT1-clean**, do zero, pré-registrada.

**12. Próxima ação.** Não tocar. Backlog distante (Cris previu supertrend voltar ~2027-2028).

---

## 8. Deep dive — XAUUSD_4H_BREAKOUT_CONTINUATION

**1. Identidade.** XAUUSD_4H_BREAKOUT_CONTINUATION. Arquétipo **DECISIVE_BREAKOUT_CONTINUATION** — **breakout decisivo, NÃO pullback-continuation** (sub-arquétipo distinto da L1). 4H LONG. `family_origin: B`. Universo: close>swing_high(10) + regime gate. Status catalog: `validation_status=ACTIVE_CANDIDATE` / `deployment=LIVE_DORMANT` — **rótulo enganoso** (não deployado; recheck legacy dormant desde 2026-05-24, indicator signals bypassam recheck desde 2026-05-17). Supersede `XAUUSD_4H_LONG_REJECTION_SWING`.

**2. Hipótese.** "XAU paga bem em continuação 4H quando regime é trending bull com volatilidade expandindo." Breakout da máxima de 10 barras com corpo decisivo + RSI alinhado, filtrado por 5 gates de regime. Resolve o "quando não operar" (fora de bull/ADX/ATR favoráveis, não dispara).

**3. Construção.** Substituiu REJECTION_SWING em 2026-05-12. Backtest CSV legacy (n=234, +64.57R, PF1.64). Revalidação canônica v1 (2026-05-29) sobre slim: n=115, +25.3R, PF1.48. Pesquisa D1a (2026-06-01): filtro macro 1D. Visual review de 25 D1a-rejects. **Sem promoção.**

**4. Gates reais.**

| Gate | Condição | Campo | SHIFT1 | Lookahead | Status |
|---|---|---|---|---|---|
| Breakout | `close>swing_high(10)[1]` | OHLC | causal (usa [1]) | nenhum | KEEP |
| Bull candle | `close>open` | OHLC | causal | nenhum | KEEP |
| Body | `body_pct≥0.5` | OHLC | causal | nenhum | KEEP |
| RSI mom | `RSI(14)>RSI-MA` | RSI | causal | nenhum | KEEP |
| ADX | `ADX(14)≥20` | ADX | causal | nenhum | KEEP |
| EMA200 | `close>EMA200` | EMA | causal | nenhum | KEEP |
| Golden cross | `EMA50>EMA200` | EMA | causal | nenhum | KEEP |
| EMA50 slope | `EMA50_now>EMA50_5ago` | EMA | causal | nenhum | KEEP |
| ATR expand | `ATR14>SMA(ATR14,20)` | ATR | causal | nenhum | KEEP |
| **D1a (research)** | `close_1D>EMA200_1D AND EMA50_1D>EMA200_1D` no último **1D fechado (no-lookahead)** | EMA 1D | **SHIFT1 ✓ (explicit no-lookahead)** | nenhum | REUSABLE |
| Stop | `low_signal−0.5·ATR14`; abort se R>5ATR | OHLC | causal | nenhum | KEEP |
| Exit | target +4R; BE@+1R; time 24 | — | causal | nenhum | KEEP |

Notável: os gates são **estruturalmente causais e lookahead-free** (catalog marca `lookahead_free:true`; D1a é explicitamente no-lookahead). O problema **não** é look-ahead — é **fonte SLIM + in-sample + sem OOS**.

**5. Indicadores.** EMA50/200 (regime macro), ADX (força), ATR (vol), RSI (momentum), swing_high(10) (breakout), 1D EMA (D1a). Bubbles testados (H5) mas **bloqueados** porque o extractor zera `bubble_event_price`/`bubble_poc_*`. NAS/RSI-div (H1c/H2b) testados como diagnostic visual, não mecânico.

**6. Estudos/métricas.**

| Estudo | Range | Fonte | n | R | WR | PF | OOS? |
|---|---|---|---|---|---|---|---|
| Legacy CSV | 2019-2026 | CSV agregado (sem trades) | 234 | +64.57R net | 28.6% | 1.64 | não (in-sample) |
| Revalidação v1 | 2016-2026 | **canonical SLIM** | 115 | +25.28R | 30.4% | 1.48 | não (in-sample) |
| + D1a | 2016-2026 | SLIM + 1D causal | 90 | +32.20R | 33.3% | 1.86 | não (WF interno) |

Exit reasons v1: 9 target / 52 stop / 25 stop_be / 29 time. **Natureza:** **SLIM, in-sample.** WF interno (3 janelas) e regime-segmentação **bem feitos**, mas **não é OOS** (o set que derivou D1a não o valida) e **não é RAW**. **NÃO é validação de edge.**

**7. Trades/casos.** D1a remove 25 trades (−6.93R net, só 1 target perdido). Visual review: ~20/25 rejeições corretas (topo/exaustão), ~5 falsos-positivos (+8.48R deixados na mesa, mas event-driven/não-replicáveis — decisão: não criar exceção). Regime residual negativo: chop_inflation_bear (2022, blow-off +3.18 daily-ATR acima EMA200; aceito como custo raro).

**8. Comparação c/ L1.** **Sub-arquétipo distinto:** breakout decisivo (chase da máxima) vs pullback-and-go calmo (L1 entra no respiro, este entra no rompimento). Regime: ambos exigem bull macro (L1 regime_l1_v4 D-1; este EMA200/golden-cross/ADX/ATR). Exit: este +4R/BE@1R/time24 vs L1 +3R. **L1 NÃO cobre breakout decisivo.** Complementar como possível **L2 breakout** — mas só com gate manifest novo, RAW e sem o canal recheck legacy.

**9. Riscos/contaminação.** Rótulo catalog `ACTIVE_CANDIDATE` **enganoso**; canal recheck/Telegram **legacy** (dormant, mas existe); **SLIM** como fonte de toda métrica; sem OOS; legacy CSV sem trade-level (reconciliação impossível). Bubbles bloqueadas por extractor zerando POC.

**10. Aprendizados.** **D1a (filtro macro 1D direção-only, causal/no-lookahead)** é um padrão limpo e reaproveitável (melhora R + estabilidade + simplicidade, preserva targets). Confirma que **regime macro 1D ajuda continuação 4H**. H1/H2/H5 como **diagnostic visual**, não filtro mecânico (degradam ou são cosméticos em PF). "Stop 0.5ATR é pequeno demais para blow-off" — lição de SL em regime parabólico.

**11. Veredito: `CONTAMINATED_LEGACY / KEEP_REFERENCE`** (a entrada catalog + canal recheck). O **filtro D1a + gates de regime** = `REVALIDATION_CANDIDATE / NEEDS_RAW_BACKTEST + NEEDS_OOS` (possível **L2 breakout** futura). Corrigir o rótulo do catalog é bloco futuro autorizado (não neste).

**12. Próxima ação.** Não reabrir agora. Não corrigir catalog neste bloco (read-only). Reavaliar como L2 breakout **depois** do Caminho B, exigindo RAW + OOS + gate manifest + desligar dependência do canal recheck legacy.

---

## 9. Comparação consolidada com a L1 EMA21 CONTINUATION refinada

L1 (config verificada): pullback-continuation, regime_l1_v4 BULL D-1, close>EMA21>SMA50 + slopes + BOS + OB zone touch + body≥0.35 + F5 vol≤1.0 + stack anti-extensão (ret5≤1.42%, ext_ema≤2.95ATR, zone_w≥0.6ATR, dist_zone≤1.81ATR) + NAS SHIFT1≥1.31 + RSI gate `rsi_vs_ma≤−9.35`; SL `max(zone_OB_low,swing6_low)−0.1ATR`; target +3R; scanner=runtime; study-values por timestamp; chart-management; Telegram candidate-only; broker inativo. Evidência: **in-sample / NOT_VALIDATED_OOS** (risco assumido).

| Eixo | a6/a6_a7 | A1 BALANCE | A1'/L5 | BREAKOUT | L1 (ref) |
|---|---|---|---|---|---|
| Hipótese | reversal/fundo | reversal anchored-B | trend supertrend | breakout decisivo | pullback-continuation |
| Regime | sem gate | anchor-B | supertrend (lookahead) | EMA200/ADX/ATR | regime_l1_v4 D-1 ✓ |
| NAS | rescue (mapping) | — | — | — | SHIFT1 causal ✓ |
| RSI | RWS + A7 div-cluster | — | — | RSI>MA | gate −9.35 ✓ |
| OB/zone | SMC supply/demand | — | MA20/50 | swing_high(10) | OB v11 + zone quality ✓ |
| Anti-extensão | NOT range_middle | — | dist_MA / slope cap | (sem) | stack v1 ✓ |
| SL | swing10−1ATR | −1.5ATR | −1.5ATR | low−0.5ATR | estrutural max(zona,swing6)−0.1ATR ✓ |
| Exit | SMC BOS (repinta) | +15R/time72 | +3R/time24 | +4R/BE@1R/time24 | +3R fixo |
| scanner=runtime | não | não | não | não | **sim ✓** |
| Live readiness | pesquisa (slim) | refutada | refutada | legacy/slim | operacional (parcial) ✓ |
| Evidência | in-sample/slim | INVALIDADA | INVALIDADA | in-sample/slim | in-sample (sem OOS) |
| Lookahead audit | ❌ pendente | ✅ falhou | ✅ falhou | causal (slim base) | causal ✓ |

**O que a L1 já cobre:** continuação calma em uptrend (pullback-and-go), regime D-1 causal, anti-extensão, RSI exhaustion, SL estrutural, target fixo, alinhamento scanner=runtime. **O que a L1 NÃO cobre:** reversão/fundo (a6_a7, Caminho B), breakout decisivo (BREAKOUT), trend supertrend (L5). **Único com valor independente vivo:** a6_a7 (reversal) e o filtro D1a/gates do BREAKOUT (breakout) — ambos **complementares**, não redundantes, mas **não OOS/RAW**. A1 BALANCE e A1'/L5 são **incompatíveis** (refutadas por look-ahead).

---

## 10. O que foi absorvido pela L1

- **Nada das famílias deste bloco foi absorvido diretamente** (são reversal/breakout/trend, ≠ continuation). A L1 absorveu a linhagem **continuation F4+F5** (deep dive anterior), não estas.
- **Conceitos transferíveis (não código):** RSI exhaustion (a L1 já tem `rsi_vs_ma≤−9.35`; A7 oferece variante temporal/cluster a comparar); anti-extensão (a L1 tem stack v1; BREAKOUT confirma que regime macro 1D/extensão importam — paralelo ao D1a); SL estrutural ATR-buffered (comum a todas).

---

## 11. O que ainda tem valor independente

1. **a6_a7 (reversal)** — candidato reversal mais maduro fora do Caminho B; ortogonal à L1. Valor real, **mas slim/in-sample/não-auditado** e **compete com o Caminho B** no mesmo slot reversal.
2. **D1a + gates de regime do BREAKOUT** — padrão de filtro macro 1D causal limpo; possível **L2 breakout** futura (sub-arquétipo distinto da L1).
3. **A7 (anti RSI-bear-div cluster)** — filtro de exaustão reaproveitável; comparar com o RSI gate da L1.

---

## 12. O que deve morrer / arquivar

- **A1 BALANCE** — `REJECTED_DO_NOT_REOPEN` (look-ahead em outcome). Arquivar como caso-escola.
- **A1' SUPERTREND / L5 (v1)** — `REJECTED_DO_NOT_REOPEN` (look-ahead em regime daily). Arquivar; L5 nova só do zero com SHIFT1.
- **Rótulo `ACTIVE_CANDIDATE` do BREAKOUT no catalog** — enganoso; **corrigir em bloco futuro autorizado** (não agora). O canal recheck legacy deve ser desligado de qualquer revival.
- **a6** (predecessor) — `KEEP_REFERENCE` (não "morrer"; é base do a6_a7).

Nenhum arquivo físico a mover/deletar neste bloco (read-only).

---

## 13. Riscos e contaminações (consolidado)

| Risco | Onde | Severidade |
|---|---|---|
| Look-ahead em **outcome** | A1 BALANCE | 🔴 fatal (refutada) |
| Look-ahead em **regime daily** | A1'/L5 | 🔴 fatal (refutada) |
| **SLIM** como fonte de métrica | a6, a6_a7, BREAKOUT | 🟠 invalida números até RAW |
| **Nunca lookahead-audited** | a6, a6_a7 | 🟠 risco residual não medido |
| **SMC BOS exit repinta** (sem SHIFT1 confirmado) | a6, a6_a7 | 🟠 possível inflação de exit |
| Mapping bubbles/NAS antigo | a6, a6_a7, A1, A1' | 🟠 BUY=plot_0/2/4, SELL=plot_6/8/10 (confirmar) |
| Rótulo catalog enganoso | BREAKOUT | 🟡 cosmético/operacional |
| Canal **recheck/Telegram legacy** | BREAKOUT | 🟡 dormant mas existe |
| Sem OOS (in-sample) | todas | 🟠 não prova edge |
| `regime_B_v3` como autoridade | (não usado por estas; vigiar) | 🔴 proibido live |
| `vol_entry_z` | (não usado por estas) | 🔴 proibido |

---

## 14. Priorização antes do Bottom Catcher

| Ordem | Item | Racional |
|---|---|---|
| **1 (P0)** | **Caminho B bottom-catcher — gate manifest** | candidato canônico reversal/bottom; já versionado; clean no lookahead audit (B v1.5 SHIFT1); ortogonal à L1; RAW-validatable. **Não deslocado por nenhuma das 5.** |
| 2 (P0-infra) | Completar base-rule live da L1 | runtime; desbloqueia candidatos operacionais reais; exige Pre-Change Discipline |
| 3 (P1) | **a6_a7** como 2ª lógica reversal | só **depois** do Caminho B; NEEDS_RAW + lookahead audit + gate manifest; sobreposição de slot a resolver |
| 4 (P2) | **D1a/BREAKOUT** como L2 breakout | sub-arquétipo distinto; NEEDS_RAW + OOS; desligar canal recheck |
| — | A1 BALANCE, A1'/L5 | DO_NOT_REOPEN (refutadas) |

---

## 15. Veredito final por família

| Família | Veredito | Próxima ação |
|---|---|---|
| **a6** | `KEEP_REFERENCE` | base do a6_a7; não tocar isolada |
| **a6_a7** | `REVALIDATION_CANDIDATE` + `NEEDS_RAW_BACKTEST` + `NEEDS_LOOKAHEAD_AUDIT` + `NEEDS_GATE_MANIFEST` | reavaliar **depois** do Caminho B |
| **A1 BALANCE** | `REJECTED_DO_NOT_REOPEN` / `KEEP_REFERENCE` (caso-escola) | não tocar; reabrir só com hipótese nova sem anchor-em-outcome |
| **A1' SUPERTREND / L5** | `REJECTED_DO_NOT_REOPEN` / `KEEP_REFERENCE` (caso-escola) | não tocar; L5 nova só do zero com regime SHIFT1 |
| **XAUUSD_4H_BREAKOUT_CONTINUATION** | `CONTAMINATED_LEGACY / KEEP_REFERENCE`; D1a = `REVALIDATION_CANDIDATE / NEEDS_RAW + NEEDS_OOS` | corrigir rótulo catalog (bloco futuro); reavaliar como L2 breakout depois do B |

---

## 16. Próximo bloco recomendado

**Caminho B bottom-catcher — preparar o gate manifest (read-only, sem backtest).** Extrair os predicados exatos do packet em memory (B v1.5/v1.6: convergência 4 agents + anti_demand + rsi≤30 + circuit breakers + Dead Hours + Sweet Spot + filtro composto v1.6 + V_stair) e mapeá-los para RAW + SHIFT1 + mapping bubble plot_id atual, **sem rodar backtest** — para o Cris revisar antes de qualquer execução. É o P0 já apontado no REEVALUATION_PLAN e não foi deslocado por nenhuma das 5 famílias deste bloco.

---

## 17. Apêndice — Devil's Advocate (checklist obrigatório)

| Pergunta DA | Resposta | PASS? |
|---|---|---|
| Alguma família classificada por **nome** sem gate real? | Não — gates extraídos de código/config/memory para todas (§4-8). | ✅ |
| Algum **in-sample** chamado de validação? | Não — todas as métricas marcadas in-sample/SLIM; "NÃO é validação" explícito. | ✅ |
| Algum **look-ahead** ficou escondido? | Não — A1 BALANCE (outcome) e A1'/L5 (regime daily) explicitados; a6/a6_a7 flaggadas como **nunca auditadas** (risco residual declarado). | ✅ |
| Algum uso de **regime_B_v3** tratado como live? | Não — não usado por estas; vigiado como proibido. | ✅ |
| Algum **vol_entry_z** voltou como hipótese válida? | Não. | ✅ |
| **A1'/L5** tratado com caveat de look-ahead? | Sim — REJECTED_DO_NOT_REOPEN, 88%→46% documentado. | ✅ |
| **BREAKOUT** teve rótulo catalog checado contra gates reais? | Sim — `ACTIVE_CANDIDATE` declarado enganoso; gates causais mas fonte SLIM/sem OOS. | ✅ |
| **a6/a6_a7** confundidas com **F4+F5**? | Não — F4+F5 é **continuation**; a6/a6_a7 é **REVERSAL** (linhagem V1 trigger union), distinta também de A1/BALANCE (anchored-B). | ✅ |
| **L1** descrita com config refinada correta? | Sim — verificada contra scanner.py (§9). | ✅ |
| **Bottom Catcher** analisado além de contraste? | Não — só contraste (§9/§14/§16). | ✅ |
| Alguma **produção** tocada? | Não — read-only; só este relatório criado. | ✅ |

**DA verdict: PASS.**

---

*Documento read-only. Nenhum backtest rodado, nenhum scanner executado, nenhum código/catalog/strategy_rules/runtime/scheduler/RAW/event-store/broker tocado, nenhum Telegram, nenhum MCP/chart. Métricas citadas são in-sample/SLIM/reconstrução conforme as fontes do §2.*
