# RAW / Source-Field Mapping — XAU_4H_BREAKOUT_D1A / v1

**Data:** 2026-06-16 · **Tipo:** mapping de campos read-only · **NOT_VALIDATION.**
**Regra central (project_authority/02 + SKILL_02):** RAW/source = fonte de verdade; **SLIM = não validatório** (apenas reconciliação/screening). Toda feature deve ser recomputável de OHLCV RAW com fórmula explícita e causal.

> ⚠️ **Este bloco NÃO toca RAW.** Apenas lista a disponibilidade verificada por `ls` read-only e especifica o que precisa ser derivado/recomputado quando o rebuild for autorizado.

> **🔄 Atualização v1.1 (2026-06-16) — feature mapping canônico resolvido.** Após auditar a CFEL (`scripts/extract_replay_features.py` schema v2 + `docs/data/FEATURE_EXTRACTION_POLICY.md`) e o backtest implementado (`scripts/backtest_xau_4h_breakout_continuation_v1.py`). Ver `docs/XAU_INDICATOR_FEATURE_MAPPING_CANONICAL_AUDIT.md` + `docs/XAU_4H_BREAKOUT_D1A_FEATURE_MAPPING_AUDIT.md`. Mudanças: **RSI/RSI_MA = study_values TV (não OHLCV recompute), hard stop levantado**; **ATR = `atr14_wilder` (campo CFEL, class=diagnostic) + ATR_MA20(SMA,20)**; **ADX = `adx_wilder` Python (backtest v1)**; **swing10 = `close[i]>max(high[i-10:i])` (CFEL `:419-423`)**; registry confirma RAW 4H 2016-2026 + 1D 2012-2026. **D1a 1D permanece o único blocker estrutural.**

---

## 0. Disponibilidade RAW verificada (read-only)

| Fonte | Path | Existe? |
|---|---|---|
| RAW XAUUSD 4H | `/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/` | ✅ presente |
| RAW XAUUSD 1D | `/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1D/` | ✅ presente |
| (também presentes) | `15M/`, `30M/`, `1H/` | — não usados nesta família |
| SLIM 4H (legacy v1) | `/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD/4H/*.jsonl` | referência apenas |

**Conteúdo interno dos diretórios 4H/1D NÃO foi inspecionado neste bloco** (para não tocar RAW). Confirmar arquivos/cobertura temporal/schema é a **primeira ação da Rodada 1** (autorizada), seguindo a ordem de lookup RAW (`feedback_raw_data_lookup_order`): registry → HD externo → slim → /tmp.

**Hard stop (project_authority/02):** se, ao abrir a Rodada 1, faltar 4H OU 1D RAW com cobertura suficiente, **parar** — não cair para slim como fonte de verdade.

---

## 1. Campos 4H OHLCV (base)

| Campo | Fonte RAW? | Derivado? | Fórmula derivada | Causal? | SHIFT1? | Sanity check |
|---|---|---|---|---|---|---|
| `open` | ✅ RAW direto | não | — | sim (bar fechado) | não | monotonic ts, sem dup |
| `high` | ✅ RAW direto | não | — | sim | não | `high≥max(open,close)` |
| `low` | ✅ RAW direto | não | — | sim | não | `low≤min(open,close)` |
| `close` | ✅ RAW direto | não | — | sim | não | finito, >0 |
| `volume` | RAW **se existir** | não | — | sim | não | **não usado** por nenhum gate; só registrar se presente (não bloquear se ausente) |
| `timestamp` | ✅ RAW direto | não | — | — | — | ordenado, passo 4H, UTC, bar **fechado** |
| `ATR_14` (**`atr14_wilder`**) | CFEL post_pass (`extract:404-414`) | sim | Wilder(TR,14); TR=max(h−l,|h−pc|,|l−pc|) | sim | não | >0; **breakout usa `atr14_wilder`** (CFEL class=diagnostic; `atr14_sma_tr`=oficial CFEL mas NÃO usado). Declarar divergência. |
| `ATR_MA20` (R5) | Python (`backtest_v1:229`) | sim | `SMA(atr14_wilder, 20)` | sim | não | período 20 (≠ `atr14_sma30_ratio`); breakout-específico |
| `ADX_14` (**`adx_wilder`**) | Python (`backtest_v1:84-140`) | sim | Wilder DMI→DI±→DX→Wilder-smooth(DX) | sim | não | **não é campo slim/study**. Adotar `adx_wilder` (v1) como canônico; 2ª impl ewm no sweep → reconciliar |
| `EMA50` | Python (`backtest_v1:52,227`) | sim | EMA de close, `alpha=2/51` | sim | não | converge após ~50 barras (warmup) |
| `EMA200` | Python (`backtest_v1:228`) | sim | EMA de close, `alpha=2/201` | sim | não | **warmup 200 barras** descartado |
| `RSI` | **study_values TV** (`extract:283`) | **não — lido** | TV RSI(14) Wilder (default); `sv["Relative Strength Index"]["RSI"]` | sim | não | **CANONICAL_CONFIRMED HIGH** — não recomputar de OHLCV |
| `RSI_MA` | **study_values TV** (`extract:284`) | **não — lido** | TV "RSI-based MA" (default SMA 14); `sv["Relative Strength Index"]["RSI-based MA"]` | sim | não | **RESOLVIDO (hard stop levantado)** — campo capturado, official HIGH; gate T4 = `rsi>rsi_ma` |
| `swing10_high_prior` (**`close_above_swing_high_10`**) | CFEL post_pass (`extract:419-423`) | sim | `close[i] > max(high[i-10:i])` — máx das 10 barras **estritamente anteriores** (exclui o bar atual) | sim — usa i-10..i-1 | implícito | **CANONICAL_CONFIRMED** — rolling-high, NÃO fractal; ≡ `highest(high,10)[i-1]` |
| `body` | derivado | sim | `abs(close − open)` | sim | não | ≥0 |
| `range` | derivado | sim | `high − low` | sim | não | >0 (skip se =0) |
| `body_ratio` (**`body_pct`**) | CFEL post_pass (`extract:426`) | sim | `abs(C-O)/(H-L)` | sim | não | 0–1; gate `≥0.5`; official HIGH |
| `EMA50_slope` | derivado | sim | `EMA50[i] − EMA50[i−5]` (>0 ⇒ R4 pass) | sim — usa `[i−5]` | não | sinal, não magnitude |

