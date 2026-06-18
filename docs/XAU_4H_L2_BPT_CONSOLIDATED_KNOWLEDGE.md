# XAU 4H L2/BPT — Conhecimento Consolidado (canônico, 6 rodadas)

**Status:** `CANONICAL_KNOWLEDGE · LIVING · NO_OUTCOME_PROMOTED` · **Atualizado:** 2026-06-18
Consolida os achados PRECISOS das últimas ~6 rodadas (a pedido do Cris). É a fonte de verdade desta frente. Sem produção/SLIM/Caminho B.

---

## 1. Onde estamos (1 parágrafo)

L2/BPT é um setup LONG estrutural (reclaim de polaridade após BOS/CHoCH). O detector mecânico **v2.2** captura os winners mas gera ruído (massa ≈ base rate). O discriminador real **NÃO é feature local** (supply/demand/bubbles/NAS/RSI isolados); é **posicional-estrutural** — onde a entrada está na perna e a direção da perna macro. Achamos 1 eixo causal validado (**legpos**) e o reframe correto dos indicadores (**identificar topo macro, não comparar trades**). Ainda não há estratégia/outcome promovido.

## 2. Fatos validados (duráveis)

1. **Detector v2.2** = candidate generator, **recall 17/17 BOM**, ~1109/ano. NÃO é estratégia. Census v1 = NULL (recall 0/17). Anchor de recall = v2.2.
2. **PRUNED_BASE_V2** = `overextended_entry OR src_redundant OR bear_flag` → 7763→**2965 (−61.8%)**, recall 17/17 preservado. CANDIDATE_BASE.
3. **2965 candidatos = só 276 episódios** estruturais (média 10.7 sinais/perna). Unidade correta = **episódio**, não candidato/bar.
4. **Features LOCAIS não separam:** supply/demand quality, bubbles, NAS, RSI, outcome-anatomy — todas ≈ base rate. Motivo: medem folhas; o sinal é estrutural-global.
5. **Outcome proxy (MFE/MAE forward) media DRIFT, não edge** (lift 0.99× vs base rate 67%). Corrigido para **trade real com SL estrutural**: BOM WR **73.3%**, avgR +1.15, **lift 1.83×**; UNKNOWN ≈ base rate (lift 1.05×). Edge demonstrado nos **labels**, não na massa.
6. **R_ceiling 1.5ATR era estruturalmente ERRADO.** O SL estrutural real dos monumentais é **3-4 ATR** (verificado vs `stop_cris`: GT21 ~3.9ATR, GT27 ~4.4ATR). "SL curto demais" e "R_ceiling abort" são o mesmo bug.

## 3. Ground-truth visual do Cris (11 prints full-res lidos)

3 erros sistêmicos:
1. **Cegueira macro-bear** (o mais grave) — compra repique em bear leg/topo/exaustão.
2. **SL curto demais** — winner vira loser (estrutural ~3-4 ATR).
3. **Entrada precipitada** — vários sinais na perna, entra no errado.

Rótulos (41 episódios):
- **WINNERS a preservar (8, atualizado §8c):** E1, E5, E13, E17, E21, E27, E30, E40. *(E23 reconciliado OUT 2026-06-18 = top-exhaustion, ver §8c; antes listado como 9º winner.)*
- **12 VALID_SETUP_BAD_SL** (viram winners com SL estrutural): E2,E3,E4,E19,E20,E22,E28,E29,E31,E32,E38,E41.
- **13 MACRO_BEAR / não-long:** E15,E24,E34,E39,E36,E6,E7,E8,E9,E10*,E37,E11.
- **3 PREMATURE:** E25,E26,E35 (entrada real = E27).
- **E12** = retomada mas precipitada (borderline-block).
- **E10*** = EXCEÇÃO: pullback forte indistinguível de reversão bull = **entrada correta da estratégia** (não bloquear).

## 4. O eixo causal validado: `legpos` (maturidade da perna, 60d)

`legpos` = posição do preço na faixa de 60 dias (0=fundo, 100=topo). **Primeiro e único feature que separou um par antes inseparável:**
- **E40 (winner) legpos 56 · E39 (trap) legpos 89.** E39 confirmado pelo Cris = "reteste de polaridade de fundo dentro de bear leg iniciada".
- Isola os **top-traps** (E15/E24/E34/E39 = legpos 89-95) no estrato HIGH.
- **Cuidado:** legpos NÃO separa no agregado (inverte) porque há 2 mecanismos (abaixo).

## 5. Mapa 2×2 dos mecanismos (a estrutura real do problema)

