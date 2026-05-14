# Fase 1 — Validação manual com Leonardo (rename CANDIDATO_FORTE → CONFIRMED_ENTRY)

Data: 2026-05-13 | Total D2R: 155 | Trades selecionados: 22

## Objetivo

Validar visualmente se a hipótese estatística bate com o chart real:

- **Hipótese A:** os CANDIDATO_FORTE losers eram majoritariamente zone_touch sem confirmação fechada (não deveriam ter sido promovidos).
- **Hipótese B:** os CANDIDATO_FORTE winners tinham candle fechado de confirmação (reentry, breakout_retest, line_break).
- **Hipótese C:** alguns OBSERVACAO que tinham entry_model=confirmation_close ganharam apesar da classificação — deveriam ter sido CONFIRMED_ENTRY.

## O que olhar nos charts

Para cada trade, abrir o ativo+TF no chart, navegar ao timestamp UTC do alerta e verificar:

1. **A zona/linha desenhada existia visualmente?** (a estrutura era clara, não overfit?)
2. **Houve candle fechado de rejeição / reclaim / BOS antes da entrada?** (gatilho objetivo?)
3. **O stop estava em posição estrutural ou em armadilha óbvia?** (logo abaixo do sweep, etc.)

---

## CF LOSERS — 11 trades

Hipótese: maioria zone_touch sem confirmação fechada. Se confirmar, deveriam virar **SETUP_ZONE_WATCH** (downgrade).

### CF LOSER #1 — 2026-05-04 11:00 UTC

- **Ativo / TF / Direção:** XAUUSD 30M long
- **Drawing:** `AUTO_CLAUDE_DYNAMIC_XAUUSD_30M_DEMAND_BB_20260502_1230`
- **Entry model:** `reentry`
- **Plano:** ENTRY 4566.19 / SL 4520.0 / TP1 4612.19 (R:R 1.0) / TP2 4658.0 (R:R 1.99)
- **Outcome:** -1.0R | MFE +0.37R | MAE -1.43R | setup_valid_retro=False | candidate_strong_retro=True
- **O que aconteceu:** Tinha zona dinâmica clara, direção definida (long), stop técnico abaixo do sweep low (4520) e R:R provisório ~2:1 com alvo 4658. Operável em termos estruturais, mas a regra de RSI extremo (RSI 39.37 não estava em sobrevenda nem recém saindo de sobrevenda profunda) limita a classificação máxima a SET
- **Bloqueio/eval:** O bloqueio principal apontado ('stop estruturalmente largo, ausência de bubbles e NAS100 fresco enfraquecem') foi profético. O stop em 4520 (46 pts) foi atingido ~3 horas depois do alerta na vela das 14:00 UTC (low 4514.61), e o preço continuou para 4500.57. O sweep+reentry sem cluster bubbles, sem 

### CF LOSER #2 — 2026-05-05 06:45 UTC

- **Ativo / TF / Direção:** US500 15M short
- **Drawing:** `AUTO_CLAUDE_US500_4H_LTA_MASTER`
- **Entry model:** `line_break`
- **Plano:** ENTRY 7220.0 / SL 7240.0 / TP1 7177.0 (R:R 2.15) / TP2 7140.0 (R:R 4.0)
- **Outcome:** -1.0R | MFE -0.11R | MAE -1.01R | setup_valid_retro=False | candidate_strong_retro=False
- **O que aconteceu:** Classificado como SETUP_CANDIDATO_FORTE provisório, mas o gatilho faltante ('fechamento 15M abaixo da LTA com retest+rejeição') nunca confirmou. Preço NUNCA fez novo low abaixo do entry — lowest pós-alerta foi 7222.1 (apenas 2pt abaixo). Stop 7240 batido em ~3.5h, depois rally para 7350+. Falso romp
- **Bloqueio/eval:** RSI 15M não extremo (59.67) + ausência de bubbles + ausência de fechamento confirmado abaixo da LTA — todos esses bloqueios mencionados pela análise foram validados pelo movimento subsequente. SETUP_CANDIDATO_FORTE foi classificação otimista demais; o cluster NAS100 SHORT 7219-7240 atuou como liquid

### CF LOSER #3 — 2026-05-06 04:00 UTC