---

## 2. Campos 1D (para D1a)

| Campo | Fonte RAW? | Derivado? | Fórmula | Causal? | SHIFT1? | Sanity check |
|---|---|---|---|---|---|---|
| `daily close` | ✅ RAW 1D direto | não | — | sim | **sim — último 1D fechado** | finito, >0; `ts`=open UTC, candle fecha D+1 (provado) |
| `daily EMA50` | **GERADO** de RAW 1D | sim ✅ | EMA close 1D, `alpha=2/51` | sim | herda do 1D fechado | ✅ `generated/xau_1d_ema_features.jsonl` (3584 barras, warmup 2012) |
| `daily EMA200` | **GERADO** de RAW 1D | sim ✅ | EMA close 1D, `alpha=2/201` | sim | herda do 1D fechado | ✅ warmup-ready 2013-04 (estável pré-2016); `warmup_ready` flag |
| `daily timestamp` | ✅ RAW 1D direto | não | `time`=**open 22:00 UTC**; candle dura 24h, fecha 22:00 D+1, representa pregão D+1 | — | — | provado; `close_time=open+86400` |
| `latest_closed_daily(eval)` | **IMPLEMENTADO+PROVADO** | sim ✅ | **`daily.close_time ≤ bar_open_4h`** (CAUSAL) — **NÃO** `open_time<bar_time` (PROD vaza 83,3%, provado) | **sim — CRÍTICO** | **sim** | `docs/XAU_4H_BREAKOUT_D1A_EMA1D_SHIFT_AUDIT.md`: 15.434 barras, ORIG leak 12.854 (83,3%), CAUSAL **0 leaks**, 349 d1a divergências |

