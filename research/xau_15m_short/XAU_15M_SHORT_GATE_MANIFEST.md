# XAU 15M SHORT — GATE MANIFEST (RASCUNHO para revisão do Cris, 2026-08-16)

> Passo 0 do playbook (`XAU_SHORT_15M_BUILD_PLAYBOOK.md`) sob `XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1`.
> **RASCUNHO** — rever/afinar antes de qualquer medição. O bloco ```json``` é a autoridade lida pelos blockers
> (`check_xau_15m_*` + GS1/GS3). Toda leitura de RAW pelo leitor canónico `raw_reader` (GS2), nunca ler o .gz diretamente à mão.

## Bloco machine-readable (1º bloco json — autoridade)

```json
{
  "lab_name": "XAU_15M_SHORT",
  "strategy": "XAU 15M SHORT — teste-e-rejeicao-no-iman (V1) / quebra-1H+15M+retest (V2)",
  "direction": "SHORT",
  "universe": "todos os candidatos SHORT nos baldes-alvo, 2024-05 -> 2026-05 (RAW) + store (recall GT)",
  "timeframe": "15M",
  "trade_ids": "todos os eventos SHORT etiquetados no bucket estrutural",
  "raw_files": [
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-08-25_to_2024-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-11-25_to_2025-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz"
  ],
  "raw_reader": "my-strategy/core/raw_reader.py (GS2 canonico; RR.resolve_gz + RR.iter_records/series_flat/study/boxes) para 15M/1H/4H",
  "recall_gt_source": "RAW via replay-collect da semana 08/2026 (safe_backtest_window.sh --replay-collect; Cris autorizou 2026-08-16) — GT#1 fica DENTRO do RAW, nao no store",
  "recall_threshold": "gt_caught == gt_total (casos-ancora: GT#1 + criterio de aceitacao); estrito, o detetor TEM de apanhar os shorts-verdade conhecidos",
  "bucket_engine": "MOTOR EXISTENTE (Cris 2026-08-16, nao construir novo): macro_regime = Layer1 1D (macro_structural_v3.build_layer1) + regime 4H (regime-engine); leg_state = perna imediata 1H (_leg_read); family = bucket estrutural derivado desses",
  "derived_files": [],
  "allow_resample": false,
  "htf_stale_declared": "declarar o freeze conhecido de htf_1D/4H no arranque do lab; contexto 1H/4H lido do RAW as-of via raw_reader",
  "context_tfs": {"entry_retest": "15M (principal)", "context": ["1H", "4H"]},
  "fields": ["15M: ob_supply/svp_vah/svp_poc/bb_upper/smc_choch/bubbles_sell/nas_top/rsi/atr", "1H (contexto): ob_supply/smc_choch/leg_state/rsi", "4H (contexto): ob_supply/smc_choch/regime"],
  "structural_buckets": ["RANGE_distribution_top_bear", "BEAR_active", "countertrend_bounce_in_bear", "BULL_excess_top", "BEAR_shallow_bounce"],
  "buckets_excluded_no_short": ["BEAR_deep_capitulation", "BULL_impulse", "RANGE_accumulation_bottom"],
  "hypotheses": [
    "V1 teste-e-rejeicao-no-iman-superior: preco TESTA o iman superior (BB15M + cluster SVP15M + OB15M nao-testado acima) e REJEITA la' (fecho terco inferior + buyers presos + iniciativa sell, idealmente CHoCH down) -> SHORT",
    "V2 quebra-1H+15M+retest: quebra de estrutura confirmada 1H+15M seguida de retest ao nivel rompido -> SHORT",
    "SL = supply/nivel-rompido +0.1ATR (nunca teto fixo); target 3R fixo, gate de sinal RR>=2",
    "direcao vem da perna imediata 1H (nao do macro-1D lento); regime = contexto/size, nao veto de direcao"
  ],
  "nulls": ["permutation within-bucket", "feature-search null", "mining-null (best-of-K corrigido)"],
  "da_plan": "Agent tool adversarial: causalidade (close-only SHIFT1)/source(raw_reader)/runner/null/clustering/staleness; testar V1 vs V2 lado a lado sem cherry-pick",
  "outputs": [
    "research/xau_15m_short/results/short_events.csv",
    "research/xau_15m_short/results/short_backtest_panel.csv",
    "research/xau_15m_short/results/recall_report.json"
  ],
  "stop_conditions": [
    "source guard FAIL (leitura fora do raw_reader)",
    "bucket estrutural ausente no output (structural-first FAIL)",
    "recall do GT#1 < limiar prereg (GS3)",
    "capado usado como arbitro",
    "OOS/cross-asset proposto"
  ],
  "scripts": [
    "research/xau_15m_short/short_detector.py",
    "research/xau_15m_short/short_recall.py",
    "research/xau_15m_short/short_backtest.py"
  ]
}
```

## Prosa

