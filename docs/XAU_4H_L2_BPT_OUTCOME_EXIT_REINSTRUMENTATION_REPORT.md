# XAU 4H L2/BPT — OUTCOME/EXIT RE-INSTRUMENTATION REPORT

**2026-06-22.** Re-instrumentar a régua econômica (realR capado +3.9R) antes de julgar entrada/engine/automação.
DIAGNÓSTICO. Fonte = frozen 4H OHLC contíguo. 1 DA (PASS_WITH_LIMITATIONS, 1 bug corrigido). Sem produção/promoção/OOS.

## Respostas às 8 perguntas

**1. Onde a convexidade foi apagada?** No nó **Outcome/Exit**: o realR é capado em +3.9R (target). 17 episódios
grudados no teto; **21 runners comprimidos** (capados ~3.9R quando o path correu >5R); 30 monstros (MFE≥10R)
achatados. A régua reportava hit-rate, não convexidade.

**2. Há dados para reconstruir R não-capado?** **SIM.** `repro_recovery/raw_features_2020_2026.jsonl` é a série
4H contígua (9880 bars) — a MESMA fonte do realR original. Reconstrução causal (entry C[i], SL de bars≤i, path
j>i, stop-first). Correção à auditoria anterior: o OHLC contíguo p/ path forward **existe** (o que falta é micro-
estrutura intra-barra, não o path).

**3. Quais runners foram comprimidos?** 21. Top: 2020-07-17 **+30.7R**, 2026-01-09 +24.9R, 2023-03-08 +19.8R,
2025-09-28 +18.8R, 2024-09-04 +18.7R, 2023-03-09 +18.0R, 2026-01-18 +17.1R, 2025-12-16 +17.1R.

**4. A entrada segue sem edge ou só sem hit-rate edge?** Sem **alpha de TRIGGER** nas duas dimensões: L2/BPT
runner_freq 26.1% vs random-long **context-matched** 25.5% (p=0.42); random até tem mais monsters (12.8% vs 10.9%).
**Ressalva honesta (DA):** L2/BPT bate random-long **GLOBAL** em +4.2pp — concentra em REGIMES de maior convexidade
(timing/regime, ainda beta), e o CI (n=72 runners) não permite afirmar edge exatamente zero, só descartar edge
GRANDE. **Conclusão: a entrada não adiciona alpha de seleção; a convexidade é do mercado.**

**5. O engine falha em convexidade ou só em WR capado?** Falha nas **duas**. ENGINE_TAKE runner_freq 24.8% < baseline
26.1%; ENGINE_SKIP 30.8% > TAKE; SKIP per-trade (let-run e V-stair) > TAKE. O engine é **anti-seletivo** — empilha
runners no SKIP. Não separa, não preserva. (Corrige o over-reach de atribuir ao engine papel de capital-preservation —
não demonstrado, contradito.)

**6. Qual é o verdadeiro ponto de estrangulamento?** O **nó Outcome/Exit** (cap), confirmando a Theory of Constraints
do Cris. Mesma entrada, exits diferentes: capado **+84.2R** · let-run **+241.2R** · V-stair **+207.7R** (corrigido).
Com custo 0.35R/trade: let-run **+144.6R**, V-stair **+111.1R**. O cap destruiu **~45-65% da edge recuperável**.
A entrada é gargalo **secundário** (edgeless de trigger), mas o valor destruído morava no exit.

**7. Qual é a nova função objetivo?** `docs/XAU_4H_L2_BPT_CONVEXITY_TARGET_FUNCTION_SPEC.md`. Primária = **captura de
convexidade uncapped** (sumR realizado sob exit convexo) + **runner/monster preservation** + **expectancy uncapped**.
WR = contexto/sanity, NUNCA árbitro. maxDD/streak = restrição (FundedNext ≤5), não objetivo. A estratégia é um
**HARVESTER DE CONVEXIDADE**, não um seletor.

**8. Próximo bloco lógico?** Modelar custo/slippage realista + **calibrar o exit convexo** (let-run vs V-stair vs
variantes) sobre a régua uncapped, por sub-janela P1/P2 (isolar beta 2023-26). Questão aberta a TESTAR (não concluir):
um gate de regime melhora capital-preservation nos vazios bear? Tudo medido em convexidade uncapped, dentro dos 276.

## Veredito honesto (corrigido pelo DA)
- **(a) O cap destruiu a maioria da edge econômica — ROBUSTO** (sobrevive a custo: +144R let-run vs +84R capado).
- **(b) Entrada e engine NÃO têm alpha de convexidade** — entrada sem alpha de trigger (só regime/beta); engine
  anti-seletivo. A convexidade é **beta**, capturada pelo EXIT.
- O gargalo do Cris estava certo: **o nó Outcome/Exit era a restrição.** Mas consertá-lo não resgata a seleção —
  revela que a estratégia é um harvester de convexidade-beta cuja alavanca é o exit, não a entrada.

## Edge source (T6, por episódio)
CONVEXITY_ALPHA 38 · RISK_SHAPING_EDGE 34 · EXIT_MANAGEMENT_EDGE 22 · BETA_ONLY 14 · NO_EDGE 168. A edge operável
está no eixo **EXIT/risco**.

DA = PASS_WITH_LIMITATIONS (bug V-stair corrigido, 2 over-statements corrigidos). Outputs:
`results/l2_bpt_outcome_exit_inventory.csv`, `..._convexity_destruction_audit.csv`,
`..._uncapped_or_proxy_outcomes_276.csv`, `..._entry_attribution_convexity_audit.csv`,
`..._macro_engine_convexity_evaluation.csv`, `..._edge_source_classification.csv`,
`..._prior_negative_conclusions_reclassification.csv`, `..._outcome_exit_reinstrumentation_da.csv`.
