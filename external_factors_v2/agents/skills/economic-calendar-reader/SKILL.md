---
name: economic-calendar-reader
description: "Lê o calendário macro US de alto impacto (NFP/Nonfarm Payrolls, CPI, FOMC, PPI, Retail Sales, ISM, PCE, Jobless Claims) e produz a janela de evento próxima com release_ts, impacto e camada (A=reação imediata / B=macro lento). Use para External Factors XAU quando precisar saber QUANDO um evento que move o dólar/ouro vai sair. Triggers: 'próximo NFP', 'calendário macro', 'event window', 'quando sai o CPI', 'payroll esta semana'. Fontes canônicas: ForexFactory, Trading Economics, Investing Calendar."
---

**DISCLAIMER (obrigatório):** Saída é contexto AI-gerado para revisão humana. NUNCA é gate automático nem recomendação de trade.

# Economic Calendar Reader (XAU)

Produz a lista de eventos macro US de alto impacto próximos, com release_ts (UTC), impacto e camada.

## When to Use
Quando o External Factors precisa antecipar **event windows** que movem USD→ouro. Ex.: NFP (1ª sexta, 8:30 ET) — validado em event-study: o ouro reage ~2-2,6x o range normal no NFP (p<0.001).

## Instruções
1. Eventos determinísticos (gerar localmente, keyless): NFP=1ª sexta; Jobless Claims=toda quinta; ADP=~2 dias antes do NFP. release 8:30 ET (12:30 UTC EDT / 13:30 EST).
2. Eventos com data variável (CPI/FOMC/PCE/Retail/ISM/GDP): obter das fontes canônicas (ForexFactory/TradingEconomics). Sempre com release_ts exato.
3. Para cada evento: {event, date, release_ts, impact(HIGH/med), layer(A/B), driver}. Marcar `imminent` se ≤96h.
4. **Determinismo:** este skill só estrutura o calendário (datas/horas/labels). NÃO estima magnitude numérica de surpresa — isso é dado (Tier-1), não geração.
5. Saída JSON consumível pelo Synthesizer + monitor.
