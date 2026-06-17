# XAU 4H L2/BPT — BOM Tiering & Supply-Risk Tradeoff

**Status:** `DIAGNOSTIC · HYPOTHESIS_ONLY · NOT_STRATEGY · NOT_VALIDATION` · **Data:** 2026-06-17
**RAW-only · sem backtest/PnL novo/filtro final/veto promovido/plotagem/MCP/produção/SLIM.**

> Correção conceitual: "supply nunca pode ser veto" foi rígido demais. Aqui mede-se **custo/benefício por tier**: um supply-veto pode ser aceitável **se só matar BOM fracos/sacrificáveis**.

---

## 1. Executive summary

Classifiquei os 17 BOM em tiers (fundamentado em `classe` do Ground Truth + R medido onde existe + força do candle) e testei 7 regras de supply-risk em **nível de evento**. Resultado-chave:
- **`supply ≤ 0.5 ATR` mata ZERO BOM** (nem A, B ou C) e corta **2/6 NAO + 415 UNKNOWN (−14%)**. → veto parcial **de custo zero** sobre os BOM conhecidos.
- **`supply_near≤1.0 + polarity_under_supply`** (categoria NAO-exclusiva) mata **0 BOM**, corta **2 NAO + 405 UNKNOWN**. → cirúrgico, custo zero.
- Subir para **`supply ≤ 1.0 ATR` mata 4 B-tier** (GT01, GT08, **GT17A**, **GT24** — 2 frágeis) → **não aceitável** sem revisão visual.
- **A-tier (monumentais) intactos em TODAS as regras.** **C-tier (GT13A/GT15/GT25) não são casos de supply-risk** (têm supply longe/céu limpo) → nenhuma regra de supply os sacrifica.

## 2. BOM tiers (`results/l2_bpt_bom_tiers.csv`)

| Tier | GT_ids | base |
|---|---|---|
| **A_TIER_PROTECT** (6) | GT02, GT03, GT18, GT21, GT23, GT27 | classe BIG_WINNER ou R medido ≥4 (GT03 11.5R, GT02 4.47R) |
| **B_TIER_PROTECT_IF_POSSIBLE** (8) | GT01, GT08, GT09, GT10, GT13B, GT17A, GT20, GT24 | winners sólidos (absorção clara) |
| **C_TIER_SACRIFICABLE** (3) | GT13A, GT15, GT25 | candle fraco/pequeno/atípico, sem R grande medido |

Caveat: **R só foi medido para GT02/GT03/GT20**; demais tiers usam `classe` + força do candle do GT = **julgamento/calibração, confirmar visual**. Frágeis (survivor único): GT13B, GT17A, GT23, GT24.

## 3. Supply-risk tradeoff (`results/l2_bpt_supply_risk_tradeoff.csv`, event-level)

| Regra | A | B | C | BOM mortos | NAO cut | UNK cut | risco |
|---|--:|--:|--:|---|--:|--:|---|
| **supply ≤ 0.5 ATR** | 0 | 0 | 0 | — | 2/6 | 415 | **LOW (custo zero)** |
| supply ≤ 1.0 ATR | 0 | 4 | 0 | GT01,GT08,GT17A,GT24 | 4/6 | 858 | MED (mata B + 2 frágeis) |
| supply ≤ 1.5 ATR | 0 | 6 | 0 | +GT13B,GT20 | 4/6 | 1203 | MED |
| supply_blocks_target_2ATR | 0 | 0 | 0 | — | 0 | 0 | inútil (não isola survivor) |
| supply_near1.0 + no_demand_support | 0 | 0 | 0 | — | 1 | 134 | LOW (cut fraco) |
| supply_near1.0 + no_origin_of_leg | 0 | 0 | 0 | — | 0 | 0 | inútil |
| **supply_near1.0 + polarity_under_supply** | 0 | 0 | 0 | — | 2/6 | 405 | **LOW (custo zero)** |

## 4. Fronteira aceitável

1. **Existe regra que corta muito ruído sem matar A-tier?** Sim — e mais: **sem matar NENHUM BOM**: `supply ≤ 0.5 ATR` (415 UNK + 2 NAO) e `supply_near1.0 + polarity_under_supply` (405 UNK + 2 NAO). A-tier intacto em todas.
2. **Existe regra que mata só C-tier?** **Não** — os C-tier têm supply longe/céu limpo; supply-rules não os tocam. Sacrificar C exigiria outro eixo (não supply).
3. **Supply veto parcial é aceitável?** **Sim, na borda tight (≤0.5 ATR)** — custo zero sobre BOM, corta 1/3 dos NAO conhecidos. Acima de 1.0 ATR começa a matar B-tier (incl. frágeis) → não aceitável sem visual.
4. **Hard veto, soft warning ou visual-priority?** As duas regras custo-zero → **soft_warning + visual_priority** (candidatas a hard-veto **após** Cris confirmar que: (a) os 2 NAO cortados são realmente losers, (b) o UNKNOWN cortado é ruído). Não promover a hard veto agora (NAO n=6).
5. **Quais BOM precisam ser plotados antes de decidir?** Os B-tier com supply colado que `≤1.0/1.5 ATR` mataria — **GT17A, GT24, GT13B** (frágeis) + GT01, GT08, GT20 — e o A-tier **GT23** (SUPPLY_BLOCKS_TARGET, fragile, supply 1.44 ATR, sobrevive mas por margem). Plotar para entender por que venceram coladas no supply.

## 5. Achados

- **Corrige a rigidez:** supply-risk **tight** (≤0.5 ATR) é veto-candidato de custo zero — a versão binária "supply existe" é que era inadequada, não a distância.
- O eixo que mata winners é **profundidade do veto** (0.5→1.0 ATR perde 4 B-tier). Manter tight.
- C-tier não é endereçável por supply; se um dia quisermos podá-los, o eixo é candle-quality, não supply.
- A-tier robusto a tudo (monumentais têm céu limpo ou supply distante).

## 6. O que precisa de visual review

GT17A, GT24, GT13B (frágeis, supply ≤1 ATR, venceram), GT23 (A-tier fragile, blocks_target), GT01/GT08/GT20 (B-tier supply colado). + amostra dos 2 NAO cortados por `supply≤0.5` para confirmar que são losers reais.

## 7. DA appendix

- Não tratou 17/17 como dogma absoluto? ✅ tiers + C sacrificável avaliados; mas achou que supply tight custa **zero** BOM (não precisou sacrificar ninguém).
- Não sacrificou BOM monumental? ✅ A-tier intacto em todas as regras.
- Não promoveu filtro final? ✅ tudo HYPOTHESIS_ONLY; recomendação = soft_warning/visual_priority.
- Não usou PnL inexistente? ✅ R só onde o GT mede (GT02/03/20); resto marcado julgamento.
- SLIM? ❌. Plotagem? ❌. Produção intacta? ✅. Caminho B? ❌.

**DA verdict: PASS — tiers fundamentados; supply-risk tight (≤0.5 ATR) corta 2 NAO + 415 UNK com custo ZERO de BOM; aprofundar o veto mata B-tier frágeis; A-tier robusto; nada promovido a veto final; produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_bom_tiers.csv`, `l2_bpt_supply_risk_tradeoff.csv`. Tiers = julgamento sobre GT (R medido só 3/17) — confirmar visual.*
