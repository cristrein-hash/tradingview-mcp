# L2/BPT — VISUAL-ANCHORED REGIME MEASUREMENT (62)

**2026-06-22.** Bloco fechado sob o canon efaf48a. Diagnóstico/calibração nos 62 (ensino). NÃO produção, NÃO
276/OOS, NÃO promoção. Âncora = leitura VISUAL do Cris (prints + verdicts + estrutura macro XAU 2020-2026).

## 1-3. Escopo, por que existe, canon
A auditoria anterior (5ac3f9e) provou que o gargalo NÃO é a confluência — é a **medição de regime/contexto**: o
escalar regimeB over-fira em bull-leg (corta winners) e é cego ao bear-junk (deixa passar T40). Este bloco
**ancora a camada-1 (regime) na leitura visual**, rebaixando o regimeB a EVIDÊNCIA. Prioridade causal: visual >
D1 backbone > auction > regimeB-evidência; supply CONDICIONADA ao regime; risk/SL eixo próprio; outcome só calibração.

## 4. Taxonomia visual de regime
`results/l2_bpt_visual_regime_taxonomy_62.csv` (13 estados: BULL_RUN/BULL_PULLBACK/MARKUP_THROUGH_SUPPLY/
RANGE_BULL_ACCUMULATION/BOTTOM_TURN/CAPITULATION_RECLAIM/BEAR_MARKDOWN/BEAR_PULLBACK_TRAP/CORRECTIVE_RISK/
RANGE_CHOP/MICRO_TOP/LATE_TOP_RESIDUAL/UNKNOWN), cada um com Auction Theory + sinais visuais + prior layers que
apoiam vs as que NÃO podem vetar sozinhas.

## 5. Falhas da medição anterior (quantificadas)
`results/l2_bpt_regime_measurement_failure_audit_62.csv`: **SUPPLY_LENS_INVERTED_IN_BULL 21** (supply-perto-em-
bull lido como rejeição), **REGIMEB_MISSES_BEAR_JUNK 11** (regimeB pontua bull em contexto bear; ex. T40 cs=+3),
**REGIMEB_OVERFIRES_IN_BULL 5** (broken&combined<0 em bull; ex. T19), RISK_SL_CONFUSED_WITH_ENTRY 12,
MICROSTRUCTURE_FEATURE_MISSING 4, TRUE_RESIDUAL 1, OK 20.

## 6-7. Nova medição vs anterior + calibração
| métrica | antiga | corrigida 5ac3f9e | **VISUAL-ANCORADA** |
|---|---|---|---|
| concordância com Cris (n=18) | 6/18 | 13/18 | **16/18** |
| big winners TAKE (n=32) | 8 | 23 | **27** |
| RUNNERS TAKE (n=5) | 1 | 4 | **5/5** (S20/S25/S26/S32/S35) |
| cortes errados (PROTECT não-TAKE) | 10 | — | **1 (T34→risk-review)** |
| manutenções erradas | 3 | — | **1 (T30)** |

## 8. Trade-a-trade highlights
- **T9 / T42 / T40 → SKIP** (VA_BEAR_PULLBACK): bull-pullback intra-bear macro / bear-junk. Corrige o vazamento
  (T9 era TAKE; print confirma "T9=SKIP"; T40 Cris=BLOCK).
- **T19 → TAKE** (VA_BULL_MARKUP): o over-fire regimeB (broken&combined<0 em bull-leg) corrigido pelo visual.
- **T34 → REVIEW (VA_RISK_SL):** Cris "entrada BOA, stopou por SL curto = falha risk_sl" → roteado ao eixo
  risco, NÃO cortado como entrada ruim.
- **S25/S26/S27/S29/S30/S35/S36/S37 → TAKE:** bull-run markup; supply-perto = rompimento, não veto. Resgatados.
- **S15 → TAKE (VA_BOTTOM_TURN):** reversão de fundo preservada (era SKIP).
- **S7/S8/S13:** S13 SKIP (bear-markdown 2022, ok); S7 SKIP (bear-pullback); S8 TAKE (recovery/bottom).
- **T17/T20/T32 → WATCHLIST:** resíduo auction-irredutível, não force-resolved.

## 9. Calibração (outcome só agora, por tipo de saída)
structural_winner 22 + monumental 5; good_entry_scratch_exit 4 (estrutura boa, saiu BE = exit); review_won 3;
bear_context_won_beta_or_bottom 2; acceptable_loser 8; review_loser 9; residual 4; take_stopped_check_SL 1 (T30).

## 10. O que foi corrigido
A medição de regime ancorada no visual **conserta o gargalo nos 3 eixos**: over-fire em bull (T19), inversão de
supply (S25-S37 resgatados), bear-junk (T9/T40/T42 cortados). Concordância 6→16/18, RUNNERS 1→5/5, cortes
errados 10→1, sem repetir o erro-duplo.

## 11. O que NÃO foi resolvido (honestidade, per DA)
- **A medição visual NÃO é reproduzível por features causais em 20/62 (32%)** — é uma camada de CALIBRAÇÃO
  ancorada no HUMANO (a timeline macro + verdicts), NÃO uma auto-feature promovível. A concordância 16/18 é
  **parcialmente tautológica** nos 18 trades rotulados pelo Cris.
- **A timeline de fases carrega HINDSIGHT irredutível:** algumas bordas alinham com datas winner/loser (a janela
  RALLY_TO_WAR_TOP de ~1 dia começa na data do T19; a borda BEAR 2025-10-01 fica logo após o último S-winner).
  Segura SÓ por ser **congelada, não-promovida e pendente de OOS verdadeiro** (bear 2013-2016, canon §7).
- **Scorecard honesto:** 1 corte errado (T34, roteado a risco) + **1 manutenção errada (T30, bull-leg TAKE que
  stopou)** — defensável (estrutura boa stopada por gestão), mas é um TAKE que perdeu, não-escondido.
- T17/T20 microestrutura permanece feature-missing; S5/S12 risk-review.

## 12. Próximo passo recomendado
NÃO promover. A frente que emerge: o REGIME é input HUMANO discricionário (visual), o ENGINE faz a convergência
auction/risco/exit — exatamente o enquadramento já aprovado pelo Cris (decisão de operar = discricionária
humana regime-aware). Diagnóstico apenas; aguardo direção.

DA = PASS (2 correções de honestidade incorporadas). Agentes auditores (Regime Measurement + Prior Layers) = PASS.
Outputs: `results/l2_bpt_visual_regime_taxonomy_62.csv`, `..._visual_anchored_regime_map`/`reading`/`comparison`/
`calibration_62.csv`, `..._regime_measurement_failure_audit_62.csv`, `..._agent_audit.csv`, `..._da.csv`.
