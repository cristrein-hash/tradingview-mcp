# L2/BPT Trend-Exit — Execution/Risk Layer · Pre-Registration

**Cris 2026-07-08.** Bloco `L2_BPT_TREND_EXIT_EXECUTION_RISK_LAYER`. Modo: research-only / risk-layer / prereg-first / RAW-first. **Não produção, não Telegram/runtime/broker/chart, não RAW/Supabase write, não SHORT, não mudar status para production, não esconder caveats, não vender sizing como edge.**

## 1. Strategy scope
- **L2/BPT trend-exit / regime-flip** = `USER_APPROVED_OFFICIAL_NOT_PRODUCTION`. Produção só com autorização explícita do Cris. Este bloco **analisa/define** a camada exec/risco; não liga produção.

## 2. Baseline a reproduzir (fail-loud se não bater)
- **SELECT-17:** let-run120 **+36.2R** · hold500 **+90.3R** · trend-exit/regime-flip **+105.3R** (maxDD −4.1R, streak 3).
- **FULL-245:** let-run120 **+52.5R** · hold500 **+257.6R** · trend-exit/regime-flip **~+385.7R a +399.2R** (maxDD ~−72, streak 22).
- **#6** mecânico **+1.15R**. Caveat: ~78% do ganho nos 17 = horizonte/exposição.

## 3. Source mapping
- RAW 4H: `my-strategy/research/revalidation/raw_4h_ohlc.jsonl` (entry=C[bar_idx], alinhado).
- Entry/risk/SL: `.../XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv` (SL_CONTEXT).
- Regime detector: `phase48_bear_deep_zone.Q.segs` (phase10; DA anterior confirmou FSM online causal, não look-ahead).
- Scripts committed usados: `l2_bpt_trailing_exit_test.py` (regime-flip), `l2_bpt_17_reproduce.py`. **Zero SLIM/proxy** (RAW OHLC + régua derivada de RAW).

## 4. Risk questions (a responder)
- Qual DD realista? (17: −4.1R; full: −72R — qual é a estratégia real?)
- Qual streak? (17: 3; full: 22.)
- Quanto do ganho vem de exposição/horizonte? (~78%.)
- Quais trades criam DD/streak hostil? (full-base; os STOP em clusters.)
- Quais stops largos 2025 geram gap risk? (#13 97pt, #14 82pt, #16 173pt, #17 124pt.)
- Que sizing mantém risco operável? (fixed-fractional R; efeito no $-exposição.)
- Que cap de exposição reduz risco sem matar edge? (max hold, max concorrentes.)
- O que muda para produção? (gap-model, exposição, frequência-vs-DD.)

## 5. Candidate risk layers (pré-registados, sem otimização pós-hoc)
1. fixed-fractional sizing (R-normalizado; nota $-exposição, não muda R).
2. risk cap per trade (skip/reduz se stop-width > X pt).
3. max hold cap (sair a X barras em vez de 500: testar 240/360).
4. max adverse excursion cap (sair se open-DD > X·R).
5. max calendar exposure (max dias em trade).
6. regime-trail com hard cap (regime-flip + cap mais curto).
7. gap buffer (losers dos stops largos a −1.5/−2R = tail model).
8. stop-width cap (skip trades com stop > X pt/ATR).
9. partial de-risk após +X R (50%@+2R + trail resto).
10. prop/funded DD guard (halt novas entradas após DD < −X).
11. pause após streak (halt após N losers seguidos).
12. review-only para stop-width extremo (flag, não auto).

## 6. Metrics (por variante · SELECT-17 e FULL-base separados)
total R · net-after-cost · maxDD · worst streak · ret/DD · max hold bars · avg hold bars · exposure-days · worst trade · gap-risk proxy · #trades impacted · runners lost · **#6 outcome**.

## 7. Acceptance (classificar no report)
`EXECUTION_LAYER_READY_FOR_USER_REVIEW` · `RISK_CONTROL_ONLY` · `PRODUCTION_BLOCKED_BY_DD` · `PRODUCTION_BLOCKED_BY_GAP_RISK` · `NO_SAFE_EXECUTION_LAYER_FOUND`.

## 8. Forbidden interpretations
Não chamar produção · não aprovar runtime · não esconder full-base DD/streak · não tratar hold longo como inteligência pura de regime · não usar R capped/cosmético como árbitro único · não rebaixar a estratégia oficial sem decisão do Cris.
