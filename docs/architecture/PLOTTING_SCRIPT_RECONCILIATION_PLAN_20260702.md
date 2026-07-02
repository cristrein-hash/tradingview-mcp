# PLOTTING SCRIPT RECONCILIATION PLAN (2026-07-02)

**Base:** `docs/project_authority/PLOTTING_CANON_MASTER.md` (APPROVED) + `PLOTTING_MEMORY_AUDIT_20260702.md`.
**Modo desta fase:** read-only — **nenhum script editado, nenhum chart/TradingView/MCP tocado, nenhuma produção**. Verificações extras executadas via grep/read (widths exatos + chamadores reais de `draw_clear`).

## 0. Achados novos desta fase (além do audit)

1. 🔴 **`alert-bridge/draw_xau_4h_trades.py` chama `draw_clear` INCONDICIONALMENTE (L239)** — o script-referência do canon viola o NO_CLEAR default do master. O audit tinha flagado só o corpo stale (label R, width 10); o clear é mais grave.
2. **11 chamadores reais** de `draw_clear` no repo (o audit flagou 5): o de referência acima + 7 em 15M (`plot_substrate4/flow_tagged/cleansky/nas_cut/choch` L112 · `plot_sweptsempre_window/bull` L120) + **3 em 4H L2 v1** não inventariados antes (`plot_lineB_55new_only`, `plot_conv_le1_removed_trades`, `plot_lineB_k2_only`).
3. As demais ~17 menções a draw_clear são **declarações negativas** ("NÃO draw_clear") — compliant.
4. Widths 15M exatos: **8** (substrate4, swept_keep, sweptsempre×2, fixed_base, flow_tagged, cleansky, nas_cut, choch) · **10** (entry2, deeprange, reversals, rb_range, strategy, candidates) · **12** (engine7, 5atr_a2, 5atr_a2_h1eff, 5atr_regime170, chosen).

## 1. Classificação por script — 4H

