# XAU 15M LONG BOTTOM — Engine de diferenciação de potência dos fundos (PLANO)
*Plano para aprovação — 2026-06-27. Nada executado/aprovado ainda. Frente: 2ª estratégia (LONG BOTTOM); depois 15M SHORT TOP.*

## 0. Objetivo
Construir a BASE: ler cada um dos **205 fundos M8** (e espelho 209 topos depois) com leitura **multi-feature convergente** e descobrir, **de forma causal (as-of a barra do fundo, SHIFT1)**, o que diferencia **MONSTRO/FORTE (foco) + MÉDIO (usar) de FRACO (descartar)**. Sobre essa base roda depois a busca exaustiva de entradas sem look-ahead.

## 1. ⚠️ Enquadramento honesto (encarar a parede, não fingir que é fácil)
Todo o programa (4H L2/BPT + cross 5ATR×tiers + cluster decisive + buyatlow) converge num achado: **features de SNAPSHOT na entrada NÃO separam forte de fraco no agregado** (cross-test AUC ∈ [0,45–0,57] = acaso; disc8: nenhuma feature isolada move WR >1pp). O que **carrega sinal** é:
- **Posicional-estrutural** — legpos (posição na perna), dealing-range position (discount vs premium).
- **Trajetória/path (multi-barra, dinâmico)** — sweep-reclaim, flush-V vs grind, aceitação-de-valor, deslocamento pós-evento.
- **Regime/leg context** — d1_macro_leg, weekly_slope, regime≠BEAR.
- **Convergência de múltiplas vozes fracas** — conv≤1 (4 vozes) é o template mais próximo que já existe de "graduar fundo".
- **Pós-entrada (o edge validado mais forte)** — dispR@8 / mfeR / up_closes / maeR.

⟹ O engine **NÃO** pode ser caça-feature-isolada (o erro superficial/binário). Tem que ser **trajetória + posicional + convergência + combos 2-3 + clustering**, com snapshots só como membros de combo. Se a parede da entrada se confirmar, o engine **pivota** para a camada pós-entrada (edge validado) como camada operacional — e isso é dito de cara.

## 2. Mapa de features consolidado (10 famílias)
Marcações: **D**=durável/validado · **C**=contexto (informa, não corta) · **X**=descartado isolado (guardar p/ combo) · **★**=prioridade p/ separar potência.

### F1 — Posicional-estrutural ★D
legpos30/60/90 (posição na perna; baixo=forte) · dealing_range_pos 4H/1D (DISCOUNT=forte) · f5_range_pct · op_structure_state (HH/HL vs LH/LL) · bars_since_choch_up · bos_density.

### F2 — Trajetória/Path (DSPA) ★D
f1_swept_low_reclaim + sweep_depth_atr + bars_since_sweep (sweep+reclaim=forte) · f2_flush_state (FLUSH_V=forte / GRIND_DOWN=fraco) + drop_atr + consec_down · f3_acceptance_state (HOLDING/ACCEPTED=forte) · downleg_shape/overlap/redbar_streak/accel_decel (limpeza da perna) · downleg_traversed_zones (vácuo de liquidez).

### F3 — Supply/Demand (Custom OB = BigBeluga proxy) ★D/C
sup_cat (CLEAN_SKY/SUPPLY_NEAR_REJECTING…) ★ · dem_cat (SUPPORTING_RETEST/ORIGIN/TOO_DEEP…) · pol_cat (reclaim-accepted/under-pressure/floating) · clean_sky_atr / dist_supply_atr / overhead_supply_density ★ (room=teto do runner) · dist_demand_atr / in_demand / demand_fresh / n_demand_near (stack) · zone_virgin / mitig_count / freshness · zone_stack_confluence (15M∩HTF∩VAL).

### F4 — SVP / Value-area (volume real) ★D/C
f6_svp_state (ACCEPTING_ABOVE_VALUE=fuel) · svp_acc (aceitação-de-valor — lead condicional mais forte 4H, lift 1.28) ★ · dist_POC/VAL_atr · below_VAL · va_width · rel_volume (climax). ⚠️ **BLOQUEADO:** histograma POC/VAH/VAL de volume não serializado no 15M RAW (lever conhecido em falta).

### F5 — Regime / Macro ★D
macro 4H (BULL/BEAR/NEUTRAL; ≠BEAR=validado) ★ · regime_B_v3 (state/combined/cascade) · deep_cascade≤−3 (pocket winner-rich) ★ · weekly_slope ★ · rsi_1d · trend_30/90_atr · d1_macro_leg (backbone) · htf_regime_align.

### F6 — Flow / Bubbles / NAS C/X
bub_buy/sell s/m/L (BUY=plot_0/2/4, SELL=plot_6/8/10) · sell_decel / flow_accel / buy_sell_ratio4 / sell_skew_mig · bub_large_sell_10b (climax-then-absorb) · nas_long_new_8b (prob de reação, não magnitude) · vol_climax / vol_dryup_then_spike. ⚠️ bubble como SELETOR de entrada = **exausto** (mecânico; só near-positive em capitulação profunda macro_drop≥15ATR).

### F7 — Momentum / RSI / Capitulação ★D/C
rsi_low / rsi_min8 (oversold=exaustão) · rsi_bull_div_20b ★ (LL preço + HL RSI=forte) · rsi_headroom (lente WR-only validada 15M) · drop20_atr (capitulação) · capit (CLIMAX_RECLAIM vs FALLING_KNIFE; regime-bound) · sweet_spot_falling_knife · rsi_reclaim_speed / ema21_reclaim_bars.