| | mecanismo | episódios | discriminador |
|---|---|---|---|
| **Trap A** | exaustão/topo macro | E15,E24,E34,E39 (high legpos) | maturidade + topo macro 1D |
| **Trap B** | reclaim em downtrend 1D | E6-E11,E36,E37 (low/mid legpos) | tendência/estrutura 1D |
| **Win 1** | reversão do fundo | E27,E30,E40 | legpos baixo/médio + sweep |
| **Win 2** | pullback em uptrend | E1,E5,E13,E17,E21 | slope 1D positivo |

*(E23 movido para Trap A / top-exhaustion na reconciliação §8c — blow-off top, não pullback.)*

**Por isso nenhum feature único separa** — é problema multi-mecanismo. Cada eixo cobre PARTE.

## 6. O reframe dos indicadores (insight do Cris, 2026-06-18)

Os indicadores (RSI-div, bubbles, NAS, volume) **NÃO comparam winner×loser**. Eles servem para **identificar um TOPO MACRO BEAR LEGÍTIMO vs um pullback em leg-bull-middle**. Por isso só o **E24** acendeu (topo macro real). Indicadores = **confirmação de topo**, não gatilho de trade.

## 7. BLOQUEIO SEQUENCIAL / bear-leg — RETRATADO (não validou na base completa)

🚫 **RETRATADO 2026-06-18:** o bloqueio por estado bear-leg parecia conceito-válido nos 41 rótulos curados (8/8 a jusante de topos) mas **era circular** (o set continha os winners-alvo). Na **base tradável completa (276 episódios, SL estrutural)** NÃO validou: bloqueia **5/9 winner-episodes**, **REDUZ sumR** (+63→+51), pior no held-out 2023-26. DA verdict: FATAL. Detalhes em [[project_l2_bpt_legbear_block]] (memória) e `XAU_4H_L2_BPT_1D_LEG_DECOMPOSITION.md`.
- **Lição central:** com **SL estrutural (sem teto)**, até os reclaims em regime bear são **net-positivos no agregado** — o SL já administra o regime bear; um bloqueio de regime **destrói valor** (remove os winners de recuperação). Confirmado novamente em 2026-06-18: o subset bear-context é WINNER-RICH (9/15 monumentais; avgR +0.28 > base +0.23), não loser-prone.
- **Gatilho exaustão-4H** = inutilizável (dispara 189-380×, recall falha 6-7/9). **Gatilho 1D raro** (CHoCH/BOS bear no 1D) também testado e refutado como gate duro (mata E1/E17 do fundo COVID). 7 abordagens convergem: subconjunto **não filtrável na entrada**.
- **Resolução real:** veto HUMANO via flags `legbear`/`overbought` no Telegram (requisito FUTURO, [[project_l2_bpt_telegram_bear_flags_FUTURE]]) — automação não separa, humano sim. Único filtro automático limpo = extreme-top E24, como veto-soft.

## 8. Regras metodológicas permanentes (aprendidas a duro)

- **Recall-gate antes de qualquer métrica** (detector tem que preservar os winners conhecidos).
- **Lift sobre base-rate**, nunca taxa absoluta (drift do mercado infla tudo).
- **Por episódio**, não por candidato/bar (dedup serial).
- **Distância+qualidade**, não presença binária; threshold apertado fabrica falso-nulo.
- **Não fabricar leitura visual** — marcar PENDING/AWAITING_USER; não inventar o que o print não mostra.
- **Não se deslumbrar** — descartar com dado o eixo que não serve, em vez de empurrar.

## 8b. Exit lab + teste decisivo (2026-06-18) — exit é ruído, edge é regime-bound

Com SL estrutural FIXO, variou-se só o exit (R/BE/parcial/trail) sobre a base 276. **3 DAs.**
- **Nenhuma política bate baseline +3R fora do ruído** (avgR +0.21..+0.30, SE da diff ~0.19 em n=276). Exit-tuning in-sample.
- **BE ingênuo PIORA a média** (scratch nos monumentais que recuam pela entrada antes do run; BOMsumR 8→4). Mecânica robusta: scratch perto da entrada baixa a média → contra BE/parcial.
- **Split temporal revelou o fato dominante — edge NÃO-ESTACIONÁRIO:** build 2020-22 avgR **+0.02** (chato); holdout 2023-26 **+0.39** (sumR +61R). É captura de beta long-gold no bull, não edge estacionário (= padrão Caminho B 2020-22).
- **Monumentais 13/15 no build, 2 no holdout** → objetivo "preservar monumentais" intestável OOS.
- **partial50@2R+6R** = curva marginalmente mais lisa (bootstrap maxDD 17 vs 18R, streak 9/12 vs 11/15) a sumR chato — só vale por sobrevivência prop-firm (streak ≤5), não R total.
- **Conclusão:** exit NÃO é a alavanca (é ruído). Alavanca real = **contexto de regime** (deploy só em BULL via Regime Classifier v3) ou SHORT espelho. Baseline +3R = default. Scripts `/tmp/exit_lab.py`, `/tmp/exit_decisive.py`.

