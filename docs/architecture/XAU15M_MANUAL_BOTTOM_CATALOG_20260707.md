# XAU 15M — Catálogo das Marcações Manuais do Cris (fundos, entrys, regras)

**Data:** 2026-07-07 · **Meta nova (Cris):** detectar MAIS fundos sem look-ahead + verificar se têm entry 3×1.
**NÃO** é mais meta FundedNext. Ordem que funciona: **ESTRUTURA (6-9 meses) → INDICADORES → ENTRY sem look-ahead.**
**Fonte:** extração MCP de 251 shapes do gráfico (`draw_get_properties`/`getPoints`).

## 1. O que o Cris marcou no gráfico (via MCP)

| tipo | qtd | significado |
|------|-----|-------------|
| `text_note` "VELA DE FUNDO" | 42 | velas de fundo verdadeiro (conjunto AMPLIADO: abr/2025 → jun/2026) |
| `text_note` "VELA DE ENTRY / ENTRY CORRETA" | 24 | vela de entrada correta (o 3×1), no retest/reação da zona |
| `text_note` "FUNDO NÃO VÁLIDO POIS PERNA BEAR CLARA ANTECEDE" | 3 | regra de invalidação estrutural |
| `text_note` "FUNDOS NÃO VÁLIDOS DE PEQUENA ACUMULAÇÃO" | 1 | regra de invalidação |
| `text_note` "POLARIDADE TOPO" | 1 | inversão de polaridade (topo) |
| `circle` (fundos) | 50 | fundos marcados (círculos vermelhos) |
| `long_position` #C/#S + labels | 65 | os 65 trades plotados (30 ✓ / 35 ✗) |

## 2. Achado 1 — ESTRUTURA MACRO: todos os fundos são pullback em BULL macro

Estrutura dos ~6-9 meses anteriores a cada vela de fundo (causal, agregação diária, EMA50/EMA100):
**42/42 fundos em regime BULL macro** (bull% 80-100%, EMA50>EMA100 em quase todos). O ouro esteve em
tendência de alta macro todo o período. **Regra estrutural 0: só procurar fundo LONG quando o macro é BULL.**

Duas sub-famílias por profundidade da retração da perna de alta macro (`retr_up_macro`):
- **RASO** (retr 0,06-0,35): pullback superficial em BULL forte — a maioria (set-out/2025, dez/2025).
- **CORREÇÃO** (retr 0,44-1,0): fundo de correção profunda em BULL (fev/mar/mai/jun 2026).

## 3. Achado 2 — regra "PERNA BEAR CLARA ANTECEDE" = ponto intermediário de correção

Os 3 inválidos (05/08/16-mar-2026) têm **drop_before 8,8-9,1 ATR-dia** mas ficam ANTES do fundo final; a
queda continua depois deles. O fundo VÁLIDO da mesma correção é 23-24-mar (retr_up 0,72-0,86 = fundo profundo).
**A diferença não é o tamanho do drop** (fundo válido 04-mai tem drop 10,6 ATR) — é se a estrutura **já
reverteu** (fundo final = válido) ou **ainda cai** (intermediário = inválido). Detecção causal: o fundo final
tem reversão estrutural confirmada (CHoCH+/higher-low/varredura), o intermediário não. "Pequena acumulação"
(13-jan) = drop_before só 0,8 ATR → fundo raso demais, sem capitulação real.

## 4. Achado 3 — ENTRY: no retest da zona, 1,5h-38h após o fundo

Pareamento das 24 velas de ENTRY com a VELA DE FUNDO anterior: a entrada vem **1,5h a 38h depois** do fundo
(nunca na própria vela de fundo). Dois modos:
- **lag curto (1,5-2,2h):** entrada na reação imediata (reclaim rápido).
- **lag longo (10-38h):** entrada no **retest da zona de demanda** que o fundo criou (o padrão que o Cris
  descreveu; visível no print com zonas DEMAND/SUPPLY do Custom OB Detector, "Strong Low"/"Weak High").
"Nem sempre há retest" — parte dos fundos parte direto (lag curto).

## 5. Winners #C/#S vs marcações

Winners (18/30) e losers (19/35) ficam igualmente perto de uma vela de fundo (<=12h) → **estar num fundo não
basta**; o que separa é a ENTRY correta (o momento no retest/reação). Confirma o achado de método anterior: a
entry é o discriminador dentro do fundo válido, e o fundo válido depende da estrutura macro.

## 6. Padrão do mercado 15M (síntese para a nova camada de entry)

`BULL macro (estrutura 6-9m)` → `correção/pullback cria fundo com reversão estrutural (não intermediário de
perna BEAR)` → `fundo gera zona de demanda` → `ENTRY no retest/reação da zona (1,5-38h depois), 3×1`.

## 7. Próximos passos (em curso, ordem que funciona)

1. Dividir fundos+entrys por FAMÍLIAS (RASO / CORREÇÃO / com-retest / sem-retest).
2. Por família: features de INDICADORES discriminantes (reversão estrutural, zona de demanda, absorção).
3. Detecção causal do fundo válido (excluir intermediários de perna BEAR) — a regra do Cris matematizada.
4. ENTRY 3×1 no retest da zona, sem look-ahead.

## Reprodução
`catalog_manual_tags_20260707.py` · `catalog_pairing_20260707.py` · `macro_structure_before_20260707.py`
Resultados em `results/catalog_*_20260707.json` e `results/macro_structure_before_20260707.json`.
Extração MCP: 251 shapes (50 círculos, 42 velas-fundo, 24 velas-entry, 4 inválidos, 1 polaridade, 65 trades).
