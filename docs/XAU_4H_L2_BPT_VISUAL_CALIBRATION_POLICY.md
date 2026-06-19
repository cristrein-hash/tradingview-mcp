# XAU 4H L2/BPT — Política de Calibração Visual / Discricionária

**2026-06-19.** Escopo: XAU_4H_L2_BPT_BOS_CHOCH. Calibração **discricionária assistida por engine** a partir
dos 13 prints (`ENGINE_ L2:BPT_ 2.zip`). **NÃO é regra automática, NÃO promove, NÃO altera engine/registry.**
Guia para o humano (Cris) decidir QUANDO operar, bloquear, reduzir ou revisar.

## Enquadramento (acordado com Cris)
A estratégia é **LONG 4H pensada para bull / virada / fundo**. O OOS bear 2013-2016 (refutado) é **limite de
regime confirmado**, NÃO invalidação. O objetivo NÃO é um bot regime-resilient; é **lucro prop-firm com uso
regime-aware + filtro humano**. A pergunta é "em quais estruturas operar/bloquear/revisar", não "funciona em
todo regime".

## Famílias visuais dos winners (dos prints #1–#17)
1. **bottom_reversal** — BOTTOM(NAS) + drop + reclaim (#6/#7, #11, #13, #1/#2 COVID).
2. **demand_reclaim** — demanda 4H defendida tocada + reclaim verde (#8, #12, #15).
3. **capitulation_reclaim** — flash-crash/dump + reclaim (#3 ago/2021, COVID mar/2020).
4. **bull_pullback_continuation** — uptrend recuando a demanda/EMA, não-overbought (#16/#17).

Núcleo comum: **demanda defendida + reclaim + espaço limpo até supply + SL estrutural + regime bull/turning**.

## Política operacional discricionária (4 categorias)

### TAKE_CANDIDATE (humano confirma e opera)
- **Presente:** demanda 4H defendida sob o preço; reclaim verde (corpo) após toque/sweep; BOTTOM(NAS) ou CHoCH/BOS coerente; espaço limpo até a supply (target alcançável ≥ ~2.5R); regime bull_continuation / pre_bull_turn / demand_reclaim.
- **Bloqueia:** supply colada; entrada esticada (já correu vários R); late_top.
- **Reduz confiança:** range/mid sem tese; reclaim sem corpo.

### REVIEW_ONLY (decisão 100% humana)
- capitulation_reclaim (take válido, MAS gestão pós-entrada exige humano — chop frequente, ex. #3); #10-like (entrada tardia perto de TOP); mid_range_noise; SL não-estrutural; sinal só por bull-beta/drift sem estrutura própria.

### BLOCK (não operar LONG)
- bear_continuation (downtrend puro — regime OOS 2013-2016); late_top_exhaustion (legpos90+RSI overbought+rise20+distribuição); faca-caindo sem reclaim; sem demanda defendida; bear_bounce em supply overhead.

### WATCHLIST_ONLY (observar, sem ação)
- mid_range_noise com possível formação de fundo ainda não confirmada; pré-reclaim.

## Quando o humano decide (sempre)
- capitulation_reclaim (gestão), entradas tardias, ranges, qualquer regime ambíguo, e exceções a BLOCK (ex. bottom nascente dentro de um bear que está virando — como out/2023).

## Gap de cobertura identificado (TRANSFORM → hipótese futura)
- **img13:** "FALTOU UMA ENTRADA NESSA PERNA DE ALTA" (jun-jul/2020). O engine **sub-aciona** continuação bull
  limpa. **Hipótese futura (não agora):** uma entrada de *bull_pullback_continuation* que cubra pernas de alta
  saudáveis sem fundo/capitulação. Registrar como UNTESTED quando for trabalhado (via Hypothesis Registry).

## Conexão com componentes do engine (sem promover)
Ver `results/l2_bpt_visual_vs_engine_components.csv`. Resumo: Stage A = gate de regime; demand_supply = fator
#1 dos winners; NAS BOTTOM/TOP = confluência (nunca isolado); exhaustion_top + DA veto = candidatos a bloquear
late_top/bear; **capitulation+rsi = útil SÓ dentro do regime permitido** (refutado em bear puro); bull_beta =
flag de "drift sem estrutura".

## Travas
Isto é **calibração humana**. Não vira regra automática, não promove, não altera registry/library/engine/
decisions_merged. capit+rsi permanece **CONTEXT_ONLY** (refutada como regra de lucro automática). O valor está
no **uso regime-aware com leitura humana**, não em automatizar.
