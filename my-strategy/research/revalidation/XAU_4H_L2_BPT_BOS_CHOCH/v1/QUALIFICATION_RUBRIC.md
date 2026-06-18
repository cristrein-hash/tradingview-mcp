# L2/BPT Trade Qualification — RUBRICA DE RACIOCÍNIO (raciocínio cego ao resultado)

Protocolo multifatorial para decidir, trade-a-trade, TAKE / REVIEW / SKIP + direção LONG/SHORT.
**NÃO é fórmula de threshold.** É leitura probabilística do contexto completo (88 fatores). A decisão precisa ser **explicável**. Importa TODOS os fatores que geraram positivo nas estratégias anteriores.

## Princípio central (destilado de TODAS as estratégias que funcionaram)
**O edge XAU 4H LONG = reversão-de-fundo / reclaim-de-demanda com CONVERGÊNCIA multifatorial, ENTRANDO BAIXO, EVITANDO TOPOS.** BOS/CHoCH = confirmação secundária, nunca o gatilho. O espelho SHORT = topo-exaustão / bounce-em-supply em estrutura quebrada.

## Assinaturas conhecidas (priors, NÃO gates)
- **WINNERS** (E1/E17/E27/E30/E40 — bottom reversals): trend_90 negativo ou pullback fundo; demanda 4H colada e defendida (dist≤~1ATR, touched_on_retest=1, V_REVERSAL_DEMAND); legpos baixo/médio (NÃO topo); F_STRICT False; SL apertado (~1ATR); CHoCH bullish recente; RSI oversold-ish; sinais de absorção (SELL-bubble no fundo / bull-div / NAS LONG). `closer_to=WINNERS`.
- **SHOULD-NOT-LONG** (E23/E24/E15/E34/E39 — topos/tardios/bounces): trend_90 fortemente positivo; rise20 blow-off; RSI overbought (>70); legpos90 alto (>85); F_STRICT True / TOP_EXHAUSTION; supply overhead bloqueando target; BOS bearish recente; SL largo. `closer_to=LOSERS`.

## expected_setup_type (classificar PRIMEIRO o estado de mercado)
- **bottom_reversal** (→LONG): capitulação/oversold (drop20 alto, rsi baixo, below_VAL, falling-knife/consec_down) + virada (demanda colada abaixo, CHoCH bullish, NAS LONG, absorção SELL-bubble, bull-div). O berço dos monumentais.
- **demand_reclaim** (→LONG): reclaim de demanda 4H defendida (dist colado, touched_on_retest, corpo de reclaim bullish) em contexto não-tóxico (sem topo/overhead pesado).
- **bull_pullback** (→LONG, modesto): uptrend saudável (price>SMA50, trend_90>0 moderado) recuando a demanda/EMA, legpos médio, não-overbought, sem div bear.
- **late_top** (→SHORT ou SKIP-long): legpos90 alto + RSI overbought + rise20 blow-off + F_STRICT + supply perto + bear-div.
- **bear_bounce** (→SHORT ou SKIP-long): downtrend, bounce em supply overhead que bloqueia target 2ATR, estrutura fraca.
- **unclear** (→REVIEW/SKIP): sinais mistos/contraditórios, sem convergência.

## Decisão
- **TAKE**: convergência multifator FORTE para a direção (bottom_reversal/demand_reclaim demanda-backed + não-tóxico + ≥2-3 confluências independentes; OU late_top/bear_bounce claro p/ SHORT) E risco bem-formado (SL razoável, não LATE_WIDE de blow-off). Parecido com winners conhecidos.
- **REVIEW**: convergência parcial / fatores conflitantes / demanda longe / SL largo / contexto ambíguo onde julgamento humano agrega. (allow_under_human_review=True)
- **SKIP**: sem convergência; LONG dentro de topo/overhead; SHORT contra demanda forte; LATE_WIDE sem edge; sinais contraditórios dominam.

## Pesos qualitativos (orientação, não soma)
ALTA importância: demanda colada+defendida, legpos/F_STRICT (anti-topo), trend_90/RSI_1D (macro), supply overhead bloqueando target, capitulação (drop20+rsi_min), similaridade winners/losers.
MÉDIA: NAS LONG/SHORT, bubbles absorção (SELL no fundo / BUY ratio), CHoCH/BOS direção, Session VP (below_VAL/POC) [tratar causalidade c/ cautela], bear/bull-div (A7), reclaim body, sweet-spot falling-knife.
CONTEXTO: dead_hour, rel_volume, va_width, atr_level, smc structure.

## Output por trade (schema)
`episode_id, bar_idx, decision(TAKE/REVIEW/SKIP), direction(LONG/SHORT/NONE), confidence(0-100), expected_setup_type, positive_factors[], negative_factors[], decisive_reason, closest_known_examples[], allow_under_human_review(bool)`

## Regra dura
A decisão é CEGA ao resultado (realR/exitype). O raciocínio só vê o packet causal. Validação posterior na base COMPLETA (276) vs baselines — se só imita os 10 curados, falha lá.