- **Ativo / TF / Direção:** XPTUSD 15M short
- **Drawing:** `AUTO_CLAUDE_DYNAMIC_XPTUSD_15M_SUPPLY_BB_20260502_2045`
- **Entry model:** `zone_touch`
- **Plano:** ENTRY 2001.0 / SL 2005.0 / TP1 1988.53 (R:R 3.12) / TP2 1981.2 (R:R 4.95)
- **Outcome:** -1.0R | MFE +0.29R | MAE +1.43R | setup_valid_retro=False | candidate_strong_retro=True
- **O que aconteceu:** Classificação CANDIDATO_FORTE explicitamente exigia 'aguardar candle de rejeição fechado + RSI cruzando 70 + CHoCH 15M bearish' antes da entrada. Confirmação nunca veio: na barra seguinte preço rompeu HTF P3 2003.02 e disparou para 2008.80, depois 2013.43 (BOS bullish), continuando até 2099+.
- **Bloqueio/eval:** Bloqueio totalmente confirmado. Stop 2005 atingido na barra seguinte (H=2006.71, +1.43R adverso em 15min). RSI 69.26 esticado mas estrutura ainda bullish e ausência de rejeição = falta de gatilho. Política de exigir confirmação evitou perda imediata de 1R + provável invalidação maior se o trade foss

### CF LOSER #4 — 2026-05-06 08:00 UTC

- **Ativo / TF / Direção:** USOUSD 30M long
- **Drawing:** `AUTO_CLAUDE_USOUSD_30M_DEMAND_ZONE_INTRADAY`
- **Entry model:** `zone_touch`
- **Plano:** ENTRY 98.79 / SL 98.2 / TP1 100.88 (R:R 3.54) / TP2 101.2 (R:R 4.08)
- **Outcome:** -1.0R | MFE +1.91R | MAE -1.0R | setup_valid_retro=False | candidate_strong_retro=True
- **O que aconteceu:** Setup had clear technical stop below P3 98.47, planned R:R 3.5+, and SETUP_CANDIDATO_FORTE confluences. However, trade stopped out hard on the very next 30M bar (low 96.01, then continued to 89.47) — the 'velocidade da queda' blocker was prophetic.
- **Bloqueio/eval:** Main blocker (velocidade da queda + falta CHoCH/BOS LTF + volume bearish) was completely correct. Initial 30M reaction touched ~+1.94R then collapsed straight through stop. Wait-for-confirmation rule would not have saved the trade either (next bar open 99.87 → 96.01 same bar).

### CF LOSER #5 — 2026-05-06 10:30 UTC

- **Ativo / TF / Direção:** XAUUSD 30M short
- **Drawing:** `AUTO_CLAUDE_XAUUSD_30M_SUPPLY_ZONE_INTRADAY`
- **Entry model:** `zone_touch`
- **Plano:** ENTRY 4709.0 / SL 4720.0 / TP1 4670.0 (R:R 3.55) / TP2 None (R:R None)
- **Outcome:** -1.0R | MFE +0.0R | MAE -1.25R | setup_valid_retro=False | candidate_strong_retro=True
- **O que aconteceu:** Zone, direction, technical stop and R:R >= 2:1 all defined. Tradeable setup — but stop hit immediately as price ran from 4704 to 4722.80 in the candle right after the alert, breaking the supply at 4711.94 HTF. Target 4670 was reached ~1.5h later (low 4660.61), but only post-stop, so retrospectively 
- **Bloqueio/eval:** The eval correctly flagged 'gatilho de reversão ainda não apareceu — preço pode romper 4711.94'. That blocker materialized exactly: the very next 30M candle broke 4711.94 and tagged 4722.80, invalidating the SHORT thesis before any rejection candle formed. Eval was right to wait, but SETUP_CANDIDATO

### CF LOSER #6 — 2026-05-06 11:30 UTC

