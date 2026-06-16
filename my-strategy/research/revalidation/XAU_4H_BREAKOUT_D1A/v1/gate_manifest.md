# Gate Manifest (preliminar) — XAU_4H_BREAKOUT_D1A / v1

**Data:** 2026-06-16 · **Tipo:** manifesto de reconstrução read-only · **NOT_VALIDATION.**
**Escopo exclusivo:** XAUUSD_4H_BREAKOUT_CONTINUATION / D1a / DECISIVE_BREAKOUT.
**Este bloco:** preparação mecânica. Nenhum backtest rodado, nenhum threshold novo inventado, nenhuma plotagem, nada operacional tocado.

---

## 0. Identidade

| Campo | Valor |
|---|---|
| `strategy_family` | `XAU_4H_BREAKOUT_D1A` |
| `symbol` | XAUUSD (`PEPPERSTONE:XAUUSD` no slim legacy) |
| `timeframe` | 4H |
| `direction` | LONG |
| `archetype` | `DECISIVE_BREAKOUT` / PRO-MOMENTUM (catalog: `DECISIVE_BREAKOUT_CONTINUATION`) |
| `relation_to_L1` | **ortogonal**, módulo separado, futura **L2 breakout candidate** (não fundir no motor L1 anti-extensão) |
| `status` | **RECONSTRUCTION_IN_PROGRESS / DESIGN_TEST_READY — not validated** |
| `family_origin` | B (catalog) — rótulo histórico, não autoridade de gates |
| `legacy_id` | catalog `XAUUSD_4H_BREAKOUT_CONTINUATION` (`ACTIVE_CANDIDATE` / `LIVE_DORMANT`) |

> **Catalog usado apenas como referência de status/rótulo, NÃO como verdade de gates.** O rótulo `ACTIVE_CANDIDATE` é legacy enganoso (não deployado; canal recheck:931 neutralizado 2026-06-15). Gates abaixo vêm de `methodology.md` + `config.json` + Pine #01 + `regime_filter_test.py` + packet experimental.

---

## 1. ⚠️ Discrepâncias de fonte que este manifesto resolve (nome ≠ definição)

Antes dos predicados, três divergências documentadas (ver `feedback_name_vs_definition_mismatch`) que **devem ser tratadas como decisão canônica deste rebuild**, não como erro a propagar:

1. **Config-label mismatch (R vs S).** O `config.json` e o `config_id` de cada linha do `trades.jsonl` dizem **`S_full_trend_htf`**. Mas os gates **realmente implementados e revalidados** em `methodology.md §3` são `ADX≥20 + close>EMA200 + EMA50>EMA200 + EMA50_slope + ATR_expanding` = **`R_full_trend_regime`** (n=234 no sweep). `S_full_trend_htf` é config **diferente** (`adx20 + close>ema200 + ema50>ema200 + htf_1d`, n=427, **sem slope/ATR**).
   → **Decisão canônica do rebuild:** o conjunto de regime R1-R5 = **`R_full_trend_regime`** (o que foi de fato rodado). O label `S_full_trend_htf` do v1 é tratado como **erro de rótulo**, não como definição.

2. **D1a ≠ htf_1d_bullish.** O `htf_1d_bullish` do sweep legacy é `close_1D > EMA50_1D` (`regime_filter_test.htf_context`, via `merge_asof` backward). O **D1a** (research 2026-06-01, descrito em `summary.md`) é **mais estrito**: `close_1D > EMA200_1D AND EMA50_1D > EMA200_1D`. **Não são o mesmo gate.** A "redundância" do htf_1d sobre o EMA-stack (observada no sweep) **não** prova nada sobre o D1a — tensão não resolvida, a ser medida no design test (Rodada 3).

3. **Entry: close vs next-bar-open.** O packet/Pine spec original entra no **close do candle de sinal** ("Entrada ideal: close"). A revalidação v1 entra em **next_bar_open** (anti-lookahead). → **Decisão canônica do rebuild:** entry = **next-bar-open** (realismo anti-lookahead). O close-entry legacy fica só como referência histórica.

---

## 2. Predicados — Trigger (T1-T4)

Em candle 4H **fechado** `i`. Todos obrigatórios.

