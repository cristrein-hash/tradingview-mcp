# RTSE_PHASE3_PLAN_V0 — Motor multi-fator confidence-graded (síntese de 6 especialistas)

**Status:** PLANNING / aguardando aval do Cris. **Nenhum código.** Síntese das 6 lentes (microestrutura · MTF aninhado · momentum/exaustão · volatilidade/aceitação · macro/EF · novidade), deduplicada por EIXO ORTOGONAL. Implementa a Fase 3 do `RTSE_PHASE_PLAN_V0`.

## 0. Princípios que os 6 convergiram (sozinhos = robusto)
1. **`confidence` = CONTAGEM de eixos ortogonais alinhados** (não soma de pesos a dedo) — schema §5a. Todos chegaram nisto.
2. **A curva latência↔FP se MANUFATURA** desacoplando "cedo" (TF baixo / 1 eixo) de "confirmado" (TF alto / N eixos). O consumidor escolhe o ponto (turn_state EARLY→MATURING→CONFIRMED = profundidade do cascade). Não se vence a lei — modela-se a curva.
3. **Cortador de FP nº1 = ACEITAÇÃO vs REJEIÇÃO do nível rompido** + **counter-pullback aninhado (dip vs flip, exige frame do TF alto)**.
4. **Velocidade = info EXÓGENA + lead multi-TF** (única forma legítima de furar a parede: lower-TF lead, 15M-vs-30M divergência, change-point CUSUM, cross-asset lead-lag, coil→expand).
5. **Simetria:** o v5 é só-BEAR; as novas features cobrem turn-UP (os 205 fundos M8 subatendidos).
6. **FAILED_TURN causal = retração** (divergência resolvendo / sweep revertendo / propagação estagnando) → deixa o sinal early "recuar" sem hindsight → sobe recall sem pagar FP cheio.

## 1. Inventário de features por EIXO ORTOGONAL (valida cada eixo, NUNCA o produto cartesiano)

**A — Regime estrutural (camada macro estável; o que falta ao v5 cru)**
- A1 `mtf_regime_alignment` — lógica v5 nas 5 TFs (15M/30M/1H/4H/1D), agreement assinado [MTF].
- A2 `swing_structure_agreement` — HH/HL/LH/LL consenso entre TFs [MTF].

**B — Gatilhos de velocidade (baixa latência, EARLY)**
- B1 `lower_tf_lead` — 15M/30M segura contra HTF + swing-break (simétrico, turn-up incluído) [MTF].
- B2 `tf_divergence_15m_30m` — 15M flipa antes do 30M ratificar = janela de aviso [MTF/Micro/Novelty].
- B3 `micro_choch_up` — 1ª higher-low nativa 15M após o fundo (sub-dia) [Micro].
- B4 `changepoint_cusum` — CUSUM/BOCPD online no stream de retornos; `h` = orçamento de FP = a curva como algoritmo [Novelty].
- B5 `coil_then_expand` — compressão ATR ≥K barras → 1ª expansão que fecha na direção [Micro/Vol/Novelty].
- B6 `cross_asset_lead` — virada de DXY/real-yield PRECEDE a do ouro (info exógena; daily, melhor no ruler de regime que no M8 intraday) [Macro/Novelty].

**C — Aceitação vs rejeição (o CORTADOR DE FP — real turn vs pullback)**
- C1 `level_acceptance_score` — fração de CLOSES (corpo, não pavio) que segura além do nível rompido [Vol].
- C2 `failed_break_reversion` — rompeu e voltou = LIQUIDITY_SWEEP/FAILED_TURN (o workhorse anti-FP) [Vol/Micro].
- C3 `sweep_reclaim_speed_depth` — velocidade+profundidade do swept_prior_low (rápido+raso = genuíno) [Micro].
- C4 `absorption_ratio` — pavio + volume-rank + fecho forte na barra do fundo [Micro] (⚠️ tick-volume relativo).
- C5 `mtf_acceptance_alignment` — aceitação concorda em 15M/1H/4H [Vol].
- C6 `sequence_grammar_SRA` — sweep→reclaim→acceptance ORDENADO (ordem carrega info) [Novelty] (V1/RESEARCH_ONLY até passar null).

**D — Momentum / exaustão (precursor + sharpener)**
- D1 `roc_rsi_divergence` — preço low-menor + RSI sobe (swings causais) [Mom].
- D2 `leg_velocity_accel` — 1ª/2ª derivada; desaceleração ANTES do flip de sinal [Mom/Novelty].
- D3 `thrust_then_stall` — impulso ≥2.5ATR depois stall (prerequisito = filtro de ruído) [Mom].
- D4 `time_since_extreme` — relógio de exaustão (eixo TEMPO, novo) [Mom].
- D5 `rsi_band_shift` — transição de banda RSI + NAS_RSI (sustentado, não cross solto) [Mom].

**E — Volatilidade / whipsaw (FP-cutter + shaper de incerteza)**
- E1 `atr_regime_step` — slow-ATR REBASE (regime real) vs spike fast-only (pullback) [Vol].
- E2 `vol_of_vol` — assenta (real) vs errático (whipsaw) → popula `risk_of_whipsaw` [Vol].
- E3 `climax_vs_grind` — clímax=V rápido (EARLY/baixa-lat) vs grind=sangra (MATURING/+FP) → ROTEIA latência/FP [Mom/Micro].