- **Ativo / TF / Direção:** XAUUSD 30M short
- **Drawing:** `AUTO_CLAUDE_XAUUSD_30M_SUPPLY_ZONE_INTRADAY`
- **Entry model:** `confirmation_close`
- **Plano:** ENTRY 4692.0 / SL 4722.8 / TP1 4619.0 (R:R 2.37) / TP2 4557.0 (R:R 4.38)
- **Outcome:** -1.0R | MFE +1.02R | MAE -1.0R | setup_valid_retro=False | candidate_strong_retro=True
- **O que aconteceu:** Estrutura operável: zona supply 30M clara (4705-4741), stop técnico definido acima do swing high 4722.8, alvos plausíveis em P3 mid (4619) e P3 inferior (4557), R:R T1 ~2.37 (passa o mínimo 2:1). Trigger de confirmação (close abaixo de 4694) materializou-se no candle das 11:30 (close 4692.06). Setup
- **Bloqueio/eval:** Bloqueio principal apontado (sem candle fechado de rejeição/CHoCH-BOS local) era válido no momento do alerta. Quando o candle de 11:30 fechou em 4692 com perda de 4694, o gatilho confirmou e a entrada teria ocorrido. Apesar de ter atingido brevemente ~1R favorável (low 4660.61 no candle das 12:00 UT

### CF LOSER #7 — 2026-05-06 13:00 UTC

- **Ativo / TF / Direção:** XPTUSD 60M short
- **Drawing:** `AUTO_CLAUDE_XPTUSD_1H_SUPPLY_ZONE_INTRADAY`
- **Entry model:** `zone_touch`
- **Plano:** ENTRY 2022.0 / SL 2030.0 / TP1 1988.53 (R:R 4.18) / TP2 None (R:R None)
- **Outcome:** -1.0R | MFE +2.49R | MAE -1.0R | setup_valid_retro=False | candidate_strong_retro=False
- **O que aconteceu:** Entry 2022/stop 2030/alvo 1988.53 acionado na barra 13:00 (high 2026.69). Low 2002.11 às 14:00 (MFE +2.49R) ofereceu janela de parcial mas nunca chegou perto do alvo 1988.53. Barra 15:00 disparou para high 2047.40, atingindo o stop. Sem gestão ativa (parcial em 2R/breakeven), trade resultou em -1R.
- **Bloqueio/eval:** Bloqueio 'RSI não em sobrecompra, sem NAS100 SHORT/bubbles, perda de 2019 não confirmada' foi confirmado pelos fatos: a rejeição inicial não se sustentou, preço fez sweep do low 2005 e reverteu explosivamente +30 pontos acima do stop em ~2h. As confirmações que faltavam eram exatamente o que segurou

### CF LOSER #8 — 2026-05-07 07:00 UTC

- **Ativo / TF / Direção:** XAUUSD 60M short
- **Drawing:** `AUTO_CLAUDE_XAUUSD_1H_SUPPLY_ZONE_INTRADAY`
- **Entry model:** `zone_touch`
- **Plano:** ENTRY 4739.0 / SL 4751.0 / TP1 4711.0 (R:R 2.33) / TP2 4699.0 (R:R 3.33)
- **Outcome:** -1.0R | MFE +0.61R | MAE +1.21R | setup_valid_retro=False | candidate_strong_retro=False
- **O que aconteceu:** R:R formal >=2 e stop tecnico claro acima do high da zona supply 1H. Era tradeable como SETUP_CANDIDATO_FORTE com revisao humana, mas stop ultra-colado (4751) sentado no wick high 4749.89 sem buffer.
- **Bloqueio/eval:** Claude apontou corretamente que rejeicao 1H nao estava confirmada e tendencia D continuava forte. Bloqueio era valido — a barra seguinte (08:00) levou high a 4753.54, ainda dentro do contexto altista, e os retestes subsequentes nas 5-6 barras seguintes acabaram empurrando preco a 4763.48 antes de qu

### CF LOSER #9 — 2026-05-07 09:00 UTC

- **Ativo / TF / Direção:** XAUUSD 60M short
- **Drawing:** `AUTO_CLAUDE_XAUUSD_1H_SUPPLY_ZONE_INTRADAY`
- **Entry model:** `reentry`
- **Plano:** ENTRY 4731.0 / SL 4760.0 / TP1 4670.0 (R:R 2.1) / TP2 4665.0 (R:R 2.28)
- **Outcome:** -1.0R | MFE +0.31R | MAE +1.12R | setup_valid_retro=False | candidate_strong_retro=False
- **O que aconteceu:** Tinha stop tecnico claro (acima de 4753.54 swing high), R:R borderline ~2:1, direcao SHORT clara e 4 confluencias. Atendia criterios SETUP_CANDIDATO_FORTE para revisao humana — mas R:R apertado deixou pouca margem.
- **Bloqueio/eval:** Bloqueios listados (R:R apertado 1.7-2.0, RSI 1H em 63 nao overbought, Bubbles=0) eram validos. O preco refez o topo entre 12:00-14:00 UTC e 14:00 wick a 4763.48 tirou stop. Tese direcional estava correta — preco eventualmente desceu a 4647.91 em 2026-05-08 e 4500 range posterior — mas o timing intr

### CF LOSER #10 — 2026-05-07 13:45 UTC

- **Ativo / TF / Direção:** ETHUSD 30M long
- **Drawing:** `AUTO_CLAUDE_DYNAMIC_ETHUSD_30M_DEMAND_BB_NESTED_20260502_1545`
- **Entry model:** `zone_touch`
- **Plano:** ENTRY 2313.88 / SL 2296.54 / TP1 2331.22 (R:R 1.0) / TP2 2348.56 (R:R 2.0)
- **Outcome:** -1.0R | MFE +0.29R | MAE -1.58R | setup_valid_retro=False | candidate_strong_retro=False
- **O que aconteceu:** Setup atendia critérios formais de SETUP_CANDIDATO_FORTE: zona nested PO3 4H + cluster NAS100 LONG + sweep do PO3 boundary + R:R 2:1 + stop técnico claro. Por regra era tradeable como revisão humana. Retroativamente o stop em 2296.54 foi violado rapidamente (bar 1778162400 low 2286.56), antes de qua
- **Bloqueio/eval:** Blocker original (ausência de candle de rejeição fechado + RSI não em sobrevenda absoluta + sem bubbles) provou-se CRÍTICO e correto. A política experimental SETUP_CANDIDATO_FORTE deixou o setup elegível para Telegram apesar desses gatilhos faltantes, mas o stop foi atingido sem reação estrutural. C

### CF LOSER #11 — 2026-05-07 22:30 UTC

- **Ativo / TF / Direção:** XAUUSD 30M short
- **Drawing:** `AUTO_CLAUDE_DYNAMIC_XAUUSD_30M_SUPPLY_BB_20260502_1230`
- **Entry model:** `zone_touch`
- **Plano:** ENTRY 4693.0 / SL 4725.0 / TP1 4619.77 (R:R 2.29) / TP2 None (R:R None)
- **Outcome:** -1.0R | MFE +0.35R | MAE +1.0R | setup_valid_retro=False | candidate_strong_retro=True
- **O que aconteceu:** Classificação SETUP_CANDIDATO_FORTE SHORT com 5 confluências fortes declaradas (zona dinâmica supply 30M tocada, rejeição inicial mecha→close, NAS100 SHORT signals em 4717-4723, HTF P3 top 4693.22, price action esticado), R:R = 2.29 (>= 2:1), stop técnico claro acima de 4725. Atendia critérios mínim
- **Bloqueio/eval:** O blocker (RSI 30M = 39, não em sobrecompra nem recém saindo) foi corretamente identificado e justifica não promover para SETUP_VALIDO formal. Em hindsight, este foi exatamente o ponto fraco do setup: faltava momentum exhaustion. Price prosseguiu de 4693 até 4773.53 (MAE 2.52R) antes de finalmente i

---

## CF WINNERS — 5 trades

Hipótese: ganharam porque tinham candle fechado de confirmação (reentry, breakout_retest). Devem virar **SETUP_CONFIRMED_ENTRY** no esquema novo.

### CF WINNER #1 — 2026-05-04 16:15 UTC

- **Ativo / TF / Direção:** US500 15M long
- **Drawing:** `AUTO_CLAUDE_US500_4H_LTA_MASTER`
- **Entry model:** `reentry`
- **Plano:** ENTRY 7188.0 / SL 7177.0 / TP1 7221.8 (R:R 3.07) / TP2 None (R:R None)
- **Outcome:** +3.07R | MFE +18.4R | MAE +0.0R | setup_valid_retro=True | candidate_strong_retro=True
- **O que aconteceu:** Clear technical stop below sweep low 7177.5, planned R:R ~3:1, multiple strong confluences (RSI 27.61 deep oversold, P3 box low reclaim, LTA reentry, fresh NAS100 LONG, sweep+recovery). Confirmation candle close >7190 confirmed in the 16:15→17:00 gap (first visible bar opens 7193, closes 7202). Pric
- **Bloqueio/eval:** Stated blocker (waiting for close >7190 with bubbles) was technically prudent but quickly resolved — confirmation candle printed within ~45 minutes and stop was never threatened. Target 1 (7221.8 ≈ 3.07R) hit ~12h after the alert; price continued to 7390+ for an MFE of ~18.4R. Blocker was procedural

### CF WINNER #2 — 2026-05-06 05:00 UTC

- **Ativo / TF / Direção:** USDJPY 240M long
- **Drawing:** `AUTO_CLAUDE_DYNAMIC_USDJPY_4H_INVALIDATION_LINE`
- **Entry model:** `reentry`
- **Plano:** ENTRY 155.83 / SL 154.95 / TP1 157.94 (R:R 2.4) / TP2 None (R:R None)
- **Outcome:** +1.0R | MFE +1.32R | MAE -0.25R | setup_valid_retro=True | candidate_strong_retro=True
- **O que aconteceu:** Clear technical stop below 154.95 sweep wick, planned R:R 2.4, valid SETUP_CANDIDATO_FORTE confluences (sweep+reentry of 155.03 BB SMC + HTF P3 zone, RSI 4H extreme 30.23, dynamic invalidation line touch).
- **Bloqueio/eval:** HTF bearish context blocker was real (downtrend from 160.73→155.03). Trade reacted up to 156.995 reaching 1R, but did not power through to 157.94 target within 48h window — consistent with HTF resistance. Caution was warranted.

### CF WINNER #3 — 2026-05-06 12:00 UTC

- **Ativo / TF / Direção:** XAUUSD 30M short
- **Drawing:** `AUTO_CLAUDE_DYNAMIC_XAUUSD_30M_SUPPLY_BB_20260502_1230`
- **Entry model:** `reentry`
- **Plano:** ENTRY 4712.0 / SL 4725.0 / TP1 4670.0 (R:R 3.23) / TP2 4640.0 (R:R 5.54)
- **Outcome:** +3.23R | MFE +3.95R | MAE -1.0R | setup_valid_retro=True | candidate_strong_retro=True
- **O que aconteceu:** Plano de retest 4710-4715 com stop 4725 foi acionado na barra 12:30 (high 4715.5) e o low 4660.61 às 13:00 UTC ja entregou alvo 1 (4670) em ~1h, com MFE +3.95R antes de qualquer recuperação relevante. Stop só foi atingido ~19h depois quando target 1 já estava capturado.
- **Bloqueio/eval:** Bloqueio 'preço extended, aguardar retest' foi correto e operacionalmente útil — o retest ocorreu rapidamente (12:30 high 4715.5) e ofereceu R:R limpo. Sem o retest, entry a mercado em 4690 também teria batido +2R, mas com MFE menor em relação ao risco maior.

### CF WINNER #4 — 2026-05-07 01:00 UTC

- **Ativo / TF / Direção:** ETHUSD 240M short
- **Drawing:** `AUTO_CLAUDE_ETHUSD_4H_LTB_MASTER`
- **Entry model:** `breakout_retest`
- **Plano:** ENTRY 2346.0 / SL 2362.0 / TP1 2295.0 (R:R 3.19) / TP2 2216.0 (R:R 8.13)
- **Outcome:** +3.19R | MFE +5.85R | MAE +0.06R | setup_valid_retro=True | candidate_strong_retro=True
- **O que aconteceu:** Strict eval entry 2348-2356 was never touched — max retest high was 2346.88 (07:00 May 7). Using the LTB retest zone 2335-2356 with entry near the pullback high 2346 and stop 2362 (Claude's stated stop), risk 16 / reward 51 → R:R 3.19. Target 1 2295 was hit at low 2286.56 only 6 bars later. Target 2
- **Bloqueio/eval:** RSI 4H neutral and absence of Bubbles/NAS100 fresh were correctly identified as preventing full SETUP_VALIDO. The SETUP_CANDIDATO_FORTE classification was the right intermediate call: clear stop, multiple structural confluences (sweep + 4H bearish close + LTB + HTF resistance stack), R:R well above 

### CF WINNER #5 — 2026-05-07 15:00 UTC

- **Ativo / TF / Direção:** ETHUSD 15M long
- **Drawing:** `AUTO_CLAUDE_DYNAMIC_ETHUSD_15M_INVALIDATION_LINE_20260502_1545`
- **Entry model:** `reentry`
- **Plano:** ENTRY 2297.0 / SL 2285.0 / TP1 2316.0 (R:R 1.58) / TP2 2327.0 (R:R 2.5)
- **Outcome:** +2.5R | MFE +2.6R | MAE -0.63R | setup_valid_retro=True | candidate_strong_retro=True
- **O que aconteceu:** Setup tinha entrada de reentry pós-sweep clara acima de 2296.54, stop técnico abaixo de 2286.50 (low do sweep + CHoCH BB), e dois alvos com R:R viáveis. Após o alerta (close ~2297 no evento, equiv ~2314.69 no chart), preço rallyou ~+1.36% em ~7 horas sem retestar o stop. Drawdown máximo equivalente 
- **Bloqueio/eval:** Bloqueio 'sem fechamento 15M de confirmação acima de 2300' foi rigoroso demais — a confirmação chegou na vela imediatamente seguinte. Ausência de bubbles e de sinal NAS100 LONG fresco no nível não invalidou a tese; as 4 confluências (reentry D6, RSI saindo de oversold, sweep HTF PoT, CHoCH BB) suste

---

## OBS + confirmation_close WINNERS — 6 trades

Hipótese: o gatilho de confirmação JÁ está sendo capturado em alguns OBSERVACAO, mas eles não foram promovidos. Estes deveriam ter sido **SETUP_CONFIRMED_ENTRY**.

### OBS CC WINNER #1 — 2026-05-04 17:15 UTC

- **Ativo / TF / Direção:** US500 15M long
- **Drawing:** `AUTO_CLAUDE_US500_4H_LTA_MASTER`
- **Entry model:** `confirmation_close`
- **Plano:** ENTRY 7205.0 / SL 7176.0 / TP1 7240.0 (R:R 1.21) / TP2 7251.0 (R:R 1.59)
- **Outcome:** +1.59R | MFE +5.0R | MAE -0.16R | setup_valid_retro=False | candidate_strong_retro=False
- **O que aconteceu:** Planned R:R with structural stop below P3 low (7177) was 1.21 to T1 and 1.59 to T2 — below the 2:1 minimum. Even though the trade would have closed at the stated T2 (price reached 7251 within ~5h and continued to 7400+), the setup did not meet SETUP_VALIDO or CANDIDATO_FORTE criteria at the time of 
- **Bloqueio/eval:** Blocker (R:R < 2:1 with structural stop) was rule-correct. However, in this case the price action confirmed the LTA defense and ran 5R+ favorable without ever threatening the structural stop. A secondary, tighter intraday stop framework could have unlocked the trade.

### OBS CC WINNER #2 — 2026-05-04 18:00 UTC

- **Ativo / TF / Direção:** XAUUSD 240M long
- **Drawing:** `AUTO_CLAUDE_XAUUSD_4H_LTB_MASTER`
- **Entry model:** `confirmation_close`
- **Plano:** ENTRY 4525.0 / SL 4498.0 / TP1 4583.0 (R:R 2.15) / TP2 4619.0 (R:R 3.48)
- **Outcome:** +3.48R | MFE +8.88R | MAE -0.56R | setup_valid_retro=True | candidate_strong_retro=True
- **O que aconteceu:** The setup had three structural confluences (LTA 4H touch, lower border of POT3 box at 4521.44, dense NAS100 LONG cluster 4505-4525), a clear stop just below the 4500.57 low, and R:R of 2.15 to T1 and 3.48 to T2 — both meeting the 2:1 minimum. The stated trigger (4H close above 4525) fired at the nex
- **Bloqueio/eval:** D1 blocker was 'no rejection confirmed yet, RSI not extreme, no bubbles cluster'. While conservative, this missed a valid CANDIDATO_FORTE — the policy allows classification with 3+ strong confluences and R:R>=2:1 even without RSI extreme, bubbles, or fresh NAS100 in candle. The 4H LTA touch + POT3 l

### OBS CC WINNER #3 — 2026-05-05 14:00 UTC

- **Ativo / TF / Direção:** USOUSD 240M short
- **Drawing:** `AUTO_CLAUDE_USOUSD_1D_LTA_MASTER`
- **Entry model:** `confirmation_close`
- **Plano:** ENTRY 103.03 / SL 103.95 / TP1 100.8 (R:R 2.42) / TP2 None (R:R None)
- **Outcome:** +2.42R | MFE +3.27R | MAE +0.91R | setup_valid_retro=True | candidate_strong_retro=True
- **O que aconteceu:** Using the alert candle's rejection close (4H O=103.05, H=103.935, L=102.05, C=103.03) as the trigger gives a clear stop above 103.93 and target at next BB demand 100.80. Planned R:R 2.42:1 meets the rule. After rejection close, price hit T1 within 12h (low 100.025 on +2 bar).
- **Bloqueio/eval:** D1 cited 'no rejection confirmed' but the same alert bar closed as a clear shooting-star rejection (close 103.03 well below high 103.935). RSI 47 was the formal blocker but the structural rejection was textbook. Trade reached T1 cleanly with peak MFE 3.27R.

### OBS CC WINNER #4 — 2026-05-05 18:00 UTC

- **Ativo / TF / Direção:** XAUUSD 240M long
- **Drawing:** `AUTO_CLAUDE_XAUUSD_4H_LTB_MASTER`
- **Entry model:** `confirmation_close`
- **Plano:** ENTRY 4626.13 / SL 4540.0 / TP1 4798.39 (R:R 2.0) / TP2 4884.52 (R:R 3.0)
- **Outcome:** +1.71R | MFE +1.71R | MAE -0.01R | setup_valid_retro=False | candidate_strong_retro=True
- **O que aconteceu:** Long breakout trigger fired on the next 4H candle close: 4H closed at 4626.13 (strongly above 4586.69 with force), as the original plan required. Conservative confirmation_close entry at 4626.13 with stop below 4540 gives risk 86 points and a 3:1 plan target. Forward: lowest subsequent low was 4625.
- **Bloqueio/eval:** At signal time the direction was genuinely indefinida and the trigger had not yet fired — waiting was correct. The blocker resolved on the very next 4H close (breakout with force). Retroactively, the long side became a strong candidate immediately after this signal; on the post-close 4H, it could ha

### OBS CC WINNER #5 — 2026-05-07 12:00 UTC

- **Ativo / TF / Direção:** ETHUSD 60M short
- **Drawing:** `AUTO_CLAUDE_ETHUSD_1D_RECENT_HIGH`
- **Entry model:** `confirmation_close`
- **Plano:** ENTRY 2317.0 / SL 2335.92 / TP1 2298.08 (R:R 1.0) / TP2 2279.16 (R:R 2.0)
- **Outcome:** +2.0R | MFE +3.42R | MAE -0.0R | setup_valid_retro=False | candidate_strong_retro=False
- **O que aconteceu:** Planned R:R declarado pelo Claude foi 1.5:1 (curto de falso rompimento) — abaixo do mínimo 2:1 da política. Direção operacional estava ambígua no signal (alert era breakout long, lean bearish era leitura derivada). Retroativamente, com stop técnico 2335.92 e alvo estrutural 2279, o trade teria ating
- **Bloqueio/eval:** Blocker original (R:R inviável para long + RR curto insuficiente) foi parcialmente válido: o long realmente não funcionou (cluster 2330-2335 segurou e preço caiu). Já o short, se reformulado com alvo estrutural mais distante (sweep do swing low), teria sido tradeable a 2:1. Sugere que a leitura de R

### OBS CC WINNER #6 — 2026-05-07 16:00 UTC

- **Ativo / TF / Direção:** XAUUSD 60M short
- **Drawing:** `AUTO_CLAUDE_XAUUSD_1H_SUPPLY_ZONE_INTRADAY`
- **Entry model:** `confirmation_close`
- **Plano:** ENTRY 4729.36 / SL 4767.0 / TP1 4685.0 (R:R 1.18) / TP2 4660.0 (R:R 1.84)
- **Outcome:** +1.84R | MFE +2.42R | MAE +0.53R | setup_valid_retro=False | candidate_strong_retro=False
- **O que aconteceu:** Planned R:R to T1 (4685) was 1.18, below 2:1 minimum; T2 also failed at 1.84. Only T3 (4619.77) gave 2.91:1 but was structurally distant. Per strict rules the setup was not tradeable. Retrospectively the move reached 2.42R max before reversing, and stop only hit ~5 days later after T1+T2 already fil
- **Bloqueio/eval:** R:R blocker was correctly applied per the literal policy rule (item 7 of setup_candidato_forte_policy). The 1H rejection had 5+ structural confluences but the chosen primary target (T1=4685) sat too close to entry. Outcome shows the rejection was real — T2 filled cleanly and price reached 2.42R favo

---

## Decisão pós-validação

- Se **Hipóteses A+B+C confirmadas visualmente** (≥75% dos trades batem o padrão): seguir para Fase 2 (reclassificar os 155 D2R no esquema novo e medir win%/avg R por categoria).

- Se **padrão NÃO bate** (muitos CF losers tinham confirmação mas falharam, ou muitos winners eram zone_touch puro): voltar pra prancheta — não é o `entry_model` que discrimina; investigar outras features.