| # | Gate | Predicado exato | Campo | Causalidade |
|---|---|---|---|---|
| T1 | breakout | `close[i] > highest(high, 10)[i-1]` (rompe a máxima das 10 barras **anteriores**) | `close_above_swing_high_10` (slim) → recomputar de RAW | causal — usa `[i-1]`, nunca a swing atual/futura |
| T2 | bullish candle | `close[i] > open[i]` | OHLC | causal |
| T3 | corpo decisivo | `body_pct[i] >= 0.5` onde `body_pct = abs(close-open)/(high-low)` | `body_pct` (slim) → derivável de OHLC | causal |
| T4 | momentum RSI | `RSI(14)[i] > RSI_MA[i]` | `rsi`, `rsi_ma`, `rsi_above_ma` (slim) → recomputar de RAW | causal |

**Nota T1:** no legacy a swing usada é `swhi_10 = high.rolling(10).max()` consultada em `[i-1]` (`prev_swing_high`). Mecânica RAW deve replicar: máxima das 10 barras estritamente anteriores ao bar de sinal.
**Nota T4 (RSI_MA):** a definição exata de `RSI_MA` (período/tipo de MA da RSI) **NÃO está formalizada** nas fontes — o slim entrega o booleano `rsi_above_ma` pronto e o legacy lê colunas `'RSI'` e `'RSI-based MA'` (estudos TradingView). **Hard-stop candidato** (§7): RSI_MA precisa de definição explícita (período + tipo) antes de recomputar de RAW.

---

## 3. Predicados — Regime (R1-R5 = `R_full_trend_regime`)

Todos no candle de sinal `i`, todos obrigatórios. (Fórmulas Wilder/EMA de `regime_filter_test.compute_indicators` + `methodology.md §2`.)

| # | Gate | Predicado exato | Fonte da fórmula |
|---|---|---|---|
| R1 | força direcional | `ADX(14)[i] >= 20` | Wilder DMI: TR, +DM, −DM com suavização Wilder (`ewm alpha=1/14`); DI±; DX; ADX = Wilder-smooth de DX |
| R2 | bias macro | `close[i] > EMA(200)[i]` | `EMA(200)` de close, `alpha=2/(200+1)` |
| R3 | golden cross | `EMA(50)[i] > EMA(200)[i]` | EMA close 50/200 |
| R4 | slope vivo | `EMA(50)[i] > EMA(50)[i-5]` (≡ `ema50.diff(5) > 0`) | EMA50 atual vs 5 barras atrás |
| R5 | vol expandindo | `ATR(14)[i] > SMA(ATR(14), 20)[i]` | ATR14 Wilder; ATR_MA20 = SMA de ATR14 sobre 20 barras |

> ⚠️ **Detalhe de fórmula a confirmar em RAW (Rodada 1):** `methodology.md` diz `ATR_MA(20) = SMA` de `atr14_wilder`, mas `regime_filter_test.compute_indicators` usa `df['atr_ma20'] = df['atr14'].rolling(20).mean()` (SMA) — consistente. Já o **ADX** no sweep usa `ewm(alpha=1/14)` sobre TR recomputado, **não** o `atr14` base. Reconciliar fórmula ADX (e a `atr14` base do slim vs recompute) é parte do RAW mapping.

---

## 4. Predicados — D1a (filtro macro 1D, causal)

Camada de **contexto de direção macro 1D** aplicada **on top** de T1-T4 + R1-R5. **NÃO é trigger, NÃO é entrada, NÃO é regime-model completo** — é um **gate booleano de direção macro**.

| # | Gate | Predicado exato |
|---|---|---|
| D1a | direção macro 1D | manter o long só se, no `signal_iso`, o **último candle 1D já fechado antes do bar 4H de sinal** satisfaz: `close_1D > EMA200_1D` **AND** `EMA50_1D > EMA200_1D` |

Regras duras de D1a:
- **Usar o último 1D fechado** antes do bar 4H avaliado (most-recent **completed** daily). **Nunca** usar o 1D em formação (o D do próprio dia ainda aberto). Este é exatamente o ponto que quebrou A1' SUPERTREND (look-ahead daily) — aqui a regra documentada é causal, mas **NEEDS_SHIFT1_AUDIT** em RAW para confirmar empiricamente (não confiar em "causal-by-construction").
- EMAs 1D (`EMA50_1D`, `EMA200_1D`) computadas da série de **close 1D**, `alpha=2/(period+1)`.
- **D1a é macro-context filter, não trigger.** Não altera a entrada nem o stop; só permite/bloqueia.
- **D1a ≠ htf_1d_bullish legacy** (§1.2): htf_1d era `close_1D>EMA50_1D`; D1a é stricter (`close>EMA200 AND EMA50>EMA200`).

---

## 5. Stop / Target / Exit (legacy — congelado como baseline, com fragilidades marcadas)

