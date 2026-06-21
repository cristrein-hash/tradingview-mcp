# REGIME/CONTEXT/FUEL v1 — RELATÓRIO DIAGNÓSTICO

**2026-06-21.** Diagnóstico. Sem outcome como predicado. Engine/decisions/produção intocados.

## Layers executadas
- **L1 provenance:** 91 features (84 packet + 7 externas). Join causal externas via shift D-1 (0 join_issues, shift≥1 dia → look-ahead eliminado). `macro_leg` CONFIRMADO MORTO (REFERENCE_ONLY 276/276). Stage A não separa A/B (usado só como feature).
- **L2 sets:** A(bull cortado)=26 · B(bear aceito)=18 · C(ambíguo, fora do fit)=18. T40→B (must-block); C = T34/T36/S39/S19/T27/S14 + REVIEW/TRANSFORM.
- **L3 univariado/pairwise/árvore:** discriminador top = `dist_4h_supply_low_atr` (≡ reclaim_dist_from_supply, colineares) ba=0.946, es=2.66, threshold 2.33 (A=perto/baixo, B=longe). Árvore prof≤3: `dist_supply<2.33` → 19A/0B puro. Externas (regime_B_v3 dd13w ba 0.726) agregam valor MODERADO, não lideram. Momentum (rsi/rsi_1d) moderado.
- **L4 robustness:** shuffle-null P(null≥real)=0.0 (não-aleatório). Split temporal train2020-23→test2024-26 ba=0.808 (segura), MAS reverso INVIÁVEL (B late n=3) → held-out FRÁGIL. n=44, B-side n=3.

## L5 — INTERPRETAÇÃO DE MERCADO (e a refutação)
A separação estatística é FORTE mas **FALHA o critério de âncoras** (preservar big winners):
- **anchors_preserve 9/18** — a regra CORTA T34/T35/T37/T41 (supply moderada 2.4-5.2 ATR, mas bull confirmado) e S29/S30/S31/S32/T39 (**dist_supply=None porque NÃO há overhead = contexto ATH/no-overhead bullish — a regra não os enxerga**).
- **anchors_block 1/2** — deixa passar S40 (must-block, supply 0.58).

**Causa raiz:** `dist_4h_supply` sozinho **conflaciona dois mercados**: (a) markup rompendo supply próxima (A-set), e (b) NÃO-overhead/ATH (dist=None, os big winners S29-32/T39). É exatamente a distinção **no-overhead-bullish vs supply_colada** que o Cris flagou — e nenhuma feature ÚNICA resolve. O sinal forte A-vs-B é em parte ARTEFATO da composição dos sets, não leitura de regime generalizável.

## CONCLUSÃO: CANDIDATO FRACO / PRECISA FEATURE NOVA
- `dist_4h_supply` (e o v0 que o elegeu) = **threshold frágil**: alto A-vs-B in-sample, mas falha âncoras + held-out frágil. **NÃO é a leitura de regime.**
- **Precisa de FEATURE COMPOSITA** (eixo D explícito): tratar `has_4h_supply_overhead=no` (None) como **bullish ATH** + momentum, e NÃO penalizar dist_supply moderada em contexto bull confirmado. O `dist_supply` puro entra como UM termo, condicional ao has_overhead — nunca sozinho.
- Externas antigas (regime_B_v3 drawdown_13w) = valor moderado, candidatas a TERMO secundário, não líder.
- **Evidência insuficiente para regra; suficiente para direcionar a próxima feature.** Calibração, não validação. Nada promovido.

## Próximo (não-agora): engenharia de feature composita has_overhead-aware + re-teste contra âncoras + held-out.
