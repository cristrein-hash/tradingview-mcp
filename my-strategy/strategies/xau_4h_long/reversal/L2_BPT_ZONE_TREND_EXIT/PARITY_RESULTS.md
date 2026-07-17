# L2/BPT ZONE TREND-EXIT — FASE 1: PARITY RESULTS

**Data:** 2026-07-17 · **Motor:** `l2_engine.py` (port VERBATIM do research, py3.9 stdlib-only, dados por argumento, zero I/O)
**Árbitro:** paridade byte-exata contra os artefactos canónicos do research. Corridas reais abaixo (logs em `parity/_v1_run.log`, `parity/_v4_run.log`).

## Sumário

| Gate | Script | Resultado |
|------|--------|-----------|
| V-1 FSM regime + segmentos + prefix-stability | `parity/parity_regime_online.py` | G1 PASS · G2 PASS · G3 PASS · G4 (prefix 300) EM CURSO |
| V-2 Seleção-17 | `parity/parity_select17.py` | **PASS** (byte-a-byte) |
| V-3 Trend-exit regime-flip | `parity/parity_trend_exit.py` | **PASS** (105.3 / −4.1 / 3 · FULL +399.2) |
| V-4 Re-derivação da régua (245) | `parity/parity_rederive_regua.py` | **PASS** (G1..G3 + G4 bónus entry/sl) |

## V-1 — FSM de regime (vs `phase10_hybrid_regime.py` original)

Input: `my-strategy/research/revalidation/raw_4h_ohlc.jsonl` (9880 bars, t0=1577761200, load idêntico ao phase10 — sort por t, SEM descartar a última barra degenerada, porque o original não descarta; paridade manda).

- **G1 PASS** — array `run(0.03,1.15,0.88)` do engine == phase10, barra a barra (9880/9880).
- **G2 PASS** — segmentos (era ≥2023) byte-idênticos ao builder do phase10 (`json.dumps` ==): 44 segs vs 44 segs.
- **G3 PASS** — onsets BEAR presentes: d0=2023-05-25 ✓ · d0∈{2026-01-29,2026-01-30} ✓. BEAR d0s: `['2023-05-25','2026-01-29','2026-01-29','2026-01-30']`.
- **G4 (prefix-stability, últimas 300 barras)** — EM CURSO no momento deste draft; ver secção final.

## V-2 — Seleção-17 (contrato `l2_bpt_causal_selector.py:54-56`)

Pipeline engine-only: FSM(raw) → `build_segments` → `prepare_segments` → `keep_signal` sobre a régua (`l2_bpt_regua_structural.csv`, 245 sinais) → comparação com `research/results/l2_bpt_17_trades.csv`.

```
V-2 RESULT: PASS — engine reproduz os 17 byte-a-byte (245 -> 17)
  por regime: BULL=6, RANGE=10, BEAR=1
  bar_idx: [4918, 4926, 5016, 5103, 5826, 5875, 6376, 6791, 7149, 7549, 8133, 8216, 8236, 8893, 8905, 8978, 9007]
```

## V-3 — Trend-exit / regime-flip (gates `l2_bpt_trend_exit_execution_risk_layer.py:106-109`)

R por trade arredondado 2dp (como `sim()`), painel com round 1dp. SEL17 derivado pelo próprio engine (não lido do canon).

```
SELECT-17: N=17 sumR=+105.3 WR=59% maxDD=-4.1 streak=3 retDD=26.0 worst=-1.35
FULL-245 : N=245 sumR=+399.2 WR=31% maxDD=-71.8 streak=22 retDD=5.6 worst=-1.35
G1 sumR≈105.3 PASS (105.3) · G2 maxDD==-4.1 & streak==3 PASS · G3 FULL≈399.2 PASS (399.2)
V-3 RESULT: PASS
```

## V-4 — Re-derivação da régua sobre o frozen (`repro_recovery/raw_features_2020_2026.jsonl`)

Cadeia: detector v2.2 → prune V2 (overextended_entry | src_redundant | bear_flag) → episódios (gap≤6, rep=primeiro, ATR presente) → `context_sl` (demanda 4H passada como argumento, `l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv`) → traded set.

