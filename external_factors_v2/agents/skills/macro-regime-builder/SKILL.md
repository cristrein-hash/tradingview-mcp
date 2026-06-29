---
name: macro-regime-builder
description: "Sintetiza o REGIME macro de pano de fundo para o ouro (risk_on/risk_off/neutral + tightening/easing) a partir do grounding Tier-1 (yields nominais/reais, USD broad, curva 2s10s, VIX, Fed funds). Use no External Factors Camada B (macro lento) para enquadrar se o ambiente é supportive/neutral/bearish para LONG de ouro. Triggers: 'regime macro', 'pano de fundo do ouro', 'risk on/off estrutural', 'estamos em aperto ou afrouxamento', 'macro regime XAU'. NÃO usar como gate de entrada. Fontes: FRED (Tier-1)."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação de trade. Modelado em LSEG `macro-rates-monitor` + tradermonty `macro-regime-detector` (vocabulário de regime; SEM método OOS/cross-val — trava do projeto).

# Macro Regime Builder (Camada B)

Lê o grounding numérico Tier-1 (pronto) e produz um LABEL de regime macro — síntese multi-componente, NÃO eixo único.

## When to Use
Camada B (macro lento): smart money rota big money em dias/semanas. Para rotular o regime estrutural que serve de pano de fundo ao LONG de ouro.

## Instruções (fronteira de determinismo)
1. Receba os números Tier-1 (real_yield_10y/5y, usd_broad, curve_2s10s, breakeven_10y, vix, fed_funds + Δ20d). **NUNCA gere número — só ECOE e rotule.**
2. Síntese de 4 perguntas (convergência ortogonal, não fator isolado):
   - **Stance de política:** Fed funds Δ recente + nível → tightening / easing / hold.
   - **Sinal de bonds:** curva (2s10s) + direção do real yield → restrictive / accommodative.
   - **Condições financeiras / risco:** VIX nível+Δ → risk_off (VIX↑) / risk_on (VIX↓).
   - **USD:** usd_broad Δ20 → headwind (USD↑) / tailwind (USD↓) ao ouro.
3. Combine em regime nomeado: `risk_on`/`risk_off`/`neutral` (eixo de risco) + `tightening`/`easing` (eixo de política). Ouro tende supportive em easing + real-yield↓ + USD↓; bearish no inverso.
4. ⚠️ Calibração honesta: o NÍVEL estático destes drivers NÃO provou edge nas estratégias (Fase 1 null) → `confidence` baixo, é **contexto/flag**, não sinal.
5. Saída: `{macro_regime: risk_on|risk_off|neutral, policy_axis: tightening|easing|hold, gold_backdrop: supportive|neutral|bearish, drivers_echoed:{...Tier-1...}, confidence, note}`. Sem evidência clara → neutral.
