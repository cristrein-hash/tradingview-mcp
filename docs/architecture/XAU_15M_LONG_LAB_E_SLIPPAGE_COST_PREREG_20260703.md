# LAB E — SLIPPAGE/COST · PRÉ-REGISTRO (2026-07-03, ANTES de qualquer cálculo)

**Bloco:** XAU_15M_LONG_LAB_E_SLIPPAGE_COST · research-only · autorizado por Cris no lab plan aprovado (ordem E→A→B→C/D).

## 1. Strategy scope
`XAU 15M LONG · swept-runner base #4 FINAL hour-causal` — **LONG only** (split canon) · N435 · detector **v5 retido intacto** · nenhum gate/filtro/entrada muda · no SHORT · no production · cobertura 2024-05-25→2026-05-25.

## 2. Source/data mapping
- **Input trade set:** os 435 trades derivados do engine aprovado REAL (`engine_substrate4_v5_hourcausal.py` via exec — mesma técnica dos plots/leitura; seleção `cand[v5h≠BEAR]`).
- **Source lineage (RAW-only, zero SLIM):** RAW gz HD → `build_causal_primitives.py` → `primitives/*.json` (+bubbles/htf) → engine. Source guard mecânico ativo no dir.
- **Fields por trade:** `cj_t` (entry time) · `entry` = close@cj ($) · `sl` = flush−0,1ATR ($) · `risk_$ = entry−sl` · `R` (let-run realizado, adimensional) · `yr` · regime v5h. Tick 0.01 (XAUUSD Pepperstone).
- **Conversão custo→R:** POR TRADE, via risco em $: `cost_R_i = cost_$_roundtrip / risk_$_i`; `R_net_i = R_i − cost_R_i`. Honesta porque risk_$ é conhecido por trade (entry/sl reais); **não finge microestrutura** (sem book/fill data — limitação declarada §8).

## 3. Cost model (cenários FIXADOS antes do cálculo — não escolher por resultado)
Custo = **$ por round-trip** (spread entry + slippage entry + slippage exit), constante por trade (sem diferenciação por sessão — declarado; Ásia tende pior, sem dados de fill para modelar):
- **S0 baseline:** $0,00 (controle — deve reproduzir painel aprovado)
- **SA conservative-low:** $0,40
- **SB conservative-mid:** $0,80
- **SC conservative-high:** $1,50
- **SD stress:** $3,00

Referência de plausibilidade (declarada, não calibrada em dados próprios): spread típico XAUUSD Pepperstone razor ~$0,05-0,20 + slippage de mercado em 15M; SB≈custo realista de trabalho; SD=stress deliberado.

## 4. Exact predicates
População = **os mesmos 435** (assert) · nenhuma exclusão pós-hoc · LONG only · todos os anos · regime v5 atual · **sem novo filtro, sem nova entrada, sem re-otimização**. Único cálculo: subtração de custo por trade.

## 5. Metrics (por cenário)
N · WR (R_net>0) · sumR · avgR · maxDD · r/DD · breakdown anual (2024/2025/2026) · worst losing streak · **flips** (trades que cruzam de R>0 para R_net≤0) · runners (R_net≥3) preservados/impactados · sensibilidade por bucket de R bruto (≤−0,5 / −0,5..0 / 0..1 / 1..3 / ≥3) · custo médio implícito em R por cenário/ano.

## 6. Sanity checks (fail-loud)
N=435 em todos os cenários · S0 reproduz **N435 WR47,6% +291,5R avgR0,670 DD−11,0 r/DD26,58 streak−8/+6 · 39,7/213,6/38,3** (ou parar e documentar mismatch) · sumR estritamente decrescente S0→SD · nenhum cenário melhora nada · nenhum gate/trade/data muda.

## 7. Acceptance criteria (definidos ANTES)
- **COST_ROBUST:** SB (realista) mantém lucro forte e r/DD aceitável (guia: sumR_SB ≥ ~70% do baseline e r/DD_SB ≥ ~10, todos os anos positivos).
- **COST_SENSITIVE_BUT_STILL_VALID:** SB positivo mas com degradação material (ano negativo ou r/DD < 10) — OFICIAL_FN condicionado a discussão.
- **COST_FRAGILE:** SB destrói edge (sumR ≤ ~30% do baseline ou r/DD < 5 ou ano fortemente negativo) — OFICIAL_FN bloqueado.
- Se **apenas SD (stress)** destruir: registrar como SENSIBILIDADE, não invalidação.
- BLOCKED_BY_DATA_MAPPING se o mapeamento §2 falhar.

## 8. Forbidden interpretations
Não usar para aprovar produção · não é OOS · não reotimizar gates · **não escolher cenário de custo por conveniência pós-resultado** · não extrapolar para SHORT · não concluir sobre o gap RAW pós-2026-05-25 · não fingir precisão microestrutural (modelo $ constante/round-trip declarado).

## Outputs (pequenos)
`research/xau_15m_bb_nas_leonardo/results/lab_e_slippage_cost_results.csv` (linhas = cenário×ano + cenário total) · `.../lab_e_slippage_cost_summary.json`. Script: `research/xau_15m_bb_nas_leonardo/lab_e_slippage_cost_analysis.py` (determinístico, fail-loud no baseline).
