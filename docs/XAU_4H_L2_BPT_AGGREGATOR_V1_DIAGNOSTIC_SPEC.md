# AGGREGATOR v1 — SPEC DIAGNÓSTICO (definido ANTES de rodar)

**2026-06-19.** Escopo: XAU_4H_L2_BPT_BOS_CHOCH. **Diagnóstico/laboratório, NÃO promoção.** Corrige os 6
erros do v0. Pesos/limiares = design v1 EXPLÍCITO e revisável, NÃO tunado ao outcome. Outcome só pós-hoc.

## Princípios (do bloco)
1. NAS deve ANCORAR o TAKE (não ser só +peso solto como no v0). 2. demand_supply+risk_sl = suporte estrutural
forte (âncora alternativa). 3. veto NÃO vai direto a SKIP salvo falha fatal. 4. veto comum REBAIXA para REVIEW.
5. capit+rsi = camada de refino / review-support (eleva REVIEW→TAKE só em contexto permitido), NÃO decisive.
6. bubbles, volume_vp, bull_beta, RSI isolado NÃO podem dominar. 7. Stage A orienta contexto, não decide só.
8. Objetivo = lucro prop-firm (expectancy × frequência, PF, DD/streak), não ultra-winrate.

## Definições de estado (fiel à Fase 2A/2B.5)
`state(i,s)` = veto se veto_count>0; review_flag se review_count>0 & neutral; senão net_read.

## Âncora (TAKE EXIGE ≥1)
- **Âncora A:** `nas == supportive`.
- **Âncora B:** `demand_supply == supportive AND risk_sl == supportive`.
TAKE sem âncora é PROIBIDO → impede TAKE dirigido só por bubbles/bull_beta/volume/RSI.

## Falha fatal → SKIP (só estas)
- `stage_a == late_top_exhaustion`; OU
- `exhaustion_top == hostile AND nas != supportive` (topo sem confirmação de fundo); OU
- `demand_supply == hostile AND risk_sl ∈ {hostile,veto}` (sem demanda defendida + risco ruim); OU
- sem âncora E `stage_a ∈ {bear_bounce, late_top_exhaustion}` E NÃO (capit&rsi) (bear/late sem nada).

## Veto comum → REBAIXA TAKE para REVIEW (não SKIP)
`devils_advocate == veto` OU `risk_sl == veto` OU `exhaustion_top == hostile` (não-fatal) → REVIEW.

## Decisão v1
1. Falha fatal → **SKIP**.
2. Com âncora:
   - veto comum → **REVIEW**;
   - contexto conflitante (`bear_bounce`/`mid_range_noise`) sem capit&rsi → **REVIEW**;
   - senão → **TAKE**.
3. Sem âncora:
   - capit&rsi em contexto permitido (não bear/late, risk não hostil, demand não hostil) + algum suporte → **REVIEW** (camada de refino);
   - algum suporte estrutural (nas/ds/rs supportive) → **REVIEW**;
   - nada → **SKIP**.
4. **Elevação capit+rsi (REVIEW→TAKE)** só se: já tem âncora + `stage_a ∈ {bottom_reversal_capitulation, demand_reclaim, bull_pullback_continuation, liquidity_sweep_reversal}` + sem veto comum + demand/risk não hostis. (Regime-bound, NÃO automático fora disso — coerente com a refutação OOS bear.)

## REVIEW = absorvedor de conflito real
sinais bons + risco ruim; fundo possível + contexto hostil; capit+rsi bom + regime incerto; NAS bom + supply/risk conflitante.

## Travas
Diagnóstico. Não promove, não cria regra/Telegram/produção, não altera engine/decisions_merged/registry-promoted.
