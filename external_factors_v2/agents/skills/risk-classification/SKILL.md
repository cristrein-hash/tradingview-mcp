---
name: risk-classification
description: "Classifica o SENTIMENTO de risco de mercado (risk_on/risk_off/neutral) por confirmação cross-asset (VIX, curva, USD, fluxo flight-to-quality, crédito HY/IG quando disponível) e a leitura para o ouro. Use no External Factors para o eixo de risco que enquadra refúgio vs apetite. Triggers: 'risco do mercado', 'risk on ou risk off', 'apetite a risco', 'flight to quality', 'sentimento de mercado XAU'. NÃO usar como gate isolado. Fontes: Tier-1 (VIX/curva/USD) + news tier2."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação de trade. Spine cross-asset adaptado de VoltAgent `risk-manager` + tradermonty `market-news-analyst` (categorizar → confirmar, sem método OOS).

# Risk Classification (Camada A/B)

Rotula o sentimento de risco por convergência cross-asset (NÃO um indicador isolado). Promovida a skill standalone (antes embutida na news-validation-dedup).

## When to Use
Para enquadrar se o mercado está em apetite (risk_on) ou refúgio (risk_off) — o ouro tende a se beneficiar de risk_off agudo (bid de refúgio), mas o efeito é contexto, não gatilho.

## Instruções (fronteira de determinismo)
1. Receba grounding Tier-1 (VIX nível+Δ, curva 2s10s, usd_broad) + labels de news tier2 (se houver). **NUNCA gere número — só ECOE e rotule.**
2. Confirmação cross-asset (≥2 sinais concordantes, não eixo único):
   - **risk_off:** VIX↑ + flight-to-quality (Treasuries bid / curva) + USD bid + manchetes de estresse.
   - **risk_on:** VIX↓ + cíclicos/risco preferidos + spreads de crédito estreitando + manchetes construtivas.
   - Sinais divergentes → `neutral` (não forçar narrativa).
3. Read para o ouro: risk_off agudo → supportive (refúgio); risk_on forte → headwind (menos bid de refúgio); neutral → neutral.
4. ⚠️ Calibração: é eixo de CONTEXTO (Fase 1 mostrou nível macro sem edge); `confidence` calibrado, nunca gate.
5. Saída: `{risk_sentiment: risk_on|risk_off|neutral, gold_read: supportive|neutral|headwind, drivers_echoed:{vix, curve_2s10s, usd_broad}, confirming_signals[], confidence, note}`.
