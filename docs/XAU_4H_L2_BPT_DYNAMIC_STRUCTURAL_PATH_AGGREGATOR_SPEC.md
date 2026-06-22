# XAU 4H L2/BPT — DYNAMIC STRUCTURAL PATH AGGREGATOR (DSPA) — design spec

**2026-06-23.** Engine AGREGADOR de segunda ordem (Cris), ACOPLADO ao Macro Structural Reading Engine, NÃO sucessor.
"O Macro Engine lê o ESTADO; o DSPA lê a TRAJETÓRIA que produziu o estado." Consome Macro Engine + Indicator Engine +
prior layers como EVIDÊNCIA CONDICIONAL e adiciona features de trajetória 4H/1D do path contíguo. Mandato: resolver
mislabels (skip-winners→TAKE, loser-takes→SKIP) preservando big winners e monumentais. Causal. Base 276. realR uncapped.
Multi-fatorial (satisfaz anti-miopia por design). DIAGNÓSTICO; sem produção/promoção/OOS. NÃO descartar camadas anteriores.

## Arquitetura (5 camadas)

### Camada 1 — FEATURE FOUNDATION / PATH DERIVATION (o que falta — features NOVAS de trajetória 4H/1D)
Derivadas do path CONTÍGUO (frozen 4H `raw_features_2020_2026.jsonl`; 1D `repro_recovery/XAU_1D_ohlc.jsonl`; SVP nativo
`XAUUSD_4H...SVP_LUX_RAW`). Todas CAUSAIS (só barras ≤ entrada). Lookback L padrão = 12-20 barras 4H.
1. **Liquidity sweep / sweep-then-reclaim** — pivots Williams 5/5 no path 4H; o preço VARREU (wick abaixo) uma swing-low
   anterior no lookback e FECHOU de volta acima (sweep+reclaim)? → `swept_low_reclaimed` (bool) + profundidade do sweep
   (ATR) + bars-since. Espelho p/ swing-high (supply). **Provável discriminador #1 do legitimate-buy vs trap.**
2. **Flush geometry (V vs grind)** — o down-move até a entrada: velocidade (range/barras) + consec-down + range-expansion
   → `FLUSH_V` (rápido, capitulação) / `GRIND_DOWN` (lento, distribuição) / `NO_FLUSH`.
3. **Multi-bar acceptance/rejection** — p/ o supply/demand 4H mais próximo: nº de closes acima/abaixo no lookback +
   wick-rejections + desfecho do re-test → `ACCEPTED_ABOVE` / `REJECTED` / `TESTING` (a "aceitação" que eu achei precisar
   de 1H, mas é visível em múltiplas barras 4H).
4. **Swing structure HH/HL/LH/LL** — sequência de pivots 4H → `STRUCTURE_UP` (HH+HL) / `STRUCTURE_DOWN` (LH+LL) /
   `STRUCTURE_RANGE` / `STRUCTURE_BREAK` (BOS/CHoCH causal do path, complementa o snapshot LuxAlgo).
5. **Dealing-range position (premium/discount)** — posição na range corrente (swing-high↔swing-low) → `PREMIUM` /
   `EQUILIBRIUM` / `DISCOUNT`; versão diária (1D range).
6. **SVP/POC/VAL path** — aceitação relativa ao valor ao longo do lookback (SVP nativo) → accepting-above / below-value / at-POC.
7. **regime_B_v3 TRAJECTORY** — combined_score slope + cascade trajectory + onset de distribution_flag ao longo do lookback
   (NÃO campo isolado; 28 campos untested viram trajetória).
Output Camada 1: `results/l2_bpt_dspa_path_features_276.csv` (por episódio, todas causais).

### Camada 2 — MACRO STRUCTURAL READING ENGINE (estados aprendidos, como INPUT/evidência condicional)
supply/demand · macro_state · capit/reversal · momentum/exhaustion · SVP · risk/SL · clean-sky/has-overhead ·
**bear-leg refined loser-cut** (já aprovada). Reusa `l2_bpt_full276_macro_engine_confluence.csv`. NÃO re-derivar.

### Camada 3 — INDICATOR / AUCTION CONFIRMATION ENGINE (evidência contextual)
NAS · bubbles (polaridade context-aware) · SMC BOS/CHoCH · RSI/divergence · SVP acceptance. Reusa
`l2_bpt_full276_indicator_engine_cross_v2.csv`.

### Camada 4 — DSPA (o novo cérebro) — lê TRAJETÓRIA, não "feature X separa?"
Pergunta: **que trajetória o mercado está construindo?** Classifica em estados de trajetória (convergência das camadas 1-3):
`legitimate_bear_leg_buy` · `bear_pullback_trap` · `markup_through_supply` · `supply_rejection` · `V_flush_reversal` ·
`grind_down_continuation` · `bull_pullback_continuation` · `range_chop_no_followthrough` · `top_risk_residual`.
Ex. de convergência: legitimate_bear_leg_buy = regime BEAR + swept_low_reclaimed + FLUSH_V + reclaim aceito + demand
defendida; bear_pullback_trap = regime BEAR + NO sweep + GRIND_DOWN + supply rejeitando + sem reclaim.

### Camada 5 — OUTPUT INTERMEDIÁRIO (NÃO TAKE/SKIP direto)
`TAKE_CANDIDATE` · `SKIP_STRUCTURAL` · `PRESERVE_RUNNER_RISK` · `LOSER_CUT_CANDIDATE` · `AMBIGUOUS_PATH` · `NEEDS_NEW_DATA`.
Mapa: legitimate_bear_leg_buy→PRESERVE_RUNNER_RISK; bear_pullback_trap→LOSER_CUT_CANDIDATE; markup/V_flush_reversal→
TAKE_CANDIDATE; grind_down/supply_rejection→SKIP_STRUCTURAL; range_chop→AMBIGUOUS_PATH; path indisponível→NEEDS_NEW_DATA.
**Conversão para policy (TAKE/SKIP) = etapa POSTERIOR**, só depois de validar a leitura de trajetória.

## Validação (mislabel correction, base 276, com guards)
Régua = skip-winners (runner MFE≥5 hoje em SKIP) recuperados + loser-takes (loser MFE<2 hoje em TAKE) cortados, em R
UNCAPPED (let-run). **Recall-gate: 0 monumentais skipados.** null/permutation + sub-janela P1/P2 DENTRO dos 276.
Multi-fatorial (Camada 1 É trajetória → satisfaz anti-miopia). Prior engines como evidência condicional, nunca autoridade
isolada. Comparação estagiada: Camada 1 sozinha / +Camada 2-3 / +convergência DSPA — isolar o que a trajetória adiciona.

## Sequência de implementação
1. **Camada 1 PRIMEIRO** (path features) — é o que não temos; sem isso o agregador não tem o que agregar de novo.
2. Smoke + sanidade causal (sem leak) das 7 famílias.
3. Camada 4 convergência → Camada 5 output intermediário.
4. Validação mislabel + comparação estagiada + DA.
5. Só então (etapa posterior) policy TAKE/SKIP.

## Travas
NÃO substituir camadas anteriores · prior layers vivas como evidência condicional · NÃO eixo único (convergência) ·
trajetória NÃO snapshot · dois objetivos (recuperar runner E cortar loser) · recall monumentais · null/sub-janela ·
realR capado nunca árbitro · sem produção/OOS/promoção · NEEDS_NEW_DATA é estado honesto (não forçar leitura onde falta path).