**F — Counter-pullback (o 2º eixo; integrador MTF de dip vs flip)**
- F1 `nested_counter_pullback` — HTF intacto + leg_depth/HTF-ATR + swept-reclaim + flush-vs-grind → enum {BEAR_DIP_IN_BULL, BULL_BOUNCE_IN_BEAR, RANGE_FADE, LIQUIDITY_SWEEP, NONE} [MTF].

**G — Priors (baratos, ortogonais, low-weight)**
- G1 `regime_duration_hazard` — turn-prior sobe com idade do regime (Cris boxes = survival, n=30 baixo → low-weight) [Novelty].
- G2 `session_turn_prior` — hora/sessão (London/NY open = sweep-reverte) [Novelty].
- G3 `macro_2nd_axis` — EF: real-yield Δ + USD Δ + Fed-path Δ + COT extremo + DECOUPLING → `EF_ALIGNED/CONTRADICTS` (voto fixo, low-weight, modula confiança, ⚠️COT lag 3d) [Macro].

**H — Novidade (probe, risco maior)**
- H1 `bar_sequence_surprise` (entropia/surprisal) · H2 `multiscale_fractal_align` · H3 `correlation_break` [Novelty]. Pré-registrar discretização; só entram se baterem null + adicionarem lift ORTOGONAL (não proxy de vol).

## 2. Integração (como os eixos viram estado)
- **turn_state (maturidade) = profundidade do cascade** = nº de eixos ortogonais alinhados na direção: EARLY (1-2) → MATURING (3) → CONFIRMED (4+).
- **confidence = contagem de eixos alinhados** (defensável, não-tunada) ou min-dos-críticos; reportar componentes separados.
- **counter_pullback (F1)** decide dip vs flip → roteia LONG-continue/REVIEW vs BLOCK/SHORT.
- **FAILED_TURN** = retração causal (B2 divergência-resolve / C2 sweep-reverte / propagação estagna) → recall sem FP cheio.
- **route por-profile:** cada estratégia escolhe limiar de eixos + tolerância de latência (scalp 15M age em EARLY+SL curto; swing 4H espera CONFIRMED).

## 3. ⭐ Validação (mais afiada que a Fase 2 — a sacada dos especialistas)
**Construir CLASSE POSITIVA vs NEGATIVA** (ensina dip-vs-flip, o problema real):
- **Positiva** = reversões M8 que coincidem com borda MACRO do Cris (virada real).
- **Negativa** = reversões M8 DENTRO de um regime que revertem (boxes PULLBACK / M8 que falham).
Cada eixo (A–H): mede SEPARAÇÃO positiva-vs-negativa + latência×FP vs M8, com **null + jackknife-episódio + por-ano + por-regime**, n-por-célula reportado, **NUNCA cartesiano**. Bater baselines (v5-puro, lagged-MA, swing-break, RSI causal, null) na fronteira Pareto. Empate = consolidação (declarar). Multi-M (M6/8/10/12). Red-team look-ahead em TODA feature (gate de toda fase).

## 4. Sequência de build (cheap-probe-first; gate make-or-break por sub-fase)
- **Prep de dados:** extrair 30M do HD (`/Volumes/GUTS_ LACIE/.../XAUUSD/30M/*.jsonl.gz` → `raw_30m_ohlc.jsonl`) + extrair campos RAW ricos do 15M primitives (RSI/NAS_RSI/volume-tick/zones/smc).
- **3a (sonda barata, maior alavancagem):** harness classe-positiva-vs-negativa + os 3 eixos-chave: **C (aceitação/failed-break) + B1/B2 (lead+divergência) + F1 (dip-vs-flip)**. GATE: separam positiva-vs-negativa acima do null E Pareto-batem o piso? Se NÃO → re-escopar antes de construir o resto.
- **3b:** adicionar D (momentum) + E (volatilidade) como sharpeners. GATE: cada eixo bate null individualmente.
- **3c:** priors G + macro G3 + probes H. GATE: lift ortogonal real (não proxy).
- **3d:** integrar confidence-count + cascade turn_state + route por-profile; fronteira completa vs baselines + null/jackknife/ano; regression-lock das estratégias aprovadas via API.
- **3e:** recorded_context (passivo) → só live com sign-off (Fase 7 do plano-mãe).

## 5. Apostas dos especialistas (onde concentrar)
- **Cortar FP:** C1+C2+C5 (aceitação vs rejeição) + F1 (dip vs flip) + E1/E2.
- **Velocidade:** B1+B2 (lead/divergência multi-TF) + B3 (micro-CHoCH) + B4 (CUSUM) + B6 (cross-asset lead).
- **Mais novo/promissor:** B4 CUSUM (a curva como algoritmo), B6 cross-asset lead (única info exógena), F1 (o 2º eixo), B2 (manufatura a curva com 2 relógios).
- **Baratos/ortogonais:** G1 hazard, G2 sessão.

## 6. Travas (cânone, reafirmadas)
Anti-look-ahead (close-only/SHIFT1/D-1/hour-causal; red-team gate) · réguas M8+Cris = só validação, NUNCA feature · sem bottom-picking (eixos = contexto/turn-state, não pivô) · sem OOS/cross-asset como GATE (cross-asset como FEATURE causal ok, validação dentro do ouro) · valida EIXO não cartesiano (n-adequacy) · confidence não-fitada · interpretativos (acceptance/grammar) só após null (faseado) · tick-volume só relativo · SMC/NAS/bubbles SHIFT1 voto-secundário · anti-oracle (nunca explica loser pós-fato). Detector único = consolidação; a COMBINAÇÃO confidence-graded é a aposta.
