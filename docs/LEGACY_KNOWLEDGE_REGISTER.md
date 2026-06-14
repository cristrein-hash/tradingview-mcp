# LEGACY KNOWLEDGE REGISTER

**Criado:** 2026-06-14 · **Modo:** conhecimento, não validação.

## 1. Purpose

Este documento preserva **apenas o aprendizado reutilizável** extraído das estratégias/labs antigos **contaminados** (SLIM/proxy, look-ahead, outcome contaminado, rejeição visual/R-real) da era pré-XAU-4H-LONG.

Não valida, não ressuscita e não promove nenhuma estratégia antiga. Cada item abaixo só pode entrar no novo core **se reconstruído RAW-first, causal, com visual review e walk-forward**. Origem da contaminação registrada para rastreabilidade da lição.

Fontes: Caminho A/B antigos, Body60, Demand Breakout, Capitulation, BB Confluence, Auction labs, XAU 1H Demand/Reclaim (REVIEW_LATER), Pine antigos, Regime Classifier v3, Volume features, catálogo de 30 hipóteses.

## 2. Reusable Features (só RAW-first + causal)

1. **macro-location D1** — estratificar BULL_PULLBACK / BULL_EXPANSION / BEAR ANTES de qualquer eixo; lookup D-1 causal. (origem: layer stack XAU 4H LONG)
2. **ATR-normalized distance** — `ext_from_swinglow = (close − swing_low_confirmado)/ATR`; substitui price_pos (que era look-ahead). (Caminho A)
3. **zone distance / n_supply_zones** — contagem de oferta acima (Custom OB) = teto de distribuição. (Caminho A/B)
4. **NAS first-appearance** — NAS = LONG/SHORT via `pine_labels` por first-appearance entre snapshots; NUNCA TOP/BOTTOM, NUNCA NAS_*_SIGNAL numérico (decoupled). Confluência, não gate isolado.
5. **Bubbles polarity** — `pine_shapes_bubbles.activations` causais, BUY vs SELL separados (plot 0/2/4=BUY, 6/8/10=SELL, 12=POC); polaridade obrigatória (densidade cega mata winners). (Caminho B / teste bruto)
6. **SMC CHoCH/BOS/sweeps** — CHoCH internal vs swing distinguidos; Strong-Low-Sweep; EQL; Williams 5/5 SHIFT (confirma em p+5). (Caminho B G2 / L2 SMC)
7. **Session VP nativo** — POC/VAH/VAL por sessão diária (vaVolume 70, rows 24); VAL acceptance/bounce. (Volume features)
8. **volume exhaustion** — bear-leg exhaustion silenciosa (F1-F8) + climax-wash F9 (`vol≥1.5 AND (range≥1.8ATR OR lower_wick≥50% OR body_red≥70%)`). (Volume features V2)
9. **drop_20_atr** ⭐ — falling-knife filter (`≤ ~4.64`): quedas até ~4-5 ATR/20h = capitulação madura; acima = forced selling sem edge. (XAU 1H)
10. **BE@2R** ⭐ — breakeven quando MFE≥2R; preserva WR e tail, reduz DD pela metade. (XAU 1H) — e V_stair (exit em degraus). (Caminho B)
11. **maturity filters** — consec_lower_lows / sell_count_50 / drop cap; corta falling-knife sem matar V-bottoms. (XAU 1H L4)
12. **regime flags** — macro_broken / distribution_flag / stage_dir do classifier v3 (OHLC+MA, sem pine_boxes) — **com SHIFT1 obrigatório** (bias residual 10.68% flagrado). (Regime v3)
13. **time/session filters** — bar UTC (08/12/16 = premium; 00/02/18/20 = thin/dead hours). (Caminho B / slim antigo)
14. **cross-asset (a coletar)** — DXY exhaustion, US10Y, BTC risk-off, XAG/GDX capitulação. (catálogo 30 hipóteses, não testado)

## 3. Reusable Metrics (futuro validation engine)

1. **R-real** ⭐ — R realizado, nunca MFE teórico (matou slim-WR de Capitulation/Caminho A/B).
2. **MFE / MAE** por trade.
3. **hit_5R / hit_10R / hit_20R** — perfil de cauda (fat-tail).
4. **monumental-winner preservation** ⭐ — hard constraint; qualquer filtro que mate monumental = FAIL.
5. **max losing streak / max drawdown em R**.
6. **PF / avg_R / WR / n**.
7. **Wilson lower bound** ≥ 45% (IC95).
8. **regime segmentation** — performance por BULL/TRANSITION/BEAR/CAPITULATION.
9. **temporal concentration** — % do sumR por ano (>35% num ano = frágil); time-of-day concentration.
10. **jackknife top-N** — remover top-1/3/5; se sumR≤0 sem eles, não há edge.
11. **correlação entre trades** — gap<5 bars = não-independente (block bootstrap).
12. **winner-preserving threshold discriminator** ⭐ — mínimo dos winners = threshold; descobre filtros que preservam 100% dos winners.

