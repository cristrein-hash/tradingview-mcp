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

## 2. Achado 1 — ESTRUTURA MACRO: DOIS regimes de fundo (corrigido — Cris: há fundos BEAR)

CORREÇÃO: a 1ª medição (EMA50>EMA100 secular) mascarava correções BEAR de médio prazo (numa queda de
−22% a EMA50 fica acima da EMA100 pela subida anterior). Com regime MULTI-ESCALA (secular 6-9m /
médio 1-2m via EMA20-EMA40+slope / curto), os 42 fundos dividem-se em TRÊS famílias por regime MÉDIO:

| regime médio | n | retr_up | drop_mid | d_vale | descrição |
|--------------|---|---------|----------|--------|-----------|
| **BULL-pullback** | 26 | 0,17 | 2,8 ATR | 0 | pullback raso, entra no low, alta continua |
| **BEAR-reversal** | 12 | 0,73 | 7,4 ATR | 2 | fim de queda profunda, reversão de tendência (mar-jun/2026) |
| RANGE-base | 4 | 0,34 | 5,8 ATR | 19 | base lateral longa (ago/2025, nov/2025) |

**Diferenças a compreender (mudam a detecção):**
- **BULL-pullback**: correção rasa (devolve ~17% da perna de alta), o fundo É o low, tendência de alta segue.
  Detecção: contexto BULL + pullback + reação rápida.
- **BEAR-reversal**: queda profunda (devolve ~73%, drop 7-11 ATR), o fundo é o FIM da perna de baixa.
  Detecção: contexto BEAR + capitulação + reversão estrutural (CHoCH+ que encerra a queda).

**Regra 0 revisada:** procurar fundo LONG em BULL (pullback) E em BEAR (reversão do fim da queda) —
com lógicas DIFERENTES. Não é "só BULL".

**IMPORTANTE (Cris): as regras dele são GUIAS, não leis imutáveis** — capturar o espírito, não aplicar
cortes rígidos por regime.

## 3. Achado 2 — "PERNA BEAR CLARA ANTECEDE" (guia) = a perna de baixa ainda não terminou

Os 3 inválidos (05/08/16-mar) têm `d_vale` 27-36 (o low real foi há muito; são bounces intermediários e a
queda continua depois) — vs os fundos BEAR VÁLIDOS de 23-24-mar com `d_vale` 0-3 (o fundo É o low recente que
reverteu). O espírito do guia: **rejeitar pontos onde a perna de baixa AINDA NÃO terminou; aceitar onde ela
terminou** — vale em BULL e em BEAR. Não é "tamanho do drop" nem "regime BEAR = inválido". "Pequena acumulação"
(13-jan) = drop só 0,8 ATR, retr 0,04 → sem capitulação/pullback real, ruído.

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