### F8 — Volatilidade C
atr_regime_ratio · atr_compression_pre (squeeze→flush=coiled spring) · range_expansion_at_low (climax).

### F9 — Aceitação/rejeição na barra do fundo ★D
sweep_wick_ratio / low_closepos (fecha no topo=rejeição/absorção) · close_off_low_pct · low_revisit_count (duplo/triplo fundo) · post_low_higher_low (micro-HL) · failed_breakdown (spring).

### F10 — Sessão/Tempo · Geometria/entrada C/X
session_bucket / is_session_open_30m / dead_hour · reclaim_body_atr · net_micro_location · entry_quality (refutado como separador, manter descritor). ⚠️ **BLOQUEADO:** microstrutura sub-15M/intrabar (não há OHLC contíguo).

## 3. Combos 2-3 (fraco-isolado → forte-junto) — hipóteses a varrer
1. **Capitulação-Reclaim:** sweep_depth × low_closepos × vol_climax.
2. **Continuação-em-Discount:** op_structure=uptrend-pullback × dealing_range=discount × ema_slope>0.
3. **Capitulação-Absorvida:** sell_bubble_L × vol_dryup_then_spike × rsi_bull_div.
4. **Coiled-Spring:** atr_compression × range_expansion × clean_sky.
5. **Vácuo-de-Liquidez:** downleg_traversed_zones × sweep_reclaim≤2b × range headroom.
6. **Confluence-Shelf:** zone_stack(15M∩HTF∩VAL) × zone_virgin × macro_bull.
7. **Session-Raid:** session_open_30m × sweep_depth × close_off_low.
8. **disc8 (já meio-validado):** h1_eff<0.20 × h4_pos<1.02 (estrutura-morta) — e "grind lento > spike rápido".

## 4. Leitura contextual = "Bottom Fingerprint" (não-eliminante, sem score-único)
Cada fundo = **radar de 8 eixos** (lentes-bundle), cada eixo contínuo-assinado [−1..+1], **nenhum eixo é gate** (nada é cortado por 1 eixo só):
**L1** Capitulação · **L2** Fluxo-operacional · **L3** Localização/Discount · **L4** Absorção · **L5** Momentum-turn · **L6** Room/Teto · **L7** Qualidade-de-zona · **L8** Timing.
- Eixos com polaridade dependente de regime (dist_ema, rsi_depth, sweep_speed) ficam **crus e assinados**, resolvidos pela companhia (combos), não por threshold.
- "Potência lida" = **quantas lentes convergem** (≥4/8 fortes), não soma. Convergência elimina o NÃO-convergente, não corta o outlier bom.
- O label forward (leg_atr/tier) **nunca** entra como input do fingerprint — só é a coisa contra a qual o fingerprint é lido (anti-circularidade).

## 5. Arquitetura do engine (multi-managed-agents) — fases
- **Fase 0 — Dataset causal de fundos** (1 builder salvo): para os 205 BOT (e 209 TOP depois), computar TODAS as features acima as-of a barra do fundo (SHIFT1), juntar tier/leg_atr/power_score (forward, só como label). Source-guard + manifest (RAW-only).
- **Fase 1 — Especialistas por lente** (managed agents, 1 por família F1–F10): cada um lê os 205 fundos, propõe discriminadores intra-família e devolve o **eixo assinado do fingerprint** + candidatos. Não decidem; aprofundam.
- **Fase 2 — Combo-hunter** (agents): varre interações 2-3 (lista §3 + emergentes) buscando separar MONSTRO/FORTE+MÉDIO vs FRACO, com controles: effect-size, por-ano (24/25/26), leave-block (8), Bonferroni-aware.
- **Fase 3 — Clustering não-supervisionado** dos fingerprints → **famílias de fundo** que os dados nomeiam → quais clusters carregam MONSTRO/FORTE.
- **Fase 4 — Twins contrastivos:** fingerprints quase-idênticos com tier oposto → o eixo diferenciador é a lente causal daquele contexto.
- **Fase 5 — DA adversarial** por achado (look-ahead, vazamento-do-tier-forward, n, estacionariedade, multi-testing, regime-bound).
- **Fase 6 — Síntese:** quais eixos/combos/clusters separam de fato (causalmente, honesto com a parede). = a BASE para a busca futura de entradas. Se a parede da entrada vencer → registrar e pivotar p/ camada pós-entrada (dispR@8) como operacional.

## 6. Régua de avaliação
- Alvo = **separabilidade causal** do tier (label forward), medida por AUC/lift, **controlada por estacionariedade (3 anos) + leave-block (8) + effect-size + multi-testing**. NÃO é backtest de estratégia ainda.
- Calibração in-sample nos 2 anos (sem OOS/cross-asset, por cânon). MÉDIO entra; FRACO descarta; foco MONSTRO/FORTE.
- Nada promovido sem DA + autorização. FRACO só é "descartável" se a separação for causal e robusta — senão fica como diagnóstico.

## 7. Gaps conhecidos (não fabricar)
- Volume VA histograma (POC/VAH/VAL de volume) **não serializado** no 15M RAW.
- Microstrutura sub-15M/intrabar **ausente** (sem OHLC contíguo).
- Tier é **forward** (rótulo de potência real) — jamais usado como feature; só como alvo.

## 8. Decisão pendente (Cris)
Aprovar este plano (ou ajustar escopo) antes da rodada pesada multi-agente da Fase 0→1. Sugestão de tamanho da 1ª rodada: Fase 0 (dataset) + Fase 1 (10 especialistas) + Fase 2 (combo-hunter) + Fase 5 (DA), e parar p/ ler antes de Fase 3-4.
