# XAU 15M SHORT — GATE MANIFEST

> Lab do **engine SHORT** (magnet-rejection). Aberto por ordem do Cris 2026-07-20. Segue
> `XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1`. Sem este manifest os blockers ABORTAM. O bloco json é a autoridade.
> Decisões de escopo do Cris (2026-07-20): **dataset = corpus histórico RAW 2024→2026-07-04**; os 3 casos
> recentes (4040 win, 2 sexta loss) = **forward EXPLORATORY** (não entram no número). GT = **mine-then-validate**
> (eu minero as 2 classes, Cris valida cego ao resultado).

## Bloco machine-readable (autoridade)

```json
{
  "lab_name": "XAU_15M_SHORT",
  "strategy": "XAU 15M SHORT magnet-rejection engine (NAO espelho do LONG)",
  "direction": "SHORT",
  "universe": "GT short-tops minerados do RAW 2024-05-25->2026-07-04 (2 classes: magnet-tested vs precipitate) + validados pelo Cris outcome-blind",
  "timeframe": "15M",
  "trade_ids": "GT a minerar (Stage 2) + 3 forward EXPLORATORY (2026-07-20 4040 win, 2026-07-17 2x SL)",
  "raw_files": [
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-08-25_to_2024-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-11-25_to_2025-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"
  ],
  "derived_files": [],
  "allow_resample": false,
  "htf_stale_declared": "none (BB/SVP/OB 15M sao nativos do RAW 15M; se contexto macro 1D/4H for usado no scan sera declarado o freeze la)",
  "fields": ["bb_upper_15m", "svp_value_area_high", "ob_supply_overhead_untested", "pos_in_up_leg", "is_leg_top", "choch_dn", "sell_initiative_bubbles_by_side", "reject_upper_wick", "post_climax_absorption"],
  "structural_buckets": ["BULL_excess_top", "RANGE_distribution_top_bear", "countertrend_bounce_in_bear", "BEAR_active", "BEAR_shallow_bounce", "BULL_impulse", "BULL_pullback", "management_do_not_filter"],
  "hypotheses": [
    "H1: dentro de BULL_excess_top uniao RANGE_distribution_top_bear uniao countertrend_bounce_in_bear, um top com IMAN TESTADO E REJEITADO tem hit-2R SHORT materialmente maior que tops sem teste (a classe precipitada)",
    "H2: shorts precipitados (sem teste de iman, BULL_impulse/pullback) sao <= null / negativos (o engine RECUSA sexta)",
    "H3: entry no PRECO da rejeicao (magnet-anchored, intrabar) da >=2R onde o entry close-only da <2R nos mesmos eventos (o mecanismo 4040), com direcao constante",
    "H4: rejeicoes com iniciativa vendedora presente batem rejeicoes sem iniciativa (auction necessario, nao decorativo)",
    "H5: o lift vem da ORDEM estrutura->iman->auction; nenhum indicador isolado separa win/loss dentro do evento (teto esperado, testavel contra a parede LONG)"
  ],
  "nulls": ["permutation within-bucket", "feature-search null", "mining-null", "random-entry-in-same-regime (guarda anti-beta = licao L2/BPT)"],
  "da_plan": "Agent tool adversarial LOOKAHEAD-ONLY: known_at/born_t em todo iman/OB/SVP/bubble; certificar nivel PRE-DECLARADO antes do fill intrabar (nao lookahead); SL-first first-touch no backtest; closed-bar candles; recede-one-day em contexto HTF/1D",
  "outputs": [
    "research/xau_15m_short/results/short_gt_candidates.csv",
    "research/xau_15m_short/results/short_gt_structural.csv",
    "research/xau_15m_short/claims_ledger.csv"
  ],
  "stop_conditions": [
    "GT insuficiente (<30 validos + <15 traps) => output so EXPLORATORY, sem painel numerico",
    "source guard FAIL (RAW lineage)",
    "iman nao born_t-gated (repaint) => discriminador infalsificavel",
    "nao bate random-entry-in-same-regime null => beta nao edge (label RISK_CONTROL/beta, nao ship)",
    "bucket macro_regime+leg_state+family ausente no results CSV",
    "entry intrabar sem nivel known_at antes do fill => fill-optimism artifact"
  ],
  "scripts": [
    "research/xau_15m_short/mine_short_tops.py",
    "research/xau_15m_short/short_engine.py"
  ]
}
```

## Prosa

**Estratégia / direção / universo / TF.** Engine SHORT 15M **magnet-rejection** — dispara na **teste-e-rejeição no
íman superior** (BB 15M + SVP value-area-high + OB supply overhead não-testado), em perna de alta **madura/
exausta**, com **iniciativa vendedora** na rejeição, entry **no preço da rejeição** (não no fecho tardio).
**NÃO é espelho do LONG; regime = contexto/roteador, nunca direção automática.** Universo = GT short-tops
minerados do RAW histórico + validados pelo Cris; 3 casos recentes = forward.

**RAW files.** 9 blocos `.jsonl.gz` no HD externo (2024-05-25 → 2026-07-04), com OB detector v11 + SMC + NAS +
Bubbles + RSI + BB + SVP a cada barra 15M nativa. **PROIBIDO primitives / SLIM / resample HTF** (ordem Cris
2026-07-09 `feedback_no_primitives_raw_hd_only`): a mineração lê o **RAW original direto**, extração das
features na barra. `derived_files=[]`, `allow_resample=false`.

**Source guard.** `python scripts/safety/check_xau_15m_raw_lineage.py --manifest <este>` → `RAW_LINEAGE_PASS`.

**Baldes estruturais (Stage 3 antes de indicador).** Cada evento GT (válido E trap) é atribuído a UM balde
canónico ao `known_at`, produzindo `trade_id, entry_time, macro_regime, leg_state, regime_phase,
position_in_leg, family_label, causal_regime_source`. 4040→`BULL_excess_top`; sexta→`BULL_impulse/pullback`
(traps que o engine recusa). Codificar win e traps em baldes **diferentes** = o jogo todo.

**Hipóteses.** H1-H5 congeladas acima (Stage 5), antes de qualquer cálculo.

**Nulls + DA.** random-entry-in-same-regime (guarda anti-beta, a lição que matou o "edge" do L2/BPT) +
permutation intra-bucket + feature-search/mining null + jackknife por-ano + distribuição de streak (FN).
DA = só-lookahead via Agent tool real.

**Outputs.** CSVs pequenos (candidatos, estrutural, ledger). Report `docs/architecture/XAU_15M_SHORT_ROUND_<data>.md`.

**Critérios de parada (fail-loud).** Ver `stop_conditions` no json. **Ceiling risk declarado:** o LONG 15M
capou em ~10% precisão (features de trajetória não separam win/loss); se o íman-teste não bater os nulls,
o engine é rotulado `EXPLORATORY`/assist-only, não é promovido.

## STOP points (Cris decide)
1. ✅ Escopo + fonte (feito 2026-07-20). 2. Suficiência do GT (~30 val + ~15 trap) antes de número.
3. Aprovação do congelamento de hipóteses. 4. Promoção a runtime.

## Estado
`STAGE_1_MANIFEST` — criado 2026-07-20. Próximo: source guard + Stage 2 (mineração das 2 classes, `mine_short_tops.py`).
