# AUDITORIA DA RODADA 367c2e8 — relatório

**2026-06-22.** Auditoria crítica do processo da rodada MACRO READING POLISH / AUTOMATION-PATH (commit 367c2e8).
Nenhum experimento novo rodado. Nada operacional tocado. DA externo = `FAIL_SUPERFICIAL_GATE_REGRESSION`.

## 1. A rodada foi profunda ou superficial?
**Superficial.** Reduziu a leitura macro a uma feature `macro_phase` e a um gate `TAKE=BULL_RUN`.

## 2. Rodou engine completo ou não?
**Não.** O engine de 9 especialistas (`macro_structural_specialists.py`) existe e **não foi invocado**. Os "4
specialist agents" reportados foram escritos à mão, não spawnados. Só o DA foi agente real.

## 3. Esqueceu features/camadas?
**Sim, praticamente todas.** `feature_coverage_audit.csv`: 26 camadas auditadas, **1 usada** (macro_phase).
Ignoradas e marcadas `SIM_OBRIGATORIO` no rerun: sup_cat, supply broken/rejecting, fuel/clean-sky,
momentum/legpos, capit+rsi, risk_sl, D1 macro_reader_leg rico, e o próprio engine de 9 especialistas.

## 4. A macro_phase é útil?
**Marginalmente, e rebaixada.** Estruturalmente é "preço a ≤4% da máxima de 126d + acima SMA200" = relabel de
"perto da máxima". 89% da edge em 2023-26 e WR 43.5% no bull 2020 real ⇒ **codifica recência do melt-up
2023-25, não regime estrutural** (artefato A1'/drift-bull que o canon §7 nomeia). Vale **só como termo fraco de
evidência condicional** dentro do engine (inputs `dist_from_126d_high` + `close_vs_SMA200`, **sem threshold**),
onde momentum/auction/fuel podem contradizê-la no topo — **nunca como gate/policy**.

## 5. A policy TAKE=BULL_RUN deve ser mantida?
**Não como policy.** Apenas como candidato parcial rebaixado (`OVERFIT_REJECTED`). Contra bear_leg_v3 (13/16
runners) ela **perde** convexidade (9/16); o "melhora em TODAS as métricas" valia só contra o baseline fraco
(visual_anchored 5/16) = comparison-selection bias.

## 6. Precisa rerun?
**Sim.** Rerun com engine completo, classificado como `NEEDS_RERUN_WITH_FULL_ENGINE`.

## 7. Escopo correto do rerun
1. **Invocar de fato `macro_structural_specialists.py`** — os 9 especialistas, convergência por episódio.
2. **Cruzar** macro_phase (sem threshold, como input fraco) com sup_cat, supply broken/rejecting, fuel,
   capit+rsi, legpos×momentum, demand, SVP/acceptance, risk_sl.
3. **Remover o threshold fitado** — substituir por convergência estrutural (canon §3/§7).
4. **Comparar contra bear_leg_v3** (baseline forte omitido), não só visual_anchored.
5. **null/permutation + ablation + jackknife + robustez ±20% + sub-janelas temporais** — tudo DENTRO dos 276
   (SEM OOS/cross-asset — travado).
6. **Salvar o script gerador** (reprodutibilidade) e auditar o gerador do daily file p/ fechar o look-ahead.
7. **Reportar o drought de 18 meses (17 episódios, 2020-07→2022-01) como o blocker prop-firm headline**, não
   um footnote de streak 15.

## 8. Camadas obrigatórias no rerun
Engine de 9 especialistas · sup_cat/supply/fuel · capit+rsi · legpos×momentum · demand · SVP/acceptance ·
risk_sl/structural SL · D1 macro_reader_leg rico · comparação bear_leg_v3 · visual-anchored como evidência.

## Causa do losing streak (resposta a "o que macro_phase não viu")
`losing_streak_audit.csv` (17 episódios reais): supply overhead (SUPPLY_NEAR_AND_REJECTING / SUPPLY_BLOCKS_TARGET
= fuel baixo) em ~metade; `MACRO_RANGE`/`MACRO_TRANSITION` no leitor rico que a macro_phase **sobrescreveu** para
BULL_RUN; um `FALLING_KNIFE` (2021-11-22); e o topo macro exato de 2020-08 (ATH 2075) ainda marcado BULL_RUN
(feature lagging). **A macro_phase entrou em topos/ranges porque "dist da máxima" só cai DEPOIS do topo formado.**

## Classificação final
**`FAIL_SUPERFICIAL_GATE_REGRESSION` + `NEEDS_RERUN_WITH_FULL_ENGINE`.** A `macro_phase` é uma peça (evidência
condicional fraca), não a leitura macro sofisticada necessária. O resultado 367c2e8 fica **rebaixado a
descoberta parcial de feature**; a policy não é mantida. Honestidade registrada: a falha foi de disciplina de
processo, não de dado.

DA = `FAIL_SUPERFICIAL_GATE_REGRESSION`. Outputs: `results/l2_bpt_macro_polish_367c2e8_process_inventory.csv`,
`..._feature_coverage_audit.csv`, `..._prior_specs_audit.csv`, `..._losing_streak_audit.csv`,
`..._da_audit.csv`, `results/l2_bpt_macro_phase_feature_audit.csv`,
`docs/XAU_4H_MACRO_POLISH_367C2E8_SELF_AUDIT.md`.
