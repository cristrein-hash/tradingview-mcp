# XAU 15M A1A2 FUNDO DETECTOR — GATE MANIFEST

> Lab autorizado por Cris 2026-07-17 ("ABRE AGORA... indicadores principais no estágio correto, SÓ
> pós-estrutura e contexto"). Objetivo: mecanizar a deteção dos fundos A1/A2 (hoje discricionários) —
> a hipótese-mãe é que o discriminador mora na TRAJETÓRIA SEQUENCIAL do pullback (como no Cp e no RWS),
> não nas features snapshot já esgotadas (teto MON+FORTE ~10%). Template: BOTTOM_ENGINE_LOGIC_REFERENCE
> (estrutura → contexto → confluência, select-event-first). Protocolo: XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1.

## Bloco machine-readable (obrigatório — 1º bloco json do ficheiro)

```json
{
  "lab_name": "XAU_15M_A1A2_FUNDO_DETECTOR",
  "strategy": "XAU 15M LONG A1/A2 pullback-bottom detector (mecanização do fundo discricionário)",
  "direction": "LONG",
  "universe": "swing-lows fractais m=3 confirmados em macro-1D BULL (macro_structural_v3) dentro da cobertura RAW 15M 2024-05-25..2026-05-25; positivos = GT A1 (14) + A2 (18) de REGIME_GT_FUNDOS_UNIFIED_20260714.json; negativos = swing-lows do MESMO bucket estrutural que não são GT",
  "timeframe": "15M",
  "trade_ids": "GT unificado: my-strategy/research/revalidation/results/REGIME_GT_FUNDOS_UNIFIED_20260714.json (61 fundos; alvo classe A: A1_pullback_fundo=14, A2_pullback_raso=18)",
  "raw_files": [
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-08-25_to_2024-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-11-25_to_2025-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz"
  ],
  "derived_files": [],
  "allow_resample": false,
  "htf_stale_declared": "toda a janela RAW termina 2026-05-25 (15M/4H/1D); nenhum dado live/pós-2026-05-25 entra no lab; HTF = RAW NATIVO 4H/1D do HD",
  "fields": ["ohlcv 15M", "bubbles BUY/SELL size1-3 (plots 0/2/4 e 6/8/10, com bars_ago; buffer causal 3b como no Cp)", "NAS top/bottom", "OB/demand-supply boxes (Custom OB baseline)", "RSI", "volume", "ATR", "macro_structural_v3(1D)", "leg 4H v3"],
  "structural_buckets": ["BULL_pullback", "BULL_impulse"],
  "hypotheses": [
    "H1 (acumulação sequencial): a acumulação/absorção de bubbles ao longo do PULLBACK (janelas multi-barra estilo RWS buy_recent/Cp act_dens cumulativo, causal) separa fundos GT A1/A2 dos swing-lows não-GT do MESMO bucket",
    "H2 (micro-forma do turno): a sequência barra-a-barra da viragem (velocidade da queda, contração de range, sequência de rejeições/wicks, velocidade do reclaim) separa GT de não-GT",
    "H3 (retest-da-escada): fundo GT coincide com retest de degrau anterior da escada de markup (direção PLT/DM 15/8) mais frequentemente que não-GT",
    "H4 (indicadores PÓS-estrutura, ordem do Cris): RSI/NAS/OB-demand/SVP avaliados DENTRO do bucket, DEPOIS de estrutura+contexto, acrescentam discriminação incremental sobre H1-H3 — nunca como filtro global"
  ],
  "nulls": ["permutation within-bucket (swing-lows do mesmo bucket BULL_pullback)", "feature-search null (nº de features/janelas testadas)", "mining-null"],
  "da_plan": "Agent tool adversarial: causalidade (known_at/buffer bubbles, fractal confirm p+3, close-only), source guard, runner, null adequado, clustering temporal dos GT, staleness",
  "outputs": ["my-strategy/research/revalidation/a1a2_fundo_lab/results/a1a2_bucket_table.csv", "my-strategy/research/revalidation/a1a2_fundo_lab/results/a1a2_seq_features.csv", "my-strategy/research/revalidation/a1a2_fundo_lab/results/a1a2_discrimination.csv", "my-strategy/research/revalidation/a1a2_fundo_lab/results/a1a2_claims_ledger.csv"],
  "stop_conditions": ["source guard FAIL", ">30% dos GT A1/A2 fora da cobertura RAW 15M", "bucket estrutural ausente antes de indicator scan", "macro/leg reconstruído contradiz macro/leg do GT em >20% dos fundos", "qualquer número reportado sem claim no ledger"],
  "scripts": ["my-strategy/research/revalidation/a1a2_fundo_lab/s0_source_map.py", "my-strategy/research/revalidation/a1a2_fundo_lab/s1_structural_bucket.py", "my-strategy/research/revalidation/a1a2_fundo_lab/s2_sequential_features.py", "my-strategy/research/revalidation/a1a2_fundo_lab/s3_discrimination.py"]
}
```

## Prosa

- **Estratégia/objetivo:** mecanizar o fundo A1 (pullback-reteste-corretivo) e A2 (pullback-raso continuação)
  — a única camada do stack 15M LONG ainda discricionária (Cp/B já têm candidato mecânico validado). O gatilho
  de entrada (MB3 + SL low-real + 3R, aprovado 2026-07-15) encaixa por cima do detetor validado; nada se perde.
- **RAW-first:** só os ficheiros listados (HD externo, registry+manifests+sha). ZERO primitives, ZERO resample,
  ZERO dados live. HTF = RAW nativo 4H/1D.
- **Source guard:** `scripts/safety/check_xau_15m_raw_lineage.py` tem de dar RAW_LINEAGE_PASS antes de qualquer medição.
- **Estrutura primeiro (Stage 3):** tabela obrigatória por evento (GT e candidatos): t, macro_regime
  (macro_structural_v3 sobre RAW 1D), leg_state (leg 4H v3 sobre RAW 4H), position_in_leg, family_label,
  causal_regime_source. Indicator scan ABORTA sem esta tabela (`check_xau_15m_structural_first.py`).
- **Select-event-first:** o universo de comparação são swing-lows fractais confirmados DENTRO do bucket
  BULL_pullback — nunca barras soltas nem médias globais.
- **Indicadores (H4) só DENTRO do bucket, pós H1-H3** — ordem explícita do Cris 2026-07-17.
- **Hipóteses congeladas** neste manifest ANTES de qualquer cálculo (Stage 5). Qualquer hipótese nova = emenda
  declarada aqui, com contagem de looks no ledger.
- **Critério honesto de sucesso:** assinatura causal que recupere fração material dos 32 GT (recall) com
  precisão que bata os nulls dentro do bucket — números exatos a fixar ANTES do s3 no claims ledger, não depois.
  Desfecho "resíduo discricionário confirmado" é resultado válido.
- **Árbitro final:** forward (prereg A1_MB3 já congelado; ≥20 resolvidos).

## EMENDA Stage 3 (2026-07-17, declarada) — universo estrutural real
`s1_structural_bucket.py` (32/32 GT em cobertura, 32/32 casados a fractal ±6h, cross-check macro **0/32
contradições** = reconstrução idêntica ao GT). Achado: os 32 A1/A2 dividem-se em **BULL_impulse=17 /
BULL_pullback=15** (macro/leg: IMPULSO_UP 17, ACUMULACAO 11, PULLBACK_BEAR 4) — A2 raso ocorre dentro de
pernas de impulso. **Universo do lab corrigido de `[BULL_pullback]` → `[BULL_pullback, BULL_impulse]`**
(ambos macro==BULL). Base rate = 32 positivos em ~2220 fractais macro-BULL (BULL_pullback 1327 + BULL_impulse
893) ≈ **1,4%** — o alvo de discriminação da assinatura sequencial. Nenhuma stop condition disparada.