| Item | Regra legacy | Status |
|---|---|---|
| SL | `stop = low[signal_bar] − 0.5·ATR14[signal_bar]`; **sanity:** `0 < risk` e `risk ≤ 5·ATR14` (senão skip) | KEEP como baseline; **FRÁGIL** (ver fragilidades) |
| Target | `target = entry + 4·R` (4R) | KEEP como baseline |
| BE | move stop para BE quando `high[j] ≥ entry + 1·R`; aplica em `j+1` (sem lookahead intrabar) | KEEP — causal |
| Time stop | `max_hold = 24` barras; saída no `close[entry_bar+24−1]` se nem stop nem target baterem; `right_censored=true` nesse caso | KEEP — causal |
| Intrabar | **stop-first** (checa `low[j]≤stop` antes de `high[j]≥target`) | KEEP — conservador |
| Fill | next-bar-open (`entry = open[signal_bar+1]`) | KEEP (§1.3) |
| No-overlap | pular sinal se `signal_bar ≤ last_exit_bar`; 1 trade por episódio (episódio = 1 bar) | KEEP |

**Fragilidades marcadas (NÃO trocar agora — exigem teste desenhado, ver design_test_plan Rodada 4):**
- **SL 0.5·ATR pode ser frágil em blow-off** (caso 2022 chop_inflation_bear: stop pequeno demais para a expansão pós-entrada; MAE chegou a −3.23R no dump). **NÃO generalizar** "0.5ATR é frágil" — é observação de 2022, confound regime/período.
- **Exit policy precisa estudo separado** (target +4R capa MFE de 5.99R; 29/115 saem por time_limit). Não alterar sem bloco de gestão dedicado.

---

## 6. Variantes mecânicas iniciais (para a matriz de design tests — SEM otimização)

Construção incremental para **decompor de onde vem o edge**, não para escolher vencedor por total_R. Nenhum threshold novo; só liga/desliga gates já definidos.

| Variante | Composição | Propósito |
|---|---|---|
| **V0** | trigger only (T1-T4) | baseline; medir trigger sozinho (esperado: fraco, cauda-dependente) |
| **V1** | trigger + R1 (ADX) | isolar contribuição ADX |
| **V2** | trigger + EMA stack (R2+R3) | isolar EMA-stack (close>EMA200 + golden-cross) |
| **V3** | trigger + R5 (ATR expanding) | isolar "mercado vivo" |
| **V4** | trigger + R4 (EMA50 slope) | isolar slope (esperado: pior gate isolado) |
| **V5** | trigger + regime_full (R1-R5 = `R_full_trend_regime`) | a config revalidada v1 |
| **V6** | trigger + D1a | isolar D1a sobre o trigger puro |
| **V7** | trigger + regime_full + D1a | conjunto completo (R1-R5 + D1a) |
| **V8** | legacy adopted config | espelho do que a revalidação v1 rodou (= V5 na prática; manter separado para reconciliar n/R) |
| **V9** | minimal candidate | **só se o sweep justificar** — combinação mínima que preserva ~máximo do edge (candidato direcional do edge-decomp: `P = ADX + EMA-stack`). **Sem inventar threshold novo.** |

> V9 NÃO é pré-comprometido — só materializa se Rodada 2 confirmar que uma combinação mínima preserva o edge. Nenhum número atrelado neste bloco.

---

## 7. Hard stops do manifesto (gate manifest → backtest)

Antes de qualquer rebuild mecânico rodar, estes pontos devem estar resolvidos (senão STOP):

1. **RSI_MA indefinido** — período e tipo de MA da RSI não formalizados nas fontes (slim entrega booleano pronto). Resolver no RAW mapping antes de recomputar T4.
2. **Fórmula ADX** — reconciliar a versão `ewm(alpha=1/14)` do sweep com qualquer ADX que o RAW/slim já traga; confirmar `atr14` base vs recompute.
3. **Alinhamento 1D→4H do D1a** — provar empiricamente (SHIFT1-audit) que só o 1D fechado é consultado; não aceitar "causal-by-construction".
4. **swing10** — confirmar que `highest(high,10)[i-1]` é inequívoco (10 barras estritamente anteriores; sem incluir o bar de sinal).
5. **Config-label** — usar `R_full_trend_regime` como R1-R5 (não o label `S_full_trend_htf`).

Estes 5 alimentam diretamente o `raw_field_mapping.md` (campos derivados + causalidade) e os sanity checks do `design_test_plan.md`.

---

*Read-only. Métricas legacy citadas (n=234/+64.57R/PF1.64; n=115/+25.28R; +D1a 90/+32.20R) são **in-sample / SLIM / agregado** — histórico, NÃO validação. Nenhum backtest rodado neste bloco.*
