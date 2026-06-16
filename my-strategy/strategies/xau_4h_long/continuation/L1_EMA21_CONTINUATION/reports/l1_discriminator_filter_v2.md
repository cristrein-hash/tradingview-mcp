# L1 — 2ª rodada de filtragem IN-SAMPLE (v2) sobre os 49 do stack v1 — READ-ONLY

**2026-06-16 · IN-SAMPLE OPTIMIZATION / RESEARCH — NÃO é OOS, NÃO é validação, NÃO é edge provado. Produção intocada.**

## Reprodução (hard-stop check) — PASSOU
- **Baseline 63:** 17 T / 39 S / 7 TM · sumR +18.2 · PF 1.46 ✓ (bate 17/39/7)
- **Stack v1 (49):** 17 T / 29 S / 3 TM · sumR +27.4 · PF 1.94 ✓ (bate n=49/+27.4)
- Stack v1 (FIXO, não reaberto): `ret5≤1.42% AND ext_ema≤2.95ATR AND zone_w≥0.6ATR AND dist_zone≤1.81ATR`.

## Definições
winner = bateu **+3R target** · loser = bateu **−1R stop** · scratch/time = nem target nem stop em ≤60 barras (partial positivo **NÃO** é winner). **Monumental = TARGET com MFE uncapped ≥6R = {#48, #51, #52(18R), #54, #61(12.3R)}.**

## Causalidade (correção crítica do DA)
Features de preço/tempo (`atr_ratio, dow, ret*, body, upwick, ema_slope, risk_atr, hour`) = causais (OHLCV fechado). **NAS lido em SHIFT1 (bar i-1)** — o DA pegou que ler NAS no bar de entrada viola a regra close-only-causal (NAS top/bottom repinta). Re-testado: nas_dist≥1.29 at-bar +34.2R/PF3.01 vs **SHIFT1 +33.2R/PF2.84 — estável** (NAS_DISTANCE é momentum suave, não colapsa no shift). Resultado NÃO é artefato de repaint. `nas_rsi/n_bubbles/svp/vol` NÃO foram usados nos cenários finais (repaint-risk).

## Cenários (todos IN-SAMPLE sobre os 49)
| Cenário | filtro v2 (+ stack v1) | n | T | S | sumR | PF | hit | winners perdidos | monumentais perdidos |
|---|---|---|---|---|---|---|---|---|---|
| baseline 63 | — | 63 | 17 | 39 | +18.2 | 1.46 | 27% | — | — |
| stack v1 | — | 49 | 17 | 29 | +27.4 | 1.94 | 35% | 0 | 0 |
| **A ultra-conservador** | `atr_ratio≤0.0081 AND dow≤4` | 45 | **17** | 25 | +31.4 | 2.26 | 38% | **0** | **0** |
| **B monumental-safe** | `nas_dist(SHIFT1)≥1.29` | 36 | 16 | 18 | +33.2 | 2.84 | 44% | #3 (MFE 4.04R) | **0** |
| **C expectancy-max** | `nas_dist(SHIFT1)≥1.31` | 34 | 16 | 16 | +35.2 | 3.20 | 47% | #3 (MFE 4.04R) | **0** |
| D simple-first | `atr_ratio≤0.0081` | 47 | **17** | 27 | +29.4 | 2.09 | 36% | **0** | **0** |

- **A** remove ids {2,10,17,63} — 0 winner/monumental perdido.
- **B/C** removem {3,4,8,9,10,16,17,18,21,37,40,50,57(+28,43 no C)} — perdem **só #3** (winner +3R, MFE 4.04R; não-monumental). Monumentais preservados.
- **D** remove só {2,63} — 0 winner perdido (single feature, mais simples).

## DA — veredito (10 pontos)
1. NAS causalidade: **era repaint-risk (at-bar); CORRIGIDO p/ SHIFT1; estável** ✓ · 2. outcome reading: winner=+3R only, partial≠winner ✓ · 3. **selection/multiple-testing: SEVERO** — nas_dist≥1.29 é o arg-max de ~centenas de comparações; sem Bonferroni/holdout ✗ · 4. **poder estatístico: insuficiente** — n=36, Wilson CI hit ~[30%,62%] cobre a base rate ✗ · 5. exec risks: outcome é exit-defined (3R/structural ≠ V_stair real) ⚠ · 6. RAW only, sem slim ✓ · 7. baseline/stack v1 reproduzidos ✓ · 8. nenhuma feature usa futuro/candidate_id/year/label/regime_B_v3-live ✓ · 9. winner perdido (#3) listado ✓ · 10. marcado in-sample ✓.
- **overfit-on-overfit:** v2 condiciona no stack v1 (já tunado nos mesmos dados). Desconto forte.
- **#3 (MFE 4.04R) é winner material**, não "pequeno" — perda real em B/C.

## Conclusão recomendada
- **Mais defensável: A ou D** (só features causais de preço/tempo, **0 winner/monumental perdido**, +29 a +31R). `dow≤4` (corta sexta) é fino/suspeito — **D (atr_ratio≤0.0081 sozinho, +29.4R, 0 perdas)** é o mais limpo e simples.
- **B/C (NAS)** dão PF maior (2.84/3.20) e são causais (SHIFT1), mas perdem #3 e dependem de threshold tunado + multiple-testing → **hipótese**, não resultado.
- **NADA disto é edge.** Tudo in-sample sobre 49 (subset de 63). Exige **OOS independente** (sub-janela/cross-asset) + Bonferroni + revalidar sob exit real (V_stair) antes de qualquer promoção. Não tocar produção.

_Scripts: `discriminator_search_v2.py` (SHIFT1 causal). CSV: `l1_discriminator_filter_v2.csv` (49 com features + membership por cenário)._
