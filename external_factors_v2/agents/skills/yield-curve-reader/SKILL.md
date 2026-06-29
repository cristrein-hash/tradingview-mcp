---
name: yield-curve-reader
description: "Lê a curva de juros do Tesouro US (2s10s via T10Y2Y, juros reais DFII10/DFII5, breakevens T10YIE) e produz um LABEL de forma (steepening/flattening/inverted/neutral) + decomposição real-rate e implicação para o ouro. Use no External Factors para o sinal de bonds da Camada B. Triggers: 'curva de juros', '2s10s', 'curva invertida', 'juros reais e ouro', 'steepening flattening', 'yield curve XAU'. NÃO usar como gate isolado. Fontes: FRED T10Y2Y/DFII10/DFII5/T10YIE/DGS10/DGS2 (Tier-1)."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação de trade. Modelado em LSEG `swap-curve-strategy` + componente de curva do `macro-regime-detector` (sem método OOS/cross-val).

# Yield Curve Reader (Camada B)

Lê o grounding Tier-1 da curva e produz LABEL de forma + decomposição real-rate, com read para o ouro.

## When to Use
Sinal de bonds da Camada B: a forma da curva e o nível dos juros REAIS são driver primário do ouro (juro real é o custo de oportunidade de segurar metal sem yield).

## Instruções (fronteira de determinismo)
1. Receba Tier-1: curve_2s10s (T10Y2Y), real_yield_10y (DFII10), real_yield_5y (DFII5), breakeven_10y (T10YIE), nominais DGS10/DGS2 + Δ20. **NUNCA gere número — só ECOE e rotule.**
2. Forma da curva (Δ20 do 2s10s): subindo → `steepening`; caindo → `flattening`; abaixo de zero → `inverted`; estável → `neutral`.
3. Decomposição real-rate (relação, não cálculo novo): real ≈ nominal − breakeven. real_yield↓ = `accommodative` (supportive ao ouro); real_yield↑ = `restrictive` (bearish). Ecoar os valores Tier-1, não recomputar.
4. Read para o ouro: real_yield↓ + steepening pós-corte = supportive; real_yield↑ + flattening = bearish; inverted = sinal de risco macro (contexto, ambíguo p/ ouro).
5. ⚠️ Calibração: nível estático = Fase 1 null → `confidence` baixo; contexto/flag, não sinal de entrada.
6. Saída: `{curve_shape: steepening|flattening|inverted|neutral, real_rate_stance: accommodative|restrictive|neutral, gold_read: supportive|neutral|bearish, levels_echoed:{curve_2s10s, real_yield_10y, breakeven_10y}, confidence, note}`.
