# BEAR-LEG + RANGE-CHOP BLOCK GATE (com carve-out bottom/turn) — RELATÓRIO DIAGNÓSTICO

**2026-06-22.** Diagnóstico/calibração nos **62 (ensino)** — escopo travado pelo Cris (NÃO 276/OOS: evitar
contaminar leitura bull com bear puro). Determinístico, causal (D1 shift D-1), sem outcome como predicado, sem
ID-fit. Engine/decisions/produção intocados. **Pronto para o Cris avaliar por PLOTAGEM** (ver o que se perde/ganha).

## Gate
- **BLOCK_BEAR_MARKDOWN:** d1_macro_leg=MACRO_BEAR_LEG OU (macro_broken & regimeB_combined<0).
- **BLOCK_RANGE_CHOP:** MACRO_RANGE/MACRO_TRANSITION sem macro-bull (combined≤0, weekly_slope≤0).
- **CARVE-OUT PRESERVE_BOTTOM_TURN** (override do bloqueio): climax OU (rsi_min8≤32 + reclaim_body≥0.4 + demanda defendida). v2 trocou o sinal errado (drop20≥2.5) por oversold+reclaim+demanda.

## Resultado (gate v2)
| set | bloqueados | leitura |
|---|---|---|
| A (must-preserve winners) | **3/26** | perdas a evitar |
| B (bear/range bad trades) | **4/18** | alvo (T9, T11, T15, T42) |
| C (ambíguo) | 7/18 | misto |

- **Preservação: 23/26 A** mantidos (v1 22/26 → v2 23/26 ao corrigir o carve-out).
- **Bloqueio (alvo):** 4 B bear/range losers (T9, T11, T15 losers + T42 macro-bear genuíno) + 7 C.
- **Late-top-em-bull (T2/T3/T4/T16/T18/T20/T23/T25/T26/T40) NÃO bloqueados** — correto: é o resíduo auction-irredutível, NÃO o alvo deste gate.

## As 3 perdas de A (o tradeoff difícil — para PLOTAGEM)
Diagnóstico do mecanismo (não ID-fit):
- **S15 RECUPERADO** pelo carve-out v2 (fundo nov/2022: rsi_min 29, reclaim 1.3, demanda).
- **S13** (jul/2022): fundo oversold (rsi_min 27.9, reclaim 0.48) MAS **demand_ABSENT** → carve-out (que exige demanda) não dispara. É "a entrada que T27 deveria ter sido". Recuperá-lo exige **relaxar a exigência de demanda** (risco: deixar passar bear-pullbacks).
- **S7, S8** (2020-11 / 2021-04): reclaims **bull em correções macro_broken** — NÃO são fundos (rmin 33.7 / 57). É o teu caso **"regime D1 atrasado"** (marca BEAR num pullback bull). Recuperá-los exige um carve-out separado "bull-context-apesar-de-bear-flag" (demanda+contexto-bull-maior) — **o mais arriscado** (pode abrir a porta a bear-losers).

## Conclusão honesta
- **Bloqueio funciona** para bear-markdown/range losers (4 B + 7 C), com **preservação alta (23/26 A)**.
- **As 3 perdas são o núcleo difícil que o Cris previu:** a tensão fundo/virada-vs-bear-markdown e o regime-atrasado.
  Cada recuperação tem um **custo de risco** (relaxar demanda; confiar local sobre regime atrasado).
- **NÃO iterei mais o carve-out** (mais ajuste = ID-fit/overfit). A decisão do tradeoff é **visual/discricionária do Cris**.

## Próximo passo
Cris avalia por **plotagem** (pausar daemon → long_position canônico): ver os 4 B bloqueados, os 7 C, e as 3 perdas
de A (S7/S8/S13) — decidir se vale recuperar S13 (relaxar demanda) e/ou S7/S8 (carve-out regime-atrasado), ou aceitar
as perdas. Tudo nos 62; sem 276/OOS. Artefatos: `l2_bpt_bear_leg_block_gate_62.csv` (v1), `..._v2_62.csv` (v2).
