# Mechanical Rebuild Round 1 — Summary (XAU_4H_BREAKOUT_D1A)

**Data:** 2026-06-17 · **NOT_VALIDATION — research round, hypotheses-only.** · **Gross R (sem custos).**
**Engine:** `run_mechanical_rebuild_v1.py` (read-only, RAW-first, determinístico). 4H RAW 2016-2026, 15.434 barras, grid 02/06/10/14/18/22 UTC. RSI coverage 98,4%. D1a via CAUSAL `close_time≤bar_open`.

## Métricas por variante (gross)

| Var | Gates | n | tgt | stop | be | time | sumR | avgR | PF | WR | maxDD | streak |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| V0 | trigger T1-T4 | 393 | 32 | 162 | 100 | 99 | +90.96 | 0.232 | 1.55 | 30% | -10.93 | 15 |
| V1 | +ADX | 301 | 23 | 134 | 68 | 76 | +56.82 | 0.189 | 1.42 | 30% | -15.75 | 11 |
| V2 | +EMA stack (R2+R3) | 246 | 25 | 98 | 62 | 61 | +82.03 | 0.334 | 1.82 | 32% | -12.35 | 16 |
| V3 | +ATR expanding | 242 | 18 | 87 | 54 | 83 | +69.42 | 0.287 | 1.75 | 34% | -8.04 | 9 |
| V4 | +EMA50 slope | 317 | 28 | 125 | 87 | 77 | +84.36 | 0.266 | 1.65 | 29% | -12.17 | 16 |
| **V5** | full regime R1-R5 | 111 | 11 | 48 | 22 | 30 | +39.74 | 0.358 | 1.79 | 33% | -8.00 | 9 |
| V6 | +D1a only | 283 | 25 | 110 | 78 | 70 | +80.51 | 0.285 | 1.72 | 30% | -12.67 | 15 |
| **V7** | full regime + D1a | 88 | 11 | 35 | 18 | 24 | +44.65 | 0.507 | 2.20 | 35% | -5.45 | 9 |

## Trade-level SHIFT audit (D1a)

| Var | with_d1a | d1a_eval | same_day_selected | close_time_gt_bar_open | missing_daily |
|---|---|--:|--:|--:|--:|
| V6 | true | 517 | **0** | **0** | 0 |
| V7 | true | 121 | **0** | **0** | 0 |

**0 leaks** — CAUSAL alignment confirmado trade-level. (Critério: same_day_selected=0, close_time_gt_eval=0 → PASS; V6/V7 NÃO bloqueados.)

## Pré/pós-2020 (sumR gross)

| Var | 2016-2019 (n / sumR) | 2020-2026 (n / sumR) |
|---|---|---|
| V0 | 131 / +12.6 | 262 / +78.3 |
| V5 | 33 / +9.3 | 78 / +30.5 |
| V7 | 22 / +11.4 | 66 / +33.2 |

## Observações (hipóteses, não veredito)

- **D1a (V5→V7):** corta ~23 trades, sumR +39.7→+44.7, PF 1.79→2.20, DD -8.0→-5.45. Direção consistente com a prosa D1a (poda losers near-BE), mas lift de sumR pequeno e dentro de ruído com n=88.
- **ADX solo (V0→V1):** baixou R e PF — provável ruído/artefato de uma rodada, NÃO conclusão "ADX prejudica".
- **V7 PF 2.20:** carregado por 11 targets (cap +4R, sem monumentais), ~33% de sumR em 2025; gross; selecionado entre 8 variantes. **Não é edge** — point estimate com CI larga.
- 2022 (chop_inflation_bear) fraco/negativo na maioria; 2020/2024/2025 carregam.

*Gross R, sem custos. Outputs: `mechanical_rebuild_v1_{trades.jsonl,plot_ready.csv,summary.json,shift_audit.json}`. Plot-ready gerado, NÃO plotado. Ver `docs/XAU_4H_BREAKOUT_D1A_MECHANICAL_REBUILD_ROUND1_RESULTS.md`.*
