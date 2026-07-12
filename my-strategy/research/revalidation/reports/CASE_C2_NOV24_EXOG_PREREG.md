# PRÉ-REGISTO — CASO C2 (nov/2024 BEAR curto) · REGRA DE EXCEÇÃO EXÓGENA

> Escrito 2026-07-12 ANTES de rodar. STATUS: `PREREG_FROZEN`. Primeiro caso da FASE 2 do plano
> caso-a-caso (ordem Cris). Sonda prévia: dxy_ret20 overlap 2,2% · dxy_slope 3,1% · y_chg20 7,0%.

## Racional causal (declarado)
Queda curta e aguda do ouro em nov/2024 = repricing pós-eleição EUA: rally forte do dólar +
yields a subir = vento contra estrutural do ouro. O preço do ouro sozinho não distingue essa
queda de um range (6 barras 1D, EMAs coladas); o CONTEXTO exógeno distingue (sonda: 3 features
separam). A exceção usa a causa, não o sintoma.

## Regra (forma fechada — exceção estreita sobre o baseline)
No bar 4H t, rótulo = BEAR (sobrepõe o baseline) SE E SÓ SE, no último dia D conhecido (fecho
de D ≤ t, convenção D_KNOWN já auditada):
  1. `dxy_ret20(D) ≥ θ_dxy` (dólar em rally de 20d)
  2. `y_chg20(D) ≥ θ_y` (yields subindo em 20d)
  3. `gold_ret20(D) < 0` (ouro caindo em 20d — resample diário do RAW 4H, prev-day; impede
     disparo em rallies de ouro com dólar forte)
Sem histerese (exceção curta por natureza). Fora da condição, baseline intocado.

## Grelha (FECHADA)
`θ_dxy ∈ {2.0, 2.5}` (%) × `θ_y ∈ {0.25, 0.30}` (pontos de yield) = 4 combos. Nada se acrescenta.

## Critério de aceitação (CONGELADO — Cris 2026-07-12, as três)
- (a) resolve o caso: concordância da janela C2 (2024-11-10→18) > 50%
- (b) dano ≤ 0: NENHUMA das outras 18 janelas piora a concordância vs baseline
- (c) racional causal físico declarado (acima)
Reportar também: nº de barras 4H disparadas FORA de C2 (sujeira), por janela e fora de janelas.

## Restrições
- Causal close-only: features diárias do dia D usadas a partir do fecho de D (D_KNOWN);
  DA lookahead-only ANTES de medir. Sem P&L. Detector intocado (a exceção é camada de avaliação).
- Honestidade declarada: n(C2)=6 barras 1D / 8 barras 4H no escopo — a validação real é
  dano-zero nas 18 janelas + watch forward; o caso em si não tem poder estatístico.
- Falhou → falhou; variação = novo pré-registo.
