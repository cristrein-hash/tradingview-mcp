# 04 — Strategy Status Master

**Project:** Trading System  
**Purpose:** Maintain one canonical, conservative strategy-status map.  
**Rule:** Nothing is considered validated unless it has RAW/source-field trace, visual sanity checks, and explicit user approval.

---

## 1. Status Definitions

| Status | Meaning |
|---|---|
| `VALIDATED` | Passed RAW/source validation, visual review, walk-forward/sensitivity, and explicit approval. |
| `ACTIVE_CANDIDATE` | Promising research candidate, not operationally promoted. |
| `RESEARCH` | Hypothesis under study; may have useful insight but not validated. |
| `SUSPECT` | Results depend on contaminated/proxy/slim-only features, missing gate trace, or unverified semantics. |
| `REJECTED` | Rejected by R-real, visual review, methodology failure, or invalid premise. |
| `WATCH_ONLY` | May be observed/logged but must not issue live/urgent entries. |
| `DISABLED` | Must not participate in live classification or Telegram entry routing. |
| `LIVE_DORMANT` | Historically wired or present but dormant; must not be assumed active. |
| `USER_APPROVED_NOT_PRODUCTION` | Research strategy explicitly approved by the user (logic/numbers/causality confirmed + visual review by user), but deliberately NOT promoted to production. No live routing, no runtime, no execution. Documented caveats remain in force. |

---

## 2. Canonical Data Rule

All serious validation now requires:

1. RAW replay/source data as source of truth.
2. Exact source-field trace for every gate.
3. Visual/RAW spot-checks for accepted and rejected examples.
4. No SLIM/proxy-derived validation.
5. No promotion from exploratory/lab results alone.

SLIM/proxy results are historical artifacts only unless explicitly re-authorized for non-validatory screening.

---

## 3. Current XAU Strategy Map