**Predicado D1a:** `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D` no `latest_closed_daily_before_4h_bar`.
**⚠️ Alinhamento 1D→4H é o ponto de maior risco** (precedente A1' SUPERTREND: "causal-by-construction" colapsou 88%→46% sob SHIFT1-audit). Implementação correta = `merge_asof(..., direction='backward')` **com** a coluna de tempo do 1D sendo o **close-time** do candle diário (não o open-time), garantindo que o D do próprio dia (ainda aberto às 04:00/08:00/12:00/16:00/20:00 UTC) **não** seja consultado.

---

## 3. Campos de Outcome (engine de simulação)

| Campo | Fonte | Derivado? | Fórmula / regra | Causal? | Sanity check |
|---|---|---|---|---|---|
| `entry_time` | derivado | sim | `timestamp[signal_bar + 1]` | sim | = open-time da barra seguinte ao sinal |
| `entry_price` | derivado | sim | `open[signal_bar + 1]` (next-bar-open) | sim — sem same-bar fill | finito |
| `stop_price` | derivado | sim | `low[signal_bar] − 0.5·ATR14[signal_bar]` | sim | `< entry_price` (long) |
| `target_price` | derivado | sim | `entry_price + 4·risk`, `risk = entry − stop` | sim | `> entry_price` |
| `BE_trigger` | derivado | sim | em qualquer bar `j>entry`, se `high[j] ≥ entry + 1·risk` ⇒ stop→entry a partir de `j+1` | sim — sem lookahead intrabar | aplica só em `j+1` |
| `time_stop_24` | regra | — | sair em `close[entry_bar + 24 − 1]` se nem stop nem target em 24 barras | sim | `right_censored=true` nesse caso |
| `exit_reason` | derivado | sim | ∈ {target, stop, stop_be, time_limit} | — | exatamente 1 por trade |
| `exit_time` | derivado | sim | timestamp do bar de saída | sim | ≥ entry_time |
| `exit_price` | derivado | sim | preço no qual o exit_reason resolveu | sim | dentro do range do bar de saída |
| `R_result` | derivado | sim | `(exit_price − entry_price) / risk` | sim | — |
| `MFE_R` | derivado | sim | `max((high[k]−entry)/risk)` para `k∈[entry_bar..exit_bar]` | sim — janela posterior à entrada | ≥ R_result em winners |
| `MAE_R` | derivado | sim | `min((low[k]−entry)/risk)` para `k∈[entry_bar..exit_bar]` | sim | ≤0 tipicamente |

**Intrabar conservador:** a cada bar pós-entrada, checar `low[j] ≤ stop` **antes** de `high[j] ≥ target` (stop-first). Se ambos no mesmo bar ⇒ assume **stop** (conservador).

---

## 4. Política SLIM (reconciliação apenas)

O slim 4H legacy entrega prontos: `close, open, high, low, atr14_wilder, body_pct, swing_high_10, close_above_swing_high_10, rsi, rsi_ma, rsi_above_ma`. No rebuild estes servem **só para reconciliar** (comparar a recomputação RAW vs o booleano slim trade-a-trade) — **nunca como fonte de verdade**. Diferenças RAW vs slim devem ser **explicadas, não escondidas** (project_authority/03).

O `D1a` **não tem campo no slim** (nem flag 1D no `trades.jsonl` v1) — é prose-only no `summary.md`. Logo D1a **só existe via recomputação RAW de 1D**; não há reconciliação slim possível para ele.

---

## 5. Hard stops do RAW mapping (atualizado v1.1 — feature mapping resolvido)

**RESOLVIDOS pela auditoria canônica (não bloqueiam mais V0-V5):**
- ✅ **RSI_MA** — definido: study_values "RSI-based MA" (CFEL official HIGH). Hard stop **levantado**.
- ✅ **swing10** — definido inequívoco: `close[i]>max(high[i-10:i])` (CFEL `:419-423`).
- ✅ **Fórmula ATR** — `atr14_wilder` (CFEL) + ATR_MA20(SMA,20); divergência do ATR oficial CFEL **declarada** (não-blocker).
- ✅ **Fórmula ADX** — `adx_wilder` Python (`backtest_v1:84`); reconciliar vs ewm do sweep (não-blocker).
- ✅ **RAW 4H/1D** — registry confirma cobertura (4H 2016-2026; 1D 2012-2026).

**D1a — ✅ RESOLVIDO / LIBERADO p/ design tests** (`EMA1D_SHIFT_AUDIT`, 2026-06-16): (a) EMA50_1D/EMA200_1D **gerados** do RAW 1D 2012 (`generated/xau_1d_ema_features.jsonl`, warmup ok); (b) regra causal `latest_closed_daily = close_time≤bar_open` **implementada**; (c) **ORIG-vs-SHIFT audit rodado** — ORIG vaza 83,3%, CAUSAL 0 leaks, 349 d1a divergências. **V6/V7 liberados (condicional):** a implementação deve consumir a CAUSAL + este dataset e re-rodar SHIFT-audit trade-level. Caveat: close RAW vs produção mediana 1,72 (vintage, imaterial p/ direção).

**REMANESCENTES (não-blocker p/ V6/V7):**
- [ ] **Outcome engine causalidade** (same-bar fill, BE sem lookahead, stop/target stop-first) — a fixar na implementação.
- [ ] **Cobertura slim v2 4H** com RSI study em todos os blocos 2016-2026 — confirmar na Rodada 1.

> **Distinção SLIM:** o "slim proibido" é o **v1** (semântica errada). A **CFEL v2** (`extract_replay_features.py`) é o intérprete canônico oficial do RAW; campos `official_for_backtest` (RSI/RSI_MA/swing/body/ATR) usáveis com confiança declarada. RAW segue source-of-truth.

---

*Read-only. Nenhum RAW `.gz` aberto neste bloco — disponibilidade por `ls` + registry. Fórmulas rastreadas à CFEL (`extract_replay_features.py` v2), `backtest_xau_4h_breakout_continuation_v1.py`, `methodology.md`, `config.json`. v1.1 incorpora `docs/XAU_INDICATOR_FEATURE_MAPPING_CANONICAL_AUDIT.md`.*
