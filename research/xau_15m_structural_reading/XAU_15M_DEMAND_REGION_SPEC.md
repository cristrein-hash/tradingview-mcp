# SPEC — REGIÕES DE DEMANDA 15M (Cris, 2026-07-10)

## 1. Objetivo
Detectar regiões de demanda 15M corretas ANTES da entry.

## 2. Famílias
- **Capitulação**: demanda nasce do fim da queda; **não exigir zona pré-existente**.
- **Range bottom**: demanda no fundo real do range.
- **Bull pullback**: demanda por pullback proporcional em tendência viva.
- **Suporte convertido / PLT**: zona rompida, aceita acima, depois vira suporte.

## 3. Geometria
- Usar aceitação/corpos/consolidação quando aplicável.
- Não usar apenas wick/extremo.
- Banda deve ser larga o suficiente para zona visual real.
- Invalidar com tolerância estrutural, não por furo mínimo.

## 4. Autoridade
- Região recente.
- Região defendida.
- Região convertida.
- Região coerente com família.
- Zona velha sem autoridade não vale.

## 5. Proibições
- Uma banda única para todos os fundos.
- PLT como explicação universal.
- Pivô futuro.
- Comprar candle de confirmação.
- Containment simples como validade.
- Misturar região, entry e skip.

## 6. Status
- **SPEC_ONLY_NOT_TESTED.**
- Entry ainda inexistente.
- Produção não autorizada.

Fontes: leitura visual ZONAS A2 (`reports/XAU_15M_A2_ZONES_VISUAL_READING_KNOWLEDGE.md`) + caso
MISS #16 (`results/miss16_plt_check.json`) + famílias do GT (42 VELA DE FUNDO).
