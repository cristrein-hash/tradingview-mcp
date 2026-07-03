# LAB E — DA ADVERSARIAL (2026-07-03)

DA independente (subagente real; script de verificação `research/xau_15m_bb_nas_leonardo/_DA_lab_e_attack.py`; **não commitou nada** — regra de governança cumprida). Script principal não alterado.

## Verificações mecânicas — TODAS PASSARAM
1. **Sem dupla contagem:** `letrun` do engine é 100% frictionless (entry=close cj, exit=trail exato, zero spread/comissão embutido) → a subtração do lab é a única fricção.
2. **Mapeamento risk_usd verificado trade a trade:** o risco de `rmap` colidir (row errada → SL errado) foi testado — 0 cj_t duplicados; `letrun` re-executado da row mapeada **reproduz o R do engine em 435/435**. SB re-computado independentemente bate byte a byte com o summary.
3. **Baseline reproduz** (N435 WR47,6 +291,5 DD−11 r/DD26,58) · monotonicidade estrita · N constante · streak estável.
4. **Prereg respeitado:** 5 cenários pré-fixados, todos reportados (incl. SD r/DD 0,88); métricas completas; fail-loud no código; sem seleção pós-hoc.

## Achados do DA
- **Modelo $-constante é CONSERVADOR contra a estratégia em 2024:** aplica custo de era-2026 (ouro ~$5000) a trades de 2024 (~$2400; risk_usd med $5,04 vs $24,29 em 2026). Custo proporcional ao preço (~1,6bp) daria 2024-SB ≈ +26 em vez de +13,6 e o flip do SC-2024 provavelmente some. Direção do erro declarada: superestima dano.
- **Fragilidade real e localizada:** quartil de menor risco-$ de 2024 (35 trades) paga 23,5R dos 48,9R de custo do ano e contribui +0,5R bruto — trades quase-breakeven de risco minúsculo são custo-frágeis (física real; magnitude = limite superior).
- **Correção de rótulo:** aplicando o §7 do prereg como escrito ao SB ($0,80): sumR 233,6 = **80,1%** do baseline (≥70% ✓) · r/DD **16,4** (≥10 ✓) · **todos os anos positivos** ✓ → **COST_ROBUST**. Rotular "COST_SENSITIVE" seria desvio pós-hoc do prereg (conservador, mas desvio).
- **Caveat obrigatório que sobrevive:** 2024-SB retém só 34% do bruto; +$0,70 de custo flipa o ano — margem fina.

## O que o lab NÃO prova (mantido integralmente)
Produção (zero fills reais; sem custo por sessão — Ásia pior) · não é OOS (calibração nos mesmos 435) · nada sobre SHORT · nada sobre gap RAW pós-2026-05-25 · não valida o baseline idealizado (fill no close/trail exato) · custo não calibrado em fills próprios · concentração 2025 (183R/233R no SB) herdada, não resolvida.

## Veredito recomendado pelo DA
**COST_ROBUST** (pelo prereg §7 como escrito), com caveat 2024/risco-$-baixo registrado; SC/SD = SENSIBILIDADE (cláusula stress do §7).
