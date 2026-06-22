# LEG-STATE & LIQUIDITY-STRUCTURE SPECIALIST — SPEC

**2026-06-22.** Diagnóstico/calibração. Backbone estrutural do Macro Structural Reading Engine. **NÃO é
regra final TAKE/SKIP.** Strategy-agnostic (LONG/SHORT futuro). 62 = ensino. Sem outcome. Causal.

## 1. Objetivo
Classificar **em que LEG estrutural o mercado está** (o separador que entry-quality/momentum/extensão não
capturam, por design de Auction Theory) + detectar **estrutura de liquidez** (sweep/reclaim/grab). Backbone =
pivots causais; SMC BOS/CHoCH = sinal secundário esparso. Realista: bloquear bear-leg-longs robustamente +
flagar sweep-traps; aceitar resíduo de late-tops indistinguíveis (não overfit).

## 2. Inputs causais
- **Pivots/fractais (backbone):** fractal 3/3 e 2/2, swing high/low, range top/bottom, internal levels. Confirmação **capada em i** (`p+k ≤ i`, nunca futuro). Só pivots CONFIRMADOS. Sobre `raw_features` (bar_idx indexa direto, verificado).
- **SMC BOS/CHoCH (secundário, esparso ~41%):** smc_bos/smc_choch + bars_ago, causal por first-appearance/visibility-time (commit 1937d82). NÃO backbone exclusivo.
- **Supply/demand structure:** sup_cat, pol_cat, dist_supply/demand, broken/rejected, demand supported/retested, has_overhead.
- **Macro engine v1 evidences (9 especialistas, confluence_62.csv):** Supply/Demand/Volumetry/Multi-TF/Macro-Regime/Momentum/Capitulation/Fuel/Risk-SL — como evidência condicional.

## 3. Prior Failed Layers as Conditional Evidence (OBRIGATÓRIO — 18 camadas, commit 4770825)
**Tese: leg-state é backbone; camadas anteriores = evidência condicional de suporte/conflito DENTRO da leg-state.**
| Camada | Papel sob leg-state | Status |
|---|---|---|
| SMC+pivots | **backbone** (pivots HH/HL vs LH/LL + SMC shift) | ALIVE |
| Macro Engine v1 | leitor de contexto bull/regime | ALIVE |
| sup_cat/pol_cat | input 1ª classe (Supply) | ALIVE |
| SVP/volumetria | input 1ª classe (aceitação/distribuição) | ALIVE |
| has-overhead | gate condicional no Supply | ALIVE (nec.-não-suf.) |
| risk_sl/T34 | **eixo SEPARADO** (SL curto ≠ entrada ruim) | ALIVE |
| regime_B_v3 (30) / l1_v4 | Macro Regime (D-1, comportamento>nome) | ALIVE/RETEST |
| entry-quality | **2ª camada, só depois da leg** | SECOND_LAYER |
| dist_supply/dist_demand | condicional a leg + has_overhead + sup_cat | RETEST_UNDER_LEGSTATE |
| legpos | condicional a momentum + leg | RETEST_UNDER_LEGSTATE |
| Regime v0/v1 | features secundárias condicionais | RETEST_UNDER_LEGSTATE |
| capit+rsi | só em fundo/turn | CONTEXT_ONLY |
| Stage A | feature/evidência (não label-verdade) | WEAK_ISOLATED |
| Confluence v2 | **GUARD-RAIL**: nunca legpos p/ late-top; macro_broken só 3 casos | DEAD-as-rule/lição |
| macro_leg | REFERENCE_ONLY | DEAD/FORBIDDEN |
| hour_utc | session-time overfit | FORBIDDEN |
| demand_age | UNAVAILABLE | DEAD |

## 4. Leg-state (Tarefa 3)
Estados: BULL_LEG_HH_HL · BEAR_LEG_LH_LL · CORRECTIVE_BEAR_LEG · BULL_PULLBACK_WITH_HL_INTACT ·
BEAR_PULLBACK_TO_SUPPLY · RANGE_TRANSITION · REVERSAL_ATTEMPT · UNKNOWN_INSUFFICIENT_STRUCTURE.
Critério: últimos N pivots confirmados → sequência HH/HL (bull) vs LH/LL (bear); último swing-low violado
(bear) ou preservado (bull pullback); HL intacto. Só pivots confirmados (`p+k ≤ i`).

## 5. Liquidity structure (Tarefa 4)
Estados: NO_CLEAR_SWEEP · BUY_SIDE_SWEEP · SELL_SIDE_SWEEP · SWEEP_AND_RECLAIM · FAILED_BREAKOUT ·
LIQUIDITY_GRAB_REVERSAL_RISK · RANGE_LIQUIDITY_CHOP. Critério: wick acima de swing-high prévio + rejeição
(buy-side sweep, late-top risk); wick abaixo de swing-low + reclaim (sell-side sweep, bottom); SMC CHoCH/BOS
como confirmação secundária.

## 6. Cruzamento interpretável (Tarefa 5 — sem busca cega)
bull-leg+near-demand+supported=suporte · bear-leg+near-demand=TRAP · bull-leg+CLEAN_SKY+momentum=bom ·
bear-leg+CLEAN_SKY=não basta (relief) · bull-leg+high-legpos+momentum=saudável · bear/corrective+high-legpos+
supply-rejection=risco · bull-leg+supply-near-but-broken=markup · bear-leg+supply-near/rejecting=bearish ·
sweep+failed-reclaim=trap · sweep+reclaim+demand=reversal-possible · risk_sl=eixo separado · capit+rsi só em fundo/turn.

## 7. Output (auditável)
Por trade: leg_state · liquidity_state · structural_shift_state · sweep_state · confidence · supports ·
conflicts · reason_codes · feature_values · market_interpretation · prior_layers_used · prior_layers_conflicts · provenance_ok.

## 8. Travas
Diagnóstico; 62=ensino não fit-target; sem outcome/futuro; sem ID-fit; sem busca combinatória cega; não
descartar camadas por falha isolada; pivots só confirmados; SMC causal/esparso. Validação 276+OOS = bloco futuro.
