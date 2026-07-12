# PRÉ-REGISTO r2 — CASO C2 · VARIANTE COM CAP DE ONSET

> Escrito 2026-07-12 ANTES de rodar. STATUS: `PREREG_FROZEN`. Sucede o prereg r1 (REJEITADO:
> resolvia C2 a 100% mas violava dano-zero por a condição de 20d ficar quente semanas — choque ≠
> condição). Esta variante ataca exatamente essa falha.

## Regra (forma fechada)
Condição exógena (igual ao r1): no fecho do dia D, `dxy_ret20 ≥ θ_dxy` E `y_chg20 ≥ θ_y` E
`gold_ret20 < 0`.
**NOVO — cap de onset**: define-se ONSET = dia D em que a condição LIGA (true, com false em D−1).
A exceção só está ATIVA nos dias em que (condição true) E (D − onset_mais_recente < N_cap dias).
Se a condição continuar ligada além do cap, a exceção DESLIGA (choque acabou, virou condição).
Rótulo = BEAR nos bares 4H cujo último dia conhecido está ativo; resto = baseline intocado.

## Grelha (FECHADA)
- θ pares: {(2.5, 0.30), (2.0, 0.25)} — o apertado (menos sujeira no r1, escolha declarada) e o
  largo (sensibilidade).
- `N_cap ∈ {5, 8, 12}` dias.
= 6 combos. Nada se acrescenta depois.

## Critério de aceitação (IGUAL, congelado — as três)
(a) C2 > 50% · (b) dano ≤ 0 em TODAS as outras 18 janelas · (c) racional causal (choque
dólar+yields no seu ONSET = repricing; a persistência posterior é condição macro, não choque —
por isso o cap é parte do racional, não remendo).
Reportar: C2 %, pioras por janela, sujeira fora-C2 (barras e /sem), agregado.

## Restrições
Causal close-only (onset detectado só com dias fechados; D_KNOWN); DA lookahead-only ANTES de
medir; sem P&L; detector intocado; honestidade: n(C2) minúsculo — validação = dano-zero + forward.
Falhou → falhou; nova variação = novo pré-registo.
