# DA — PREREG FASE 3A BEAR-ONLY SKIP COMPOSITE (2026-07-09)

> Devil's Advocate real (Agent tool, read-only + sondas declaradas) sobre o prereg v1.0.
> **Verdict: `PARTIAL_PREREG_NEEDS_EDITS` → 6 edits aplicados no mesmo dia (v1.1) → condição de
> PASS cumprida nos termos do próprio DA.**

## O ataque central (procedeu)
O prereg v1.0 encenava um "teste" cujo desfecho decisório **já estava determinado**:
- **C está PRÉ-CONDENADO**: incremento sobre A = +30L/**+5W** → falha "≤1 winner adicional" e
  "corta >2 winners" ANTES de rodar.
- **D é DERIVÁVEL por aritmética** (11 marcados; L: 21+40−51=10; W: 1+6−6=1) — "medir D pela
  primeira vez" era falso em substância. D ⊆ A ⇒ nunca adiciona losers ⇒ "melhoria material" era
  impossível por construção.
- Sensibilidade "<70%" já se sabia passar (mínimo da grelha 73%) = critério com pass garantido.
- **K=1,5 e ndesc≥2 = ARGMAX da grelha corrida nesta base** — "contaminação suave" subvendia.
- Prosa vs código divergiam (picos vs DEGRAUS descendentes) e sem sha pinado, "não re-otimizar"
  não era executável.
- Null §11 sub-especificado; p=0,0032 já publicado apresentado como por-medir.

## O que aguentou
Universo genuinamente congelado (sha dos IDs recomputado ✓, 78=61L/17W ✓, mtimes coerentes,
freeze script não computa composites) · S2a threshold externo legítimo (filtro validado) com
caveat da variante · teto §12 correto · looks declarados (defeito era a consequência não retirada).

## Edits aplicados (v1.1)
1. Bloco re-enquadrado: **FORMALIZAÇÃO + ROBUSTEZ EPISÓDICA**, não descoberta; D derivado e
   declarado (10L/1W); nenhum composite produz headline novo.
2. §9 virou "PRÉ-DECIDIDO" (C falha winners; D não adiciona; contagens de winners = descritivas,
   n=17 ⇒ 1W=5,9pp); §10 reduzido às DUAS perguntas realmente abertas (concentração episódica do
   incremento C∖A; null cluster-aware) com regra de cluster única.
3. Código pinado (sha16 `b749b7a62386fd7c`); prosa corrigida (DEGRAUS ≥2 ⇒ ≥3 picos); argmax
   declarado duro.
4. Critério de sensibilidade removido como decisão (pré-pass conhecido).
5. Null por extenso: permutação POR BLOCO semana-ISO, 2000 trials, seed 20260709, estatística =
   losers do incremento C∖A.
6. "Excluídos por ID" → "pelo campo macro; incluídos fixados por ID".

## Consequência honesta para o Cris
O run da Fase 3A vale APENAS pelas duas perguntas abertas (robustez episódica + null cluster-aware)
e pela formalização do painel. Os números dos composites já são conhecidos. Se o Cris preferir,
pode considerar o conhecido como suficiente e reservar tudo para a janela virgem 2024-25 — decisão
dele.