## 8c. SL estrutural trade-a-trade + User reconciliation (2026-06-18)

SL estrutural medido (6 modelos causais, exit fixo partial50, base 276; doc `SL_STRUCTURAL_TRADE_BY_TRADE`). Na base não-enviesada os modelos estão **dentro do ruído**; o swing-origin (=`SL_STRUCTURE_LOW` visual) recupera bad_SL 5→10/12 mas **97/276 SL >4ATR (máx 15ATR) = inviável prop-firm sem cap**. **SL não é onde mora a edge** (próxima alavanca = entry-filter).

**User reconciliation after SL structural block (confirmada pelo Cris):**
- **E13 = winner REAL**, problema NÃO é a tese — é seleção de pivô/entrada (pegou pivô raso 2.87ATR varrido por wick; estrutura defendida real é funda ~5.3ATR). Status: `VALID_SETUP_BAD_ENTRY_OR_BAD_PIVOT_SELECTION` (não SL_ENGINE_FAIL). Implicação: selecionar swing DEFENDIDO, não o mais recente.
- **E23 = NÃO é winner a preservar** — trade de topo/blow-off (3 barras pré-ATH 2020-08-07, pico +1R, depois crash −9%). Status: `TOP_EXHAUSTION_SHOULD_NOT_LONG` / `BLOWOFF_TOP_REJECT`. **Removido da lista de winners.** Candidato a filtro de exaustão/topo.
- **E1/E17 = big winners sensíveis ao exit** — saem mutados (+0.64/+0.91R) com partial50 (cauda de reversão em V reduzida). partial50 segue APROVADO (gestão streak prop-firm) **com caveat documentado**; exit NÃO alterado.

**Lista de winners corrigida:** must_preserve (8) = E1,E5,E13,E17,E21,E27,E30,E40. valid_but_needs_better_entry = E13. should_not_long_top_exhaustion = E23 (+E15,E24,E34). exit_sensitive_big_winners = E1,E17. (CSV `results/l2_bpt_reconciliation_labels.csv`.)

## 9. OPERATING POINT (consolidado 2026-06-18, aprovado pelo Cris)

Após 5 blocos de SL/exit/cap/defended-swing, o ponto de operação está travado:
- **Entrada L2/BPT:** ainda em PESQUISA (não finalizada).
- **SL:** `NORMAL_BPT` / **swing-origem estrutural** (SL abaixo do swing/origem estrutural). Aprovado como direção.
- **Exit:** **partial50@2R+6R** (50% sai +2R trava +1R, restante BE→runner +6R, time-stop 60, custo 0.10R). Aprovado (gestão streak prop-firm; caveat: muta cauda de big V-reversal — o que NÃO é culpa do partial, é do SL/pivô, ver §8c + audit E1/E17).
- **SL ambíguo ou >4ATR:** **review HUMANO**, não cap automático (CAP4 descartado d6f36b6; defended-swing não operacionalizável por regra 8598e85).
- **E23 / topos:** **próxima frente = entry/exhaustion filter** (validar com amostra independente, NÃO com os 9 casos curados).

**Cadeia de blocos:** exit lab (§8b) → SL estrutural (§8c) → reconciliação E13/E23/E1/E17 → audit E1/E17 (SL/pivô, não exit) → CAP4 descartado → defended-swing não-funcionou-como-regra. **Meta-conclusão:** SL/exit/cap/defended-swing **não são a alavanca**; a edge é regime/drift; a próxima alavanca real é **entrada/exhaustion**. Detalhes em [[project_l2_bpt_sl_structural]] · [[project_l2_bpt_exit_lab_regime_bound]].

**Não iniciado:** entry/exhaustion filter · regime v3 · SHORT espelho.

## 10. Artefatos (docs/results desta frente)

Docs: `DETECTOR_V2_2_RECALL_AUDIT` · `V2_2_PRUNED_BASE_V2` · `V2_2_DEMAND_SUPPLY_DISTANCE_QUALITY_MODEL` · `OUTCOME_PROXY_FAILURE_AUDIT` · `FULL_RES_VISUAL_RECONCILIATION` · `SWING_STRUCTURE_PRECISION` · `LEGPOS_X_INDICATORS_TEST` · este. Results: `l2_bpt_full_res_visual_episode_review.csv`, `l2_bpt_swing_anatomy.csv`, `l2_bpt_legpos_exhaustion.csv`, `l2_bpt_real_outcome_per_episode.csv`. Scripts: `swing_anatomy.py`, `leg_maturity.py`, `bear_state.py`, `real_outcome.py`.

---

*Canônico/vivo. Sem outcome promovido, sem produção. Atualizar a cada rodada que adicionar fato preciso.*
