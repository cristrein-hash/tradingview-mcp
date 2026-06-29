---
name: geopolitical-impact
description: "Classifica a SEVERIDADE de eventos geopolíticos (guerra, sanções, eleições, choque de energia, tensão Oriente Médio/Rússia-Europa/APAC) e o impacto safe-haven no ouro (low/med/high + bullish/neutral). Use no External Factors Camada A/B quando uma manchete geopolítica de fonte canônica puder mover o bid de refúgio do XAU. Triggers: 'risco geopolítico', 'guerra e ouro', 'sanções', 'safe haven', 'choque geopolítico XAU', 'tensão no Oriente Médio'. NUNCA fonte única de decisão. Fontes: news whitelisted tier2."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação de trade. Notícia/risco geopolítico NUNCA é fonte única. Rubrica adaptada de tradermonty `market-news-analyst`.

# Geopolitical Impact (Camada A/B)

Rotula a severidade esperada de um evento geopolítico e a direção safe-haven no ouro. Output = LABEL (alinhado ao classifier `geo_severity`: low/med/high).

## When to Use
Manchetes de alto impacto (conflito armado, sanções amplas, choque de energia, eleição-divisora) que ativam bid de refúgio no ouro. Para HUMANO ponderar.

## Instruções (fronteira de determinismo)
1. Só fontes whitelisted (sources_whitelist.json tier2). Descartar blog/SEO/opinião/rumor não-confirmado → se não-confirmado, `low` + nota.
2. Rubrica de severidade (rótulo, não número de mercado):
   - **Magnitude** do evento: severe / major / moderate / minor.
   - **Amplitude** (breadth): systemic (global) / cross-asset / regional / pontual.
   - **Modificador forward:** muda regime? (escala) · confirma tendência? · contrário? (atenua).
   - Combine → `geo_severity = low | med | high`.
3. Exposição: classificar por região (Oriente Médio, Rússia-Europa, APAC, LatAm) × canal (energia, metais preciosos, fluxo de refúgio).
4. **Determinismo:** só LABELS + timestamps; NUNCA inventar número (preço/%/probabilidade). Se citar dado, ecoar do Tier-1.
5. Direção safe-haven: risco geopolítico agudo → `gold_impact: bullish` (refúgio); distensão → neutral. Honestidade: ambíguo → neutral/low.
6. Saída: `{event, geo_severity: low|med|high, region, channel, gold_impact: bullish|neutral, sources[], published_ts, note}`.