## 4. Reusable Process Lessons (virar padrão)

1. **RAW/source-field map** — toda feature traçada ao campo RAW; nunca SLIM/proxy.
2. **CLOSE-ONLY-CAUSAL** — features só de bars fechados ≤ i; entry no close[i].
3. **SHIFT1 / no-lookahead audit** — indicadores que repintam + features daily/weekly usam D-1; rodar ORIG-vs-SHIFT1 antes de promover (delta WR>5pp ou sumR>30R = look-ahead).
4. **gate manifest** — pré-registrar gates (SHA-locked) ANTES de rodar; nome ≠ definição.
5. **visual audit 100%** — revisão visual auction-theory antes de qualquer promoção.
6. **walk-forward / external window** — TRAIN/VAL/TEST + janela virgem/cross-asset; 45-grupos = calibração, NUNCA validação.
7. **rejection reason taxonomy** — registrar porquê (visual / R-real / look-ahead / SLIM / sample).
8. **safety pack + manifest + checksums** — copiar → MANIFEST → SHA256SUMS → `shasum -c`.
9. **name ≠ definition check** — comparar componentes citados vs definição interna antes de regenerar.
10. **macro-location-first** — estratificar D1 antes de eixos pooled; ancorar em ENTRY (nunca outcome); Devil's Advocate full-time; 15-problem methodology checklist (≥12/15 promover).

## 5. Reusable Code Candidates

**REUSE_AS_IS**
- `repo_root()` helper (resolução robusta de raiz do repo).
- `price_to_ticks_offset()` (plot canônico long_position; stop/target em ticks).
- Custom OB Pine v11/v12 (indicador-fonte de `pine_boxes`; não é estratégia).

**REUSE_AFTER_REWRITE**
- `_normalize_indicator_parsed` (PEPPERSTONE hard-gate + whitelist + provenance).
- Extração RAW causal (NAS first-appearance, bubble activations, swings 5/5 SHIFT, at_d1_demand v2, guarda 1D↔4H).
- regime_B_v3 classifier (OHLC+MA) — só com SHIFT1.
- Signal Outcome Lab evaluator (seed limpo do outcome engine).
- V_stair stepped-exit / BE@2R / winner-preserving discriminator.

**IDEA_ONLY**
- Combos de capitulação (cluster NAS + RSI_1D + ATR); demand-OB reclaim; BB-confluence intraday; 19 hipóteses não testadas (DXY/FOMC/1H stabilization).

**DO_NOT_REUSE**
- Detectores/score-filters baseados em SLIM.
- `enrich_indicator_outcomes` (bare-ticker → OANDA).
- `is_supertrend` (close mesmo-dia) e anchor-by-outcome (leak de trade-pai).

## 6. Do Not Repeat

1. Validar/calibrar threshold por **SLIM/proxy** (inflou 5-10× vs RAW).
2. Usar **thresholds contaminados** (calibrados em slim) sobre RAW.
3. **Same-day daily lookahead** (feature daily do dia ds dentro de bar 4H).
4. **Anchor by outcome** — ancorar em winner cujo resultado só se sabe no exit futuro.
5. **Bubbles sem polaridade** — densidade cega bloqueia BUY-bubbles (que favorecem long) → mata winners.
6. **NAS SHORT como veto isolado** perto de bull forte — é absorção, não distribuição → mata monumentais.
7. **Filtros que matam monumental winners** — quase todo filtro pré-entrada corta o tail; exigir preservação 100%.
8. **Strategy name sem verificar a definição real** (gates reais ≠ nome).
9. Cortar **"bear daily regime" hard** (mata monumentais); rescue de deep-drop >4.64 ATR (sem edge recuperável); separar good/bad no miolo BULL_EXPANSION por NAS/Bubbles no entry (irredutível → REVIEW/gestão).

## 7. Boundary Rule

**Este arquivo preserva aprendizado, não estratégias.**

Nada aqui pode validar uma estratégia. Qualquer feature, métrica, processo ou trecho de código só entra no novo core **após reconstrução RAW-first, causal, com visual review e walk-forward**. Estratégias antigas permanecem fora do core e em QUARANTINE/DELETE_CANDIDATE conforme o boundary a definir. XAU 1H LONG permanece REVIEW_LATER (não destruir). A era contaminada sobrevive apenas como este registro de lições.