| Strategy / Path | TF | Current Status | Operational Status | Main Decision |
|---|---:|---|---|---|
| `XAU_4H_DEMAND_BREAKOUT` | 4H | `REJECTED` | Suppressed / disabled | Rejected after visual/R-real review. |
| `XAU_4H_REVERSAL_CAPITULATION` | 4H | `REJECTED` | Suppressed / disabled | Legacy close-only edge failed R-real canonical revalidation. |
| `XAU_4H_REVERSAL_DISCRETIONARY` | 4H | `RESEARCH` / `WATCH_ONLY` | Telegram suppressed | May be observed only; not validated. |
| `XAUUSD_4H_BREAKOUT_CONTINUATION` | 4H | `ACTIVE_CANDIDATE` | `LIVE_DORMANT`, not promoted | D1a research-stage candidate. Needs official RAW-traced v2, visual review of kept trades, walk-forward, sensitivity, and OOS. |
| `XAUUSD_1H_DECISIVE_BODY60` | 1H | `REJECTED` | Disabled in recheck/rules/catalog | Rejected by visual review: too mechanical, late entries, similar weaknesses to 4H continuation. |
| `XAUUSD_INTRADAY_BB_CONFLUENCE` | 15M/MTF | `RESEARCH` / `NOT_DEPLOYED` | Recheck capped to observation only | BigBeluga/zone confluence thesis remains qualitative; old forward had no outcomes; labs are not validation. |
| `XAU_1H_DEMAND_RECLAIM_REENTRY_LONG v1.1` | 1H | `SUSPECT / REQUIRES RAW VALIDATION` | Not promoted | Promising concept from recent cycle, but must be treated as suspect until rebuilt/validated from RAW/source fields. |
| `Caminho A V1.4g-RWS-A6-A7` | 1H | `SUSPECT / CRITICAL` | Do not use for promotion | Contaminated by SLIM 4H/1D zone/proxy features. |
| `Caminho B FINAL` | 1H | `SUSPECT / CRITICAL` | Do not use for promotion | Contaminated by SLIM 4H/proxy features and synthetic swing-low proxy. |
| Legacy `XAUUSD_4H_LONG_REJECTION_SWING` | 4H | `REJECTED` | Disabled/dormant | Legacy rejected path. |
| Legacy `XAUUSD_1H_LONG_REJECTION_EXECUTION` | 1H | `REJECTED` | Disabled/dormant | Replaced then superseded; no active use. |
| `L2/BPT XAU 4H LONG · RTSE V2 zona-pura` | 4H | `USER_APPROVED_NOT_PRODUCTION` | Not wired; no runtime/Telegram/monitor/catalog/strategy_rules | Escopo B integral (BULL+RANGE+BEAR), N17 +36.2R. OK final + visual review by Cris 2026-07-02. See §4.4. |
| `XAU 15M LONG · swept-runner` (+ #4, 8ATR, regime-v5) | 15M | `USER_APPROVED_NOT_PRODUCTION` · **OFICIAL_FN** | Not wired; no runtime/Telegram; manual/proxy only | N435 WR47.6% +291.5R; approved (Cris 2026-06-28). **OFICIAL_FN stamped by Cris 2026-07-03** — cost condition PASSED (Lab E COST_ROBUST: SB $0.80 → +233.6R, r/DD 16.4, all years +). Re-adaptation labs em curso (E ✅ → A next). |
| `XAU 15M LONG · N96 ENTRY ENGINE` | 15M | `USER_APPROVED_NOT_PRODUCTION` | Not wired; no runtime/Telegram/monitor/broker/strategy_rules | Markup-demand pullback engine, 96 entries, 52W/44L, fixed 3R. Approved by Cris 2026-07-08. Includes intra-BEAR capitulation skip (SKIP if BEAR-v5 & 1D_px_vs_ema≥0 → 13L/0W, +4…+13R, DA=PROFITABLE_BUT_FRAGILE). RANGE/BULL-excess/D-deep = review-layers only, NOT gates. See §4.6. |
| `External Factors v2` | — | `LIVE_PASSIVE_CONTEXT_DAEMON` | LaunchAgent `com.cristrein.external-factors-v2` (cycling ~30min) | Passive-logging context; NOT integrated into trading (gate Fase 4). Only Camada-A event-reaction validated. |

---

## 3.1 Runtime reconciliation (Production Logic Re-Audit 2026-07-02)

Per `docs/architecture/PRODUCTION_LOGIC_REAUDIT_20260702.md`:

- **Live runtime = narrow:** tv-webhook-receiver + cloudflared tunnel + External Factors v2 (passive) + MCP server. **NO auto-trading; NO broker execution.**
- **4H strategy layer = DORMANT/SUPERSEDED:** `xau-l1-cycle` PAUSED (not loaded), `monitor_xau_4h_strategies.py` not running, cron empty, XAU 4H logs stale (10-jun). Older memory calling the 4H suite "core system (2026-06-03)" is **superseded**; treat those (V1.4g-RWS-A6-A7, Caminho B LONG, Regime Classifier v3) as **DORMANT** until re-verified.
- **Do not restart** any daemon (esp. `xau-l1-cycle`) without explicit authorization + the runbook (`PRODUCTION_RUNBOOK_20260702.md`).

---

## 4. Detailed Notes

### 4.1 XAUUSD_4H_BREAKOUT_CONTINUATION

Current best 4H candidate.

Known research finding:

- Baseline: positive but noisy.
- D1a filter improved the strategy historically:
  - `close_1D > EMA200_1D`
  - `EMA50_1D > EMA200_1D`
- D1a rejected many visually bad top/exhaustion trades.
- D1a false rejections existed but were accepted as cost of simplicity.

Current rule:

> Do not promote. Rebuild as RAW-traced official revalidation before any operational movement.

Required next steps:

1. Rebuild official v2 from RAW/source trace.
2. Gate manifest.
3. Visual review kept trades, not only rejected trades.
4. Walk-forward and regime split.
5. Cost/slippage/stops.
6. OOS/shadow validation.

---

### 4.2 XAU_1H_DEMAND_RECLAIM_REENTRY_LONG v1.1

Promising concept, but status is not validation.

Known current concept:

- Two-path structure:
  - Path A: aggressive capitulation/reclaim.
  - Path B: confirmed bottom/NAS-trigger secondary.
- BE@2R looked useful.
- Lowest-risk intra-event picker looked useful.
- Large tail trade justified the thesis conceptually.
- However, strategy work was affected by serious process errors and reliance on derived/proxy/slim logic.

Current rule:

> Treat as suspect exploratory work. It can guide hypotheses, but must not be used as a validated system until rebuilt from RAW/source fields.

Required next steps:

1. Rebuild from RAW, not SLIM.
2. Validate every indicator gate against RAW/visual:
   - Bubbles side/size/timing.
   - NAS label event/anchor.
   - SMC CHoCH/BOS kind/direction.
   - Demand/supply zones.
   - RSI thresholds.
3. Recreate trades only after gate manifest.
4. Visual review.
5. Walk-forward/sensitivity/OOS.

---

### 4.3 BB Confluence / Auction Labs

Current value:

- Useful as conceptual exploration.
- Not valid as strategy proof.
- Several labs relied on slim/proxy-derived fields.
- Any findings must be rechecked through RAW before reuse.

---

### 4.4 L2/BPT XAU 4H LONG · RTSE V2 zona-pura

**Status:** `USER_APPROVED_NOT_PRODUCTION`
**Flags:** `OK_FINAL_BY_CRIS_2026_07_02` · `VISUAL_REVIEW_COMPLETED_BY_USER` · `FINAL_APPROVED_BY_USER`
**Escopo aprovado:** B — integral (BULL + RANGE + BEAR), **N17 · +36.2R · WR53% · avgR+2.13 · DD−4.1 · streak3**.

Module: `regime_turnstate_engine/validation/` (`phase48_bear_deep_zone.py` = canonical panel; regime via `phase10_hybrid_regime.py`). R = let-run HZ120 + SL_CONTEXT − 0.35R cost. Data = RAW 4H OHLC + L2/BPT ruler (no SLIM). Causality confirmed (no look-ahead, DA Q1 PASS).

Full detail: `docs/L2_BPT_XAU_4H_LONG_V2_STRATEGY_CONFIRMATION_SHEET.md` (11-section confirmation sheet + DA verdict + 17-trade list) and `docs/L2_BPT_XAU_4H_LONG_RTSE_CHECKPOINT_2026_07_02.md`.

**Caveats aceites (permanecem documentados, não escondidos):**

- RANGE is part of the approved strategy but flagged **beta / concentrated / selection-overfit risk** (March-2023 episode alone = +20.6R of +23.7R RANGE).
- BEAR is part of the approved strategy via `phase48` but **n=1**; must NOT be treated as a statistical core.
- The phrase "RANGE+BEAR coração" is **calibrated**; do not use as a strong thesis. Defensible core = structural per-regime selection skeleton + let-run convexity.
- **NOT_PRODUCTION.** No Telegram, no monitor, no catalog, no strategy_rules, no runtime, no automatic execution.

**Before any future operationalization (not authorized here):** model slippage/gap (trades with risk > 80 pts), reproduce `phase40_debug_2024.py` (the "2024 piora"), and pass the standard promotion policy (§5). This entry does NOT constitute production promotion.

---

### 4.5 XAU 15M LONG · swept-runner (base #4, regime-v5)

**Status:** `USER_APPROVED_NOT_PRODUCTION` · **`OFICIAL_FN` (carimbado Cris 2026-07-03)** · zero SLIM (source guard) · zero runtime.
Audit completo: `docs/architecture/XAU_15M_LONG_REGIME_READAPTATION_AUDIT_20260702.md`.

**OFICIAL_FN (2026-07-03):** a condição de custo — única pendência técnica — foi cumprida no **Lab E (COST_ROBUST, DA-verificado)**: cenário realista SB ($0,80 round-trip) mantém +233,6R (80% do bruto), r/DD 16,4, todos os anos positivos, runners 53→51. Caveat registrado: 2024/risco-$-baixo frágil sob modelo conservador. **OFICIAL_FN ≠ produção:** segue sem runtime/Telegram/monitor/catalog/strategy_rules — operação manual/proxy apenas; qualquer wiring exige o promotion policy §5 completo + autorização. Recomendado antes de operar: calibrar custo com fills reais e re-rodar Lab E. Docs: `XAU_15M_LONG_LAB_E_SLIPPAGE_COST_{PREREG,DA,REPORT}_20260703.md`.

Decisões Cris 2026-07-02 (reconciliação):
- **Regime detector v5 MTF hour-causal = CANÔNICO atual** (`REGIME_V5_CAUSAL_CANON_RETAINED`); v1–v4 superseded. Não recalibrar override por ora.
- Marcação **BEAR-jan-2026** do Cris = `MACRO_CONTEXT_REVIEW_LAYER` **pendente** — camada de contexto macro, NÃO override automático (`BEAR_JAN_MACRO_CONTEXT_LAYER_PENDING`).
- **RAW 15M termina 2026-02**; extensão mar→jun-2026 = bloco futuro autorizado separadamente (`RAW_15M_EXTENSION_PLAN_MAR_JUN_2026`, plan-only primeiro).
- **Pendência única p/ OFICIAL_FN = slippage/custos** (só com manifest/predicados/sanity, bloco próprio).
- Re-adaptação de regime na **linha atual** do 15M (não mover p/ RTSE agora; integração futura se provar valor).

**SPLIT LONG/SHORT (decisão Cris 2026-07-02, `XAU_15M_LONG_SHORT_STRATEGY_SPLIT_DECISION_20260702.md`):**
- A estratégia 15M construída até agora é **SOMENTE LONG** (`XAU 15M LONG`). Toda análise atual do 15M permanece LONG-only.
- **`XAU 15M SHORT` = estratégia FUTURA SEPARADA** (`DEFERRED_AFTER_XAU_15M_LONG`), com lógica própria — **NUNCA espelho do LONG, NUNCA gates LONG invertidos** (espelho simétrico já refutado com dados).
- **Regime detector = roteador/contexto/camada de especialização por regime — NÃO direção automática nem licença para misturar estratégias** (direção-por-regime já refutada como beta-overlay).

---

### 4.6 XAU 15M LONG · N96 ENTRY ENGINE

**STATUS: `USER_APPROVED_NOT_PRODUCTION`** (Cris 2026-07-08). Full record: `docs/architecture/XAU_15M_N96_ENTRY_ENGINE_USER_APPROVAL_20260708.md`.

**Components (approved):**
- N96 entry engine (markup-demand pullbacks, 96 entries, 52W/44L, fixed 3R, +112R).
- **intra-BEAR capitulation skip:** within BEAR v5 hour-causal, SKIP if `1D_px_vs_ema ≥ 0` (shallow bounce). Cuts 13 losers / 0 winners, +4…+13R by detector. DA = `PROFITABLE_BUT_FRAGILE`.
- **RANGE/distribution:** NOT a gate — review-layer / gestão / size-down only.
- **BULL-excess RSI-HTF (~80):** NOT a gate — review-layer only (perm-P=0.028 but cuts 3 winners).
- **D-bear-active:** no additional gate survives multiplicity (mining-null best +6R P=0.40); intra-BEAR suffices; deep-bear knife = weak review-layer only.
- **Human management preserved (never auto-cut):** #24, #32, #64, #77 (BE/timing/quase-winner).

**NOT included:** no production, no runtime, no Telegram, no auto-trading, no strategy_rules wiring, no monitor, no broker.

**Caveats:** small-N per regime; daily/4H HTF primitives freeze 2026-05-24/06-09 (filter can't fire live until extended); forward on Cris's live ops = final arbiter. Docs: `XAU_15M_N96_{INTRA_BEAR_CAPITULATION_FILTER,INTRA_BEAR_CUT_TRADES,LOSER_FAMILY_MAP_CORRECTED,RANGE_DISTRIBUTION_FILTER_ROUND/DA,D_BEAR_ACTIVE_FILTER_ROUND/DA}_20260708.md`.

## 5. Current Promotion Policy

No strategy may be promoted unless all conditions are true:

1. RAW/source-field validation complete.
2. Gate manifest matches actual code.
3. Visual review completed.
4. Walk-forward and sensitivity passed.
5. Cost/slippage model considered.
6. Production path explicitly reviewed.
7. User explicitly approves.

---

## 6. Immediate Project Direction

Before strategy promotion:

1. Clean architecture.
2. Remove/mark contaminated artifacts.
3. Establish RAW-first workflow.
4. Preserve only useful lessons.
5. Rebuild candidates one at a time.
6. Use the simplest safe action at every step.
