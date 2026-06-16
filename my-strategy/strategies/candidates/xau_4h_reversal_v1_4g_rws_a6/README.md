# V1.4g-RWS-A6 — XAU 4H REVERSAL_LONG Official Candidate

Adopted 2026-06-03. See full memory: `~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/project_xau_4h_reversal_v1_4g_rws_a6.md`.

## Datasets (persistent copies)

- `v1_base_trades_2016_2026.jsonl` — V1 trigger union (1163 trades, full main_state)
- `v14g_rws_enriched_2016_2026.jsonl` — 187 V1.4g-RWS trades with 30+ derived features attached (bubble cluster, RSI velocity, NAS dist, SMC freshness, absorption depth)
- `v14g_rws_2023plus_with_a6_flag.jsonl` — 58 2023+ trades with `cut_by_a6` flag

## Strategy rule (in pseudo-code)

```python
def is_entry_v14g_rws_a6(state):
    # V1 trigger union (T1-T6) + risk_atr ≥ 0.887 + n_triggers ≤ 2  [already in V1 base file]
    
    # Bubble + range_middle filter
    if not state.bubble_buy_recent: return False
    if abs(state.nearest_supply_dist - state.nearest_demand_dist) / 2 <= 0.5 * state.atr14:
        return False  # V5 range middle reject
    
    # RWS filter
    if not state.rsi_above_ma_4h and state.nearest_supply_dist > 2 * state.atr14:
        return False  # rsi weak + supply far
    
    # A6 filter (with NAS rescue)
    burst = state.buy_recent_2_bubbles - state.buy_older_3_bubbles
    if burst >= 3 and state.large_buy_in_win8 == 0:
        if state.nas_recent_short_bars != 0:
            return False  # burst suspect without NAS rescue
    
    return True
```

## Metrics summary

- n=182, WR 65.4%, sumR +137.2R, streak 4, DD 4.4R
- 100% monumentals ≥5R MFE preserved (15/15)
- 100% monumentals ≥10R MFE preserved (4/4)
- Walk-forward 3/3 FundedNext rigorous

## Plot script

`plot_script.py` — canonical TradingView plot (long_position with stopLevel/profitLevel). 58 2023+ trades plotted: kept ✓ in green/red/amber, A6-cut ✗ in magenta.

## Next steps

1. Implement in `monitor_xau_4h_strategies.py` as a new strategy
2. Shadow paper 30-60 days
3. Compare live signal stream vs backtest expectation
4. Promote to live execution only after shadow validation
