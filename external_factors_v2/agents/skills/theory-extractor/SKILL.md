---
name: theory-extractor
description: "Transforma um item de teoria/análise de uma fonte credível de ouro (título+resumo) numa AFIRMAÇÃO FALSIFICÁVEL sobre o ouro: direção prevista (bullish/bearish/neutral/na) + horizonte em dias + claim curto + condicionante. Use no External Factors p/ converter teorias humanas em hipóteses testáveis pelo forward-scoring. Triggers: 'extrair claim', 'teoria falsificável', 'direção e horizonte de uma análise', 'theory extractor'. NUNCA inventa número de mercado; horizonte é estrutural (tempo)."
---

**DISCLAIMER (obrigatório):** Saída = label/hipótese para teste pela realidade. NUNCA é sinal nem recomendação. Não inventa preço/%/probabilidade de mercado.

# Theory Extractor (Tier-2)

Converte 1 item de fonte credível (não-dealer) numa hipótese falsificável sobre o OURO, para o forward-scoring dar nota ao longo do tempo.

## When to Use
Cada item novo do theory_ledger (Gold Observer/Lyn Alden/In Gold We Trust/MacroVoices/WGC/Brandt/Tavi Costa). Lê título+resumo, devolve a previsão testável.

## Instruções (fronteira de determinismo)
1. Leia título + resumo + fonte + viés. Pergunte: **isto faz uma previsão TESTÁVEL sobre o ouro?**
2. Se NÃO (ex.: ensaio de psicologia, off-topic, retrospectiva sem direção) → `gold_relevant=false`, `predicted_gold_dir="na"`, `horizon_days=null`. Não force.
3. Se SIM → extraia:
   - **predicted_gold_dir**: `bullish` / `bearish` / `neutral` (direção do PREÇO do ouro implícita pela tese).
   - **horizon_days**: janela implícita em dias (curto≈7-14, tático≈30, swing≈60-90, estrutural≈180+). Inteiro. Se vago, use 90.
   - **claim**: 1 frase falsificável (ex.: "real yield caindo sustenta ouro nas próximas semanas").
   - **conditional_on**: driver-gatilho se houver (ex.: "real_yield↓", "USD↓", "CB demand↑") ou null.
   - **confidence_label**: low/med/high (quão explícita/forte é a tese no texto).
4. **Determinismo:** só LABELS + horizonte (tempo) + texto curto. NUNCA gere preço, %, nem probabilidade numérica de mercado. Não exagere o viés da fonte (se perma-bull genérico sem tese nova, marque confidence=low).
5. Honestidade: na dúvida entre direção → `neutral`. A realidade é que vai julgar; sua função é só tornar a tese TESTÁVEL.
6. Saída JSON: `{gold_relevant, predicted_gold_dir, horizon_days, claim, conditional_on, confidence_label}`.