| Script | Classificação | Risco | Patch mínimo proposto | Prio | Dry-run | Toca chart/clear? | Autorização | 
|---|---|---|---|---|---|---|---|
| `alert-bridge/draw_xau_4h_trades.py` | **STALE_BODY_RISK + DRAW_CLEAR_RISK** (helper canônico OK) | referência copiável com canon velho + clear incondicional | (a) gate: `draw_clear` só com flag `--authorized-clear`, senão ABORT; (b) banner topo "HELPER CANONICAL / BODY LEGACY — ler MASTER"; (c) label→`#id` + width→20 no corpo | **P0** | `py_compile` + `test_canonical_plotting.py` (helper intacto); sem chart | corpo sim (gate remove) | **Sim** (edita referência) |
| `my-strategy/research/revalidation/l2_plot_4h.py` | **WIDTH_DRIFT** (6) | sliver invisível | `WIDTH=6`→`20` (1 linha) | P1 | py_compile | não | Sim |
| `plot_lineB_55new_only.py` · `plot_conv_le1_removed_trades.py` · `plot_lineB_k2_only.py` (L2 v1) | **DRAW_CLEAR_RISK** (chamadores reais, review one-shot histórico) | re-execução acidental limpa chart do Cris | banner `LEGACY ONE-SHOT — DO NOT RERUN` + mesmo gate `--authorized-clear` | P1 | py_compile | sim (gate remove) | Sim |
| `pipeline/qualification/plot_capit_rsi_trades.py` | **CANONICAL_OK** (width 20, #N, ticks, NÃO clear declarado) | — | nenhum | — | — | não | não |
| `XAU_4H_BREAKOUT_D1A/v1/plot_t8_canonical.py` | **CANONICAL_OK** (hard stops, NO clear) | duplicação do helper inline | (P3 opcional) importar helper em vez de inline | P3 | py_compile | não | Sim se P3 |
| `L1_…/reports/plot_new_only.py` · `plot_poc_cut8.py` | **CANONICAL_OK** c/ variante (azul sem-outcome; label `target+0.4ATR`) | variante de posição não declarada | nenhum agora; report futuro declara `label_mode` variante | P3 | — | não | não |
| `candidates/xau_4h_reversal_v1_4g_rws_a6/plot_script.py` | **DEPRECATED_DO_NOT_USE** (bug preço absoluto, banner presente) | rodar por engano | nenhum (banner já protege) | — | — | não | não |
| `plot_all276_winloss_blue.py` · `plot_skip_union_cut_red.py` · `plot_reading_critical_blue.py` · `plot_unknown_blind.py` · `plot_v1_review.py` (L2 v1) | **CANONICAL_OK** legacy-review (aditivos, NÃO clear, exit legacy DECLARADO na geometria) | leitura como outcome validado | nenhum; nota: replots futuros marcam `EXIT_ASSUMED_LEGACY` quando geometria legacy | P3 | — | não | não |
| `regime_turnstate_engine/validation/phase*_plot_*.py` (7 geradores JSON) | **STALE_DOCSTRING_ONLY + WIDTH_DRIFT** (width 12, R-labels, pré-canon) | copiar convenção velha | banner `LEGACY PRE-CANON — outputs históricos; novo plot segue MASTER` (sem mudança funcional) | P2 | py_compile | não (geram JSON) | Sim |

## 2. Classificação por script — 15M (`research/xau_15m_bb_nas_leonardo/`)

| Script | Classificação | Risco | Patch mínimo proposto | Prio | Dry-run | Toca chart/clear? | Autorização |
|---|---|---|---|---|---|---|---|
| `plot_substrate4` · `plot_flow_tagged` · `plot_cleansky` · `plot_nas_cut` · `plot_choch` · `plot_sweptsempre_window` · `plot_sweptsempre_bull` (7 chamadores) | **DRAW_CLEAR_RISK** (+ width 8, feature one-shots) | limpar chart vivo do Cris | gate `--authorized-clear` (ABORT default) + banner `LEGACY FEATURE ONE-SHOT`; width 8 mantido c/ banner (não re-executáveis sem gate) | **P1** | py_compile | sim (gate remove) | Sim |
| `plot_swept_keep_window` · `plot_fixed_base_window` (width 8, sem clear) | **STALE_DOCSTRING_ONLY** (one-shot, width 8) | menor | banner legacy; width 8 declarado se re-executar | P2 | py_compile | não | Sim |
| `plot_chosen_canonical` (12) · `plot_5atr_a2` (12) · `plot_5atr_a2_h1eff` (12) · `plot_5atr_regime170` (12) | **WIDTH_DRIFT** (plotters de estratégia REUSÁVEIS, aprovados 06-27) | replots futuros fora do canon 10 | `WIDTH=12`→`10` (1 linha cada) | P1 | py_compile | não | Sim |
| `plot_engine7_cell` (12) · `plot_entry2_selected` (10) | STALE_DOCSTRING_ONLY (one-shot cells) | menor | banner legacy (engine7: width 12 declarar); sem mudança funcional | P2 | py_compile | não | Sim |
| `plot_strategy_canonical` (10, direction-mode declarado) | **CANONICAL_OK** | — | nenhum; reports futuros declaram `color_mode=direction` | — | — | não | não |
| `plot_candidates_canonical` (10, direction-mode) · `plot_reversals_canonical` (10, F#/T#) · `plot_deeprange_aug2025`/`plot_rb_range` (10, azul) | **CANONICAL_OK** (variantes sancionadas §7 do master) | — | nenhum | — | — | não | não |
| `plot_candidates_labels.py` | **DEPRECATED_DO_NOT_USE** (exceção text-only pontual autorizada 06-26; nunca reutilizar) | reuso indevido | banner `ONE-TIME EXCEPTION — DO NOT REUSE` | P2 | — | não | Sim |
| `plot_v2_visual.py` | **COLOR_MODE_AMBIGUOUS** (label só verde) + exceção screenshot por-engine | leitura errada de outcome | banner declarando `color_mode` + exceção screenshot registrada; sem mudança funcional | P2 | py_compile | não | Sim |
| `cross_check_plotted.py` | **CANONICAL_OK** (verificador read-only) | — | nenhum | — | — | não | não |

## 3. Batches propostos (lote pequeno, patch mínimo, diff revisável)

- **Batch R1 (P0-P1, crítico — gate draw_clear + referência):** `draw_xau_4h_trades.py` (gate+banner+corpo) · 7 chamadores 15M (gate+banner) · 3 chamadores L2 v1 (gate+banner) · `l2_plot_4h.py` width 20 · 4 plotters de estratégia 15M width 10. **16 ficheiros, mudanças mecânicas pequenas.**
- **Batch R2 (P2, banners declarativos):** phase-plotters regime engine · one-shots 15M (swept_keep, fixed_base, engine7, entry2) · `plot_candidates_labels` · `plot_v2_visual`. **Sem mudança funcional — só banners.**
- **P3 (opcional, adiável):** t8 import helper · posição de label plot_new_only.

## 4. Regras de execução dos patches (quando autorizados)

- Nenhuma execução de plot; **dry-run = `py_compile` de cada ficheiro editado + `test_canonical_plotting.py`** (helper) — zero MCP/chart.
- Outputs de dados NÃO são alterados (patches não mudam CSV/JSON gerados; width/gate afetam só desenho futuro).
- `draw_clear` pós-patch: ABORT por default com mensagem "requires --authorized-clear (Cris)"; comportamento antigo só com a flag = **DRAW_CLEAR_REQUIRES_EXPLICIT_APPROVAL implementado em código**.
- Commit por batch com diff stat; safety report após cada batch.

## 5. Rollback

- `git revert <commit do batch>` — patches são aditivos/mecânicos, sem migração de dados.
- Scripts one-shot históricos preservam comportamento original acessível via flag (gate) ou git history.
- Nenhum output/dado tocado → rollback = puro git.

## 6. Critérios de aceitação desta fase (cumpridos)

- [x] Master + audit lidos · [x] scripts §13 mapeados + **8 scripts extra** descobertos (3 chamadores 4H L2 v1 + verificação exaustiva de widths) · [x] classificação por script (taxonomia Cris) · [x] patch mínimo + prioridade + dry-run + chart-touch + autorização por script · [x] 4H/15M separados · [x] rollback · [x] **zero edição de script** · [x] zero chart/produção · [x] commit local sem push.

## 7. Decisões pendentes do Cris

1. Aprovar **Batch R1** (16 ficheiros, crítico) — inclui editar o script-referência.
2. Aprovar **Batch R2** (banners declarativos).
3. P3 opcional: executar ou adiar.
4. Confirmar que one-shots históricos ficam com width original + banner (em vez de normalizar 8→10 em scripts que não devem ser re-executados).
