# XAU 4H L2/BPT — DYNAMIC MULTI-FACTORIAL MARKET READING STATE MACHINE (design spec)

**2026-06-22.** Design ANTES de rodar números. Substitui o erro recorrente (snapshot de eixo único na barra i)
por uma leitura DINÂMICA multi-fatorial de TRAJETÓRIA — a máquina que o macro engine deveria ter sido (e colapsou
num flag bull estático). Causal (só barras passadas até a entrada). Avaliada nos DOIS objetivos. DIAGNÓSTICO.

## 0. Princípio (o que corrige a miopia)
- Cada sub-estado vem de uma **TRAJETÓRIA** (janela de lookback de barras passadas), NUNCA de um snapshot na barra i.
- A leitura é a **CONVERGÊNCIA** de sub-estados ortogonais, NUNCA um fator isolado.
- Avalia **DOIS objetivos**: (A) capturar convexidade (não skipar runner) E (B) evitar topo (cortar loser/DD/streak).
- Usa o conjunto quantificado COMPLETO (84-feat + SVP + bubbles + NAS + SMC), não fatia fina.
- Valida por null/sub-janela DENTRO dos 276 — calibração ≠ validação.
- **markup-vs-rejeição é DINÂMICO** (preço aceita acima da oferta *ao longo do tempo* vs é empurrado de volta) —
  por isso o `supply_category` na barra i deu flat; a trajetória de interação é o que carrega o sinal.

## 1. Os 6 sub-leitores DINÂMICOS (cada um = máquina de estados de trajetória, causal)

**(1) SUPPLY INTERACTION (markup vs rejeição — núcleo dinâmico).**
Sobre lookback L (≈12-20 barras 4H), rastrear a oferta overhead mais próxima: sequência de toques e desfecho
(aceito = fecha e segura acima / rejeitado = empurrado de volta). Estados: `MARKUP_ACCEPTED` (rompeu e segura acima),
`MARKUP_BREAKING` (rompendo agora), `TESTING` (tocando, indeciso), `REJECTING` (rejeitado ≥2× no lookback), `CLEAR`.
Inputs: `supply_broken_before`, `supply_rejected_before`, `reclaim_dist_from_supply_atr`, `dist_4h_supply_low_atr`,
`has_4h_supply_overhead` + DERIVAR do path: nº de barras fechando acima/abaixo da oferta no lookback, recência do rompimento.

**(2) LEG MATURITY / MOMENTUM TRAJECTORY.**
Perna jovem ou exausta? Estados: `YOUNG_IMPULSE`, `MID_LEG`, `LATE_EXTENDED` (legpos alto + desacelerando),
`EXHAUSTED` (legpos>90 + momentum neg + rsi_bear_div). Inputs: `legpos30/60/90` (trajetória: convergindo alto = tarde),
`slope20_atr` desaceleração, `consec_up`, `rsi_bear_div_20b`, `trend_30_atr` + DERIVAR: rise20-agora vs rise20-prévio.

**(3) PULLBACK CHARACTER (acumulação vs distribuição — dinâmico).**
O pullback/reclaim está sendo COMPRADO ou DISTRIBUÍDO? Estados: `BOUGHT_DIP` (raso, reclaim rápido, buy bubbles),
`DEEP_RECLAIM`, `DISTRIBUTION` (lower highs no lookback, sell bubbles, reclaim fraco). Inputs: `reclaim_body_atr`,
`drop20_atr`, `bub_buy_*` vs `bub_sell_*` (sequência), + DERIVAR: lower-highs no lookback.

**(4) CAPITULATION / REVERSAL (dinâmica de fundo — ONDE OS RUNNERS SE ESCONDEM, achado da inversão).**
Estados: `CLIMAX_RECLAIM` (flush + oversold + reclaim), `FALLING_KNIFE` (flush sem reclaim), `BOTTOM_FORMING`, `NONE`.
Inputs: `drop20_atr`, `rsi_min8`, `reclaim_body_atr`, `demand_origin_of_leg`/`demand_touched_on_retest`. **Eixo prioritário:
o teste de estados aprendidos mostrou STRONG_BEAR_CONFIRM/CORRECTIVE_BEAR_LEG com runner-lift 1.25-1.36 — os monstros
vêm de reversão, e os engines liam ao contrário.**

**(5) REGIME BACKBONE (contexto lento — CONDICIONA, não gate).**
`BULL` / `BEAR_MARKDOWN` / `RANGE`. Inputs: `macro_reader_leg`, `regime_B_v3` (D-1), weekly slope. Backbone que muda
o SIGNIFICADO dos sub-estados (supply-near em BULL = markup; em RANGE/topo = rejeição).

**(6) VOLUME ACCEPTANCE (SVP, dinâmico).**
`ACCEPTING_ABOVE_VALUE` / `IN_VALUE` / `REJECTED_BELOW`. Inputs: `below_VAL` (trajetória), `dist_POC_atr`, `dist_VAL_atr`, `va_width_atr`.

