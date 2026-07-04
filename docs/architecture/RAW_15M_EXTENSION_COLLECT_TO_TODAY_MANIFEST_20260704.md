# RAW 15M EXTENSION — COLLECT TO TODAY · MANIFEST (2026-07-04)

**Bloco:** RAW_15M_EXTENSION_COLLECT_TO_TODAY_20260704 · autorização integral Cris (full-flow, sandbox-first, promote-only-after-checks; 5 aprovações do plano §10 cobertas pelo GO). Protocolo = `RAW_15M_EXTENSION_PLAN_MAR_JUN_2026.md` + skill `replay-backtest-manager`. Sem produção/Telegram/trading; sem backtest sério antes de RAW+derivados validados; kill-check do Sistema A só em R10.

## Estado ANTES (R0-R2)
- Push prévio: `cc2e219`+`7c5253d` → origin/main OK; repo limpo (untracked vivos: .mcp.json, alert-bridge/logs/, base4_maturation_features.json, lab_g_candidates.jsonl — regeneráveis/vivos).
- Safety: BLOCKER=0, WARNING=1 (Caminho B TRUE_RISK), INFO=50. Disco: local 162Gi livres · HD `GUTS_ LACIE` 416Gi livres.
- **RAW vivo:** `/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/` — 8 blocos gz contíguos `2024-05-25 → 2026-05-25`, manifests completos (sha256+roundtrip YES). 8º bloco: `XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz` (130M · archived_sha256 `ecb1788dbad696015369f34afc52336a1c90d9da2eb65e060095695196e73e9a` · 5710 bars · dataset 2026-02-24→2026-05-25). Primitives do 8º: 5714 bars, última barra **2026-05-25 00:00 UTC (t=1779667200)**.
- **Derivados vivos ligados:** `research/xau_15m_bb_nas_leonardo/primitives/*.primitives.json` (8 blocos) · bubbles/ · htf_primitives/ · `entry_candidates_htf.jsonl` (4502) · `results/lab_g_candidates.jsonl` (regenerável).
- **Preflight (skill, 6 checks):** enrich ausente ✓ · server.js = só o MCP desta sessão (legítimo, necessário) ✓ · receiver /health OK local + público 200, `claude_recheck:true`, pause_flag false ✓ · flag ausente ✓ · launchd: só `com.cristrein.tv-webhook-receiver` (PID 841) — **daemon monitor 4H já estava parado ANTES (DORMANT): não tocado, não será restaurado** · cron vazio ✓.
- **Chart (CDP):** `PEPPERSTONE:XAUUSD` · 15 · **baseline do 8º bloco COMPLETO no chart** (Custom OB Detector v11 — Alert · LuxAlgo SMC · NAS TOP BOTTOM · Market Order Bubbles · RSI) + extras presentes e registrados (Market Structure CHoCH/BOS [LuxAlgo], Volume, HTF Power of Three ×2, Session Volume Profile) — extras não fazem parte do contrato do coletor.

## Alvo
- Período: **2026-05-25 → 2026-07-04** (bloco curto, ~2.700 barras estimadas; cap do wrapper 8000 OK). Overlap de ~1 dia no início por design (dedup na validação).
- Símbolo/TF: PEPPERSTONE:XAUUSD · 15.

## Comandos planejados
1. Coleta (janela segura, restore trap em todo exit path): `alert-bridge/safe_backtest_window.sh --replay-collect --timeframe 15 --symbol PEPPERSTONE:XAUUSD --start-date 2026-05-25 --end-date 2026-07-04` → staging nativo `alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl` (RAW vivo do HD NÃO tocado durante coleta).
2. Validação R4 (schema/monotonia/dups/gaps/junção com t=1779667200/OHLC-sane/checksum) → `results/raw_15m_extension_validation_20260704.json` + `raw_15m_extension_gap_report_20260704.csv`.
3. R5 continuidade lógica (RAW = blocos independentes por design; "merged candidate" = conjunto 8+1 validado na junção; prefixo antigo intocado por construção — blocos originais nunca modificados).
4. R6 source guard (`_source_guard.py` / validador RAW-first).
5. R7 promoção: sha256 original → gzip → sha256 gz → cópia HD → `gzip -t` → roundtrip → manifest novo em `TradingData/manifests/` (formato dos 8). Original local retido (backup natural).
6. R8 primitives do bloco novo em SANDBOX (`/tmp` scratchpad) → validação (contagens, junção, prefixo dos 8 intocado por construção) → R9 promoção aditiva para `primitives/`.
7. R10 kill-check Sistema A (spec congelada; janela virgem pós-2026-05-25).

## Rollback
- Staging: `rm` do jsonl local + primitives sandbox (nada oficial tocado).
- Pós-promoção: remover gz novo + manifest novo do HD (8 blocos originais nunca modificados — imunes por construção); primitives novo = deletar o `.primitives.json` novo (aditivo).
- Checksums old registrados acima; new serão registrados no REPORT.

## R4/R6 — resultados (pré-promoção)
- **R4 PASS** (`validate_raw_extension_20260704.py`): coleta 8000 registros → normalizado **2709 barras reais** (cauda pós-replay 5290 descartada + 1 dup consecutivo keep-first) · 2026-05-24 23:45 → **2026-07-03 16:30 UTC** (fim = último bar antes do fechamento de sexta/feriado 4-jul) · junção com 8º bloco contígua (1ª barra nova 00:15, gap 15min; 2 barras de overlap por design) · 0 dup · 0 não-monotônico · 30 gaps todos legítimos (fds/sessão/**Memorial Day 25-mai early-close**) · sha256 normalizado `0a9d87cf0ed0f4a0f693fb0ea271a2aa618226f21c4932273e7fc10fb33a96bd`.
- **R6 source guard:** cadeia de promoção **PASS** (build_causal_primitives · extract_bubbles · engine_substrate4_v5_hourcausal · build_engine3_features). 2 FAILs em auxiliares = **falso-positivos pré-existentes do heurístico de token** (não-regressões; scripts intocados por este bloco): `lab_entry_candidates.py` L124 `macro_bear` é ATRIBUIÇÃO de campo (fonte real = macro_regime_4h.json, input registrado do pipeline desde Engine 2) · `lab_g_context_inventory.py` lê dados exclusivamente via exec do engine (que referencia primitives) — heurístico de allowed-token não vê. **Pendência registrada: calibração do guard** (mesma classe do incidente GUARDRAIL_CARD no safety scanner). Decisão de prosseguir tomada com evidência; sujeita a veto do Cris no report.

## Estado operacional a restaurar em R12
Nada foi pausado por este bloco até aqui (wrapper pausa/restaura sozinho com trap). Daemon 4H permanece como estava (parado antes → não restaurar).
