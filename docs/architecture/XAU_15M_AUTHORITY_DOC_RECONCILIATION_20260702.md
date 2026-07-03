# XAU 15M — AUTHORITY DOC RECONCILIATION (2026-07-02)

**Natureza: doc-only.** Zero scripts, zero RAW, zero coleta, zero backtest, zero plots, zero chart/TradingView/MCP, zero produção/runtime/Telegram/daemons. XAU SHORT intocado.
**Fonte:** `docs/architecture/XAU_15M_LONG_REGIME_READAPTATION_AUDIT_20260702.md` (aprovado) + Decisões Cris 2026-07-02 (A–E).

## Docs alterados, conflito original → correção aplicada

### 1. `00_PROJECT_OVERVIEW.md` (§7 Strategy Status Summary)
- **Conflito:** tabela de status não citava 15M (stale vs 04); também faltava o L2/BPT 4H aprovado.
- **Correção:** adicionadas 2 linhas — `XAU 15M LONG · swept-runner (base #4, regime-v5)` = USER_APPROVED_NOT_PRODUCTION, RAW-only/zero SLIM, sem produção/runtime, pendência única = slippage, ponteiro p/ 04 §3/§4.5; e `L2/BPT XAU 4H LONG · RTSE V2` = USER_APPROVED_NOT_PRODUCTION (ponteiro 04 §4.4).

### 2. `05_SYSTEM_ARCHITECTURE_CURRENT.md` (§3.4 e §3.6)
- **Conflito:** arquitetura não registrava a inexistência de runtime 15M nem o timeframe/dataset 15M.
- **Correções:** (a) nota pós-§3.4: **NÃO existe runtime 15M** (nenhum daemon/monitor/cron/LaunchAgent; `run_xau_15m_pullback_ohlcv.py` = coletor histórico offline); não assumir nem criar sem autorização. (b) timeframe canônico ganhou linha "15M for XAU 15M LONG research (approved strategy, not production)" + registro da cobertura RAW **2024-05→2026-02** e da extensão mar→jun-2026 como bloco futuro autorizado separadamente (nunca fora do `safe_backtest_window.sh`).

### 3. `07_INCIDENTS_AND_PROCESS_LESSONS.md` (Incident 6) — o mais crítico
- **Conflito:** wording pré-bug-de-ticks mandava "point2/stopLevel/profitLevel must be **absolute price levels**" — seguir isso **reintroduziria o bug de 2026-06-11** e contradiz o PLOTTING_CANON_MASTER.
- **Correção:** regra substituída pela correta (**OFFSETS EM TICKS**, mintick XAUUSD 0.01, fórmulas exatas, width 4H=20/15M=10), com aviso explícito de que o wording original era pré-bug e que **PLOTTING_CANON_MASTER prevalece** (autoridade + leitura obrigatória antes de plot).

### 4. `04_STRATEGY_STATUS_MASTER.md` (ponteiro mínimo — §4.5 novo)
- **Motivo:** registrar as decisões A/B/C/D do Cris no doc canônico de status: **v5 = detector canônico retido** (`REGIME_V5_CAUSAL_CANON_RETAINED`; v1-v4 superseded; sem recalibração por ora) · BEAR-jan-2026 = **MACRO_CONTEXT_REVIEW_LAYER pendente** (não override automático) · RAW termina 2026-02, extensão = `RAW_15M_EXTENSION_PLAN_MAR_JUN_2026` (bloco futuro separado) · slippage = pendência única OFICIAL_FN (só com manifest/sanity, bloco próprio) · re-adaptação na **linha atual** (RTSE = integração futura condicional).

## Por que doc-only

Os 5 conflitos do audit eram documentais (docs de autoridade stale vs estado real verificado). Corrigi-los ANTES de qualquer coleta/backtest/re-adaptação elimina o risco de uma fase futura seguir instrução errada (especialmente o Incident 6, que geraria plots com bug). Nenhuma mudança altera comportamento de código.

## Confirmações

- Zero produção/RAW/scripts tocados (diff = 4 docs authority + este relatório).
- Safety report: **BLOCKER=0 · WARNING=1 (Caminho B TRUE_RISK) · INFO=50** — inalterada.
- Supabase × cards locais já estavam consistentes (audit §5.5) — nenhuma ação de memória necessária além dos docs.

## Próximos blocos (ordem definida pelo Cris, cada um sob autorização própria)

1. **RAW_15M_EXTENSION_PLAN_MAR_JUN_2026** — plan-only (sem coleta).
2. Se aprovado: coleta RAW Replay controlada (`safe_backtest_window.sh`, preflight completo).
3. **Slippage/cost manifest** (pendência única do OFICIAL_FN).
4. **Regime v5 + macro-context re-adaptation** (camada BEAR-jan como contexto).
- XAU SHORT permanece bloqueado até depois do XAU 15M.
