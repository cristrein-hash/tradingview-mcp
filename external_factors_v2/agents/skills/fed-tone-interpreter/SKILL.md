---
name: fed-tone-interpreter
description: "Interpreta o TOM de comunicações do Fed (minutes, discursos, statement FOMC) como label hawkish/neutral/dovish para contexto do ouro. Use no External Factors Camada B. Triggers: 'tom do Fed', 'hawkish dovish', 'FOMC minutes', 'fed speak', 'powell tone'. Fonte: Federal Reserve (texto oficial)."
---

**DISCLAIMER (obrigatório):** Contexto AI-gerado para revisão humana. NUNCA gate automático nem recomendação.

# Fed Tone Interpreter (Camada B)

## When to Use
Pós-FOMC/minutes/discursos: rotular o tom (hawkish=USD↑/ouro↓ contexto; dovish=ouro↑ contexto).

## Instruções
1. Ler SÓ texto oficial do Fed (whitelist). 
2. Produzir label hawkish/neutral/dovish + 1-2 trechos de evidência (citação).
3. **Determinismo:** NUNCA gerar números (taxa, prob de corte) — esses vêm do Tier-1/FedWatch. Só o LABEL de tom.
4. Saída: {fed_tone, evidence[], note}. Honestidade: ambíguo → neutral.
