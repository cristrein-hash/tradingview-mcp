# GATE MANIFEST — XAU 15M HTF ANCHOR + OB CAUSAL READING (2026-07-09)

> Bloco de LEITURA (medidor contínuo, sem entry/backtest). Prereg:
> `research/xau_15m_structural_reading/reports/XAU_15M_HTF_ANCHOR_OB_PREREG.md`. Autorizado pelo Cris.

```json
{
  "lab_name": "xau_15m_htf_anchor_ob_reading",
  "strategy": "XAU 15M LONG — mapa de âncoras HTF (família BEAR) + verificação causal OB Detector 1H/30M (leitura contextual, sem estratégia)",
  "direction": "LONG",
  "timeframe": "15M",
  "raw_files": [
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-08-25_to_2024-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-11-25_to_2025-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1H/XAUUSD_60m_replay_2024-05-25_to_2025-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1H/XAUUSD_60m_replay_2025-05-25_to_2025-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1H/XAUUSD_60m_replay_2025-11-25_to_2026-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/30M/XAUUSD_30m_replay_2024-05-25_to_2024-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/30M/XAUUSD_30m_replay_2024-11-25_to_2025-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/30M/XAUUSD_30m_replay_2025-05-25_to_2025-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/30M/XAUUSD_30m_replay_2025-11-25_to_2026-05-25.jsonl.gz"
  ],
  "derived_files": [
    {
      "path": "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json",
      "source_ref": "GT manual do Cris via MCP 2026-07-07 (avaliação apenas, nunca feature)",
      "checksum": "sha256:8171b99d3ae5298116e71b2d8b34cd940a76201fe9283e068b843933954ae59f"
    },
    {
      "path": "/Users/cristrein/tradingview-mcp/research/xau_15m_structural_leg_engine/results/f0_bars_cache.jsonl",
      "source_ref": "derivação 1:1 dos 9 RAW 15M (loader F0, sha verificado ao ler)",
      "checksum": "sha256:e968f17ba15f3b08b4266f13c9e3ca9c6e62d020695fdf3288ff89ac0a72113b"
    }
  ],
  "allow_resample": true,
  "resample_clause": "1D price-agg INTERNA de closes 15M do RAW declarado (dias FECHADOS D-1) apenas para px_vs_ema1d e macro v5 — padrão canónico; OB/zonas lidos DIRETO dos RAW 30M/1H nativos (snapshot alive-at-T), NUNCA resample",
  "htf_stale_declared": "30M/1H congelam 2026-05-25 => marcas 2026-06-10/06-24/06-30 UNSCORABLE para OB (declarado por episódio); 1D price-agg interna cobre até 2026-07-03",
  "structural_buckets": ["BEAR_deep_capitulation", "BEAR_shallow_bounce", "BULL_pullback", "RANGE_accumulation_bottom", "countertrend_bounce_in_bear"],
  "emission_policy": "leitura apenas — nenhum evento/entry/backtest; medidor contínuo sem cortes; OB = evidência DENTRO de conjuntos estruturais já definidos (protocolo §C respeitado)",
  "outputs": [
    "/Users/cristrein/tradingview-mcp/research/xau_15m_structural_reading/results/htf_anchor_map_bear_result.json",
    "/Users/cristrein/tradingview-mcp/research/xau_15m_structural_reading/results/ob_causal_check_result.json"
  ],
  "claims_ledger": "/Users/cristrein/tradingview-mcp/research/xau_15m_structural_reading/claims_ledger.csv",
  "scripts": [],
  "stop_conditions": [
    "HD desmontado => BLOCKED sem fallback",
    "counts das familias != 26/4/12 no catálogo => STOP fail-loud",
    "qualquer necessidade de tuning pós-olhar => STOP (novo prereg)",
    "entry/backtest/producao/Telegram/broker => NUNCA (fora de escopo)"
  ]
}
```
