#!/usr/bin/env python3
"""Diagnostico honesto do REGIME SEQUENCIAL RSI/EMA: testa condicoes soltas e o INVERSO,
para verificar se o regime separa em ALGUMA direcao (mantendo causalidade <=j)."""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import RSI, EMA, N, ENTRIES, score
from wf_cand_rsi_ema_regime import rsi_ma_at, frac_rsi_above_ma, ema_slope_up


def scan(label, pred):
    keep = set()
    undef = 0
    for e in ENTRIES:
        r = pred(e)
        if r is None:
            undef += 1
            continue
        if r:
            keep.add(e["n"])
    sc = score(keep)
    print(f"{label:52s} N={sc['N_kept']:2d} hit3r={sc['hit3r_kept']:.3f} "
          f"poison={sc['poison_ratio']:.2f} wc={sc['winners_cut']} lc={sc['losers_cut']} "
          f"y25={sc['y2025']} y26={sc['y2026']} undef={undef}")
    return sc


print("BASE:", score([e["n"] for e in ENTRIES]))
print()
print("--- so EMA21 slope up nas ultimas K barras (mantem) ---")
for K in (5, 8, 10, 12, 16, 20):
    scan(f"ema_slope_up K={K}", lambda e, K=K: ema_slope_up(e["j"], K))

print("\n--- so RSI sustentado acima da MA (frac>=thr) ---")
for K in (8, 12, 16):
    for f in (0.5, 0.6, 0.7):
        scan(f"frac_rsi_above K={K} f={f}", lambda e, K=K, f=f:
             (lambda v: None if v is None else v >= f)(frac_rsi_above_ma(e["j"], K, 14)))

print("\n--- INVERSO: regime NAO-up = pullback/momentum-down (mantem) ---")
for K in (8, 10, 12, 16, 20):
    scan(f"NOT ema_slope_up (EMA a descer/flat) K={K}",
         lambda e, K=K: (lambda s: None if s is None else (not s))(ema_slope_up(e["j"], K)))

print("\n--- INVERSO combinado: EMA a descer E RSI abaixo da MA (deep pullback) ---")
for K in (8, 12, 16):
    for f in (0.4, 0.5):
        def pred(e, K=K, f=f):
            s = ema_slope_up(e["j"], K)
            fa = frac_rsi_above_ma(e["j"], K, 14)
            if s is None or fa is None:
                return None
            return (not s) and (fa <= f)
        scan(f"deep_pullback K={K} frac<= {f}", pred)
