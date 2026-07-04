# MTF SIGNATURE GATE TEST — DA ADVERSARIAL (2026-07-04)

DA pós-resultado independente (subagent real; scripts `_DA_gate_{1,2,3}*.py`, não commitou — verificado). Implementação do gate reproduzida do zero (lentes verbatim 35/35; painéis E1/E2 dígito a dígito; runner-kill 52/53 ✓; nulls 27-45 pct ✓).

## MECANISMO DO COLAPSO (adjudicado com decomposição)
Assinatura recomputada nos 35 alvos sob 4 variantes:
| Variante | gate pass | supply_far | demand_near |
|---|---|---|---|
| A: tempo dele + **preço desenhado** (=discovery) | **60%** ✓ | 66% | 83% |
| **B: tempo dele + close REAL** | **6%** | 23% | 20% |
| C: cj do candidato + close@cj (=gate test) | 9% ✓ | 20% | 29% |
| D: cj + preço desenhado | 37% | 46% | 60% |
Controles no cj: 8,0%. **B ≈ C ≈ controles → o driver era o PREÇO FICTÍCIO** (âncora retroativa no fundo do flush, mediana 3,29 ATR15 / 1,11R abaixo do close): o desconto empurra o supply para >3 ATR acima E puxa a demanda 1H para ≤1 ATR — **as duas pernas inflam pelo mesmo offset; a "confluência MTF" era 1 artefato contado 2×**. O lift "corrigido" do discovery (5,7-6,7×) deslocou o TEMPO dos controles mas nunca reprecificou os alvos — o null de multiplicidade randomizava rótulos, não preços, e não podia capturar isto. Lift like-for-like real ≈ **1× (nada)**.

## Runners e Sistema A
As duas pernas matam quase tudo a preço real: no cj o close está mediana **1,86 ATR60 ACIMA** da demanda 1H mais próxima, e o flush cria supply fresco a ~0,96 ATR overhead. Runners falham 98% vs não-runners 95% (não é anticorrelação específica). **Sistema A 21 fora-da-base: 0/21 pass, mesma geometria — NÃO é substrato distinto sob estas lentes** (segue distinto pelo eixo swept/contexto, não por esta assinatura).

## Contaminação declarada
Ficam contaminadas as camadas sugestivas PREÇO-DEPENDENTES do discovery (inside_demand 1H 3,5×; demanda 30M+1H empilhada 3,1×). Pistas preço-INDEPENDENTES (CHoCH ≤24b, absorção SELL-M/L, anti-iniciativa BUY, NAS-recência) não foram refutadas AQUI, mas nunca passaram o null lá — sem reabilitação implícita.

## Veredito DA: **SIGNATURE_GATE_FAIL** (e o discovery-lift = REFUTADO como artefato de fill-fiction). Nada vira REVIEW_LAYER (não há melhoria de contexto/risco a preservar).
