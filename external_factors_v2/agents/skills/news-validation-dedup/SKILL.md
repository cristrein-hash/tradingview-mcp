---
name: news-validation-dedup
description: "Valida, deduplica e classifica notícias financeiras de fontes canônicas (Reuters/Bloomberg/FT/WSJ/AP) que possam impactar o ouro, produzindo um label de risco (risk_on/risk_off/neutral) e reliability por fonte. Use no External Factors Tier-2 para ingestão limpa de news. Triggers: 'news do ouro', 'risk on off', 'manchete macro', 'dedup notícias', 'impacto news XAU'. NUNCA fonte única de decisão."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação. Notícia NUNCA é fonte única de decisão.

# News Validation & Dedup (Tier-2)

Ingestão estruturada de news whitelisted → label de risco + dedup + reliability.

## When to Use
Camada A/B: manchetes de alto impacto (geopolítica, Fed, dados US) que movem USD→ouro. Para HUMANO ponderar, nunca auto-trade.

## Instruções
1. Só fontes whitelisted (sources_whitelist.json tier2). Descartar blogs/SEO/opinião.
2. Dedup: agrupar manchetes do mesmo evento (cosine/headline-match); 1 evento = 1 entrada.
3. Para cada cluster: {headline, sources[], source_reliability(high/med), risk_label(risk_on/risk_off/neutral), published_ts, layer}.
4. **Determinismo:** só LABELS + timestamps; NUNCA inventar números (preço/yield/%); se citar dado, ecoar do Tier-1.
5. Honestidade: se ambíguo → neutral. Saída JSON p/ Synthesizer.
