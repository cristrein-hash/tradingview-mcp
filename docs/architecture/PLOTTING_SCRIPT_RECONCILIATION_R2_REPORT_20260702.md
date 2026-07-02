# PLOTTING SCRIPT RECONCILIATION — BATCH R2 REPORT (2026-07-02)

**Natureza:** 100% declarativo — 1 linha de banner inserida na linha 2 (após shebang) de cada ficheiro. **Zero mudança funcional** (provado: `git diff --numstat` = exatamente +1/−0 em todos os 14). Zero chart/MCP/TradingView/produção/RAW; zero width/output/draw behavior alterado.

## 1. Ficheiros marcados (14) e banner aplicado

### `LEGACY_PRE_CANON / DO_NOT_USE_AS_CANONICAL` + `PLOTTING_CANON_MASTER_REQUIRED` (8 — regime_turnstate_engine/validation/)
`_plot_l2_base_trades_2023.py` · `phase29_plot_70_boxfloor.py` · `phase34_plot_regime_thirds.py` · `phase46_plot_skeleton_fundo.py` · `phase49_plot_zona_all.py` · `phase53_gen_v3_plot.py` · `phase55_capit_letrun_plot.py` · `phase57_plot_l2extra.py`
**Por quê:** geradores de dados/JSON de plot com convenção pré-canon (width 12, labels R-value); outputs históricos válidos como registro, mas a convenção não pode ser copiada para novos plots.

### `HISTORICAL_ONE_SHOT / DO_NOT_USE_AS_CANONICAL` + `PLOTTING_CANON_MASTER_REQUIRED` (4 — 15M sem draw_clear)
`plot_swept_keep_window.py` · `plot_fixed_base_window.py` (width 8) · `plot_engine7_cell.py` (width 12) · `plot_entry2_selected.py` (width 10)
**Por quê:** células/janelas de feature de junho/2026, executadas 1×; widths originais preservados (Decisão Cris 2026-07-02: não normalizar one-shots).

### `EXCEPTION_PLOT` (2 — 15M exceções pontuais)
- `plot_candidates_labels.py` — text-only autorizado PONTUALMENTE pelo Cris 2026-06-26; **DO_NOT_REUSE** sem nova autorização (canon = long_position+label, nunca text-only).
- `plot_v2_visual.py` — `EXCEPTION_PLOT / REPORT_MODE_REQUIRED`: screenshots autorizados só para este engine (Cris 2026-06-26); reports devem declarar `color_mode` (label verde-only ≠ outcome-mode completo).

## 2. Confirmação de zero mudança funcional

- `git diff --numstat`: **14 ficheiros, todos exatamente +1 inserção / 0 deleções** — só o banner.
- Nenhuma linha de código tocada; nenhum width/label/cor/gate/output alterado.
- `py_compile` **14/14 OK**.
- Safety report: **BLOCKER=0 · WARNING=1 (Caminho B TRUE_RISK) · INFO=50** — inalterado.
- Nenhum script precisou de mudança funcional durante o R2 (regra "parar e reportar" não foi acionada).

## 3. Riscos remanescentes

- Banners não impedem execução — os 4 one-shots 15M deste lote **não têm draw_clear** (aditivos), risco de re-execução é só poluição visual; os que limpavam chart já foram gated no R1.
- `plot_v2_visual.py` mantém captura de screenshot (exceção autorizada) — banner exige declaração em report; revogação da exceção = decisão futura do Cris.
- P3 deferred (exit-code do script-referência; import inline do t8; posição de label plot_new_only) — registrados, sem risco operacional.

## 4. Rollback

`git revert <commit R2>` — remoção limpa de 14 linhas de comentário; nenhum efeito colateral possível.

## 5. Estado da reconciliação pós-R1+R2

- 11/11 chamadores draw_clear gated (R1) · 5 reusáveis com width canônico (R1) · 14 legacy/one-shot/exceções marcados (R2) · script-referência alinhado ao MASTER (R1).
- **Pendente:** PLOTTING_CANON_AGENT / workflow versionado (próximo bloco, sob autorização) · P3 deferred.
