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
- **9 WINNERS confirmados:** E1, E13, E17, E27, E30, E40, E21, E23, E5.
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
| **Win 2** | pullback em uptrend | E1,E5,E13,E17,E21,E23 | slope 1D positivo |

**Por isso nenhum feature único separa** — é problema multi-mecanismo. Cada eixo cobre PARTE.

## 6. O reframe dos indicadores (insight do Cris, 2026-06-18)

Os indicadores (RSI-div, bubbles, NAS, volume) **NÃO comparam winner×loser**. Eles servem para **identificar um TOPO MACRO BEAR LEGÍTIMO vs um pullback em leg-bull-middle**. Por isso só o **E24** acendeu (topo macro real). Indicadores = **confirmação de topo**, não gatilho de trade.

## 7. O conceito de BLOQUEIO SEQUENCIAL (validado em estrutura, gatilho pendente)

Detectado o topo macro → abre **estado bear-leg** → bloqueia a **sequência** de losers a jusante (E33/E6/E7/E36/E9/E8/E37/E11) — como consequência do topo, não trade-a-trade.
- ✅ **Conceito correto:** os 8 alvos do Cris estão TODOS a jusante de topos detectados (8/8 em toda variante).
- ❌ **Gatilho exaustão-4H = inutilizável:** dispara 189-380× (legpos alto é o estado normal de uptrend), recall-gate falha (bloqueia 6-7/9 winners) em TODA variante testada.
- → **Gatilho correto = evento estrutural 1D RARO** (CHoCH/BOS bear no 1D após perna de alta sustentada), com a exaustão-4H como confirmação. = decomposição de perna 1D.
- **Exceções a respeitar:** E10 (pullback forte = não bloquear); E12 (borderline, idealmente bloquear).

## 8. Regras metodológicas permanentes (aprendidas a duro)

- **Recall-gate antes de qualquer métrica** (detector tem que preservar os winners conhecidos).
- **Lift sobre base-rate**, nunca taxa absoluta (drift do mercado infla tudo).
- **Por episódio**, não por candidato/bar (dedup serial).
- **Distância+qualidade**, não presença binária; threshold apertado fabrica falso-nulo.
- **Não fabricar leitura visual** — marcar PENDING/AWAITING_USER; não inventar o que o print não mostra.
- **Não se deslumbrar** — descartar com dado o eixo que não serve, em vez de empurrar.

## 9. Próximo bloco aprovado (1D leg decomposition)

Codificar a **decomposição de perna no 1D** (continuação de perna de alta 1D vs repique contra-tendência em perna de baixa 1D) como o **gatilho seletivo** do estado bear-leg + o gate **1D-trend** (cobre o cluster bear, a reclamação mais alta do Cris). Tudo com **recall-gate** contra os 9 winners e respeitando E10. Só então outcome (SL estrutural sem teto, por episódio, lift vs base rate).

## 10. Artefatos (docs/results desta frente)

Docs: `DETECTOR_V2_2_RECALL_AUDIT` · `V2_2_PRUNED_BASE_V2` · `V2_2_DEMAND_SUPPLY_DISTANCE_QUALITY_MODEL` · `OUTCOME_PROXY_FAILURE_AUDIT` · `FULL_RES_VISUAL_RECONCILIATION` · `SWING_STRUCTURE_PRECISION` · `LEGPOS_X_INDICATORS_TEST` · este. Results: `l2_bpt_full_res_visual_episode_review.csv`, `l2_bpt_swing_anatomy.csv`, `l2_bpt_legpos_exhaustion.csv`, `l2_bpt_real_outcome_per_episode.csv`. Scripts: `swing_anatomy.py`, `leg_maturity.py`, `bear_state.py`, `real_outcome.py`.

---

*Canônico/vivo. Sem outcome promovido, sem produção. Atualizar a cada rodada que adicionar fato preciso.*
