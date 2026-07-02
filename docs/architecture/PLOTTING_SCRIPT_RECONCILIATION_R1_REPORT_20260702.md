# PLOTTING SCRIPT RECONCILIATION — BATCH R1 REPORT (2026-07-02)

**Escopo executado:** 16 ficheiros, patches mínimos, zero chart/MCP/TradingView, zero produção/RAW, zero lógica de trading, zero dados/outcomes alterados.
**Base:** `PLOTTING_SCRIPT_RECONCILIATION_PLAN_20260702.md` (aprovado) · `PLOTTING_CANON_MASTER.md` (autoridade).

## 1. Ficheiros alterados (16) — risco original → patch aplicado

### Script-referência (P0)
**`alert-bridge/draw_xau_4h_trades.py`** — risco: draw_clear incondicional (L239) + screenshot incondicional (violação canon §5, achado durante o patch) + corpo stale (label R-value, largura=horizon).
Patch: **(a)** `draw_clear` gated por `--authorized-clear`, default = NO_CLEAR com mensagem clara + plotagem ADITIVA (`--clear-only` sem autorização = bloqueado, exit 1) · **(b)** screenshot gated por `--screenshot`, default = `SCREENSHOT_SKIPPED` declarado · **(c)** banner de autoridade do MASTER no docstring · **(d)** largura da caixa = nova constante `BOX_BARS=20` × `BAR_SECONDS=14400` no `point2` — **`HORIZON_BARS=10` INTACTO** (participa do cálculo de `close_R`; outcome não foi tocado, comentário explícito no código) · **(e)** label → `#<k+1>` cronológico a `entry + 0.5×R_dollars` (cor outcome-mode mantida).

### Gates draw_clear em one-shots históricos (10) — HISTORICAL_ONE_SHOT / DO_NOT_USE_AS_CANONICAL
- 7×15M (`plot_substrate4`, `plot_flow_tagged`, `plot_cleansky`, `plot_nas_cut`, `plot_choch`, `plot_sweptsempre_window`, `plot_sweptsempre_bull`): banner no site + gate — sem `--authorized-clear` → **ABORT antes de qualquer desenho** com `DRAW_CLEAR_BLOCKED` (json), `c.stop()` e exit 1. **Width original (8) mantida** (Decisão 6 Cris).
- 3×4H L2 v1 (`plot_lineB_55new_only`, `plot_conv_le1_removed_trades`, `plot_lineB_k2_only`): banner + gate — sem flag → `sys.exit("DRAW_CLEAR_BLOCKED …")`.

### Widths de scripts REUSÁVEIS (5)
- `my-strategy/research/revalidation/l2_plot_4h.py`: WIDTH **6 → 20** (canon 4H).
- `plot_chosen_canonical.py`, `plot_5atr_a2.py`, `plot_5atr_a2_h1eff.py`, `plot_5atr_regime170.py` (15M, aprovados 06-27): WIDTH **12 → 10** (canon 15M) + comentário citando MASTER §10.

## 2. Confirmação NO_CLEAR default

Nenhum caminho de código restante executa `draw_clear` sem `--authorized-clear`. Repo-wide pós-patch: 11/11 chamadores gated. Sem fallback silencioso — todo bloqueio imprime mensagem explícita (mensagem clara/ABORT), conforme regra dura da Decisão 3.

## 3. Testes executados

- `python3 -m py_compile` nos **16/16** ficheiros → OK.
- `python3 alert-bridge/test_canonical_plotting.py` → **PASS** (helper `price_to_ticks_offset` intacto: 1000/3000 ticks; cores; hard-stops direcionais).
- `--help` do script-referência → novas flags parseiam; caminho de abort pré-MCP (pause flag ausente) funciona **sem tocar MCP/chart**.
- Gates internos dos one-shots não são executáveis sem MCP (ficam após `client.start()`) — validados por py_compile + revisão do diff; primeiro uso real (autorizado) confirmará em runtime.
- Safety report: **BLOCKER=0 · WARNING=1 (Caminho B TRUE_RISK) · INFO=50** — inalterado.

## 4. Scripts que continuam exigindo autorização explícita (por design)

- QUALQUER uso de `--authorized-clear` (11 scripts) = só com autorização do Cris por execução.
- `--screenshot` no script-referência = só a pedido explícito.
- Os 10 one-shots históricos = `DO_NOT_USE_AS_CANONICAL`; re-execução completa requer autorização mesmo com flag.
- `plot_script.py` (v1_4g_rws_a6) segue DEPRECATED_DO_NOT_USE (não tocado — banner pré-existente).

## 5. Observações (fora de escopo R1, registradas)

- `draw_xau_4h_trades.py`: `main()` retorna código mas o processo sai com 0 (chamada sem `sys.exit(main())`) — pré-existente, não tocado (Karpathy #3); candidato a P3/futuro.
- Batch R2 (banners declarativos em legacy pré-canon/exceções) pendente de execução após validação deste R1.

## 6. Rollback

`git revert <commit R1>` — patches aditivos/mecânicos; zero dado/output alterado; comportamento antigo dos gates acessível via flag ou git history.
