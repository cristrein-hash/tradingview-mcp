---
name: usd-regime-analyzer
description: "Classifica o REGIME do dólar americano (strong/weak/ranging) a partir do USD broad/trade-weighted (DTWEXBGS) + diferencial de juros reais, e produz a leitura inversa para o ouro. Use no External Factors quando precisar saber se o dólar é headwind ou tailwind estrutural ao XAU. Triggers: 'regime do dólar', 'dólar forte ou fraco', 'DXY e ouro', 'USD trend', 'dólar pesa no ouro?'. NÃO usar como gate isolado. Fontes: FRED DTWEXBGS/DFII10/DFF (Tier-1)."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação de trade. Estrutura modelada em LSEG `macro-rates-monitor` (## Core Principles + Output com coluna Signal).

# USD Regime Analyzer (Camada B)

Lê o grounding Tier-1 do dólar e produz um LABEL de regime + read inverso para o ouro.

## When to Use
Para enquadrar o dólar como headwind/tailwind ao LONG de ouro. O USD é driver inverso clássico: USD↑ ≈ ouro↓.

## Instruções (fronteira de determinismo)
1. Receba Tier-1: usd_broad (DTWEXBGS nível + Δ20), real_yield_10y (DFII10), fed_funds (DFF). **NUNCA gere número — só ECOE e rotule.**
2. Classifique o regime (multi-sinal, não snapshot):
   - **Tendência (Δ20):** USD broad subindo consistente → `strong`; caindo → `weak`; oscilando sem direção → `ranging`.
   - **Driver de juros reais:** real_yield↑ tende a sustentar USD forte (suporte de carry); real_yield↓ enfraquece.
   - **Sinal por linha (estilo Signal-row):** cada driver vira um read (headwind/tailwind/neutral ao ouro).
3. Read para o ouro: `strong` → headwind (gold bearish); `weak` → tailwind (gold supportive); `ranging` → neutral.
4. ⚠️ Calibração: na Fase 1, `usd_chg20` foi o único positivo (Δ+2,24) MAS = BETA (USD↓≈ouro↑≈bull), n24 → NÃO é edge isolado. `confidence` baixo; contexto/flag.
5. Saída: `{usd_regime: strong|weak|ranging, gold_read: headwind|tailwind|neutral, drivers_echoed:{usd_broad, real_yield_10y, ...}, confidence, note}`. Sem direção clara → ranging/neutral.
