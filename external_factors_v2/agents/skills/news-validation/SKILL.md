---
name: news-validation
description: "Valida notícias financeiras de fontes canônicas que possam impactar o ouro: confirma autenticidade/whitelist, atribui label de risco preliminar (risk_on/risk_off/neutral) e marca para handoff. Use no External Factors Tier-2 como primeiro filtro da ingestão de news. Triggers: 'validar notícia', 'essa news é real', 'manchete macro do ouro', 'impacto news XAU', 'filtrar notícia'. Delega dedup a news-deduplication, tier de fonte a source-reliability. NUNCA fonte única de decisão."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação. Notícia NUNCA é fonte única de decisão.

# News Validation (Tier-2)

Primeiro filtro da ingestão de news: autenticidade + whitelist + label de risco preliminar. Decomposta de news-validation-dedup (dedup e reliability viraram skills próprias).

## When to Use
Camada A/B: manchetes de alto impacto (geopolítica, Fed, dados US) que movem USD→ouro. Para HUMANO ponderar, nunca auto-trade.

## Instruções (fronteira de determinismo)
1. **Whitelist primeiro:** só fontes em sources_whitelist.json tier2. Não-whitelisted → descartar (handoff a source-reliability p/ tier formal). Descartar blog/SEO/opinião/rumor.
2. **Autenticidade:** manchete atribuível a fonte nomeada + timestamp. Sem atribuição → marcar `[UNSOURCED]` e rebaixar.
3. **Label de risco preliminar:** risk_on / risk_off / neutral (refinamento cross-asset é da risk-classification).
4. **Handoffs:** clusterização → `news-deduplication`; tier/peso da fonte → `source-reliability`; severidade geo → `geopolitical-impact`.
5. **Determinismo:** só LABELS + timestamps; NUNCA inventar número (preço/yield/%); se citar dado, ecoar do Tier-1.
6. Honestidade: ambíguo → neutral. Saída: `{headline, source, published_ts, risk_label_prelim, authentic: bool, layer, note}`.
