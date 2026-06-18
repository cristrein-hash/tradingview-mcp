# XAU 4H L2/BPT — SL Estrutural por Contexto (demanda 4H)

**Status:** `RESEARCH · CAUSAL · REPAINT-AUDITED · EXPECTANCY-NEUTRAL · NOT_PROMOTED` · **Data:** 2026-06-18
Sessão dedicada de SL: ancorar o SL na zona de DEMANDA 4H defendida (causal) p/ ter SLs por contexto (curto quando defendido perto, largo quando é a base funda). Exit FIXO partial50@2R+6R. Classificação por TIPO DE SAÍDA. DA dedicado. Não promove estratégia.

---

## 1. Executive summary
O SL mecânico swing-origin (mediano 5.7ATR) era largo demais. O **SL ancorado em demanda 4H** resolve isso: SLs **por contexto, variados (0.5–11ATR, mediano 2.81)**, com **>4ATR caindo de 92→43** e máx 15→11 — SLs genuinamente curtos defendidos (E17 1.03ATR vira WIN_RUNNER +3.90, era scratch a 8.4ATR) E largos onde a base é funda. **Resolve a queixa do Cris (largura).** PORÉM, no bootstrap pareado vs mecânico (n=245), a expectância é **WASH** (delta_avgR/sumR/DD straddle zero, P~0.53) — apertar ajuda uns (E17) e stopa outros, **empata**. As melhorias agregadas de avgR/DD vêm mais do **no_trade (31 TOP_EXHAUSTION)** que do SL em si. **Repaint audit PASSOU** (boxes de demanda estáveis, ancoradas em candles passados, sem shift pós-entry). **tight_6bar tem sumR maior (+84 vs +74) mas DD/streak piores (25.5/12 vs 16.5/7)** → context-demand SL é a variante de **menor risco (prop-firm)**, não de maior retorno. E13 = sweep-loss irredutível.

## 2. Why mechanical SL failed
Swing-origin = pivô 5/5 mais recente abaixo da entrada, sem teto. Pega o **fundo da perna/crash** (E17 8.4ATR, E1 5.3ATR) → SL gigante na maioria, R-múltiplos comprimidos, muitos time-exits/scratch. Nunca foi a intenção (Cris).

## 3. RAW audit (`..._raw_audit.csv`)
Causal: OHLCV 4H, ATR14, pivots Williams (j≤i-5, só fallback), **demanda 4H as-of-bar (OB Detector, snapshots replay)**, dist_4h_demand_low_atr (distância, não flag — lição a6d8e3a), legpos/RSI (gate). **REPAINT-AUDITED:** boxes de demanda têm coords estáveis bar−3..+3 (E1/E13 pré-existem; E17 forma no entry-bar e não shifta depois = causal pra close-entry). Proibidos/excluídos: deep_confluence, vol×1D-bear, outcome_proxy, at_D1_demand binário, SLIM. Cobertura demanda 97%; 3% fallback swing-origin.

## 4. Tipos estruturais de contexto
TOP_EXHAUSTION_NO_LONG (legpos≥85 & RSI≥70) → no_trade · V_REVERSAL_DEMAND (demanda ≤2ATR) · NORMAL_DEMAND_BASE (demanda 2-5ATR) · LATE_WIDE_REVIEW (demanda >5ATR ou ausente → fallback swing + review).

## 5. SL candidates (`..._candidates.csv`)
retest_low, min10/20/30, recent_pivot, swing_origin, **demand_low** (a âncora escolhida). A demanda 4H = estrutura defendida que a entrada retestou → SL = demand_low − 0.1ATR, floor 0.3.

## 6. Policy definitions
**SL_CONTEXT (adotada p/ teste):** no_trade se TOP_EXHAUSTION; senão SL = nearest_4h_demand_low − 0.1ATR (tight se demanda perto, largo se funda); fallback swing-origin se demanda ausente/>5ATR (review). Sem teto 1.5, sem CAP4, sem outcome-future. Classificação por tipo de saída (target/partial/runner/stop/time).

## 7. Key cases
| caso | SL ctx | exit | R | mec |
|---|---|---|---|---|
| E17 | 1.03ATR | WIN_RUNNER | +3.90 | era 8.4ATR scratch ✓✓ |
| E21 | 2.90 | WIN_RUNNER | +3.90 | ✓ |
| E40 | 1.83 | WIN_held | +3.32 | ✓ |
| E27 | 2.29 | WIN_held | +2.83 | ✓ |
| E5 | 1.72 | WIN_BE | +0.90 | ✓ |
| E1 | 4.22 | scratch | +0.82 | preservado |
| E30 | 4.53 | scratch | +0.97 | preservado |
| E13 | 2.87 | STOP | −1.10 | demanda(1548) varrida por wick(1546) — irredutível |
| E23 | — | NO_TRADE | — | top ✓ |
| E15/E24/E34 | — | STOP_LOSS | −1.10 | não viram no_trade, mas perdem (corretos, não falsos-wins) |

