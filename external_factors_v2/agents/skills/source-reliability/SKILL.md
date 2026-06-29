---
name: source-reliability
description: "Pontua a CONFIABILIDADE de uma fonte de notícia/dado financeiro em tiers (high/medium/low/reject) — Tier 1 oficiais (.gov: Fed, Treasury, BLS, SEC), Tier 2 wires premium (Bloomberg/Reuters/WSJ/FT), Tier 3 especializados, abaixo = reject. Use no External Factors para ponderar o peso de cada manchete antes do Synthesizer. Triggers: 'confiabilidade da fonte', 'essa fonte é confiável', 'tier da notícia', 'peso da fonte', 'source reliability', 'fonte canônica?'. Guardrail: fonte não-whitelisted → reject. Fontes: sources_whitelist.json."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático. Rubrica de tiers de tradermonty `market-news-analyst` + guardrail [UNSOURCED] da Anthropic + provenance/corroboração do VoltAgent `data-researcher`.

# Source Reliability (Camada A/B)

Atribui tier de confiabilidade + peso a cada fonte. Promovida a skill standalone (antes embutida na news-validation-dedup). Output alinhado ao classifier `source_reliability`.

## When to Use
Antes de o Synthesizer ponderar manchetes: separar fonte oficial de wire premium de especializado de ruído. Fonte não-whitelisted = `reject` (não entra no contexto).

## Instruções (fronteira de determinismo)
1. Confronte a fonte com `sources_whitelist.json`. Não-whitelisted → `reject` + nota.
2. Tiers (rótulo, não score de mercado):
   - **Tier 1 `high`:** oficiais/reguladores — Fed, Treasury, BLS, SEC/EDGAR, BEA, BCEs.
   - **Tier 2 `high/medium`:** wires premium — Bloomberg, Reuters, WSJ, FT, AP, CNBC.
   - **Tier 3 `medium/low`:** especializados — S&P Global/Platts, MarketWatch, WGC/LBMA/CME (commodity).
   - **Abaixo `reject`:** blogs, social, SEO, opinião não-atribuída.
3. Corroboração: dado confirmado por ≥2 fontes independentes high/medium → eleva confiança; fonte única low → rebaixar.
4. **Determinismo:** só LABELS de tier + peso categórico; NUNCA inventar número de mercado. Rastrear proveniência (qual fonte disse o quê).
5. Saída: `{source, tier: high|medium|low|reject, confidence_weight: high|med|low, corroborated: bool, note}`. Na dúvida → tier mais baixo (conservador).