```
frozen: 9880 bars
candidatos v2.2: 7763 (esperado 7763) [11s]
G1 pruned base V2: PASS — engine 2965 vs CSV 2965
G2 episódios/reps: PASS — engine 276 reps vs 276-file 276
G3 régua 245 bar_idx: PASS — engine 245 traded (31 no_trade TOP_EXHAUSTION) vs régua 245
G4 entry/sl byte-iguais: PASS — entry 245/245, sl 245/245
V-4 RESULT: PASS (G4 bónus: PASS) [11s]
```

Nota G4: reproduz inclusive o quirk de arredondamento da cadeia original (`sl_atr` guardado com 2dp em `l2_bpt_sl_context_policy_results.csv` → `setup_ctx` do `_DA_regua_structural_letrun.py` multiplica o valor arredondado pelo ATR). Não houve resíduo — a régua fechou byte-exata, sem precisar do precedente decision-invariant do doc §5.

## CENSO B_ctx (dependência de bolhas do chart)

```
CENSO 245 (régua): tipos={'A': 164, 'B': 75, 'B_ctx': 6} variants={'classic_BOS': 245}
  -> B_ctx: 6 [2488, 4346, 5724, 6791, 9628, 9805]  (2.4% da base)
CENSO 17 (SELECT): tipos={'A': 6, 'B': 10, 'B_ctx': 1} variants={'classic_BOS': 17}
  -> B_ctx: 1 [6791]
```

Leitura para a fase 2 (runtime/chart):
- **Nenhum** candidato sobrevivente é `contextual_no_BOS` (Variant 2) — todos `classic_BOS`.
- `tipo=B_ctx` (aceite SÓ por `is_tipo_B_contextual`, i.e., ≥5 sell-bubbles nos últimos 10 bars) cobre 6/245 da base e **1/17 da seleção (bar 6791)**. Ou seja: o runtime live SEM feed de bolhas perderia ~2.4% dos sinais da base e 1 dos 17 aprovados.
- As bolhas também entram como *gate alternativo* dentro do Variant 1 (o `is_b_ctx` é testado em todos os candidatos), portanto o feed `bubbles_recent` (plots 6/8/10, `bars_ago` 0..10) É requisito do chart live para paridade plena.
- `nas_recent`/`smc_recent`: NÃO usados por nenhuma camada portada. RSI do frozen: usado só no gate TOP_EXHAUSTION (`rsi>=70` categórico) — o resíduo rsi do pipeline doc §5 é decision-invariant aqui também.

## Divergências abertas

Nenhuma. Todos os gates byte-exatos fecharam sem tolerância além das originais (V-3 usa a tolerância do próprio gate do research: `abs(sumR-105.3)<0.6`).

## Quirks preservados (NÃO corrigir sem re-paridade)

1. `bars=(end-start)/14400` nos segmentos = tempo-calendário, não nº de barras (phase48:15).
2. Barra de flip pertence ao hi/lo do segmento ANTERIOR (phase10:119-129, bisect_right).
3. Corte de segmentos `end<1672531200` descartados; hi/lo arredondados 2dp.
4. `PL5` do `swing_origin` usa 5 barras de FUTURO (sl_context.py:14-16) — só afeta o fallback `LATE_WIDE_REVIEW`.
5. Última barra do raw é degenerada (o=h=l=c) e NÃO é descartada (o research não descarta; o load é idêntico).
6. `sl_atr` com 2dp na cadeia régua (ver G4 acima).
7. Detector: 1 candidato/barra (dedup por entry_idx, melhor score); loop começa em i=50.

## O que falta para a FASE 2 (runtime/MCP)

- Feed live: OHLC 4H + `bubbles_recent` (sell plots 6/8/10, bars_ago≤10) + RSI (categórico ≥70) + zonas de demanda 4H as-of-bar (argumento `dsq` do `context_sl`) — o builder live da demanda ainda não existe fora do research.
- FSM precisa do histórico completo desde 2020 (EMA300, CUSUM, zigzag são path-dependent) — runtime deve carregar o histórico frozen + append live, não recomeçar curto.
- Decisão de bootstrap: manter raw_4h_ohlc.jsonl como seed canónico e append de barras fechadas.
- Portar para o runtime: agendamento por barra fechada 4H, alerta/ordem, e reconciliação (fora do escopo fase 1).

*(Draft — secção V-1 G4 será atualizada com o resultado real da corrida de prefix-stability.)*
