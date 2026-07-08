# OPEN STATE CHECKPOINT — 2026-07-08

**Cris.** Checkpoint completo e seguro do estado aberto/não-commitado/não-pushado/não-sincronizado. Modo: inventory/doc-first. Sem novo research, sem produção, sem push sem autorização.

## 1. Git state
- **HEAD = `b517312`** · **origin/main = `b517312`** → **sincronizados; ZERO commits locais pendentes de push.**
- Working tree: **sem modificações tracked.** Só untracked (secção 2).
- Últimos commits pushados (sessão): `a32b25a` (correção N96) · `c05dbc1` (RANGE/distribution) · `737ff9b` (D-bear) · `059fd5d` (aprovação N96) · `b517312` (protocolo XAU 15M).
- Safety: BLOCKER=3 (pré-existentes `catalog_*`, report-only), WARNING=1, INFO=50. **Zero risco produção/RAW/chart.**

## 2. Arquivos locais untracked (classificação)
| ficheiro | classe | motivo |
|---|---|---|
| `research/l2_bpt_17_reproduce.py` | KEEP_COMMIT | reproduz os 17 aprovados + painel + MFE (fundacional) |
| `research/l2_bpt_read_cris_exits.py` | KEEP_COMMIT | leitor MCP dos desenhos do Cris |
| `research/l2_bpt_read_targets_mcp.py` | KEEP_COMMIT | lê alvos extendidos (+87.6R teto) via MCP |
| `research/l2_bpt_realistic_target_exit.py` | KEEP_COMMIT | cenário realista +81.6R (first-touch causal) |
| `research/l2_bpt_target_vs_sl_timing.py` | KEEP_COMMIT | diagnóstico SL-vs-alvo timing |
| `research/l2_bpt_trailing_exit_test.py` | KEEP_COMMIT | **regime-flip +105/+399R (headline trend-exit)** |
| `research/l2_bpt_plot_canonical.py` | KEEP_COMMIT | plot canónico 4H dos 17 (reprodução) |
| `research/l2_bpt_exit_forward_diagnostic.py` | NEEDS_REVIEW | escrito mas NÃO corrido; redundante c/ trailing_exit_test; rever/remover |
| `research/results/l2_bpt_17_trades.csv` | KEEP_COMMIT | fonte dos 17 (entry/sl/exit/R), pequeno |
| `research/results/l2_bpt_cris_targets.{csv,json}` | KEEP_COMMIT | alvos do Cris lidos por MCP, pequeno |
| `research/results/l2_bpt_cris_exits_raw.json` | KEEP_COMMIT | dump bruto MCP, pequeno |
| `research/xau_15m_bb_nas_leonardo/make_n96_valid_plot_source.py` | KEEP_COMMIT | gera fonte dos 83 válidos N96 |
| `research/xau_15m_bb_nas_leonardo/n96_valid_trades.csv` | KEEP_COMMIT | fonte de plot 83 válidos, pequeno |
| `research/xau_15m_bb_nas_leonardo/plot_n96_valid_canonical.py` | KEEP_COMMIT | plot canónico 15M dos 83 válidos |
| `research/xau_15m_bb_nas_leonardo/remove_n96_cut_trades.py` | KEEP_COMMIT | remoção cirúrgica dos 13 cortados (ferramenta) |

Nenhum output massivo, nenhum RAW, nenhum secret. Tudo pequeno e reproduzível.

## 3. Estado XAU 15M N96
- **`XAU_15M_N96_ENTRY_ENGINE = USER_APPROVED_NOT_PRODUCTION`** (Cris 2026-07-08, commit `059fd5d`, status master §4.6).
- Inclui **filtro intra-BEAR capitulation** (BEAR v5 causal, SKIP se `1D_px_vs_ema≥0`): corta **13 losers / 0 winners**, +4…+13R, DA=PROFITABLE_BUT_FRAGILE.
- **RANGE / BULL-excess / D-deep = review-layers, NÃO gates** (docs RANGE/D-bear rounds, commits `c05dbc1`/`737ff9b`).
- Gestão humana preservada: #24,32,64,77. **NÃO produção/runtime/Telegram/broker/strategy_rules.**

## 4. Estado do protocolo
`XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 = ACTIVE` (commit `b517312`). Confirmado presente e a correr:
- `scripts/safety/run_xau_15m_lab_gate.py` (runner, `--help` OK) · `check_xau_15m_raw_lineage.py` · `check_xau_15m_structural_first.py` · `check_xau_15m_claims_ledger.py`.
- **Regra-mãe:** *sem `macro_regime` + `leg_state` + `family_label`, nenhum indicador vira evidência.* Sem `XAU_15M_LAB_GATE_PASS`, lab não está completo.

## 5. Estado L2/BPT trend-exit / regime-flip (EXPLORATORY)
Detalhe em `L2_BPT_TREND_EXIT_EXPLORATORY_CHECKPOINT_20260708.md`. Resumo honesto:
- Estudo criado; **DA executado** (2×). **Causalidade PASS — regime-flip NÃO é look-ahead** (FSM online byte-idêntico na era de trading).
- **SELECT-17:** let-run120 **+36.2R** / hold500-burro **+90.3R** / regime-flip **+105.3R** (retDD 26×, streak 3, DD −4.1). Versão online-causal: **+105.3R (idêntico)**.
- **FULL-245:** let-run120 **+52.5R** / hold500 **+257.6R** / regime-flip ~**+399.2R** (online-causal **+385.7R**; gap = warmup pré-2023).
- **Caveat central:** ~78% do ganho nos 17 é **HORIZONTE/exposição** (120→500 barras), não inteligência de regime; o detector adiciona só **~+15R** sobre hold500, sobre **2 topos macro in-sample**.
- **#6 = winner mecânico +1.15R** (CAP-driven), NÃO +3R. Os +3R do #6 = leitura discricionária/target estrutural do Cris, **ainda não mecanizada**.
- **Full-base DD/streak HOSTIL:** DD ~−72 / streak 22 (incompatível prop/FundedNext); a tameness dos 17 vem da seleção de entrada, não do exit.
- **Status: `EXPLORATORY / NEEDS_FORMAL_PREREG` — NÃO aprovado.**

## 6. Supabase delta pendente (a criar como seed, NÃO aplicar)
Seed: `supabase/seeds/memory_delta_open_state_checkpoint_20260708.sql`. Review: `SUPABASE_DELTA_OPEN_STATE_CHECKPOINT_REVIEW_20260708.md`. Registar (idempotente, sem RAW/candles/secrets/outputs massivos):
1. N96 approved not production.
2. XAU 15M protocol active.
3. L2/BPT trend-exit = EXPLORATORY / NOT_FOR_DECISION.
4. Untracked chart/research scripts pendentes de classificação/commit.

## 7. Decisões abertas
- Formalizar ou não o L2/BPT trend-exit (prereg formal vs arquivar).
- **#6:** aceitar mecânico +1.15R vs a tua leitura discricionária +3R (alvo estrutural).
- Extensão daily/HTF pós-2026-05-24/06-09 para forward/live.
- Destino final dos scripts de chart untracked (agora classificados KEEP_COMMIT).
- Quando abrir **XAU 15M SHORT** sob o protocolo novo.

## 8. Próximos blocos permitidos (NÃO iniciados)
- Aplicar o Supabase delta seed (com autorização).
- L2/BPT trend-exit prereg formal (full-base, DD/streak control, gap-model, DA).
- XAU 15M SHORT bootstrap + manifest (sob `XAU_15M_LAB_GATE`).
- Push deste checkpoint (aguarda autorização).
