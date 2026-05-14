#!/usr/bin/env python3
"""Drill into BTC winner: brk_dec_b60_r12 + BTCD_strong_bull + tgt 2.5R + 3R."""
import sys
sys.path.insert(0, '.')
from audit_btc_v2_macro import (load_btc, load_macro_dxy, load_macro_btcd,
                                  attach_macro, htf_context, run_long,
                                  metrics, yearly, cost_sens,
                                  trg_breakout_decisive, has_base_trend,
                                  BTC_FILES, OUT_DIR)
import pandas as pd
import numpy as np

print("=== Loading ===")
data = {tf: load_btc(p) for tf, p in BTC_FILES.items()}
df4 = data['4H']
df_dxy = load_macro_dxy()
df_btcd = load_macro_btcd()
df4 = htf_context(df4, data['12H'], 'htf12h')
df4 = htf_context(df4, data['1D'], 'htf1d')
df4 = attach_macro(df4, df_dxy)
df4 = attach_macro(df4, df_btcd)

# Winner candidate signal
def sig_winner(df, i, row):
    if not trg_breakout_decisive(df, i, row, body=0.6, rng=1.2): return False
    if not row.get('btcd_strong_bull', False): return False
    return True

# Variants of winner
def sig_winner_dxy_bear(df, i, row):
    if not sig_winner(df, i, row): return False
    return row.get('dxy_bearish', False)

def sig_winner_dxy_strong(df, i, row):
    if not sig_winner(df, i, row): return False
    return row.get('dxy_strong_bear', False)

# Test multiple targets for winner family
print("\n=== Target sweep for sig_winner (brk_dec_b60_r12 + BTCD_strong_bull) ===")
for trg in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]:
    tr = run_long(df4, sig_winner, trg, 24, f'tgt{trg}R')
    m = metrics(tr)
    print(f'tgt{trg}R: n={m["n"]} PF={m["pf_net"]} avg={m["avg_r_net"]} no_top5={m["r_no_top5_net"]} no_top10={m["r_no_top10_net"]}')

# Best candidate: target 2.5R — detailed analysis
print("\n=== DEEP DIVE: sig_winner + target 2.5R ===")
tr = run_long(df4, sig_winner, 2.5, 24, 'sig_winner_tgt2.5R')
m = metrics(tr)
print(f"Metrics: {m}")
print(f"\nYearly:\n{yearly(tr).to_string(index=False)}")
print(f"\nCost sensitivity:\n{cost_sens(tr).to_string(index=False)}")

# Also target 3.0R for comparison
print("\n=== sig_winner + target 3.0R (alt) ===")
tr3 = run_long(df4, sig_winner, 3.0, 24, 'sig_winner_tgt3R')
m3 = metrics(tr3)
print(f"Metrics: {m3}")
print(f"\nYearly:\n{yearly(tr3).to_string(index=False)}")

# Add DXY layer to BTCD winner
print("\n=== ADDING DXY layer on top of winner (target 2.5R) ===")
for name, fn in [('+DXY_bear', sig_winner_dxy_bear), ('+DXY_strong_bear', sig_winner_dxy_strong)]:
    tr_d = run_long(df4, fn, 2.5, 24, f'sig_winner_{name}')
    m_d = metrics(tr_d)
    print(f'\n{name}: n={m_d["n"]} PF={m_d["pf_net"]} avg={m_d["avg_r_net"]} no_top5={m_d["r_no_top5_net"]} no_top10={m_d["r_no_top10_net"]} win={m_d["win_rate"]}')
    if m_d['n'] >= 10:
        print(yearly(tr_d).to_string(index=False))

# Save winner trades
tr = run_long(df4, sig_winner, 2.5, 24, 'WINNER_BTCD_strong_bull_brk_dec_b60_r12_tgt2.5R')
pd.DataFrame(tr).to_csv(OUT_DIR / 'BTC_winner_trades.csv', index=False)
print(f"\nSaved: BTC_winner_trades.csv ({len(tr)} trades)")
