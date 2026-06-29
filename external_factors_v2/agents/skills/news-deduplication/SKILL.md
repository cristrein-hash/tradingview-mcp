---
name: news-deduplication
description: "Deduplica e agrupa manchetes financeiras que reportam o MESMO evento (várias fontes → 1 cluster), evitando contagem dupla no contexto do ouro. Use no External Factors Tier-2 depois da news-validation. Triggers: 'dedup notícias', 'agrupar manchetes', 'mesma notícia em várias fontes', 'cluster de news', 'evitar contar duas vezes'. Recebe news já validadas; entrega clusters únicos ao Synthesizer. NUNCA fonte única de decisão."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação.

# News Deduplication (Tier-2)

Agrupa manchetes do mesmo evento em 1 entrada. Decomposta de news-validation-dedup (validação virou skill própria).

## When to Use
Após news-validation: quando o mesmo evento aparece em Reuters + Bloomberg + WSJ, contar 1 vez (não inflar peso/severidade por repetição).

## Instruções (fronteira de determinismo)
1. Entrada = lista de news JÁ validadas (de news-validation).
2. **Clusterizar** por evento: headline-match / similaridade semântica (mesmo fato, mesma janela temporal). 1 evento = 1 cluster.
3. Para cada cluster: escolher headline canônica + listar todas as fontes (`sources[]`); manter o `published_ts` mais antigo (primeira aparição = causal).
4. Reconciliar labels divergentes dentro do cluster → o mais conservador (na dúvida, neutral). Peso por número de fontes INDEPENDENTES corroborando (handoff a source-reliability), não por repetição da mesma wire.
5. **Determinismo:** só agrupamento + LABELS + timestamps; NUNCA inventar número.
6. Saída: `{cluster_id, headline_canonica, sources[], n_independent, risk_label, published_ts, layer}`. Entrega clusters únicos ao Synthesizer.
