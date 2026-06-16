# RAW / Source-Field Mapping — XAU_4H_BREAKOUT_D1A / v1

**Data:** 2026-06-16 · **Tipo:** mapping de campos read-only · **NOT_VALIDATION.**
**Regra central (project_authority/02 + SKILL_02):** RAW/source = fonte de verdade; **SLIM = não validatório** (apenas reconciliação/screening). Toda feature deve ser recomputável de OHLCV RAW com fórmula explícita e causal.

> ⚠️ **Este bloco NÃO toca RAW.** Apenas lista a disponibilidade verificada por `ls` read-only e especifica o que precisa ser derivado/recomputado quando o rebuild for autorizado.

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
| `ATR_14` | derivado | sim | TR = max(h−l, |h−pc|, |l−pc|); ATR14 = Wilder smooth (`ewm alpha=1/14`) | sim | não | >0; comparar vs `atr14` base do slim (reconciliar) |
| `ADX_14` | derivado | sim | +DM/−DM Wilder; DI±=100·DMs/ATR; DX=100·|DI+−DI−|/(DI++DI−); ADX=Wilder-smooth(DX) | sim | não | 0–100; **fórmula a reconciliar** (sweep usa ewm sobre TR recomputado, não atr14 base) |
| `EMA50` | derivado | sim | EMA de close, `alpha=2/51` | sim | não | converge após ~50 barras (warmup) |
| `EMA200` | derivado | sim | EMA de close, `alpha=2/201` | sim | não | **warmup 200 barras** descartado |
| `RSI_14` | derivado | sim | RSI Wilder de close, 14 | sim | não | 0–100 |
| `RSI_MA` | derivado | **sim — ⚠️ definição ausente** | período + tipo de MA da RSI **NÃO formalizados** (slim entrega `rsi_above_ma` pronto; legacy lê coluna TV `'RSI-based MA'`) | sim | não | **HARD STOP** — definir período/tipo antes de usar T4 |
| `swing10_high_prior` | derivado | sim | `highest(high, 10)[i-1]` = máx das 10 barras **estritamente anteriores** ao sinal | sim — usa `[i-1]` | implícito (i-1) | nunca incluir o bar de sinal |
| `body` | derivado | sim | `abs(close − open)` | sim | não | ≥0 |
| `range` | derivado | sim | `high − low` | sim | não | >0 (skip se =0) |
| `body_ratio` | derivado | sim | `body / range` (= `body_pct`) | sim | não | 0–1; gate `≥0.5` |
| `ATR_MA20` | derivado | sim | SMA de ATR14 sobre 20 barras | sim | não | usado em R5 |
| `EMA50_slope` | derivado | sim | `EMA50[i] − EMA50[i−5]` (>0 ⇒ R4 pass) | sim — usa `[i−5]` | não | sinal, não magnitude |

---

## 2. Campos 1D (para D1a)

| Campo | Fonte RAW? | Derivado? | Fórmula | Causal? | SHIFT1? | Sanity check |
|---|---|---|---|---|---|---|
| `daily close` | ✅ RAW 1D direto | não | — | sim | **sim — último 1D fechado** | finito, >0 |
| `daily EMA50` | derivado de close 1D | sim | EMA close 1D, `alpha=2/51` | sim | herda do 1D fechado | warmup |
| `daily EMA200` | derivado de close 1D | sim | EMA close 1D, `alpha=2/201` | sim | herda do 1D fechado | **warmup 200 dias** |
| `daily timestamp` | ✅ RAW 1D direto | não | — | — | — | ordenado, passo diário, UTC |
| `latest_closed_daily_before_4h_bar` | derivado | sim | para o bar 4H em `t`, o 1D com `close_time ≤ t` mais recente | **sim — CRÍTICO** | **sim** | **prova empírica obrigatória** (SHIFT1-audit): nunca o D em formação |

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

## 5. Hard stops do RAW mapping

Parar (não rodar rebuild) se qualquer um:

- [ ] **RAW 4H ou 1D ausente / cobertura insuficiente** (confirmar conteúdo dos diretórios na Rodada 1).
- [ ] **Daily alignment não puder ser provado** causal (SHIFT1-audit do D1a falha ou é ambíguo).
- [ ] **swing10 ambíguo** (não se conseguir garantir 10 barras estritamente anteriores).
- [ ] **RSI_MA sem definição** (período/tipo) — bloqueia T4.
- [ ] **Fórmula ADX/ATR não fechada** (reconciliação ewm/Wilder/atr14-base indefinida).
- [ ] **Outcome engine não garante causalidade** (same-bar fill, BE com lookahead, stop/target ambíguos no mesmo bar).

---

*Read-only. Nenhum RAW lido/derivado neste bloco — apenas disponibilidade verificada por `ls`. Fórmulas extraídas de `regime_filter_test.py`, `methodology.md`, `config.json`. SLIM tratado só como reconciliação.*
