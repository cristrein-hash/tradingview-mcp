# AMD LIVE SIGNALING — SPEC (Cris 2026-07-19)

Sinalização live da estratégia AMD (Accumulation→Manipulation→Distribution) / H4 liquidity-sweep.
**Human-in-the-loop:** o SISTEMA faz a parte OBJETIVA (deteção 24/7 do setup H4 sweep+reclaim + lista de
candidatos FVG/OB no 1H); o **CRIS** faz a parte DISCRICIONÁRIA (qual FVG é o correto + entry manual no 1H
= o edge dele); o **JOURNAL** (já live) captura o trade dele e APRENDE a seleção ao longo do tempo.
Alert-only, NUNCA auto-negocia, NUNCA gateia/invalida estratégias aprovadas. Causal close-only, RAW-canónico.

## Decisões travadas (Cris 2026-07-19)
1. **Bias = `amd_v2` EMA20-D1** (paridade com o backtest DA-limpo); Layer1 logado como CONTEXTO, não troca o sinal.
2. **Tag de ligação:** o Cris escreve o token na tag verde, ex. `#7 amd L_3990 fvg1` → F4 liga trade↔setup por token (fallback = proximidade).
3. **Janela ativa do setup = 16h** (≈4 velas H4 = `FVG_WAIT_H1` validado).
4. **Ping-2 inclui FVGs ainda não-retestados** (para pré-posicionar), rotulados.
5. **UM só daemon** vigia `raw_4h_ohlc` + `raw_1h_ohlc` (não proliferar).

## Fonte de dados (verificado)
4H/1H live com história completa nos ficheiros REV (`raw_4h_ohlc.jsonl` ~10k barras / `raw_1h_ohlc.jsonl`
~12k), lidos via `store_reader.bars("240"/"60")` — **zero dependência do HD externo**. Frescura por heartbeat
(`store_reader.fresh`). Fail-closed se stale. Detetor = `amd_lab/amd_v2.signals_v2` (reuso direto, DA-limpo).

## Os 2 pings
- **Ping 1 "SETUP ARMADO"** (fecho H4): sweep+reclaim válido (killzone L/NY + bias alinhado + once-per-level +
  fresco ≤1 barra) → Telegram gated `AMD_PRODUCTION_AUTHORIZED`. Triplo gate anti-flood.
- **Ping 2 "CANDIDATOS FVG 1H"** (monitor 1H, janela 16h): lista TODOS os FVG/OB candidatos (zona + OB + SL
  abaixo/acima do OB + entry + R + estado RETESTADO/FORMADO). Cris escolhe + entra + marca #N.

## Fases (dry-first, gate do Cris entre cada)
- **F1** detetor H4 daemon + Ping-1 + ledger `amd_setups.jsonl` (fonte única). `com.cristrein.xau-amd-cycle`
  (WatchPaths raw_4h + StartInterval), watchdog. **P0 = F1 dry.**
- **F2** listador 1H + Ping-2 (adapta `entry_fvg_ob` para LISTAR). Janela 16h, expiry, dedup por candidate_id.
- **F3** eixo `axes.amd_setup` no E0 (voz advisory, nunca veto) + o journal já capta o #N (link por token).
- **F4** `amd_learn.py`: junta journal-trades ↔ setups ↔ candidatos → `amd_selection_gt.jsonl` (qual FVG ele
  escolhe). Mecanizar só após N≥30-40 + prereg+forward + gate do Cris. Default = human-in-the-loop indefinido.

## Schemas
- `amd_setups.jsonl`: {setup_id, dir, level, level_kind, h4_bar_t, sweep_wick, h4_close, close_pos, bias,
  bias_layer1(contexto), killzone, armed_ts, window_expires_epoch, state, ping1_sent, candidates_pinged[]}.
- `amd_selection_gt.jsonl` (F4): {setup_id, trade_id, chosen{...}, offered[...], chosen_candidate_id,
  features_of_choice{...}, match_confidence}.

## Travas
Alert-only · causal close-only · store-first single-reader (tab_pin), nunca toca/pausa o chart · Telegram
gated pelo wrapper · Lisboa nas horas humanas · RAW-canónico · reusa amd_v2/Cp/journal (uma fonte, um ledger)
· baixa-frequência/alta-convicção (raro, não flood). Nunca gateia estratégias aprovadas.

Refs: `amd_lab/amd_v2.py` (detetor, DA 4/4 causal) · padrão runtime `CP_CAPITULATION/run_cp_cycle.py` ·
`copilot/journal/` (captura #N) · `store_reader.py` · Layer1 `current_layer1.json`.