**Estratégia / direção / universo / TF.** XAU 15M SHORT. Duas variantes de ENTRADA **pré-registadas e testadas lado a lado** (o mercado decide qual/ambas têm edge, não pré-escolhemos): **V1** teste-e-rejeição no íman superior (BB15M + cluster SVP15M + OB15M não-testado acima); **V2** quebra de estrutura 1H+15M + retest ao nível rompido. Universo = todos os candidatos SHORT etiquetados nos baldes-alvo, RAW 2024-05→2026-05 (2 anos multi-regime) + store para o recall-GT.

**RAW files / leitor.** 8 blocos 15M do `dataset_registry.json` (acima), lidos SEMPRE pelo **`raw_reader`** canónico (GS2). Sem derived files no arranque (o motor lê OB/SMC/SVP/Bubbles/NAS/RSI direto do RAW as-of via `RR.study/boxes/bubbles`).

**Multi-TF (Cris 2026-08-16):** **15M = TF principal de ENTRADA e validação de retestes**; **1H e 4H = CONTEXTO obrigatório** (não só 15M). O motor lê 15M para o gatilho/retest e 1H+4H para a moldura estrutural (regime, perna, OB/SMC/supply HTF). Tudo as-of via `raw_reader` (15M/1H/4H).

**Dados do GT (RESOLVIDO — Cris autorizou coleta):** o RAW replay acaba ~2026-05-25 e o GT#1 (13/08) é pós-dataset. Faz-se um **replay-collect da semana 08/2026** (`safe_backtest_window.sh --replay-collect`, com o preflight próprio) para o GT#1 ficar **DENTRO do RAW** — mais fiel. O block coletado entra em `raw_files` (PENDING até coletado). Backtest de expectância no RAW 2 anos + a semana coletada.

**Regime / perna / baldes (Stage 3, ANTES de indicadores) — MOTOR EXISTENTE (Cris 2026-08-16, não construir novo).** Cada candidato é etiquetado com o bucket estrutural pelo que **já existe**: **macro_regime** = Layer1 1D (`macro_structural_v3.build_layer1`) + regime 4H (regime-engine); **leg_state** = perna imediata 1H (`_leg_read`); **family** = bucket derivado desses. **Alvo do SHORT:** `RANGE_distribution_top_bear`, `BEAR_active`, `countertrend_bounce_in_bear` (primários) + `BULL_excess_top`, `BEAR_shallow_bounce` (cautela). **NUNCA shortar:** `BEAR_deep_capitulation` (território Cp), `BULL_impulse`, `RANGE_accumulation_bottom`. Direção do candidato = perna imediata 1H (não o macro-1D lento).

**Hipóteses (congeladas antes do cálculo, Stage 5).** V1 e V2 acima + SL supply+0.1ATR + 3R/RR≥2. Grid pré-registado no json; nada afinado ao dado visível.

**Nulls + DA.** Permutação intra-bucket, feature-search null, mining-null (best-of-K corrigido). DA adversarial via Agent tool: causalidade close-only SHIFT1, fonte=raw_reader, runner, clustering, staleness. V1 vs V2 comparadas sem cherry-pick.

**Recall-GT (GS3, Passo 2 — ANTES da expectância).** O detetor tem de recapturar o **GT#1 (13/08 retest 4406,5 → quebra 05:30 O4406,5→L4386,6 C4387,9 −18,6 → caiu a 4356)** + os casos do critério de aceitação, com recall ≥ limiar pré-registado. `short_recall.py` produz `recall_report.json {ts, threshold, recall, gt_total, gt_caught, detector}`. Sem isto, `short_backtest.py` está bloqueado por GS3.

**Outputs esperados.** `short_events.csv` (candidatos + bucket + variante), `short_backtest_panel.csv` (painel completo N·WR·sumR·avgR·DD·return/DD·streak·por-ano), `recall_report.json`.

**Critérios de parada (fail-loud).** Leitura fora do raw_reader · bucket ausente no output · recall<limiar · capado como árbitro · OOS/cross-asset proposto.

---
**DECISÕES SELADAS (Cris 2026-08-16):** (1) recall-gate GS3 = **`gt_caught==gt_total`** dos casos-âncora (estrito). (2) GT **dentro do RAW** via replay-collect da semana 08/2026 (autorizado). (3) bucket pelo **motor existente** (Layer1 1D + regime 4H + perna-1H); MTF **15M entrada + 1H/4H contexto**.

**PRÓXIMOS PASSOS (após selar):** Passo 1 RAW lineage (`check_xau_15m_raw_lineage`) → **replay-collect da semana 08/2026** (preflight próprio: enrich/evaluator ausentes, orphan server.js limpo, receiver+public /health, pause flag, XAU monitor loaded, confirmar chart symbol/TF/indicadores manualmente) → Passo 2 recall-gate (GT#1) → Passo 3 structural-first labeling (motor existente) → Passo 4-6 detetor V1/V2 → Passo 9 painel+null+DA. Nada corre até o manifest estar commitado.