**(7) BEAR-LEG BUY LEGITIMACY (Cris) — perceber COMPRA LEGÍTIMA em bear leg vs trap. CAMADA CRÍTICA.**
Dentro de um bear leg (regime BEAR_MARKDOWN ou macro_broken), distinguir DINAMICAMENTE:
- `LEGITIMATE_BEAR_BUY`: fundo/reversão real se formando DENTRO do bear — o bear leg está **EXAURINDO** (down-slope
  achatando, cascade_score subindo, oversold extremo) + capitulação-climax + reclaim com corpo + demand defendida +
  rsi_bull_div. SÃO os V-reversals (E1/E17 COVID) = runners que vivem em contexto bearish (reconcilia o achado da inversão).
- `BEAR_PULLBACK_TRAP`: dead-cat/pullback dentro de bear leg AINDA IMPULSIVO — sem capitulação, supply rejeitando acima,
  momentum ainda bearish, down-slope ainda íngreme. São losers.
O discriminador é a **DINÂMICA do bear leg**: exaurindo (compra legítima) vs impulsivo (trap). Inputs: `drop20_atr` +
`reclaim_body_atr` + `rsi_bull_div_20b` + `rsi_min8` + demand defendida + DERIVAR do path: desaceleração do down-slope
(slope-agora vs slope-prévio), recência/profundidade do flush, cascade trajectory do regime_B.
**Por que é crítica:** o `bear_leg_block` (lift 1.63) era o único layer que separava, MAS é bloqueio CEGO — cortaria
os E1/E17. Esta camada REFINA: bloqueia BEAR_PULLBACK_TRAP, PRESERVA LEGITIMATE_BEAR_BUY → recupera os runners que o
block cego corta E mantém o corte de losers. Ataca diretamente "winners skipados em contexto bear".

## 2. A leitura CONVERGENTE (per-episódio, condicionada ao regime) — 7 sub-leitores
- `REVERSAL_RUNNER`: capit CLIMAX_RECLAIM/BOTTOM_FORMING + demand defendida + NOT bear-markdown-confirmado → espera runner.
- `LEGITIMATE_BEAR_BUY` (camada 7): EM bear leg, mas bear EXAURINDO + capit-climax + reclaim + bull_div → runner em contexto bear (E1/E17).
- `MARKUP_CONTINUATION`: supply MARKUP_ACCEPTED/BREAKING + leg YOUNG/MID + pullback BOUGHT_DIP + acceptance acima → continuação runner.
- `TOP_TRAP_AVOID`: supply REJECTING + leg LATE_EXTENDED/EXHAUSTED + pullback DISTRIBUTION → loser, EVITAR (o que o filtro de supply É PARA).
- `BEAR_PULLBACK_TRAP` (camada 7): EM bear leg AINDA impulsivo + sem capit + supply rejeitando → loser, EVITAR.
- `AMBIGUOUS`: misto → review.
A convergência (≥2-3 sub-estados concordando) define a leitura; um sub-estado isolado nunca. Note que LEGITIMATE_BEAR_BUY
e BEAR_PULLBACK_TRAP ocupam o MESMO contexto bruto (long em bear leg) — separados SÓ pela dinâmica (exaurindo vs impulsivo).

## 3. Avaliação DUPLO-OBJETIVO (within 276, null + sub-janela)
- **(A) Convexidade:** REVERSAL_RUNNER + MARKUP_CONTINUATION → runner-rate (MFE≥5) vs base 26.1% (lift>1).
- **(B) Top-avoidance:** TOP_TRAP_AVOID → loser-rate (MFE<2) vs base 60.9% E runner-cut BAIXO (poupa runner). **Isto ataca o
  Lstreak-16 / maxDD-28.9 que o let-run deixou aberto** = a outra metade dos dois gargalos acoplados.
- Deve **bater os baselines estáticos**: supply_reject lift 1.08, bear_leg 1.63. Se a versão dinâmica não bate o
  estático, o sinal não é dinâmico → reportar honesto.
- null permutation + P1/P2 sub-janela. realR uncapped (let-run/V-stair) como régua, nunca capado.

## 4. Limitação de dados (declarada)
Micro intra-4H NÃO existe (frozen é 4H) — então sweep/aceitação intra-barra é FEATURE_UNAVAILABLE. PORÉM a trajetória
INTER-barra 4H sobre o lookback É construível do frozen path (causal, barras passadas) — a máquina opera em resolução
de trajetória 4H. NÃO prometer micro que não temos.

## 5. Guardrails anti-miopia (baked no design)
NÃO snapshot · NÃO eixo isolado · NÃO objetivo único · NÃO fatia fina de features · NÃO calibração-como-validação ·
markup/rejeição SEMPRE como trajetória condicionada a regime · prior layers vivas como evidência condicional.
Próximo: implementar os 6 sub-leitores do frozen path + a convergência + a avaliação duplo-objetivo. Sem promoção, sem OOS.
