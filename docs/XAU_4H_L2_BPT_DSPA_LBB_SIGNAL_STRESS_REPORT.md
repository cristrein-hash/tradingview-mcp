# XAU 4H L2/BPT — DSPA LBB SIGNAL STRESS REPORT

**2026-06-23.** Stress & anatomia do sinal LBB. Base única 276. Diagnóstico; sem OOS/produção/promoção. realR capado
NUNCA árbitro (MFE uncapped só na avaliação). DA = PASS_WITH_LIMITATIONS (corrigiu over-read meu).

## Tarefa 2 — Anatomia (A / B / C)
| versão | n | runner% | lift | loser% | monum | hyper_p | P1/P2 |
|---|---|---|---|---|---|---|---|
| A demand+acceptance | 136 | 29.4 | 1.13 | 58 | 16 | 0.135 | 24.6/33.3 |
| B +bear_context | 76 | 30.3 | 1.16 | 57 | 8 | 0.205 | 26.8/34.3 |
| C full_confluence_LBB | 37 | 37.8 | 1.45 | 54 | 6 | 0.064 | 38.9/36.8 |

**PERGUNTA CENTRAL — a confluência completa agrega além do par? NÃO.** C-over-B permutation **p=0.121**; Fisher
C-vs-B-rest **p=0.137**. A hyper_p até PIORA ao estreitar (A 0.135 → B 0.205); o 0.064 de C é o menor set pescando o
ponto mais alto, não incremento real. **A convergência categórica está over-specified — o par carrega tudo.**

## Tarefa 3 — 21 numeric features ignorados — NÃO AGREGAM (multiple-testing noise)
Meu flag "SEPARATES" era só threshold de lift (≥1.5/≤0.66) **sem teste de significância** — erro. Fisher próprio (DA):
**ZERO features passam p<0.05 nem sem correção** (menor f2_flush_bars p=0.127; f2_velocity p=0.21). Bonferroni
(0.05/21) / FDR: **nenhum sobrevive**. E **f2_velocity é CIRCULAR** (14/14 FLUSH_V são velocity-hi; fora de FLUSH_V o
lift cai 1.64→1.20 = re-expressa a categórica FLUSH_V já usada). Os 6 "leads" são hull/ruído.

## Tarefa 4 — Stress
- **Leave-1-year-out (36-39% todos anos): ARTEFATO**, não robustez — LBB é uniforme entre anos (2020:4 2021:10 2022:4
  2023:8 2024:9 2025:1 2026:1; nenhum >27%), então dropar 1 ano quase não move o set.
- **drop-one-evidence tiny-n: RUÍDO** — sweep n=4 (75%), flush_V n=12 (50%), capit n=7 (43%) = a um coin-flip de colapsar.
- **LBB vs BPT contraste:** Fisher p≈0.045 (do bloco anterior) ainda vale — carregado tanto por BPT ser runner-poor
  (13%, 0 monumentais) quanto por LBB.

## Tarefa 5 — Falhas reportadas sem mascarar
1. **O sinal É demand+acceptance em bear context** — não a convergência completa. As 8 evidências extras não agregam.
2. **Os 21 numéricos não agregam** — eram multiple-testing noise; f2_velocity circular.
3. **A estabilidade P1/P2 e leave-1-year-out são artefatos de distribuição**, não robustez estatística.
4. **Até o par é p=0.135 (não-significativo)** — a n=37/76/136 o sinal NÃO é resolvível além do par a esta amostra.
5. **NÃO over-read confirmado:** eu havia lido os numéricos como "a refinação real" — era erro de multiple-testing, corrigido.

## Status final da feature
**`APPROVED_AS_CONDITIONAL_PATH_EVIDENCE`** (reclassificado honesto). O LBB é um lean estrutural coerente
(legitimate-bear-buy = demand-defendida + aceitando em bear), MAS estatisticamente é **o par demand+acceptance, fino e
não-resolvível** além disso a esta amostra. NÃO feature-dead (é o 1º sinal novo alinhado à pergunta certa, e o contraste
LBB-vs-BPT vale). NÃO promovível, NÃO automation-ready. **NÃO construir f2_velocity/f7_slope/numéricos em nada** (ruído).

## Próxima recomendação objetiva (DA)
Largar a linha "numéricos são a refinação" (ruído). O único ponto legítimo em aberto é se o **par demand+acceptance**
carrega edge real — e a n=136/p=0.135 **não é resolvível dentro dos 276**. Confirmação exigiria expansão de amostra
(travada: sem OOS/cross-asset). Logo: **preservar o LBB como evidência condicional fina; NÃO over-build.** A frente de
ganho real volta a ser outra (não dissecar mais um subset de 37 trades que a estatística não sustenta).

DA = PASS_WITH_LIMITATIONS. Outputs: `results/l2_bpt_dspa_lbb_signal_anatomy.csv`, `..._numeric_path_feature_test.csv`,
`..._ablation.csv`, `..._permutation_null.csv`, `..._da.csv`.
