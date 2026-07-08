# L2/BPT XAU 4H — Trend-Exit / Regime-Flip · Exploratory Checkpoint

**Cris 2026-07-08.** Estudo exploratório de gestão de exit por tendência. **Status: `EXPLORATORY_NOT_APPROVED`.** Não produção, não altera a régua aprovada (SL_CONTEXT + let-run HZ120 permanece a oficial).

## Objetivo
Cris: em macro-regime BULL o exit deve seguir a tendência (segurar enquanto o regime/estrutura aguenta, sair na quebra), não cortar no horizonte fixo de 120 barras. Testar se um exit causal de gestão-de-tendência recupera R sobre o let-run, sem look-ahead e sem aumentar losers.

## Gatilho: "dinheiro na mesa"
- Análise MFE da régua oficial: R capturado +36.2R vs MFE pico +102.7R. **DA #1 (mirage):** 69% do gap está em losers (pico intrabar não-capturável). Não é oportunidade sistemática.
- Alvos extendidos pelo Cris (lidos via MCP do `profitLevel` dos long_positions): teto-hindsight **+87.6R** (0 losers). **Cris rejeitou como exagero** (exceto #6). Cenário realista first-touch **+81.6R** (3 losers). **DA #2:** 67% (+54.5R) dos alvos ficam em preços NUNCA vistos à entrada (#17 +26%/+1024pts) = hindsight; metade causalmente-definível = +27.1R < let-run. **O let-run já captura o upside causal disponível via target.**

## Regras testadas (pré-registadas, causais, custo 0.35R)
1. **let-run HZ120** (baseline/oficial): stop-first, fecha às 120 barras.
2. **regime-flip (→BEAR)**: segura até o regime (phase10) virar BEAR; sai no close; SL stop-first; cap 500 barras.
3. **trail higher-low**: stop sobe sob cada higher-low confirmado; sai na quebra. (Pior — cortou no ruído.)

## Resultado bruto
| exit | FULL-245 | SELECT-17 |
|---|---|---|
| let-run HZ120 | +52.5R (DD−38, stk12) | +36.2R (DD−4.1, stk3) |
| hold-500 burro (sem regime) | +257.6R | +90.3R |
| **regime-flip** | ~+399.2R (DD−71.8, stk22) | **+105.3R (DD−4.1, stk3, retDD 26×)** |
| trail higher-low | −36.9R | +15.0R |

## Resultado DA (2 auditorias adversariais)
- **Causalidade = PASS.** Reimplementação FSM estritamente-online (só dados ≤ barra) = **byte-idêntica na era de trading** (onsets BEAR 2023-05-25, 2026-01-29/30). O filtro `≥15-bar significância` vive só na seleção de entrada (`bear_deep`), NÃO no rótulo de exit. **Regime-flip NÃO é look-ahead.**
- **Online-causal:** SELECT-17 = **+105.3R (100%, idêntico)** · FULL-245 = **+385.7R** (gap 13.5 vs +399 = warmup pré-2023, não futuro).
- **O ataque real:** ~**78% do ganho nos 17 é HORIZONTE** (120→500), replicável por hold-burro (+90.3R). O sinal de regime genuíno = **+15R** (17) / +141.6R (245), assente em **2 topos macro in-sample** (detector calibrado às ground-truth boxes do Cris que incluem esses topos) → **N≈2 eventos**. Só 4/17 saem por flip; 6 vão ao cap; 7 stopam.
- **#6:** R causal honesto = **+1.15R** (sai no CAP-500, nunca vê flip; ganho = exposição). **NÃO +3R.** Os +3R do Cris = alvo estrutural discricionário (2081), não mecanizado.
- **Execução/robustez:** full-base DD −57 a −72 / streak 22 = **hostil a prop**. Tameness dos 17 = da seleção de entrada, não do exit. Gap nos stops largos 2025 sub-modelado.

## Caveats
- Benchmark honesto do regime-flip = **hold-500 burro** (+90.3R nos 17), NÃO o let-run-120. O prémio do detector (+15R) é fino e in-sample (2 topos).
- Num bull secular, "segurar mais tempo" imprime R ∝ exposição, com DD/streak proporcionais.
- Não creditar o detector de regime além de ~2 topos calibrados in-sample.

## Status e próximo passo
- **`EXPLORATORY_NOT_APPROVED`.** A régua oficial L2/BPT continua **SL_CONTEXT + let-run HZ120**.
- **Próximo (não iniciado, requer autorização):** prereg formal de um "extended-horizon / trend-exit" — full-base, controlo de DD/streak, modelo de gap nos stops largos, benchmark vs hold-500, DA — antes de qualquer adoção. **Não produção.**

## Artefactos (reprodução)
`research/l2_bpt_17_reproduce.py` · `l2_bpt_read_targets_mcp.py` · `l2_bpt_realistic_target_exit.py` · `l2_bpt_target_vs_sl_timing.py` · **`l2_bpt_trailing_exit_test.py`** (headline) · `l2_bpt_plot_canonical.py` · `results/l2_bpt_{17_trades.csv,cris_targets.*}`.
