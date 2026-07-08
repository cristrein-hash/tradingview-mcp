# XAU 15M LONG · N96 · Range/Distribution Round · Devil's Advocate

**2026-07-08.** Checagem adversarial da rodada auction-theory (`XAU_15M_N96_RANGE_DISTRIBUTION_FILTER_ROUND_20260708.md`). Read-only. Todos os números reproduzidos de `n96_range_distribution_filter_analysis.py` + `n96_range_regime_signature_eval.py` + nulls de permutação intra-regime (20k perms).

## Bottom line
- **Reproduz byte-a-byte.** BULL excess≥80 → 8 cut (5L/3W) prec 0,62 dR −4 null P=0,076. RANGE maxbar≥1,8 → 7 cut (5L/2W) prec 0,71. displacement≥1,0 → 6 cut (4L/2W) prec 0,67.
- **A alegação "três assinaturas distintas" = PARCIALMENTE REFUTADA.** Há **um eixo robusto — EXCESS de RSI-HTF (loser = RSI-HTF mais alto)** — que opera em BULL **e** BEAR. O eixo *separado* do RANGE (displacement/chase) **não sobrevive ao próprio null intra-regime**.

## Ataques
**A. Causalidade — PASS.** `excess_rsi_htf = max(4H_rsi,1D_rsi)` do último bar HTF FECHADO (`bars_upto` exclui a barra corrente). Spot-check RAW: #17 1D fechado 09-15, rsi 80,01; #21 87,29; #60 56,15 — todos fecham antes do entry. Displacement/maxbar/rangepos sobre `b15[-8:]` fechadas. Zero look-ahead.

**B. Distinção / small-N (ataque decisivo) — nulls de permutação intra-regime (20k):**
| regime | feature | AUC | perm-P |
|---|---|---|---|
| BULL | excess_rsi_htf | 0,253 | **0,028 ✓** |
| BULL | maxbar_atr_15m | 0,680 | 0,118 ✗ |
| RANGE | displacement_15m | 0,260 | **0,103 ✗** |
| RANGE | maxbar_atr_15m | 0,247 | 0,082 ✗ |
| RANGE | rangepos_4h | 0,688 | 0,214 ✗ |
| BEAR | excess_rsi_htf | 0,037 | 0,000 ✓ |
| BEAR | rsi_slope_1h | 0,868 | 0,002 ✓ |

BULL-excess sobrevive (P=0,028) e é corroborado pela MESMA feature/mesmo sinal em BEAR (P<0,001) — a consistência cross-regime é o que a torna credível sob a multiplicidade do scan (~13 features). **RANGE displacement NÃO sobrevive (P=0,103), nem maxbar (0,082).** A N=7 losers, o "maior gap" é onde o ruído de small-N infla a separação.

**C. Runner preservation.** N96 é 3R fixo (todo winner=+3R). BULL excess≥80 marca winners **#22,#52,#54** (3W p/ 5L). RANGE displacement≥1,0 marca **#1,#4** (ambos perseguiram >1 ATR e ganharam). dR negativo em toda configuração → **nenhum é corte automático lucrativo.**

**D. RANGE displacement stress — falha.** O "sinal" são 4 losers (#6,7,31,60) contra 2 winners de alto-displacement (#1 1,14; #4 1,31). Sweep de threshold: a precisão sobe (0,44→0,80) só **largando winners**, nunca capturando mais losers (loser count preso em 4). Não é separador limpo.

**E. Source — PASS.** RAW-native (15M primitives + htf_primitives 30m/60m/4H/1D, lineage source-guard). Zero SVP (poc/vah/val NULL→excluído), zero resample, zero Fractal-MTF, zero SLIM.

## F. Classificação por regime
- **BULL → REVIEW-LAYER (não GATE).** `excess_rsi_htf` = discriminador real, causal: perm-P=0,028, precisão 0,62 vs base-BULL 0,342 (1,8×). Mas dR=−4, null P(dR)=0,076 (não <0,05), marca 3 winners. **Review-layer legítimo:** "RSI-HTF ≥80 num entry BULL = distribuição late-cycle → size-down / exigir confirmação", NÃO auto-skip.
- **RANGE → NOTHING (como gate/review); no máximo hint de MANAGEMENT não-validado.** Displacement/chase falha o null (P=0,103), dR negativo, 4 losers vs 2 winners, N=7. A *história* de auction ("não perseguir spike >1 ATR num entry de range") é plausível como timing/gestão, mas **sem suporte estatístico neste N** — não promover a discriminador.
- **BEAR (ref) → GATE-adjacent, já aprovado** (excess_rsi P<0,001 + rsi_slope P=0,002 = capitulation filter).

## Caveat central
**Não são três assinaturas distintas — é UM eixo (EXCESS de RSI-HTF, loser=mais alto) partilhado por BULL e BEAR a níveis absolutos diferentes, mais rsi_slope em BEAR. RANGE não tem eixo próprio robusto.** A moldura de auction é *coerente* (exaustão/excess é real e causal) mas o "regime-DISTINTO" é **refutado** para RANGE e só **parcialmente** verdade para BULL (mesma feature que BEAR, magnitude diferente). Com N=7–9 losers/regime e multiplicidade ~13 features × 3 regimes, só ficam de pé o **BULL-excess REVIEW-LAYER** e o **filtro BEAR já aprovado**; **RANGE-chase = hipótese registada, não adotada** (precisa mais episódios de range / extensão RAW).
