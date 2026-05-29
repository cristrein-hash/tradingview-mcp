# TradingView Trade Plotting Standard

## Purpose

Plot trades visually on TradingView for manual human review.

This is an operational task, not an architecture task.

## Default standard for XAUUSD 4H

- Symbol: `PEPPERSTONE:XAUUSD`
- Timeframe: 4H / 240
- Use TradingView visual position tool:
  - Long Position for long trades
  - Short Position for short trades if needed
- Entry at actual entry price
- Stop loss visible in red
- Take profit visible in green
- Position box wide enough to be readable
- Leave drawings visible for human inspection
- Do not take screenshots unless explicitly requested
- Do not create screenshot pipelines
- Do not create manifests unless explicitly requested
- Do not create new helper architecture for simple plotting

## Required safety gate

Before plotting:

1. Pause chart-controlling process if needed:
   - `com.cristrein.xau-4h-monitor-daemon`
2. Create pause flag if needed:
   - `/tmp/claude_recheck.paused`
3. Confirm chart:
   - `PEPPERSTONE:XAUUSD`
   - `240` / `4H`
4. Clear previous drawings only if requested or needed.
5. Plot requested trades.
6. Leave drawings on chart.
7. Do not restore/clean until operator confirms review is complete.

## Do not use

- loose horizontal lines as substitute for trade plotting
- confusing custom boxes
- extra labels
- `+0.5R` / `+1R` lines unless requested
- DEMAND/supply zones unless requested
- MFE/MAE drawings unless requested
- screenshots unless requested
- batch reports unless requested

## After user review

Only after user says the review is complete:

1. Clear drawings if requested.
2. Remove pause flag.
3. Restore/restart paused chart-controlling process.
4. Validate production health.

## Operating rule

Minimum safe execution.

For plotting:
`pause if needed → validate symbol/timeframe → draw trade positions → leave visible → stop`.

Do not turn plotting into architecture.
