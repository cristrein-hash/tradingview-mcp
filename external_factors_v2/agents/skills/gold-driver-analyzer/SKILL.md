---
name: gold-driver-analyzer
description: "Classifica o estado dos DRIVERS estruturais do ouro (real yields 10Y/TIPS, dólar DXY/trade-weighted, breakevens/inflação, risk-on/off via VIX, política do Fed) em um label de contexto (supportive/neutral/bearish) para XAU. Use no External Factors para a Camada B (macro lento, rotação de smart money em dias/semanas). Triggers: 'driver do ouro', 'contexto macro do ouro', 'real yield gold', 'dólar e ouro', 'regime macro XAU'. Fontes: FRED (DFII10/DTWEXBGS/T10YIE/VIX/DFF), WGC/LBMA/CME (narrativa)."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação de trade.

# Gold Driver Analyzer (Camada B)

Lê o grounding numérico Tier-1 (passado pronto) e produz um LABEL de contexto macro do ouro.

## When to Use
Camada B (macro lento): smart money rota big money em dias/semanas, não no tick. Para enquadrar se o pano de fundo é supportive/neutral/bearish para LONG de ouro.

## Instruções (fronteira de determinismo)
1. Receba os números do Tier-1 (real_yield_10y, usd_broad, breakeven_10y, vix, fed_funds, + Δ20d). **NUNCA gere número — só ECOE e rotule.**
2. Heurística de leitura (label, não regra dura): real yield ↓ = supportive; USD ↓ = supportive; breakeven ↑ = supportive; VIX ↑ = risk-off (contexto); Fed em corte = supportive.
3. ⚠️ Honestidade calibrada pelo backtest do projeto: o NÍVEL estático desses drivers NÃO provou edge nas estratégias (Fase 1 null) — então o label é **contexto/flag**, NÃO sinal de entrada. Marcar `confidence` baixo.
4. Saída: {gold_driver_label: supportive/neutral/bearish, drivers_echoed:{...números do Tier-1...}, note}.
