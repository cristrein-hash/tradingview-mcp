# L2/BPT ZONE TREND-EXIT — XAU 4H LONG (reversal) · FASE 2 runtime

**Estado: USER_APPROVED_NOT_PRODUCTION.** Runtime construído e testado em dry-run; **nasce
TRAVADO** (hard-lock Telegram, plist não instalado, sem registo no group model). Motor validado
por paridade byte-exata (FASE 1, `PARITY_RESULTS.md`).

## O que está aprovado (OK Cris 2026-07-02; go-live L1+L2 autorizado por Cris 2026-07-17)

- **SELECT-17 = a estratégia**: N=17 · sumR **+105.3R** · WR 59% · maxDD **−4.1** · streak 3 ·
  ret/DD **26×** · worst −1.35. (V2 zona-pura integral: BULL zona-top / BEAR capitulação
  profunda / RANGE fundo pos<0.34.)
- **FULL-245 = stress de referência, NÃO a estratégia**: +399.2R · WR 31% · maxDD −71.8 ·
  streak 22 · ret/DD 5.6.
- Exit único: **regime_flip** (stop-first por barra; flip→BEAR sai no close; cost 0.35; cap 500).

### Caveats do DA aceites (permanecem abertos)
- BEAR = zona phase48 com **n=1** trade na seleção (bar 6791) — evidência mínima.
- RANGE = componente beta/overfit-risk (10/17 trades).
- Falta análise de slippage e de 2024 isolado.
- `tipo=B_ctx` depende das **bolhas do chart** (1/17 na seleção; 6/245 na base) — sem o feed
  de bolhas o runtime perde ~2.4% dos sinais (por isso o feed é requisito, fail-closed).

## Arquitetura do runtime (FASE 2, 2026-07-17)

```
launchd (NÃO instalado) -> start_l2_cycle.sh -> run_l2_cycle.py
  -> tab_pin.discover_tab("240")  [tab ausente = HARD_STOP blocked_missing_tab_240; SEM fallback]
  -> runtime_l2.py --once  [TVMCP_TARGET_CHART_ID pinado]
       l2_tv_read.py   — OHLCV paginado / boxes DEMAND / bolhas / RSI  (fail-closed)
       scanner_l2.py   — FSM história inteira + GUARD prefix-stability + detector v2.2
                         + prune V2 + episódio gap<=6 + context_sl + keep() da zona
       position_state.py — posições múltiplas alert-only, STOP-FIRST, catch-up LATE
       telegram_notify_l2.py — ENTRY-candidate / EXIT advisory (hard-locked)
Estado: .runtime_state/{l2_bars_4h.jsonl, l2_features.jsonl, l2_candidates.jsonl,
        l2_positions.json, l2_events.jsonl, l2_regime_segments.json, l2_dedup.txt, l2_cycle.log}
```

- **Ledger path-dependent desde 2020** (EMA300/CUSUM/zigzag): seed canónico
  `research/revalidation/raw_4h_ohlc.jsonl` + backfill MCP (`bootstrap_history.py`).
  Bootstrap 2026-07-17: sobreposição seed↔MCP 23 barras **diff 0.0**; barra degenerada do seed
  (snapshot 2026-05-24 22:00) substituída pela barra real; +234 barras; ledger 10114.
- **Prefix-stability**: qualquer rótulo/segmento PASSADO que mude entre ciclos → HARD_STOP sem
  alertas (guard testado: idempotente em re-corrida; deteta mutação injetada).
- **Semântica online causal no frontier**: RAW truncado à barra avaliada (sem futuro).
  Acceptance é decision-invariant (o break-bar fecha acima do nível por construção); o fallback
  `LATE_WIDE_REVIEW`/PL5 (que no research via 5 barras de futuro) pode divergir — selftest
  reproduziu entry/sl da régua byte-exato nas últimas 3 barras da régua mesmo truncado.
- **Catch-up honesto**: alertas atrasados levam `LATE (n barras)` + timestamp real; boxes de
  demanda em catch-up são as-of-agora (flag `dsq_asof:"now"`). Gap descontínuo → HARD_STOP.
- **Primeiro ciclo**: `last_processed_bar_time` = última barra do bootstrap; **sem sinais
  retroativos**.
- Histórico do gap (mai–jul 2026): RSI só nas últimas ~49 barras (cap 50 do
  `data_get_study_values_at_bar`) — sem impacto operacional (RSI só entra no gate
  TOP_EXHAUSTION na avaliação da barra nova; o passado não é varrido).

## Requisitos do chart (tab 4H dedicada, pinada por TVMCP_TARGET_CHART_ID)

Verificados 2026-07-17 na tab `0FB4416F` (PEPPERSTONE:XAUUSD · 240):
- **Custom OB Detector v11 — Alert** com boxes `text=DEMAND/SUPPLY` (context_sl) ✓
- **Market Order Bubbles - By Leviathan** (SELL = plot_6/8/10, mapeamento validado Cp) ✓
- **Relative Strength Index** (gate categórico ≥70) ✓
Qualquer estudo oculto/ausente → `blocked_missing_study:<qual>` (fail-closed, sem alertas).

## Testes executados (2026-07-17)

| Teste | Resultado |
|---|---|
| py_compile (todos os módulos) | PASS |
| Selftest position_state (STOP-first vs FLIP mesma barra; CAP; catch-up LATE; dedup; atomic IO) | PASS (7/7) |
| Selftest scanner sobre o seed (journal==pruned base V2 2965 byte-igual; frontier reproduz entry/sl da régua nas 3 últimas barras; guard idempotente + deteta mutação) | PASS |
| bootstrap_history REAL (MCP read-only) | PASS — 234 barras appendadas, overlap 23 barras diff 0.0 |
| run_l2_cycle REAL dry-run (2 ciclos) | PASS — regime BEAR, zona bear_deep [4023.76, 4488.89] logada, 0 alertas, guard had_prev sem disparo |
| Integração catch-up (3 barras reais, scratch) | PASS — candidato real podado, REGIME_FLIP LATE correto |
| Guards do notifier (hard-lock força dry-run com --send; allowlist; frases proibidas) | PASS |

## Gates de go-live (NENHUM executado — exigem autorização explícita do Cris)

1. **V-6**: Devil's Advocate da FASE 2 (runtime) — ainda não corrido.
2. **V-7**: janela de shadow-run dry-run (ciclos agendados sem Telegram) com revisão dos logs.
3. Destravas (por esta ordem, só após 1–2):
   a. registar `L2_BPT_ZONE_TREND_EXIT` em `core/group_model_xau.py` (XAU_240);
   b. `export L2_PRODUCTION_AUTHORIZED=1` no `start_l2_cycle.sh`;
   c. `--send-telegram` no wrapper;
   d. `launchctl load` do `com.cristrein.xau-l2-cycle.plist` (grade :12, offset +7min vs L1).

Advisory sempre: os alertas são candidatos/avisos de gestão para revisão humana — nunca ordem.