Hard-stop: E1✓ E17✓✓ E23✓ resolvidos; **E13 NÃO** (sweep da própria demanda). Regra NÃO é overfit (demand-anchored causal). Não vendido como solução completa.

## 8. Full-base results (276 episódios, exit partial50)
| política | n | sumR | avgR | WIN/STOP/SCR | DD | streak | SLmed | >4ATR |
|---|---|---|---|---|---|---|---|---|
| **CONTEXT_DEMAND** | 245 | +73.8 | +0.301 | 81/116/48 | **16.5** | **7** | 2.81 | **43** |
| SWING_ORIGIN(mec) | 276 | +72.6 | +0.263 | 80/123/73 | 19.8 | 6 | 3.02 | 92 |
| TIGHT_6BAR | 276 | **+84.2** | +0.305 | 106/148/22 | 25.5 | 12 | 1.97 | 10 |
(CONTEXT: 31 no_trade por TOP_EXHAUSTION). Context-demand: menos scratch (48 vs 73), >4ATR halved, melhor DD/streak; mas tight_6bar maior sumR.

## 9. Bootstrap (`..._bootstrap.csv`, 5000, pareado CONTEXT vs SWING, n=245 comum)
- delta_avgR CI [−0.075, +0.003, +0.082] **P=0.53** (wash)
- delta_sumR CI [−18, +0.7, +20] **P=0.53** (wash)
- delta_maxDD CI [−4.8, +0.3, +5.9] **P=0.46** (wash)
**Expectância indistinguível do mecânico.** O SL-contexto é lateral em R; o ganho real é distribuição de SL (mais tight/sã) + risco (DD/streak). Temporal: 2020-22 +18.4R / 2023-26 +55.4R (edge ainda concentrada no bull, como sempre).

## 10. Operational recommendation
**Adotar SL_CONTEXT (demanda 4H) como o SL estrutural — mas pelo argumento de RISCO/ESTRUTURA, NÃO de retorno.** Razões: (a) resolve a queixa de largura (context-varied, >4ATR halved, demand-anchored defendido); (b) menor DD (16.5) e streak (7) — melhor perfil prop-firm/FN; (c) causal (repaint-audited). **NÃO vender como edge** — é expectancy-neutral vs mecânico. Se o único objetivo fosse retorno bruto, tight_6bar vence (+84) mas é choppy (DD25/streak12) — pior pra FN. E13 = understood-loser. E15/E24/E34 perdem mas o F_STRICT (filtro de entrada separado) os trata como review.

## 11. O que fica aberto
- O **no_trade/F_STRICT** parece carregar parte do ganho de avgR/DD — validar o filtro isolado (já feito: F_STRICT positivo, review-flag).
- E13-tipo (demanda varrida) = irredutível por SL; aceitar ou tratar via entrada.
- 3% fallback swing-origin — pequeno, reportado.

## 12. DA appendix
DA dedicado. Verdict: **(1) Repaint = BLOQUEANTE→auditado: boxes estáveis/causais (E17 forma no entry-bar, sem shift) — PASSA, com nuance close-entry.** (2) Bootstrap wash (P0.53) = SL é lateral em expectância; "resolve largura a expectância igual" é win operacional/risco legítimo, NÃO edge — não vender como tal. (3) 3% fallback + circularidade demanda (detectada do mesmo OHLC) — reportar subset puro; risco mitigado por repaint-audit. (4) **tight_6bar vence sumR/avgR** — context-demand só se justifica como variante de menor DD/streak (prop-firm). (5) TOP_EXHAUSTION pega só E23 dos 4 — filtro estreito, mas E15/E24/E34 perdem (não viram falso-win). (6) Conclusão: sessão SUCEDEU no objetivo estreito (matar largura exagerada), FALHOU em produzir edge; adotável só como SL risk-shaped causal, após repaint-audit (feito). Causal ✓ (j≤i-5, demanda as-of-bar). Sem CAP4/teto1.5. Exit inalterado. Sem SLIM. Produção intacta. Não promovido.

---

*Outputs: `results/l2_bpt_sl_context_{raw_audit,candidates,key_cases,policy_results,improvement_register,bootstrap}.csv`. Scripts: `sl_context.py`, `sl_context_fullbase.py`. Repaint audit inline. Sem produção, sem plotagem, sem SLIM, exit inalterado, nada promovido.*
