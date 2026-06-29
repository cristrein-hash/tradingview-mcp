---
name: event-severity
description: "Classifica a SEVERIDADE esperada de um evento macro (low/med/high) para o ouro, combinando tipo de evento + grounding numérico (consenso vs prévio, quando disponível). Use no External Factors para priorizar event windows. Triggers: 'severidade do evento', 'quão importante é esse dado', 'priorizar calendário', 'event severity XAU'."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático.

# Event Severity

## When to Use
Para rotular HIGH/med/low cada evento do calendário (NFP=HIGH validado ~2-2,6x reação no ouro; FOMC=HIGH; CPI=HIGH; jobless=med).

## Instruções
1. Tabela base de severidade por tipo (NFP/CPI/FOMC/PCE=HIGH; ADP/Retail/ISM=med; jobless=med/low).
2. Se houver surpresa esperada (consenso do Tier-1/calendário), modular o label — SEM gerar número.
3. Saída: {event, severity(low/med/high), rationale}. Só LABEL.
