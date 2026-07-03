# LAB E — SLIPPAGE/COST · RELATÓRIO FINAL (2026-07-03)

## 1. Executive verdict

**COST_ROBUST** — pelo prereg §7 aplicado como escrito (decisão de rótulo corrigida pelo DA: meu rótulo candidato "COST_SENSITIVE" era desvio pós-hoc conservador). **Com caveat obrigatório:** fragilidade concentrada em 2024/trades de risco-$ baixo, sob modelo $-constante que SUPERESTIMA o custo da era 2024 (direção do erro contra a estratégia — declarada).

## 2. Baseline reproduction

S0 reproduz o painel aprovado exatamente: **N435 · WR47,6% · +291,5R · avgR0,670 · DD−11,0 · r/DD26,58 · streak−8 · 39,7/213,6/38,3**. Verificado 2×: fail-loud do script + reprodução independente do DA (letrun 435/435).

## 3. Scenario table (round-trip $ constante/trade; custo_R = $/risk_$ por trade)

| Cenário | $RT | WR | sumR | avgR | maxDD | r/DD | 2024/2025/2026 | flips | runners | custo med (R) |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 baseline | 0,00 | 47,6% | +291,5 | 0,670 | −11,0 | 26,58 | 39,7/213,6/38,3 | 0 | 53 | 0 |
| SA low | 0,40 | 47,1% | +262,6 | 0,604 | −12,6 | 20,83 | 26,6/198,5/37,5 | 2 | 52 | 0,049 |
| **SB mid (realista)** | **0,80** | **46,0%** | **+233,6** | **0,537** | **−14,2** | **16,40** | **13,6/183,4/36,6** | **7** | **51** | **0,098** |
| SC high | 1,50 | 44,1% | +183,0 | 0,421 | −20,9 | 8,75 | **−9,3**/157,1/35,2 | 15 | 51 | 0,183 |
| SD stress | 3,00 | 41,4% | +74,4 | 0,171 | −84,8 | 0,88 | −58,2/100,6/32,0 | 27 | 48 | 0,366 |

## 4. Impacto sumR/DD/rDD

SB (realista): retém **80,1%** do sumR, r/DD 26,6→**16,4**, DD −11→−14,2 — degradação material mas dentro dos limiares pré-registrados. SC quebra 2024; SD destrói (registrados como **SENSIBILIDADE**, cláusula stress do prereg — não invalidação).

## 5. Annual sensitivity

**2024 é o ano vulnerável** (risk_usd mediano $5,04 vs $24,29 em 2026 → custo em R ~5× maior): SB-2024 retém só 34% do bruto (13,6/39,7); +$0,70 adicionais flipam o ano. 2025/2026 robustos em todos os cenários exceto stress. Nota DA: custo proporcional-ao-preço (~1,6bp) daria 2024-SB ≈ +26 — o modelo atual é o limite superior do dano.

## 6. Trade-level sensitivity

Fragilidade localizada: quartil de menor risco-$ de 2024 (35 trades, risk_usd ≥ min $1,01) paga 23,5R dos 48,9R de custo do ano e contribui +0,5R bruto. Flips totais no SB: só 7/207 winners. **Runners praticamente imunes:** 53→51 no SB (risco-$ deles é grande; custo em R pequeno) — a convexidade da estratégia É a defesa contra custo.

## 7. DA findings

Ver `XAU_15M_LONG_LAB_E_SLIPPAGE_COST_DA_20260703.md`: mecânica toda verificada independentemente (sem dupla contagem; mapeamento 435/435; baseline; monotonicidade; prereg honrado); correção de rótulo para COST_ROBUST; caveat 2024 obrigatório; modelo declaradamente conservador. DA **não commitou** (regra de governança cumprida).

## 8. O que muda para os Labs A/B/C/D

- **Lab A (trigger geometry) — segue lever nº 1, com requisito NOVO:** confirmação mais barata → risco-$ menor por trade → **custo em R por trade AUMENTA** (é exatamente a população custo-frágil que E expôs). Lab A **deve embutir o cenário SB no desenho desde o início** (painel líquido, não bruto, como critério).
- **Lab B (eliminação por contexto):** custo-neutro-a-positivo (reduz N mantendo runners); prioridade inalterada; avaliar em R líquido SB.
- **Lab C (SL_CONTEXT):** SL mais largo → risco-$ maior → custo em R menor por trade, MAS risco prop-firm maior — trade-off agora quantificável em líquido.
- **Lab D (re-entry):** cada re-entry paga round-trip adicional — null de D deve descontar custo SB por tentativa.
- **Regra transversal nova:** todo lab futuro da 15M reporta painel **bruto E líquido-SB ($0,80)**.

## 9. O que este lab NÃO prova

Não aprova produção (zero fills reais; sem custo por sessão) · não é OOS (calibração, mesmos 435) · nada sobre SHORT · nada sobre o gap RAW pós-2026-05-25 · baseline segue idealizado (fill close/trail exato) · concentração 2025 herdada · custos não calibrados em fills próprios (plausibilidade declarada no prereg).

## 10. Recommendation

- **OFICIAL_FN — condição de custo: PASSED** (COST_ROBUST no cenário realista). **O status OFICIAL_FN em si NÃO é marcado aqui** — exige aprovação explícita do Cris (única pendência técnica do checklist foi cumprida; decisão de oficializar é dele, incl. se quer calibração de custo em fills reais antes).
- **Próximo lab: A (trigger geometry)** — mantém-se o lever nº 1 da maturação, agora com o requisito de painel líquido-SB embutido. B em seguida. C/D depois, informados por E.
