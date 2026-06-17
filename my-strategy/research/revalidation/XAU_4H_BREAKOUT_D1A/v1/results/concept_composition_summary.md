# Concept Composition — Summary (XAU_4H_BREAKOUT_D1A)

**Data:** 2026-06-17 · **NOT_VALIDATION — research, hypotheses-only.** · **Gross R.**
**Engine:** reusa `run_mechanical_rebuild_v1` (causally audited, 0 SHIFT leaks). Sem gates/thresholds novos. D1a CAUSAL.

## Tiers (composições de gates existentes)

| Tier | Composição | n | sumR | PF | avgR | WR | maxDD | streak |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| T0 | trigger T1-T4 | 393 | +90.96 | 1.55 | 0.23 | 30% | -10.9 | 15 |
| T1 | +EMA stack | 246 | +82.03 | 1.82 | 0.33 | 32% | -12.4 | 16 |
| T2 | +ATR exp | 242 | +69.42 | 1.75 | 0.29 | 34% | -8.0 | 9 |
| T3 | +EMA stack +ATR | 154 | +49.62 | 1.81 | 0.32 | 34% | -9.3 | 13 |
| T4 | T3 +D1a | 122 | +49.74 | 2.06 | 0.41 | 35% | -9.45 | 12 |
| T5 | full regime +D1a (=V7) | 88 | +44.65 | 2.20 | 0.51 | 35% | -5.45 | 9 |
| T6 | full -ADX | 106 | +48.20 | 2.18 | 0.45 | 34% | -8.45 | 12 |
| T7 | full -slope | 101 | +43.48 | 2.05 | 0.43 | 37% | -5.45 | 8 |
| T8 | EMA stack +D1a | 206 | +86.10 | 2.06 | 0.42 | 34% | -11.5 | 17 |
| T9 | ATR exp +D1a | 170 | +51.37 | 1.80 | 0.30 | 34% | -10.8 | 9 |

## SHIFT audit (D1a tiers)
Todos T4-T9: same_day_selected=0, close_time_gt_bar_open=0, missing_daily=0 → **0 leaks**.

## Overlap (sinais independentes; base T0=914; todos tiers ⊆ T0)

- **EMA × ATR (T1 vs T2):** T1_only=269, T2_only=172, common=310, **jaccard 0.413** → set-complementares.
- T1→T3 (+ATR): dropa 269 = 66W/203L. T2→T3 (+EMA): dropa 172 = 52W/120L (corta majoritariamente losers).
- T3→T4 (+D1a): dropa 56 = 13W/43L, **indep sumR +0.39** (set near-zero — efeito denominador).
- ADX (34 sinais 7W/27L, −3.19R) e slope (17 sinais 7W/10L, +1.52R) → **dentro de ruído**.

membership_n: T0 914·T1 579·T2 482·T3 310·T4 254·T5 197·T6 231·T7 214·T8 501·T9 346.

## Leitura honesta (DA-incorporada)
- **Único achado robusto:** EMA × ATR complementares; EMA carrega PF-info real a alto N (1.55→1.82 sem colapsar N).
- **Resto (D1a/ADX/slope downstream de T3): blob estatístico** consistente com mecânica "trade-less → PF↑" num sistema 30%-WR. NÃO atribuir edge ortogonal.
- N colapsa 393→88 = **risco de interpolação**.

*Gross, in-sample, sem custos/OOS/visual/bootstrap. Ver `docs/XAU_4H_BREAKOUT_D1A_CONCEPT_COMPOSITION.md`.*
