# XAU 15M LAB — GATE MANIFEST (TEMPLATE)

> Copiar para `docs/architecture/XAU_15M_<LAB>_GATE_MANIFEST.md`, preencher o bloco ```json``` (machine-readable,
> lido pelos blockers) e a prosa. **Sem este manifest, os scripts do lab ABORTAM.** O bloco json é a autoridade;
> a prosa explica. Nenhum lab 15M começa sem manifest válido (`XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1`).

## Bloco machine-readable (obrigatório — 1º bloco ```json``` do ficheiro)

```json
{
  "lab_name": "XAU_15M_<LAB>",
  "strategy": "XAU 15M LONG|SHORT <engine>",
  "direction": "LONG",
  "universe": "N96 | <descricao>",
  "timeframe": "15M",
  "trade_ids": "todos | [1,2,...] | <fonte>",
  "raw_files": [
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/<file>.jsonl.gz"
  ],
  "derived_files": [
    {"path": "research/xau_15m_bb_nas_leonardo/primitives/<f>.primitives.json", "source_ref": "build_causal_primitives.py <raw>", "checksum": "PENDING"}
  ],
  "allow_resample": false,
  "htf_stale_declared": "htf_1D frozen 2026-05-24 / htf_4H 2026-06-09 | none",
  "fields": ["1D_px_vs_ema", "excess_rsi_htf", "..."],
  "structural_buckets": ["BULL_pullback", "BEAR_deep_capitulation", "management_do_not_filter"],
  "hypotheses": ["<hipotese pre-registada 1>"],
  "nulls": ["permutation within-bucket", "feature-search null", "mining-null"],
  "da_plan": "Agent tool adversarial: causalidade/source/runner/null/clustering/staleness",
  "outputs": ["research/xau_15m_bb_nas_leonardo/results/<lab>_results.csv"],
  "stop_conditions": ["N96 nao reproduz", "source guard FAIL", "HTF stale nao declarado", "bucket ausente"],
  "scripts": ["research/xau_15m_bb_nas_leonardo/<lab>_analysis.py"]
}
```

## Prosa obrigatória
- **Estratégia / direção / universo / timeframe.**
- **RAW files** (fonte de autoridade; HD externo) + **derived files** (com `source_ref` + `checksum`).
- **Source guard**: como se confirma RAW-first (script `check_xau_15m_raw_lineage.py`).
- **Campos usados** e porquê (causais).
- **Regime macro / perna / baldes estruturais** (Stage 3 antes de qualquer indicador).
- **Hipóteses** (congeladas antes do cálculo, Stage 5).
- **Nulls** apropriados + **plano de DA**.
- **Outputs esperados** (CSV/JSON pequenos).
- **Critérios de parada** (fail-loud).

## Regras
- `allow_resample=false` por default. Resample 15M→HTF como FONTE é proibido salvo autorização explícita declarada aqui.
- Todo `derived_file` exige `source_ref` + `checksum` (PENDING só antes do 1º run; depois preencher sha256).
- `htf_stale_declared` obrigatório se algum HTF é usado (declarar o freeze conhecido ou "none").
- `structural_buckets` só da lista canónica do protocolo §C.
