# XAU 4H L2/BPT — DSPA LBB SIGNAL — KNOWLEDGE STATE (preservação)

**2026-06-23.** Preservação formal da 1ª vitória parcial real da leitura dinâmica DSPA. Diagnóstico; não produção.

## Commits
- `ff2ecf3` — DSPA Layer 4 aggregation (9 estados intermediários).
- `5570264` — DSPA Layer 4 report (DA PASS_WITH_LIMITATIONS).
- (este bloco) — signal stress & preservation.

## Distribuição dos 9 estados DSPA (base 276)
MARKUP_THROUGH_SUPPLY 90 · STRUCTURAL_RISK_SL_PROBLEM 51 · LEGITIMATE_BEAR_BUY 37 · BULL_PULLBACK_CONTINUATION 32 ·
SUPPLY_REJECTION_TRAP 28 · BEAR_PULLBACK_TRAP 23 · UNKNOWN_CONFLICT 13 · REVERSAL_RUNNER 2.

## A vitória (LBB vs Bear Pullback Trap)
| | n | runner% | lift | monumentais |
|---|---|---|---|---|
| LEGITIMATE_BEAR_BUY | 37 | 38 | 1.45 | 6 |
| BEAR_PULLBACK_TRAP | 23 | 13 | 0.50 | 0 |
Fisher contraste p≈0.045; **sobreviveu P1/P2 (39%/37% vs trap 12%/17%)** = estrutural. Usa path features novas
(sweep/flush/acceptance), não snapshot. Ataca diretamente o resíduo bear-leg que os engines anteriores não separavam.

## Caveats (DA)
Sinal FINO; parte grande vem do par `demand_defended`+`acceptance_above` (95%/92%); só 9/30 path features consumidas
(21 numerics ignorados); convergência adiciona incremento real mas pequeno; n=37 → p≈0.06, NÃO edge validada.

## ANATOMIA (stress block, DA-corrigido) — o sinal é o PAR, não a convergência nem os numéricos
- A (demand+accept) n=136 lift 1.13 p=0.135 · B (+bear) n=76 lift 1.16 p=0.205 · C (full LBB) n=37 lift 1.45 p=0.064.
- **A convergência completa NÃO agrega além do par+bear** (C-over-B permutation p=0.121; Fisher C-vs-B-rest p=0.137) — over-specified.
- **Os 21 numeric features NÃO agregam** — meus "leads" eram multiple-testing noise (0 passam Fisher nem sem correção;
  f2_velocity p=0.21 e CIRCULAR com FLUSH_V). Leave-1-year-out estável = ARTEFATO (LBB uniforme entre anos).
- **Conclusão honesta (DA):** a n=37/76 isto é **demand+acceptance em bear context**; tudo além é ruído a esta amostra.
  O contraste LBB-vs-BPT (Fisher p=0.045) ainda vale, carregado tanto por BPT ser runner-poor (13%) quanto por LBB.

## Status
**`APPROVED_AS_CONDITIONAL_PATH_EVIDENCE` — não produção, não policy, não automation-ready.** Primeiro sinal NOVO
alinhado à pergunta certa (legitimate-bear-buy vs trap por TRAJETÓRIA), MAS reclassificado honesto: o sinal É o par
demand+acceptance em bear context, FINO e NÃO-resolvível além disso a n=37 (nem por mais convergência categórica nem
pelos 21 numéricos = ruído). NÃO construir f2_velocity/f7_slope em nada (DA: multiple-testing). Preservar como evidência
condicional; NÃO over-build sobre um subset de 37 trades que a estatística não sustenta. Relaciona
`XAU_4H_L2_BPT_DSPA_LBB_SIGNAL_STRESS_REPORT.md`.
