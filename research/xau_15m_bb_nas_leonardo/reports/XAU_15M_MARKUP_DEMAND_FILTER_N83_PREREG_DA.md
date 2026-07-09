# XAU 15M — MARKUP-DEMAND + FILTER N83 · PREREG Devil's Advocate

**2026-07-09.** DA real (Agent tool, general-purpose) sobre o prereg. Verdict: **BLOCKED_MISSING_N83** (defensável e honesto).

## Por ponto
1. **N83 existence — OK.** Grep independente (`N83/n83/N-83/N_83/N 83/filter_n83/FILTER_N83/N=83/"83 signals"/"83 sinais"`) = **0 matches** exceto dentro do próprio prereg. Único `n=83` = experimento vol-session não-relacionado. Nenhum results/CSV com 83 linhas. `#83` = índice de trade loser. **Não há "Filter N83" definido.** O near-miss `n96_range_distribution_filter` mantém **N82** (off-by-one) — o prereg corretamente **NÃO** o vincula a N83 (Stage 5 proíbe inventar predicado). BLOCKED (não PARTIAL preguiçoso).
2. **Base mapping — OK, 1 CONCERN.** `entry_engine_master_20260707.json`: N=164, `kind=MARKUP`=**96**, `out` 52×1/44×0 = **52W** (bate). ent/sl/tgt/out em todos. `n96_causal_regime.json` = **96/96** (BULL38/BEAR37/RANGE21). **CONCERN: family_label = loser-only 44/96** (winners sem rótulo) — o prereg marcava ✅ sem ressalva. **Corrigido:** §7 re-rotulado ⚠️ PARCIAL loser-only + pendência de cobertura 96/96.
3. **Outcome leak / proxy — OK.** Features todas lookback/causal; `out` = label 3R forward-only (não é feature); sem SLIM/proxy; RAW primitives. Base **não contaminada**.
4. **Protocol compliance — OK, 1 CONCERN.** Unidade congelada · baldes = 11 canónicos verbatim · claims ledger · RAW mapping · sanity · DA-required. 4 blockers existem. **CONCERN: faltava o gate manifest em `docs/architecture/XAU_15M_<LAB>_GATE_MANIFEST.md` (Stage 1). Corrigido:** criado `docs/architecture/XAU_15M_MARKUP_DEMAND_FILTER_N83_GATE_MANIFEST.md`.
5. **Unidade — OK.** Congelada (episódio markup-demand → reclaim); N83 mudaria só o subconjunto, não a unidade. Guard correto.
6. **Premature claim / status — OK.** Nenhum número como validação; "N83 existe" = REFUTED; swept-runner=RESEARCH_BASE_NOT_OFFICIAL, N96=USER_APPROVED_NOT_PRODUCTION corretos.

## Correções aplicadas em resposta ao DA
(a) §7 family_label → ⚠️ PARCIAL loser-only (44/96) + pendência 96/96. (b) gate manifest materializado no caminho do protocolo.

## Veredito final
**BLOCKED_MISSING_N83** — não é PARTIAL (base source mapping completa), não é FAIL_CONTAMINATED (sem leak/proxy), não é PASS (o filtro nomeado é indefinido → nenhum teste autorizável). **Não rodar teste sem autorização explícita do Cris + definição de N83.** Vincular N83 ao filtro RANGE-distribution N82 seria o único near-match — mas tem de ser escolha explícita do Cris, não assunção.
