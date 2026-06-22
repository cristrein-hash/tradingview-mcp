# XAU 4H L2/BPT — CONTEXTO APRENDIDO (2 engines) × CONVEXIDADE

**2026-06-22.** Correção (Cris): a análise de gargalo anterior usou a POLICY binária (TAKE/SKIP) e `sup_cat` cru,
NÃO os estados RICOS aprendidos pelos dois engines. Este addendum traz o contexto aprendido para a verdade de
convexidade (runner MFE≥5 vs loser MFE<2). CALIBRAÇÃO (multi-testing in-sample, 12 dims). DIAGNÓSTICO.

## Resultado: o contexto aprendido NÃO separa convexidade — e onde tem sinal, está INVERTIDO
base runner_rate = 26.1% (72/276).

**Markup-vs-rejeição que o engine aprendeu = FLAT:** supply `CLEAN_SKY_BULLISH` 0.96 ≈ `SUPPLY_REJECTING_RISK` 0.89;
momentum `HEALTHY_HIGH_LEGPOS` 1.14 ≈ `STRONG_BULL` 0.89. Combinação MARKUP_LEARNED lift **1.00** vs REJECT_LEARNED
**0.96** = **zero separação.** O "disambiguador de supply-acceptance" proposto no bloco anterior — os engines JÁ o
encodam, e é inútil na convexidade. (Dupla refutação do "next feature".)

**Sinais fortes = tiny-n (ruído):** capit CLIMAX_RECLAIM n=10 (1.53), mtf CONFLICT n=12 (1.6), ind BOTTOM n=10 (1.53),
BUBBLE_SELL_CLIMAX_BULL n=9 (1.7). Todos n<13.

**INVERSÃO COERENTE (n≥30, o achado real):**
| estado (n≥30) | runner lift |
|---|---|
| ind_confluence STRONG_BEAR_CONFIRM (31) | **1.36** |
| ind_bubbles BUBBLE_SELL_DISTRIBUTION (52) | **1.33** |
| macro_state CORRECTIVE_BEAR_LEG (43) | 1.25 |
| macro_state MACRO_BULL_RUN_CONTINUATION (44) | 1.13 |
| ind_confluence STRONG_BULL_CONFIRM (87) | 0.93 |
| ind_bubbles BUBBLE_BUY_ACCUM_PULLBACK (121) | 0.92 |
| macro_state BULL_PULLBACK_CONTINUATION (47) | **0.57** |

**Os runners escondem-se nos estados que os engines leem como BEARISH/reversão; morrem nos bull-continuation.**
Story causal: os monstros vêm de FUNDOS/capitulação/fim-de-corretiva — onde sinais bearish clusterizam — não da
continuação-bull que o engine prefere TAKE. É a edge de bottom-reversal (Caminho B) aparecendo, e os engines a leem
AO CONTRÁRIO (bull-continuation bias → perdem sistematicamente os runners de reversão).

## Implicações
1. **O gargalo de leitura NÃO é o markup-vs-rejeição de supply** (o engine já o aprendeu, é flat). Era hipótese errada.
2. **O eixo com sinal real (modesto, in-sample) = reversão/bottom**, e os engines estão polarizados ao contrário.
3. **Lifts 1.25-1.36 (n=30-43) = LEAD, não resultado** — multi-testing 12 dims; exige null/sub-janela DENTRO dos 276.
4. Reconcilia memórias: bottom-reversal convergência (capit+rsi+NAS) = Caminho B; o L2/BPT-como-bull-continuation
   sistematicamente subpondera os runners de reversão.

## Próximo (guardrail)
Testar o eixo REVERSÃO (não markup-supply) com null/sub-janela: os runners concentram em pós-capitulação/fim-de-
corretiva? Bater lift>1.0 separando os 72 runners dos 168 losers. NÃO é feature nova de supply — é re-polarizar a
leitura para reversão, que os engines invertem. Sem OOS; dentro dos 276; outcome só avaliação.
